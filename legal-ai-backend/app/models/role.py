from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_entity import BaseEntity


class Role(BaseEntity):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
