from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MealItem(BaseModel):
    name: str
    quantity: float = 1
    unit: str = "serving"
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class MealTotals(BaseModel):
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class MealStructured(BaseModel):
    items: list[MealItem] = Field(default_factory=list)
    totals: MealTotals = Field(default_factory=MealTotals)
    meal_type: str | None = "snack"
    tags: list[str] = Field(default_factory=list)
    needs_review: bool = False


class MealTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None


class MealResponse(BaseModel):
    meal_id: str
    transcript: str | None
    title: str | None
    items: list[MealItem]
    totals: MealTotals
    meal_type: str | None
    tags: list[str]
    review_status: str
    logged_at: datetime

    model_config = {"from_attributes": True}


class MealListItem(BaseModel):
    id: str
    logged_at: datetime
    title: str | None
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    meal_type: str | None
    review_status: str


class MealListResponse(BaseModel):
    items: list[MealListItem]
    next_cursor: str | None = None
