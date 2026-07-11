from fastapi import APIRouter, Query

from app.analytics import service
from app.analytics.dependencies import AnalyticsFilterDep, DbSession
from app.analytics.schemas import (
    MarginSummary,
    MarginTrendItem,
    ProfitByDepartmentItem,
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
