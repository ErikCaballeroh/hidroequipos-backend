from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sales.exceptions import RangoFechasInvalidoError
from app.sales.models import VentaTicket, VentaTicketArticulo
from app.sales.schemas import (
    FormaPagoItem,
    ProductoMasVendidoItem,
    TicketRecienteItem,
    VentaDiariaItem,
    VentasFiltro,
)

DIAS_POR_DEFECTO = 30


def _validar_rango(filtro: VentasFiltro) -> None:
    if filtro.fecha_inicio and filtro.fecha_fin and filtro.fecha_inicio > filtro.fecha_fin:
        raise RangoFechasInvalidoError()


def _aplicar_filtros_base(query, filtro: VentasFiltro):
    """Solo ventas reales: no canceladas, no eliminadas."""
    query = query.where(
        VentaTicket.deleted_at.is_(None),
        VentaTicket.esta_cancelado == 0,
    )
    if filtro.branch_id:
        query = query.where(VentaTicket.branch_id == filtro.branch_id)
    return query


def _aplicar_rango_fechas(query, fecha_inicio: date, fecha_fin: date):
    limite = (fecha_fin + timedelta(days=1)).isoformat()
    return query.where(
        VentaTicket.vendido_en >= fecha_inicio.isoformat(),
        VentaTicket.vendido_en < limite,
    )


def _aplicar_fechas_opcionales(query, filtro: VentasFiltro):
    if filtro.fecha_inicio:
        query = query.where(
            VentaTicket.vendido_en >= filtro.fecha_inicio.isoformat())
    if filtro.fecha_fin:
        limite = (filtro.fecha_fin + timedelta(days=1)).isoformat()
        query = query.where(VentaTicket.vendido_en < limite)
    return query


# ---------- 1. Gráfica de líneas: ventas y ganancias diarias ----------

async def get_ventas_diarias(db: AsyncSession, filtro: VentasFiltro) -> list[VentaDiariaItem]:
    """Serie diaria de ventas y ganancias. Si no se especifican fechas,
    regresa los últimos 30 días (incluye hoy)."""
    _validar_rango(filtro)

    fecha_fin = filtro.fecha_fin or date.today()
    fecha_inicio = filtro.fecha_inicio or (
        fecha_fin - timedelta(days=DIAS_POR_DEFECTO - 1))

    dia_expr = func.substr(VentaTicket.vendido_en, 1, 10)  # 'YYYY-MM-DD'

    query = select(
        dia_expr.label("dia"),
        func.coalesce(func.sum(VentaTicket.total), 0),
        func.coalesce(func.sum(VentaTicket.ganancia), 0),
    )
    query = _aplicar_filtros_base(query, filtro)
    query = _aplicar_rango_fechas(query, fecha_inicio, fecha_fin)
    query = query.group_by(dia_expr).order_by(dia_expr)

    result = await db.execute(query)
    datos = {
        dia: (total, ganancia)
        for dia, total, ganancia in result.all()
    }

    # Se rellenan los días sin ventas con 0 para que la gráfica no tenga huecos
    serie: list[VentaDiariaItem] = []
    cursor = fecha_inicio
    while cursor <= fecha_fin:
        clave = cursor.isoformat()
        total, ganancia = datos.get(clave, (0, 0))
        serie.append(VentaDiariaItem(
            fecha=clave, total_ventas=total, ganancia_total=ganancia))
        cursor += timedelta(days=1)

    return serie


# ---------- 2. Donut: formas de pago ----------

async def get_formas_pago(db: AsyncSession, filtro: VentasFiltro) -> list[FormaPagoItem]:
    _validar_rango(filtro)

    query = select(
        VentaTicket.forma_pago,
        func.coalesce(func.sum(VentaTicket.total), 0),
        func.count(VentaTicket.uuid),
    )
    query = _aplicar_filtros_base(query, filtro)
    query = _aplicar_fechas_opcionales(query, filtro)
    query = query.group_by(VentaTicket.forma_pago)

    result = await db.execute(query)
    return [
        FormaPagoItem(forma_pago=forma_pago, total=total,
                      numero_tickets=numero_tickets)
        for forma_pago, total, numero_tickets in result.all()
    ]


# ---------- 3. Tabla: últimos tickets ----------

async def get_ultimos_tickets(
    db: AsyncSession, filtro: VentasFiltro, limit: int = 10
) -> list[TicketRecienteItem]:
    query = select(
        VentaTicket.folio,
        VentaTicket.total,
        VentaTicket.forma_pago,
        VentaTicket.vendido_en,
    )
    query = _aplicar_filtros_base(query, filtro)
    query = query.order_by(VentaTicket.vendido_en.desc()).limit(limit)

    result = await db.execute(query)
    return [
        TicketRecienteItem(folio=folio, total=total,
                           forma_pago=forma_pago, vendido_en=vendido_en)
        for folio, total, forma_pago, vendido_en in result.all()
    ]


# ---------- 4. Tabla: productos más vendidos ----------

async def get_productos_mas_vendidos(
    db: AsyncSession, filtro: VentasFiltro, limit: int = 10
) -> list[ProductoMasVendidoItem]:
    _validar_rango(filtro)

    query = (
        select(
            VentaTicketArticulo.producto_codigo,
            VentaTicketArticulo.producto_nombre,
            func.coalesce(func.sum(VentaTicketArticulo.cantidad), 0),
            func.coalesce(
                func.sum(VentaTicketArticulo.cantidad *
                         VentaTicketArticulo.precio_usado), 0
            ),
        )
        .join(VentaTicket, VentaTicket.uuid == VentaTicketArticulo.ticket_uuid)
        .where(VentaTicketArticulo.deleted_at.is_(None))
    )
    query = _aplicar_filtros_base(query, filtro)
    query = _aplicar_fechas_opcionales(query, filtro)

    query = (
        query.group_by(
            VentaTicketArticulo.producto_codigo, VentaTicketArticulo.producto_nombre
        )
        .order_by(func.sum(VentaTicketArticulo.cantidad).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return [
        ProductoMasVendidoItem(
            producto_codigo=codigo,
            producto_nombre=nombre,
            cantidad_vendida=cantidad,
            total_vendido=total,
        )
        for codigo, nombre, cantidad, total in result.all()
    ]
