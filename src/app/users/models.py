from sqlalchemy import Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "public"}

    uuid: Mapped[str] = mapped_column(String, primary_key=True)
    branch_id: Mapped[str] = mapped_column(String, nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    rol: Mapped[str] = mapped_column(String, nullable=False)
    activo: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    synced_at: Mapped[str | None] = mapped_column(String, nullable=True)
