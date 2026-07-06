from sqlalchemy import REAL, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VentaTicket(Base):
    __tablename__ = "venta_tickets"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    folio: Mapped[str | None] = mapped_column(String, nullable=True)
    caja_uuid: Mapped[str] = mapped_column(String, nullable=False)
    usuario_uuid: Mapped[str] = mapped_column(String, nullable=False)
    operacion_uuid: Mapped[str] = mapped_column(String, nullable=False)
    cliente_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    creado_en: Mapped[str] = mapped_column(String, nullable=False)
    vendido_en: Mapped[str] = mapped_column(String, nullable=False)
    subtotal: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    total: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    descuento: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    ganancia: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    numero_articulos: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"))
    forma_pago: Mapped[str] = mapped_column(String, nullable=False)
    pago_con: Mapped[float | None] = mapped_column(REAL, nullable=True)
    total_devuelto: Mapped[float | None] = mapped_column(REAL, nullable=True)
    esta_cancelado: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"))
    cancelado_en: Mapped[str | None] = mapped_column(String, nullable=True)
    cancelado_por: Mapped[str | None] = mapped_column(String, nullable=True)
    notas: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class VentaTicketArticulo(Base):
    __tablename__ = "venta_tickets_articulos"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    ticket_uuid: Mapped[str] = mapped_column(String, nullable=False)
    producto_codigo: Mapped[str] = mapped_column(String, nullable=False)
    producto_nombre: Mapped[str] = mapped_column(String, nullable=False)
    cantidad: Mapped[float] = mapped_column(REAL, nullable=False)
    precio_usado: Mapped[float] = mapped_column(REAL, nullable=False)
    costo_usado: Mapped[float] = mapped_column(REAL, nullable=False)
    ganancia: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    descuento: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    descuento_importe: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    departamento: Mapped[str | None] = mapped_column(String, nullable=True)
    es_kit: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"))
    fue_devuelto: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"))
    cantidad_devuelta: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)
