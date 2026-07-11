from datetime import date, timedelta

from sqlalchemy import Select, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.stock.models import BranchInventory, InventoryHistory, Order, Product
from app.stock.schemas import (
    InventoryStatusPoint,
    StockFilter,
    SuggestedOrdersSummary,
)

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

    series: list[InventoryStatusPoint] = []
    cursor = start_date
    while cursor <= end_date:
        stock_on_day = await _stock_as_of(db, cursor, filter_params)
        counts = {"critico": 0, "rop": 0, "optimo": 0}
        for codigo, _branch, inventario, inv_minimo in products:
            stock = stock_on_day.get(codigo, inventario)
            rop = rop_by_product.get(codigo, inv_minimo * ROP_FALLBACK_MULTIPLIER)
            counts[_classify(stock, inv_minimo, rop)] += 1

        series.append(
            InventoryStatusPoint(
                date=cursor.isoformat(),
                critical_stock=counts["critico"],
                reorder_point=counts["rop"],
                optimal_stock=counts["optimo"],
            )
        )
        cursor += timedelta(days=1)

    return series
