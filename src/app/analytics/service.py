"""Lógica de negocio del módulo de análisis.

Se reutilizan los helpers de filtrado de ventas para mantener las mismas reglas
(excluir cancelados y borrados, aplicar rango de fechas y sucursal).
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sales.models import SaleTicket, SaleTicketItem
from app.sales.schemas import SalesFilter
from app.sales.service import (  # noqa: F401
    DEFAULT_DAYS,
    _apply_base_filters,
    _apply_date_range,
    _apply_optional_dates,
    _validate_date_range,
)
from app.analytics.schemas import (
    MarginSummary,
    MarginTrendItem,
    ProfitByDepartmentItem,
    TopProfitableProductItem,
)


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Divide evitando ZeroDivisionError; devuelve 0.0 si el divisor es 0."""
    return float(numerator) / float(denominator) if denominator else 0.0


# ---------- Tema 1: Rentabilidad (márgenes y descuentos) ----------

async def get_margin_summary(
    db: AsyncSession, filter_params: SalesFilter
) -> MarginSummary:
    """KPIs de rentabilidad: ventas, ganancia, margen %, descuento y % descuento."""
    _validate_date_range(filter_params)

    query = select(
        func.coalesce(func.sum(SaleTicket.total), 0),
        func.coalesce(func.sum(SaleTicket.profit), 0),
        func.coalesce(func.sum(SaleTicket.discount), 0),
        func.coalesce(func.sum(SaleTicket.subtotal), 0),
    )
    query = _apply_base_filters(query, filter_params)
    query = _apply_optional_dates(query, filter_params)

    result = await db.execute(query)
    total_sales, total_profit, total_discount, subtotal = result.one()

    return MarginSummary(
        total_sales=total_sales,
        total_profit=total_profit,
        margin_pct=_safe_ratio(total_profit, total_sales),
        total_discount=total_discount,
        discount_pct=_safe_ratio(total_discount, subtotal),
    )


async def get_margin_trend(
    db: AsyncSession, filter_params: SalesFilter
) -> list[MarginTrendItem]:
    """Serie mensual de ventas, ganancia y margen % para ver la tendencia."""
    _validate_date_range(filter_params)

    month_expr = func.substr(SaleTicket.sold_at, 1, 7)  # 'YYYY-MM'

    query = select(
        month_expr.label("period"),
        func.coalesce(func.sum(SaleTicket.total), 0),
        func.coalesce(func.sum(SaleTicket.profit), 0),
    )
    query = _apply_base_filters(query, filter_params)
    query = _apply_optional_dates(query, filter_params)
    query = query.group_by(month_expr).order_by(month_expr)

    result = await db.execute(query)
    return [
        MarginTrendItem(
            period=period,
            total_sales=total,
            total_profit=profit,
            margin_pct=_safe_ratio(profit, total),
        )
        for period, total, profit in result.all()
    ]


async def get_profit_by_department(
    db: AsyncSession, filter_params: SalesFilter
) -> list[ProfitByDepartmentItem]:
    """Ganancia y margen agrupados por departamento (categoría) del artículo."""
    _validate_date_range(filter_params)

    sales_expr = func.coalesce(
        func.sum(SaleTicketItem.quantity * SaleTicketItem.unit_price), 0
    )
    profit_expr = func.coalesce(func.sum(SaleTicketItem.profit), 0)
    dept_expr = func.coalesce(SaleTicketItem.department, "Sin departamento")

    query = (
        select(dept_expr.label("dept"), sales_expr, profit_expr)
        .join(SaleTicket, SaleTicket.uuid == SaleTicketItem.ticket_uuid)
        .where(SaleTicketItem.deleted_at.is_(None))
    )
    query = _apply_base_filters(query, filter_params)
    query = _apply_optional_dates(query, filter_params)
    query = query.group_by(dept_expr).order_by(profit_expr.desc())

    result = await db.execute(query)
    return [
        ProfitByDepartmentItem(
            department=dept,
            total_sales=sales,
            total_profit=profit,
            margin_pct=_safe_ratio(profit, sales),
        )
        for dept, sales, profit in result.all()
    ]


async def get_top_profitable_products(
    db: AsyncSession, filter_params: SalesFilter, limit: int = 10
) -> list[TopProfitableProductItem]:
    """Productos que más ganancia dejan (no por volumen, sino por ganancia)."""
    _validate_date_range(filter_params)

    sales_expr = func.coalesce(
        func.sum(SaleTicketItem.quantity * SaleTicketItem.unit_price), 0
    )
    profit_expr = func.coalesce(func.sum(SaleTicketItem.profit), 0)

    query = (
        select(
            SaleTicketItem.product_code,
            SaleTicketItem.product_name,
            profit_expr,
            sales_expr,
        )
        .join(SaleTicket, SaleTicket.uuid == SaleTicketItem.ticket_uuid)
        .where(SaleTicketItem.deleted_at.is_(None))
    )
    query = _apply_base_filters(query, filter_params)
    query = _apply_optional_dates(query, filter_params)
    query = (
        query.group_by(
            SaleTicketItem.product_code, SaleTicketItem.product_name
        )
        .order_by(profit_expr.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return [
        TopProfitableProductItem(
            product_code=code,
            product_name=name,
            total_profit=profit,
            total_sold=sales,
            margin_pct=_safe_ratio(profit, sales),
        )
        for code, name, profit, sales in result.all()
    ]
