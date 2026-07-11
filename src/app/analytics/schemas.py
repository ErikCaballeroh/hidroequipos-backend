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


# ---------- Tema 2: Clientes y crédito ----------

class CustomerSummary(BaseModel):
    """KPIs de clientes y crédito."""

    active_customers: int          # clientes distintos con ventas en el período
    avg_ticket_per_customer: float
    receivable_balance: float      # saldo por cobrar acumulado (cargos crédito - abonos)
    credit_sales_pct: float        # ventas a crédito / ventas totales (0..1)


class TopCustomerItem(BaseModel):
    customer_uuid: str
    customer_name: str
    total: float
    ticket_count: int


class CreditVsPaymentsItem(BaseModel):
    """Serie mensual de cargos a crédito vs abonos recibidos."""

    period: str                    # 'YYYY-MM'
    credit_charges: float
    payments: float


class AccountsReceivableItem(BaseModel):
    """Saldo por cobrar por cliente (acumulado a la fecha)."""

    customer_uuid: str
    customer_name: str
    credit_limit: float
    charges: float                 # cargos a crédito acumulados
    payments: float                # abonos acumulados
    balance: float                 # charges - payments
