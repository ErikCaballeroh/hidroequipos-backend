from fastapi import APIRouter

from app.stock import service
from app.stock.dependencies import DbSession, StockFilterDep
from app.stock.schemas import InventoryStatusPoint, SuggestedOrdersSummary

router = APIRouter()


# 1. Tarjeta: Pedidos Sugeridos
@router.get("/suggested-orders", response_model=SuggestedOrdersSummary)
async def get_suggested_orders(db: DbSession, filter_params: StockFilterDep):
    return await service.get_suggested_orders_summary(db, filter_params)


# 2. Gráfica: historial de estado de inventario (3 líneas)
@router.get("/inventory-status", response_model=list[InventoryStatusPoint])
async def get_inventory_status(db: DbSession, filter_params: StockFilterDep):
    return await service.get_inventory_status_history(db, filter_params)
