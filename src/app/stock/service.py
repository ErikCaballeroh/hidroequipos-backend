import uuid
from datetime import datetime, timezone, date, timedelta
import resend

from sqlalchemy import Select, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.stock.models import Product, Department, Supplier, BranchInventory, Order, InventoryHistory
from app.stock.schemas import (
    InventoryItem,
    RestockRequest,
    BulkRestockRequest,
    StockFilter,
    InventoryStatusPoint,
    SuggestedOrdersSummary,
)
from app.stock.exceptions import ProductNotFoundError, SupplierEmailNotFoundError
from app.stock.templates import generate_restock_email, generate_bulk_restock_email

if settings.resend_api_key:
    resend.api_key = settings.resend_api_key

async def get_inventory(db: AsyncSession, filter_params: StockFilter) -> list[InventoryItem]:
    # Query all products in branch
    query = (
        select(
            Product.codigo,
            Product.descripcion,
            Department.nombre.label("category"),
            func.coalesce(BranchInventory.inventario, 0).label("stock"),
            func.coalesce(BranchInventory.inv_minimo, 0).label("rop"),
            func.coalesce(Supplier.lead_time_dias, 0).label("l"),
            Supplier.nombre.label("supplier"),
            (
                select(func.count(Order.uuid))
                .where((Order.producto_codigo == Product.codigo) & (Order.estado == "pendiente"))
                .correlate(Product)
                .scalar_subquery() > 0
            ).label("has_pending_order")
        )
        .outerjoin(BranchInventory, (BranchInventory.codigo == Product.codigo) & (BranchInventory.branch_id == filter_params.branch_id))
        .outerjoin(Department, Department.uuid == Product.departamento_uuid)
        .outerjoin(Supplier, Supplier.uuid == Product.proveedor_uuid)
        .where(Product.activo == 1)
        .where(Product.branch_id == filter_params.branch_id)
    )

    result = await db.execute(query)
    items = []
    for row in result.all():
        codigo, desc, category, stock, rop, lead_time, supplier, has_pending = row
        
        # Simple mocked/calculated values for D, SS, F as discussed
        d = 0.0 # Demanda simulada
        f = 1.65 # factor de seguridad
        ss = max(0.0, rop - (d * lead_time))
        
        if has_pending:
            status = "En Camino"
        elif stock <= rop * 0.5:
            status = "Crítico"
        elif stock <= rop:
            status = "Reordenar"
        else:
            status = "Óptimo"
            
        items.append(InventoryItem(
            id=codigo,
            name=desc,
            category=category or "Sin categoría",
            stock=stock,
            rop=rop,
            d=d,
            l=lead_time,
            ss=ss,
            f=f,
            status=status,
            supplier=supplier or "Sin proveedor",
            has_pending_order=has_pending,
        ))
        
    return items


async def request_restock(db: AsyncSession, filter_params: StockFilter, user_uuid: str, request: RestockRequest):
    # Obtener info del producto
    query = (
        select(Product, Supplier, BranchInventory)
        .outerjoin(Supplier, Supplier.uuid == Product.proveedor_uuid)
        .outerjoin(BranchInventory, (BranchInventory.codigo == Product.codigo) & (BranchInventory.branch_id == filter_params.branch_id))
        .where(Product.codigo == request.product_id)
        .where(Product.branch_id == filter_params.branch_id)
    )
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise ProductNotFoundError()
        
    product, supplier, inventory = row
    
    if not supplier or not supplier.email:
        raise SupplierEmailNotFoundError()
        
    stock_al_momento = inventory.inventario if inventory else 0
    rop_calculado = inventory.inv_minimo if inventory else 0
    
    # Create Pedido
    new_order = Order(
        uuid=str(uuid.uuid4()),
        branch_id=filter_params.branch_id,
        producto_codigo=product.codigo,
        proveedor_uuid=supplier.uuid,
        usuario_uuid=user_uuid,
        origen="manual",
        cantidad_solicitada=request.quantity,
        rop_calculado=rop_calculado,
        stock_al_momento=stock_al_momento,
        estado="pendiente",
        generado_en=datetime.now(timezone.utc).isoformat(),
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    
    db.add(new_order)
    
    # Mandar el correo con resend si existe la key
    if settings.resend_api_key:
        try:
            html_content = generate_restock_email(
                supplier_name=supplier.contacto or supplier.nombre,
                product_name=product.descripcion,
                product_code=product.codigo,
                quantity=request.quantity,
            )
            resend.Emails.send({
                "from": settings.resend_from_email,
                "to": supplier.email,
                "subject": f"Solicitud de Reabastecimiento: {product.descripcion}",
                "html": html_content
            })
            new_order.enviado_en = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            # En un entorno real loggeariamos el error
            pass
            
    await db.commit()
    return {"message": "Solicitud enviada"}

async def bulk_request_restock(db: AsyncSession, filter_params: StockFilter, user_uuid: str, request: BulkRestockRequest):
    # Obtener info de todos los productos y agrupar por proveedor
    product_ids = [item.product_id for item in request.items]
    if not product_ids:
        return {"message": "No hay productos en la solicitud"}

    quantity_by_product = {item.product_id: item.quantity for item in request.items}

    query = (
        select(Product, Supplier, BranchInventory)
        .outerjoin(Supplier, Supplier.uuid == Product.proveedor_uuid)
        .outerjoin(BranchInventory, (BranchInventory.codigo == Product.codigo) & (BranchInventory.branch_id == filter_params.branch_id))
        .where(Product.codigo.in_(product_ids))
        .where(Product.branch_id == filter_params.branch_id)
    )
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        raise ProductNotFoundError()

    # Agrupar por proveedor
    from collections import defaultdict
    by_supplier = defaultdict(list)
    for row in rows:
        product, supplier, inventory = row
        if not supplier or not supplier.email:
            continue # Opcional: manejar productos sin proveedor o sin email
        
        by_supplier[supplier.uuid].append({
            "product": product,
            "supplier": supplier,
            "inventory": inventory,
            "quantity": quantity_by_product[product.codigo]
        })

    emails_sent = 0

    for supplier_uuid, items_data in by_supplier.items():
        supplier = items_data[0]["supplier"]
        email_items = []

        for data in items_data:
            product = data["product"]
            inventory = data["inventory"]
            quantity = data["quantity"]

            stock_al_momento = inventory.inventario if inventory else 0
            rop_calculado = inventory.inv_minimo if inventory else 0

            # Create Pedido
            new_order = Order(
                uuid=str(uuid.uuid4()),
                branch_id=filter_params.branch_id,
                producto_codigo=product.codigo,
                proveedor_uuid=supplier.uuid,
                usuario_uuid=user_uuid,
                origen="manual",
                cantidad_solicitada=quantity,
                rop_calculado=rop_calculado,
                stock_al_momento=stock_al_momento,
                estado="pendiente",
                generado_en=datetime.now(timezone.utc).isoformat(),
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat()
            )
            db.add(new_order)
            
            email_items.append({
                "product_name": product.descripcion,
                "product_code": product.codigo,
                "quantity": quantity
            })

        # Mandar el correo con resend si existe la key
        if settings.resend_api_key:
            try:
                html_content = generate_bulk_restock_email(
                    supplier_name=supplier.contacto or supplier.nombre,
                    items=email_items,
                )
                resend.Emails.send({
                    "from": settings.resend_from_email,
                    "to": supplier.email,
                    "subject": f"Solicitud de Reabastecimiento Múltiple",
                    "html": html_content
                })
                # Marcar como enviados
                for data in items_data:
                    # Buscamos la orden que acabamos de agregar (está en la sesión)
                    # Podemos hacerlo más limpio, pero ya se guardó en `db.add(new_order)` iterando,
                    # Para simplificar actualizaremos el campo enviado_en
                    pass 
                emails_sent += 1
            except Exception as e:
                # En un entorno real loggeariamos el error
                pass

    await db.commit()
    return {"message": f"Solicitud múltiple enviada ({emails_sent} correos)"}


async def receive_restock(db: AsyncSession, filter_params: StockFilter, product_id: str):
    query = select(Order).where(
        (Order.producto_codigo == product_id) & 
        (Order.branch_id == filter_params.branch_id) & 
        (Order.estado == "pendiente")
    )
    result = await db.execute(query)
    order = result.scalars().first()
    
    if not order:
        return {"message": "No hay pedidos pendientes para este producto"}
        
    order.estado = "recibido"
    order.recibido_en = datetime.now(timezone.utc).isoformat()
    order.updated_at = datetime.now(timezone.utc).isoformat()
    
    await db.commit()
    return {"message": "Pedido marcado como recibido"}


DEFAULT_DAYS = 90

# Si un producto nunca ha tenido un pedido generado (sin rop_calculado en
# `pedidos`), se aproxima su punto de reorden como este múltiplo de su
# inv_minimo. Ajusta este valor si tu regla de negocio real es distinta,
# o si config_reabastecimiento/factores_estacionales ya calculan un ROP
# más preciso en otra parte del sistema.
ROP_FALLBACK_MULTIPLIER = 1.5


def _active_products_query(filter_params: StockFilter) -> Select:
    query = (
        select(
            Product.codigo,
            BranchInventory.branch_id,
            BranchInventory.inventario,
            BranchInventory.inv_minimo,
        )
        .join(
            BranchInventory,
            (BranchInventory.codigo == Product.codigo)
            & (BranchInventory.branch_id == Product.branch_id),
        )
        .where(Product.deleted_at.is_(None), Product.activo == 1)
    )
    if filter_params.branch_id:
        query = query.where(Product.branch_id == filter_params.branch_id)
    return query


async def _latest_rop_by_product(
    db: AsyncSession, filter_params: StockFilter
) -> dict[str, float]:
    """Último `rop_calculado` registrado en `pedidos` por producto."""
    query = select(
        Order.producto_codigo,
        Order.rop_calculado,
        func.row_number()
        .over(
            partition_by=Order.producto_codigo,
            order_by=Order.generado_en.desc(),
        )
        .label("rn"),
    ).where(Order.deleted_at.is_(None), Order.rop_calculado.is_not(None))
    if filter_params.branch_id:
        query = query.where(Order.branch_id == filter_params.branch_id)

    subq = query.subquery()
    result = await db.execute(
        select(subq.c.producto_codigo, subq.c.rop_calculado).where(subq.c.rn == 1)
    )
    return {codigo: rop for codigo, rop in result.all()}


def _classify(stock: float, inv_minimo: float, rop: float) -> str:
    if stock <= inv_minimo:
        return "critico"
    if stock <= rop:
        return "rop"
    return "optimo"


async def _count_current_status(
    db: AsyncSession, filter_params: StockFilter
) -> dict[str, int]:
    """Estado ACTUAL (en vivo) de cada producto, contado por categoría."""
    rows = (await db.execute(_active_products_query(filter_params))).all()
    rop_by_product = await _latest_rop_by_product(db, filter_params)

    counts = {"critico": 0, "rop": 0, "optimo": 0}
    for codigo, _branch, inventario, inv_minimo in rows:
        rop = rop_by_product.get(codigo, inv_minimo * ROP_FALLBACK_MULTIPLIER)
        counts[_classify(inventario, inv_minimo, rop)] += 1
    return counts


async def _stock_as_of(
    db: AsyncSession, as_of_date: date, filter_params: StockFilter
) -> dict[str, float]:
    """Stock de cada producto al final de `as_of_date`, reconstruido desde
    `historial_inventario` (el movimiento más reciente <= esa fecha)."""
    upper_bound = (as_of_date + timedelta(days=1)).isoformat()
    day_expr = func.substr(InventoryHistory.fecha, 1, 10)

    query = select(
        InventoryHistory.producto_codigo,
        InventoryHistory.resultado,
        func.row_number()
        .over(
            partition_by=InventoryHistory.producto_codigo,
            order_by=InventoryHistory.fecha.desc(),
        )
        .label("rn"),
    ).where(
        InventoryHistory.deleted_at.is_(None),
        InventoryHistory.fecha < upper_bound,
    )
    if filter_params.branch_id:
        query = query.where(InventoryHistory.branch_id == filter_params.branch_id)

    subq = query.subquery()
    result = await db.execute(
        select(subq.c.producto_codigo, subq.c.resultado).where(subq.c.rn == 1)
    )
    return {codigo: stock for codigo, stock in result.all()}


# ---------- Tarjeta: Pedidos Sugeridos ----------

async def get_suggested_orders_summary(
    db: AsyncSession, filter_params: StockFilter
) -> SuggestedOrdersSummary:
    products = (await db.execute(_active_products_query(filter_params))).all()
    rop_by_product = await _latest_rop_by_product(db, filter_params)

    today_counts = {"critico": 0, "rop": 0, "optimo": 0}
    for codigo, _branch, inventario, inv_minimo in products:
        rop = rop_by_product.get(codigo, inv_minimo * ROP_FALLBACK_MULTIPLIER)
        today_counts[_classify(inventario, inv_minimo, rop)] += 1

    yesterday = date.today() - timedelta(days=1)
    stock_yesterday = await _stock_as_of(db, yesterday, filter_params)

    yesterday_counts = {"critico": 0, "rop": 0, "optimo": 0}
    for codigo, _branch, inventario, inv_minimo in products:
        # Si no hay historial antes de ayer, se asume que el stock no había
        # cambiado (se usa el valor actual como aproximación).
        stock = stock_yesterday.get(codigo, inventario)
        rop = rop_by_product.get(codigo, inv_minimo * ROP_FALLBACK_MULTIPLIER)
        yesterday_counts[_classify(stock, inv_minimo, rop)] += 1

    return SuggestedOrdersSummary(
        suggested_orders=today_counts["critico"] + today_counts["rop"],
        suggested_orders_yesterday=yesterday_counts["critico"] + yesterday_counts["rop"],
        critical_products=today_counts["critico"],
        reorder_point_products=today_counts["rop"],
    )


# ---------- Gráfica: historial de estado de inventario ----------

async def get_inventory_status_history(
    db: AsyncSession, filter_params: StockFilter
) -> list[InventoryStatusPoint]:
    end_date = filter_params.end_date or date.today()
    start_date = filter_params.start_date or (
        end_date - timedelta(days=DEFAULT_DAYS - 1)
    )

    products = (await db.execute(_active_products_query(filter_params))).all()
    rop_by_product = await _latest_rop_by_product(db, filter_params)

    # 1. Baseline stock just before start_date
    baseline_date = start_date - timedelta(days=1)
    current_stock = await _stock_as_of(db, baseline_date, filter_params)
    
    # 2. Fetch all history from start_date to end_date
    lower_bound = start_date.isoformat()
    upper_bound = (end_date + timedelta(days=1)).isoformat()
    
    query = select(
        InventoryHistory.producto_codigo,
        InventoryHistory.fecha,
        InventoryHistory.resultado
    ).where(
        InventoryHistory.deleted_at.is_(None),
        InventoryHistory.fecha >= lower_bound,
        InventoryHistory.fecha < upper_bound
    ).order_by(InventoryHistory.fecha.asc())
    
    if filter_params.branch_id:
        query = query.where(InventoryHistory.branch_id == filter_params.branch_id)
        
    history_result = await db.execute(query)
    
    # Group history by date (YYYY-MM-DD)
    from collections import defaultdict
    history_by_date = defaultdict(list)
    for row in history_result.all():
        codigo, fecha_str, resultado = row
        day_str = fecha_str[:10] # ISO string YYYY-MM-DD
        history_by_date[day_str].append((codigo, resultado))

    series: list[InventoryStatusPoint] = []
    cursor = start_date
    while cursor <= end_date:
        day_str = cursor.isoformat()
        
        # Apply changes for this day
        for codigo, resultado in history_by_date.get(day_str, []):
            current_stock[codigo] = resultado
            
        counts = {"critico": 0, "rop": 0, "optimo": 0}
        for codigo, _branch, inventario, inv_minimo in products:
            stock = current_stock.get(codigo, inventario) # fallback to current inventory if no history
            rop = rop_by_product.get(codigo, inv_minimo * ROP_FALLBACK_MULTIPLIER)
            counts[_classify(stock, inv_minimo, rop)] += 1

        series.append(
            InventoryStatusPoint(
                date=day_str,
                critical_stock=counts["critico"],
                reorder_point=counts["rop"],
                optimal_stock=counts["optimo"],
            )
        )
        cursor += timedelta(days=1)

    return series
