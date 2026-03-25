from pydantic import BaseModel


class TodayAnalytics(BaseModel):
    date_label: str
    goal_calories: int
    consumed_calories: float
    kcal_remaining: float
    protein_g: float
    protein_goal_g: int
    carbs_g: float
    carbs_goal_g: int
    fat_g: float
    fat_goal_g: int
    water_goal_ml: int


class DaySeriesPoint(BaseModel):
    date: str
    calories: float
    target_calories: int
    protein_g: float


class AnalyticsSummary(BaseModel):
    period: str
    average_daily_calories: float
    days: list[DaySeriesPoint]
    protein_daily_avg_g: float
    protein_goal_hits: int
    protein_days_in_period: int
