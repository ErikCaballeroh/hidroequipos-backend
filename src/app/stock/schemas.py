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


class StockFilter(BaseModel):
    branch_id: str | None = None
