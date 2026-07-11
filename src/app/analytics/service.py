"""Lógica de negocio del módulo de análisis.

Se reutilizan los helpers de filtrado de ventas para mantener las mismas reglas
(excluir cancelados y borrados, aplicar rango de fechas y sucursal).
"""

from datetime import timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.models import Abono, Cliente
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
    AccountsReceivableItem,
    CreditVsPaymentsItem,
    CustomerSummary,
    MarginSummary,
    MarginTrendItem,
    ProfitByDepartmentItem,
    TopCustomerItem,
    TopProfitableProductItem,
)

# forma_pago que representa una venta a crédito.
CREDIT_METHOD = "credito"


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


# ---------- Tema 2: Clientes y crédito ----------

def _is_credit(query: Select) -> Select:
    """Filtra tickets cuya forma de pago es a crédito."""
    return query.where(func.lower(SaleTicket.payment_method) == CREDIT_METHOD)


def _apply_branch(query: Select, filter_params: SalesFilter, branch_col) -> Select:
    """Aplica solo el filtro de sucursal (para saldos acumulados sin rango)."""
    if filter_params.branch_id:
        query = query.where(branch_col == filter_params.branch_id)
    return query


async def _receivable_balance(
    db: AsyncSession, filter_params: SalesFilter
) -> float:
    """Saldo por cobrar acumulado = cargos a crédito - abonos (sin rango de fechas)."""
    charges_q = _is_credit(
        _apply_base_filters(
            select(func.coalesce(func.sum(SaleTicket.total), 0)), filter_params
        )
    )
    payments_q = _apply_branch(
        select(func.coalesce(func.sum(Abono.amount), 0)).where(
            Abono.deleted_at.is_(None)
        ),
        filter_params,
        Abono.branch_id,
    )
    charges = (await db.execute(charges_q)).scalar_one()
    payments = (await db.execute(payments_q)).scalar_one()
    return float(charges) - float(payments)


async def get_customer_summary(
    db: AsyncSession, filter_params: SalesFilter
) -> CustomerSummary:
    """KPIs de clientes: activos, ticket promedio, saldo por cobrar y % crédito."""
    _validate_date_range(filter_params)

    # Métricas dentro del rango seleccionado.
    base_q = _apply_optional_dates(
        _apply_base_filters(
            select(
                func.coalesce(func.sum(SaleTicket.total), 0),
                func.count(SaleTicket.uuid),
                func.count(func.distinct(SaleTicket.customer_uuid)),
            ),
            filter_params,
        ),
        filter_params,
    )
    total_sales, _ticket_count, active_customers = (await db.execute(base_q)).one()

    credit_q = _is_credit(
        _apply_optional_dates(
            _apply_base_filters(
                select(func.coalesce(func.sum(SaleTicket.total), 0)), filter_params
            ),
            filter_params,
        )
    )
    credit_total = (await db.execute(credit_q)).scalar_one()

    return CustomerSummary(
        active_customers=active_customers,
        avg_ticket_per_customer=_safe_ratio(total_sales, active_customers),
        receivable_balance=await _receivable_balance(db, filter_params),
        credit_sales_pct=_safe_ratio(credit_total, total_sales),
    )


async def get_top_customers(
    db: AsyncSession, filter_params: SalesFilter, limit: int = 10
) -> list[TopCustomerItem]:
    """Clientes que más compran (por importe) en el rango."""
    _validate_date_range(filter_params)

    total_expr = func.coalesce(func.sum(SaleTicket.total), 0)
    name_expr = func.coalesce(Cliente.nombre, "Cliente sin nombre")

    query = (
        select(
            SaleTicket.customer_uuid,
            name_expr,
            total_expr,
            func.count(SaleTicket.uuid),
        )
        .join(Cliente, Cliente.uuid == SaleTicket.customer_uuid)
    )
    query = _apply_base_filters(query, filter_params)
    query = _apply_optional_dates(query, filter_params)
    query = query.where(SaleTicket.customer_uuid.is_not(None))
    query = (
        query.group_by(SaleTicket.customer_uuid, name_expr)
        .order_by(total_expr.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return [
        TopCustomerItem(
            customer_uuid=uuid,
            customer_name=name,
            total=total,
            ticket_count=count,
        )
        for uuid, name, total, count in result.all()
    ]


async def get_credit_vs_payments(
    db: AsyncSession, filter_params: SalesFilter
) -> list[CreditVsPaymentsItem]:
    """Serie mensual: cargos a crédito (tickets) vs abonos recibidos."""
    _validate_date_range(filter_params)

    # Cargos a crédito por mes.
    charge_month = func.substr(SaleTicket.sold_at, 1, 7)
    charges_q = _is_credit(
        _apply_optional_dates(
            _apply_base_filters(
                select(
                    charge_month.label("period"),
                    func.coalesce(func.sum(SaleTicket.total), 0),
                ),
                filter_params,
            ),
            filter_params,
        )
    ).group_by(charge_month)

    # Abonos por mes.
    pay_month = func.substr(Abono.paid_at, 1, 7)
    payments_q = _apply_branch(
        select(
            pay_month.label("period"),
            func.coalesce(func.sum(Abono.amount), 0),
        ).where(Abono.deleted_at.is_(None)),
        filter_params,
        Abono.branch_id,
    )
    if filter_params.start_date:
        payments_q = payments_q.where(
            Abono.paid_at >= filter_params.start_date.isoformat()
        )
    if filter_params.end_date:
        upper = (filter_params.end_date + timedelta(days=1)).isoformat()
        payments_q = payments_q.where(Abono.paid_at < upper)
    payments_q = payments_q.group_by(pay_month)

    charges = {p: c for p, c in (await db.execute(charges_q)).all()}
    payments = {p: v for p, v in (await db.execute(payments_q)).all()}

    periods = sorted(set(charges) | set(payments))
    return [
        CreditVsPaymentsItem(
            period=period,
            credit_charges=charges.get(period, 0),
            payments=payments.get(period, 0),
        )
        for period in periods
    ]


async def get_accounts_receivable(
    db: AsyncSession, filter_params: SalesFilter, limit: int = 50
) -> list[AccountsReceivableItem]:
    """Saldo por cobrar por cliente (acumulado): cargos crédito - abonos."""
    # Cargos a crédito acumulados por cliente (sin rango de fechas).
    charges_q = _is_credit(
        _apply_base_filters(
            select(
                SaleTicket.customer_uuid,
                func.coalesce(func.sum(SaleTicket.total), 0),
            ),
            filter_params,
        )
    ).where(SaleTicket.customer_uuid.is_not(None)).group_by(SaleTicket.customer_uuid)

    # Abonos acumulados por cliente.
    payments_q = _apply_branch(
        select(
            Abono.customer_uuid,
            func.coalesce(func.sum(Abono.amount), 0),
        ).where(Abono.deleted_at.is_(None)),
        filter_params,
        Abono.branch_id,
    ).group_by(Abono.customer_uuid)

    charges = {c: v for c, v in (await db.execute(charges_q)).all()}
    payments = {c: v for c, v in (await db.execute(payments_q)).all()}

    customer_uuids = set(charges) | set(payments)
    if not customer_uuids:
        return []

    # Datos de los clientes involucrados (nombre y límite de crédito).
    clients_q = select(
        Cliente.uuid, Cliente.nombre, Cliente.credit_limit
    ).where(Cliente.uuid.in_(customer_uuids), Cliente.deleted_at.is_(None))
    clients = {
        uuid: (name, limit)
        for uuid, name, limit in (await db.execute(clients_q)).all()
    }

    items = []
    for uuid in customer_uuids:
        name, limit = clients.get(uuid, ("Cliente sin nombre", 0))
        charge = float(charges.get(uuid, 0))
        payment = float(payments.get(uuid, 0))
        items.append(
            AccountsReceivableItem(
                customer_uuid=uuid,
                customer_name=name,
                credit_limit=limit,
                charges=charge,
                payments=payment,
                balance=charge - payment,
            )
        )

    # Mayor saldo pendiente primero.
    items.sort(key=lambda x: x.balance, reverse=True)
    return items[:limit]
