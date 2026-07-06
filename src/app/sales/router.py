from fastapi import APIRouter, Query

from app.sales import service
from app.sales.dependencies import DbSession, SalesFilterDep
from app.sales.schemas import (
    DailySaleItem,
    PaymentMethodItem,
    RecentTicketItem,
    TopProductItem,
)

router = APIRouter()


# 1. Line chart: daily sales + profit
@router.get("/daily-sales", response_model=list[DailySaleItem])
async def get_daily_sales(db: DbSession, filter_params: SalesFilterDep):
    return await service.get_daily_sales(db, filter_params)


# 2. Donut chart: payment methods
@router.get("/payment-methods", response_model=list[PaymentMethodItem])
async def get_payment_methods(db: DbSession, filter_params: SalesFilterDep):
    return await service.get_payment_methods(db, filter_params)


# 3. Table: recent tickets
@router.get("/recent-tickets", response_model=list[RecentTicketItem])
async def get_recent_tickets(
    db: DbSession,
    filter_params: SalesFilterDep,
    limit: int = Query(10, ge=1, le=100),
):
    return await service.get_recent_tickets(db, filter_params, limit)


# 4. Table: top-selling products
@router.get("/top-products", response_model=list[TopProductItem])
async def get_top_products(
    db: DbSession,
    filter_params: SalesFilterDep,
    limit: int = Query(10, ge=1, le=100),
):
    return await service.get_top_products(db, filter_params, limit)
