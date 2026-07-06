from sqlalchemy import REAL, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SaleTicket(Base):
    """Represents a completed sale transaction (ticket)."""

    __tablename__ = "venta_tickets"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    folio: Mapped[str | None] = mapped_column(String, nullable=True)

    # Identificadores de relación con otras tablas
    register_uuid: Mapped[str] = mapped_column(
        String, name="caja_uuid", nullable=False)
    user_uuid: Mapped[str] = mapped_column(
        String, name="usuario_uuid", nullable=False)
    operation_uuid: Mapped[str] = mapped_column(
        String, name="operacion_uuid", nullable=False)
    customer_uuid: Mapped[str | None] = mapped_column(
        String, name="cliente_uuid", nullable=True)

    created_on: Mapped[str] = mapped_column(
        String, name="creado_en", nullable=False)
    sold_at: Mapped[str] = mapped_column(
        String, name="vendido_en", nullable=False)

    subtotal: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    total: Mapped[float] = mapped_column(
        REAL, nullable=False, server_default=text("0"))
    discount: Mapped[float] = mapped_column(
        REAL, name="descuento", nullable=False, server_default=text("0"))
    profit: Mapped[float] = mapped_column(
        REAL, name="ganancia", nullable=False, server_default=text("0"))
    item_count: Mapped[int] = mapped_column(
        Integer, name="numero_articulos", nullable=False,
        server_default=text("0"))

    payment_method: Mapped[str] = mapped_column(
        String, name="forma_pago", nullable=False)
    paid_with: Mapped[float | None] = mapped_column(
        REAL, name="pago_con", nullable=True)
    change_given: Mapped[float | None] = mapped_column(
        REAL, name="total_devuelto", nullable=True)

    # Estado de cancelación
    is_cancelled: Mapped[int] = mapped_column(
        Integer, name="esta_cancelado", nullable=False,
        server_default=text("0"))
    cancelled_at: Mapped[str | None] = mapped_column(
        String, name="cancelado_en", nullable=True)
    cancelled_by: Mapped[str | None] = mapped_column(
        String, name="cancelado_por", nullable=True)

    notes: Mapped[str | None] = mapped_column(
        String, name="notas", nullable=True)

    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class SaleTicketItem(Base):
    """Represents a single product line within a sale ticket."""

    __tablename__ = "venta_tickets_articulos"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    ticket_uuid: Mapped[str] = mapped_column(String, nullable=False)

    product_code: Mapped[str] = mapped_column(
        String, name="producto_codigo", nullable=False)
    product_name: Mapped[str] = mapped_column(
        String, name="producto_nombre", nullable=False)
    quantity: Mapped[float] = mapped_column(
        REAL, name="cantidad", nullable=False)
    unit_price: Mapped[float] = mapped_column(
        REAL, name="precio_usado", nullable=False)
    unit_cost: Mapped[float] = mapped_column(
        REAL, name="costo_usado", nullable=False)

    profit: Mapped[float] = mapped_column(
        REAL, name="ganancia", nullable=False, server_default=text("0"))
    discount: Mapped[float] = mapped_column(
        REAL, name="descuento", nullable=False, server_default=text("0"))
    discount_amount: Mapped[float] = mapped_column(
        REAL, name="descuento_importe", nullable=False,
        server_default=text("0"))

    department: Mapped[str | None] = mapped_column(
        String, name="departamento", nullable=True)
    is_kit: Mapped[int] = mapped_column(
        Integer, name="es_kit", nullable=False, server_default=text("0"))

    # Campos de devolución
    was_returned: Mapped[int] = mapped_column(
        Integer, name="fue_devuelto", nullable=False,
        server_default=text("0"))
    returned_quantity: Mapped[float] = mapped_column(
        REAL, name="cantidad_devuelta", nullable=False,
        server_default=text("0"))

    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)
