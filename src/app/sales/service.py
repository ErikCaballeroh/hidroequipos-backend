from datetime import date, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sales.exceptions import InvalidDateRangeError
from app.sales.models import SaleTicket, SaleTicketItem
from app.sales.schemas import (
    DailySaleItem,
    PaymentMethodItem,
    RecentTicketItem,
    SalesFilter,
    TopProductItem,
)

DEFAULT_DAYS = 30


def _validate_date_range(filter_params: SalesFilter) -> None:
    if (
        filter_params.start_date
        and filter_params.end_date
        and filter_params.start_date > filter_params.end_date
    ):
        raise InvalidDateRangeError()


def _apply_base_filters(query: Select, filter_params: SalesFilter) -> Select:
    """Only real sales: not cancelled, not soft-deleted."""
    query = query.where(
        SaleTicket.deleted_at.is_(None),
        SaleTicket.is_cancelled == 0,
    )
    if filter_params.branch_id:
        query = query.where(SaleTicket.branch_id == filter_params.branch_id)
    return query


def _apply_date_range(
    query: Select, start_date: date, end_date: date
) -> Select:
    # Se usa < (día siguiente) en lugar de <= para cubrir todo el último día
    upper_bound = (end_date + timedelta(days=1)).isoformat()
    return query.where(
        SaleTicket.sold_at >= start_date.isoformat(),
        SaleTicket.sold_at < upper_bound,
    )


def _apply_optional_dates(
    query: Select, filter_params: SalesFilter
) -> Select:
    if filter_params.start_date:
        query = query.where(
            SaleTicket.sold_at >= filter_params.start_date.isoformat()
        )
    if filter_params.end_date:
        upper_bound = (
            filter_params.end_date + timedelta(days=1)
        ).isoformat()
        query = query.where(SaleTicket.sold_at < upper_bound)
    return query


# ---------- 1. Line chart: daily sales & profit ----------

async def get_daily_sales(
    db: AsyncSession, filter_params: SalesFilter
) -> list[DailySaleItem]:
    """Daily time-series of sales totals and profit.

    Defaults to the last 30 days (including today) when no dates are given.
    """
    _validate_date_range(filter_params)

    end_date = filter_params.end_date or date.today()
    start_date = filter_params.start_date or (
        end_date - timedelta(days=DEFAULT_DAYS - 1)
    )

    day_expr = func.substr(SaleTicket.sold_at, 1, 10)  # 'YYYY-MM-DD'

    query = select(
        day_expr.label("day"),
        func.coalesce(func.sum(SaleTicket.total), 0),
        func.coalesce(func.sum(SaleTicket.profit), 0),
    )
    query = _apply_base_filters(query, filter_params)
    query = _apply_date_range(query, start_date, end_date)
    query = query.group_by(day_expr).order_by(day_expr)

    result = await db.execute(query)
    data = {
        day: (total, profit)
        for day, total, profit in result.all()
    }

    # Se rellenan los días sin ventas con 0 para que la gráfica no tenga huecos
    series: list[DailySaleItem] = []
    cursor = start_date
    while cursor <= end_date:
        key = cursor.isoformat()
        total, profit = data.get(key, (0, 0))
        series.append(
            DailySaleItem(date=key, total_sales=total, total_profit=profit)
        )
        cursor += timedelta(days=1)

    return series


# ---------- 2. Donut chart: payment methods ----------

async def get_payment_methods(
    db: AsyncSession, filter_params: SalesFilter
) -> list[PaymentMethodItem]:
    _validate_date_range(filter_params)

    query = select(
        SaleTicket.payment_method,
        func.coalesce(func.sum(SaleTicket.total), 0),
        func.count(SaleTicket.uuid),
    )
    query = _apply_base_filters(query, filter_params)
    query = _apply_optional_dates(query, filter_params)
    query = query.group_by(SaleTicket.payment_method)

    result = await db.execute(query)
    return [
        PaymentMethodItem(
            payment_method=method, total=total, ticket_count=count
        )
        for method, total, count in result.all()
    ]


# ---------- 3. Table: recent tickets ----------

async def get_recent_tickets(
    db: AsyncSession, filter_params: SalesFilter, limit: int = 10
) -> list[RecentTicketItem]:
    query = select(
        SaleTicket.folio,
        SaleTicket.total,
        SaleTicket.payment_method,
        SaleTicket.sold_at,
    )
    query = _apply_base_filters(query, filter_params)
    query = query.order_by(SaleTicket.sold_at.desc()).limit(limit)

    result = await db.execute(query)
    return [
        RecentTicketItem(
            folio=folio, total=total, payment_method=method, sold_at=sold_at
        )
        for folio, total, method, sold_at in result.all()
    ]


# ---------- 4. Table: top-selling products ----------

async def get_top_products(
    db: AsyncSession, filter_params: SalesFilter, limit: int = 10
) -> list[TopProductItem]:
    _validate_date_range(filter_params)

    query = (
        select(
            SaleTicketItem.product_code,
            SaleTicketItem.product_name,
            func.coalesce(func.sum(SaleTicketItem.quantity), 0),
            func.coalesce(
                func.sum(
                    SaleTicketItem.quantity * SaleTicketItem.unit_price
                ),
                0,
            ),
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
        .order_by(func.sum(SaleTicketItem.quantity).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return [
        TopProductItem(
            product_code=code,
            product_name=name,
            quantity_sold=qty,
            total_sold=total,
        )
        for code, name, qty, total in result.all()
    ]
