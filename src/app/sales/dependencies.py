from datetime import date
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.users.dependencies import CurrentUser
from app.sales.schemas import SalesFilter

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def build_filter(
    current_user: CurrentUser,
    branch_id: str | None = Query(
        None,
        description="Only applies if the user is admin; otherwise their own branch is used",
    ),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
) -> SalesFilter:
    # Un usuario no-admin solo puede ver estadísticas de su propia sucursal
    resolved_branch = (
        branch_id if current_user.rol == "admin" else current_user.branch_id
    )
    return SalesFilter(
        branch_id=resolved_branch,
        start_date=start_date,
        end_date=end_date,
    )


SalesFilterDep = Annotated[SalesFilter, Depends(build_filter)]
