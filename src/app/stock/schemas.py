from datetime import date
from pydantic import BaseModel


class InventoryItem(BaseModel):
    id: str
    name: str
    category: str
    stock: float
    rop: float
    d: float
    l: float
    ss: float
    f: float
    status: str
    supplier: str
    has_pending_order: bool = False

    class Config:
        from_attributes = True


class RestockRequest(BaseModel):
    product_id: str
    quantity: float


class BulkRestockRequest(BaseModel):
    items: list[RestockRequest]


class StockFilter(BaseModel):
    """Query parameters to filter stock analytics endpoints."""

    branch_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None


# ---------- Tarjeta: Pedidos Sugeridos ----------

class SuggestedOrdersSummary(BaseModel):
    suggested_orders: int
    suggested_orders_yesterday: int
    critical_products: int
    reorder_point_products: int


# ---------- Gráfica: historial de estado de inventario ----------

class InventoryStatusPoint(BaseModel):
    date: str  # 'YYYY-MM-DD'
    critical_stock: int
    reorder_point: int
    optimal_stock: int
