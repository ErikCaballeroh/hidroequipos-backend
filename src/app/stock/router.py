from fastapi import APIRouter

from app.stock import service
from app.stock.dependencies import DbSession, StockFilterDep
from app.stock.schemas import InventoryItem, RestockRequest
from app.users.dependencies import CurrentUser

router = APIRouter()


@router.get("/inventory", response_model=list[InventoryItem])
async def get_inventory(db: DbSession, filter_params: StockFilterDep):
    return await service.get_inventory(db, filter_params)


@router.post("/restock")
async def request_restock(
    db: DbSession,
    filter_params: StockFilterDep,
    current_user: CurrentUser,
    request: RestockRequest,
):
    return await service.request_restock(db, filter_params, current_user.uuid, request)


@router.post("/restock/{product_id}/receive")
async def receive_restock(
    db: DbSession,
    filter_params: StockFilterDep,
    product_id: str,
):
    return await service.receive_restock(db, filter_params, product_id)
