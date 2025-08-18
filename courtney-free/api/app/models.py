from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, JSON, Float, UniqueConstraint
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(256))
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    watchlist = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    emails = relationship("UserEmail", back_populates="user", cascade="all, delete-orphan")

class UserEmail(Base):
    __tablename__ = "user_emails"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(320))
    user = relationship("User", back_populates="emails")

class Watchlist(Base):
    __tablename__ = "watchlists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    symbol: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="watchlist")
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_user_symbol"),)

class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    asof: Mapped[datetime] = mapped_column(DateTime, index=True)
    technique: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(16))  # BUY/SELL/HOLD
    buy_price: Mapped[Float] = mapped_column(Float)
    stop_loss: Mapped[Float] = mapped_column(Float)
    meta: Mapped[dict] = mapped_column(JSON, default={})

class Portfolio(Base):
    __tablename__ = "portfolio"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    symbol: Mapped[str] = mapped_column(String(32))
    qty: Mapped[Float] = mapped_column(Float, default=0.0)
    avg_price: Mapped[Float] = mapped_column(Float, default=0.0)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    open: Mapped[bool] = mapped_column(Boolean, default=True)