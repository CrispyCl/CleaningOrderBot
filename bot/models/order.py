from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class OrderStatus(PyEnum):
    pending = "pending"
    accepted = "accepted"
    completed = "completed"
    rejected = "rejected"
    canceled = "canceled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"))
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(SqlEnum(OrderStatus), default=OrderStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=True)

    author = relationship("User")

    def __repr__(self):
        return f"<Order(id={self.id}, author_id={self.author_id}, status={self.status})>"


__all__ = ["Order", "OrderStatus"]
