from datetime import date

from pydantic import BaseModel, ConfigDict


class VentasFiltro(BaseModel):
    branch_id: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None


# ---------- 1. Gráfica de líneas: ventas y ganancias diarias ----------

class VentaDiariaItem(BaseModel):
    fecha: str  # 'YYYY-MM-DD'
    total_ventas: float
    ganancia_total: float


# ---------- 2. Donut: formas de pago ----------

class FormaPagoItem(BaseModel):
    forma_pago: str
    total: float
    numero_tickets: int


# ---------- 3. Tabla: últimos tickets ----------

class TicketRecienteItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    folio: str | None = None
    total: float
    forma_pago: str
    vendido_en: str


# ---------- 4. Tabla: productos más vendidos ----------

class ProductoMasVendidoItem(BaseModel):
    producto_codigo: str
    producto_nombre: str
    cantidad_vendida: float
    total_vendido: float
