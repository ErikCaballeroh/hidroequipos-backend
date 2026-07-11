from datetime import date

from pydantic import BaseModel


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
