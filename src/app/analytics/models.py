"""Modelos usados por el módulo de análisis.

Se reutilizan los modelos de ventas (`SaleTicket`, `SaleTicketItem`) y se agregan
los modelos de clientes y abonos, necesarios para la analítica de crédito.
"""

from sqlalchemy import REAL, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Reexport: la analítica de ventas se apoya en estos modelos ya definidos.
from app.sales.models import SaleTicket, SaleTicketItem  # noqa: F401


class Cliente(Base):
    """Cliente de una sucursal; puede tener línea de crédito."""

    __tablename__ = "clientes"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    numero: Mapped[str | None] = mapped_column(String, nullable=True)
    folio: Mapped[str | None] = mapped_column(String, nullable=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    direccion: Mapped[str | None] = mapped_column(String, nullable=True)
    telefono: Mapped[str | None] = mapped_column(String, nullable=True)
    credit_limit: Mapped[float] = mapped_column(
        REAL, name="limite_credito", nullable=False, server_default=text("0"))

    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class Abono(Base):
    """Pago (abono) de un cliente hacia su saldo de crédito."""

    __tablename__ = "abonos"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    customer_uuid: Mapped[str] = mapped_column(
        String, name="cliente_uuid", nullable=False)
    operation_uuid: Mapped[str | None] = mapped_column(
        String, name="operacion_uuid", nullable=True)
    user_uuid: Mapped[str] = mapped_column(
        String, name="usuario_uuid", nullable=False)

    paid_at: Mapped[str] = mapped_column(
        String, name="fecha", nullable=False)
    amount: Mapped[float] = mapped_column(REAL, name="monto", nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String, name="forma_pago", nullable=False)
    notes: Mapped[str | None] = mapped_column(
        String, name="notas", nullable=True)

    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)
