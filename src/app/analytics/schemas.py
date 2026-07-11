"""Schemas de respuesta del módulo de análisis.

Los endpoints se agregan por tema (rentabilidad, clientes/crédito, estacionalidad).
"""

from pydantic import BaseModel


# ---------- Tema 1: Rentabilidad (márgenes y descuentos) ----------

class MarginSummary(BaseModel):
    """KPIs globales de rentabilidad para el rango seleccionado."""

    total_sales: float
    total_profit: float
    margin_pct: float          # ganancia / ventas  (0..1)
    total_discount: float
    discount_pct: float        # descuento / subtotal (0..1)


class MarginTrendItem(BaseModel):
    """Punto de la serie mensual de ventas, ganancia y margen."""

    period: str                # 'YYYY-MM'
    total_sales: float
    total_profit: float
    margin_pct: float


class ProfitByDepartmentItem(BaseModel):
    department: str
    total_sales: float
    total_profit: float
    margin_pct: float


class TopProfitableProductItem(BaseModel):
    product_code: str
    product_name: str
    total_profit: float
    total_sold: float          # importe vendido (cantidad * precio)
    margin_pct: float
