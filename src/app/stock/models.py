from sqlalchemy import REAL, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# ---------------------------------------------------------------------------
# Basado en el diagrama real de Supabase (supabase-schema-new.svg).
# Tablas: productos, inventario_sucursal, pedidos, historial_inventario.
# ---------------------------------------------------------------------------


class Product(Base):
    """Catálogo de productos. PK real = codigo (no uuid)."""

    __tablename__ = "productos"
    __table_args__ = {"schema": "public"}

    codigo: Mapped[str] = mapped_column(String, primary_key=True)
    uuid: Mapped[str] = mapped_column(String, nullable=False)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)

    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    costo: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    venta: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))

    departamento_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    proveedor_uuid: Mapped[str | None] = mapped_column(String, nullable=True)

    es_kit: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    activo: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    scope: Mapped[str | None] = mapped_column(String, nullable=True)
    controlled_by: Mapped[str | None] = mapped_column(String, nullable=True)
    auto_restock: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    checado_en: Mapped[str | None] = mapped_column(String, nullable=True)
    checado_por: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class BranchInventory(Base):
    """Stock actual por sucursal. PK compuesta (codigo, branch_id)."""

    __tablename__ = "inventario_sucursal"
    __table_args__ = {"schema": "public"}

    codigo: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, primary_key=True)

    inventario: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    inv_minimo: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))

    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class Order(Base):
    """Pedidos (sugeridos o manuales). Guarda el ROP calculado al momento."""

    __tablename__ = "pedidos"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    producto_codigo: Mapped[str] = mapped_column(String, nullable=False)
    proveedor_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    usuario_uuid: Mapped[str | None] = mapped_column(String, nullable=True)

    cantidad_solicitada: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    rop_calculado: Mapped[float | None] = mapped_column(REAL, nullable=True)
    stock_al_momento: Mapped[float | None] = mapped_column(REAL, nullable=True)

    estado: Mapped[str] = mapped_column(String, nullable=False)
    origen: Mapped[str | None] = mapped_column(String, nullable=True)
    notas: Mapped[str | None] = mapped_column(String, nullable=True)

    generado_en: Mapped[str | None] = mapped_column(String, nullable=True)
    enviado_en: Mapped[str | None] = mapped_column(String, nullable=True)
    recibido_en: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class InventoryHistory(Base):
    """Kardex de movimientos de inventario (historial_inventario).

    `habia` = existencia antes del movimiento, `resultado` = existencia
    después. Esto permite reconstruir el stock de un producto en cualquier
    fecha pasada tomando el movimiento más reciente con fecha <= esa fecha.
    """

    __tablename__ = "historial_inventario"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    producto_codigo: Mapped[str] = mapped_column(String, nullable=False)

    fecha: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    cantidad: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    habia: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    resultado: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))

    referencia_tabla: Mapped[str | None] = mapped_column(String, nullable=True)
    referencia_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    usuario_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    notas: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)
