from fastapi import APIRouter, Query

from app.users.dependencies import DbSession
from app.sales import service
from app.sales.dependencies import Filtro
from app.sales.schemas import (
    FormaPagoItem,
    ProductoMasVendidoItem,
    TicketRecienteItem,
    VentaDiariaItem,
)

router = APIRouter()


# 1. Gráfica de líneas: ventas diarias + ganancias diarias
@router.get("/daily-sales", response_model=list[VentaDiariaItem])
async def ventas_diarias(db: DbSession, filtro: Filtro):
    return await service.get_ventas_diarias(db, filtro)


# 2. Donut: formas de pago
@router.get("/payment-methods", response_model=list[FormaPagoItem])
async def formas_pago(db: DbSession, filtro: Filtro):
    return await service.get_formas_pago(db, filtro)


# 3. Tabla: últimos tickets
@router.get("/recent-tickets", response_model=list[TicketRecienteItem])
async def ultimos_tickets(
    db: DbSession, filtro: Filtro, limit: int = Query(10, ge=1, le=100)
):
    return await service.get_ultimos_tickets(db, filtro, limit)


# 4. Tabla: productos más vendidos
@router.get("/top-products", response_model=list[ProductoMasVendidoItem])
async def productos_mas_vendidos(
    db: DbSession, filtro: Filtro, limit: int = Query(10, ge=1, le=100)
):
    return await service.get_productos_mas_vendidos(db, filtro, limit)
