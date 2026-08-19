from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_entity import BaseEntity


class User(BaseEntity):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    mobile_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    profile_picture: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    email_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    mobile_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    is_locked: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )