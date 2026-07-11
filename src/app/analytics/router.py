from fastapi import APIRouter, Query

from app.analytics import service
from app.analytics.dependencies import AnalyticsFilterDep, DbSession
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

router = APIRouter()


# ==================== Tema 1: Rentabilidad ====================

# KPIs de rentabilidad (margen y descuentos)
@router.get("/margin-summary", response_model=MarginSummary)
async def get_margin_summary(db: DbSession, filter_params: AnalyticsFilterDep):
    return await service.get_margin_summary(db, filter_params)


# Tendencia mensual de margen %
@router.get("/margin-trend", response_model=list[MarginTrendItem])
async def get_margin_trend(db: DbSession, filter_params: AnalyticsFilterDep):
    return await service.get_margin_trend(db, filter_params)


# Ganancia por departamento
@router.get("/profit-by-department", response_model=list[ProfitByDepartmentItem])
async def get_profit_by_department(db: DbSession, filter_params: AnalyticsFilterDep):
    return await service.get_profit_by_department(db, filter_params)


# Productos más rentables (por ganancia)
@router.get("/top-profitable-products", response_model=list[TopProfitableProductItem])
async def get_top_profitable_products(
    db: DbSession,
    filter_params: AnalyticsFilterDep,
    limit: int = Query(10, ge=1, le=100),
):
    return await service.get_top_profitable_products(db, filter_params, limit)


# ==================== Tema 2: Clientes y crédito ====================

# KPIs de clientes y crédito
@router.get("/customer-summary", response_model=CustomerSummary)
async def get_customer_summary(db: DbSession, filter_params: AnalyticsFilterDep):
    return await service.get_customer_summary(db, filter_params)


# Top clientes por importe de compra
@router.get("/top-customers", response_model=list[TopCustomerItem])
async def get_top_customers(
    db: DbSession,
    filter_params: AnalyticsFilterDep,
    limit: int = Query(10, ge=1, le=100),
):
    return await service.get_top_customers(db, filter_params, limit)


# Serie mensual de cargos a crédito vs abonos
@router.get("/credit-vs-payments", response_model=list[CreditVsPaymentsItem])
async def get_credit_vs_payments(db: DbSession, filter_params: AnalyticsFilterDep):
    return await service.get_credit_vs_payments(db, filter_params)


# Cuentas por cobrar por cliente (saldo acumulado)
@router.get("/accounts-receivable", response_model=list[AccountsReceivableItem])
async def get_accounts_receivable(
    db: DbSession,
    filter_params: AnalyticsFilterDep,
    limit: int = Query(50, ge=1, le=200),
):
    return await service.get_accounts_receivable(db, filter_params, limit)
