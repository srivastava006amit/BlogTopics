from decimal import Decimal

from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )