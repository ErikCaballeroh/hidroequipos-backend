"""Lógica de negocio del módulo de análisis.

Se reutilizan los helpers de filtrado de ventas para mantener las mismas reglas
(excluir cancelados y borrados, aplicar rango de fechas y sucursal).
"""

from app.sales.service import (  # noqa: F401
    DEFAULT_DAYS,
    _apply_base_filters,
    _apply_date_range,
    _apply_optional_dates,
    _validate_date_range,
)
