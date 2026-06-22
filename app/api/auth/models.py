# app/auth/models.py

from datetime import UTC, datetime

from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

##
# SQLAlchemy DB model
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


# Pydantic request schema
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


# Pydantic response schema
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    email: str
    role: str
    is_active: bool


# Pydantic token response schema
class Token(BaseModel):
    access_token: str
    token_type: str
