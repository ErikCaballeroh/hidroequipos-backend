from sqlalchemy import REAL, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "productos"
    __table_args__ = {"schema": "public"}

    codigo: Mapped[str] = mapped_column(String, primary_key=True)
    uuid: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    costo: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    venta: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    departamento_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    es_kit: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    activo: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    scope: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'global'"))
    controlled_by: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'central'"))
    checado_en: Mapped[str | None] = mapped_column(String, nullable=True)
    checado_por: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)
    proveedor_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    auto_restock: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class Department(Base):
    __tablename__ = "departamentos"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    controlled_by: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'central'"))
    activo: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class Supplier(Base):
    __tablename__ = "proveedores"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    contacto: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    telefono: Mapped[str | None] = mapped_column(String, nullable=True)
    lead_time_dias: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    activo: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class BranchInventory(Base):
    __tablename__ = "inventario_sucursal"
    __table_args__ = {"schema": "public"}

    codigo: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, primary_key=True)
    inventario: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    inv_minimo: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text("0"))
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)


class Order(Base):
    __tablename__ = "pedidos"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    producto_codigo: Mapped[str] = mapped_column(String, nullable=False)
    proveedor_uuid: Mapped[str] = mapped_column(String, nullable=False)
    usuario_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    origen: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'manual'"))
    cantidad_solicitada: Mapped[float] = mapped_column(REAL, nullable=False)
    rop_calculado: Mapped[float | None] = mapped_column(REAL, nullable=True)
    stock_al_momento: Mapped[float] = mapped_column(REAL, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'pendiente'"))
    generado_en: Mapped[str] = mapped_column(String, nullable=False)
    enviado_en: Mapped[str | None] = mapped_column(String, nullable=True)
    recibido_en: Mapped[str | None] = mapped_column(String, nullable=True)
    notas: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)
