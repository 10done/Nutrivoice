import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    daily_calorie_goal: Mapped[int] = mapped_column(Integer, default=2000)
    daily_protein_goal_g: Mapped[int] = mapped_column(Integer, default=150)
    daily_carbs_goal_g: Mapped[int] = mapped_column(Integer, default=220)
    daily_fat_goal_g: Mapped[int] = mapped_column(Integer, default=65)

    fiber_goal_g: Mapped[int] = mapped_column(Integer, default=30)
    water_goal_ml: Mapped[int] = mapped_column(Integer, default=2500)

    store_voice_audio: Mapped[bool] = mapped_column(Boolean, default=False)

    meals = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
