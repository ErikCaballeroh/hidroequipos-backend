from datetime import date

from pydantic import BaseModel, ConfigDict


class SalesFilter(BaseModel):
    """Query parameters to filter sales analytics endpoints."""

    branch_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None


# ---------- 1. Line chart: daily sales & profit ----------

class DailySaleItem(BaseModel):
    date: str  # 'YYYY-MM-DD'
    total_sales: float
    total_profit: float


# ---------- 2. Donut chart: payment methods ----------

class PaymentMethodItem(BaseModel):
    payment_method: str
    total: float
    ticket_count: int


# ---------- 3. Table: recent tickets ----------

class RecentTicketItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    folio: str | None = None
    total: float
    payment_method: str
    sold_at: str


# ---------- 4. Table: top-selling products ----------

class TopProductItem(BaseModel):
    product_code: str
    product_name: str
    quantity_sold: float
    total_sold: float
