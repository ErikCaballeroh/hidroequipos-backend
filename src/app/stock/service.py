import uuid
from datetime import datetime, timezone
import resend
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.stock.models import Product, Department, Supplier, BranchInventory, Order
from app.stock.schemas import InventoryItem, RestockRequest, StockFilter
from app.stock.exceptions import ProductNotFoundError, SupplierEmailNotFoundError
from app.stock.templates import generate_restock_email

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
