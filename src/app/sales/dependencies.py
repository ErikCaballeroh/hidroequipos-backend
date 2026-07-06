from datetime import date
from typing import Annotated

from fastapi import Depends, Query

from app.users.dependencies import CurrentUser
from app.sales.schemas import VentasFiltro


async def build_filtro(
    current_user: CurrentUser,
    branch_id: str | None = Query(
        None, description="Solo aplica si el usuario es admin; de lo contrario se usa su propia sucursal"),
    fecha_inicio: date | None = Query(None),
    fecha_fin: date | None = Query(None),
) -> VentasFiltro:
    # Un usuario que no es admin solo puede ver estadísticas de su propia sucursal
    branch_final = branch_id if current_user.rol == "admin" else current_user.branch_id
    return VentasFiltro(
        branch_id=branch_final,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


Filtro = Annotated[VentasFiltro, Depends(build_filtro)]
