"""Dependencias del módulo de análisis.

El filtrado (rango de fechas + aislamiento por sucursal según rol) es idéntico al
de ventas, por lo que se reutiliza `SalesFilter` y la dependencia `build_filter`.
"""

from app.core.database import get_db  # noqa: F401
from app.sales.dependencies import DbSession, SalesFilterDep  # noqa: F401
from app.sales.schemas import SalesFilter  # noqa: F401

# Alias semántico para la analítica; misma forma que el filtro de ventas.
AnalyticsFilter = SalesFilter
AnalyticsFilterDep = SalesFilterDep
