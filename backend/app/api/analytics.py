from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.meal_log import MealLog
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary, DaySeriesPoint, TodayAnalytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _user_today_bounds(user: User) -> tuple[datetime, datetime]:
    # MVP: use UTC day; later use user.timezone
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


@router.get("/today", response_model=TodayAnalytics)
def analytics_today(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TodayAnalytics:
    start, end = _user_today_bounds(user)
    logs = list(
        db.scalars(
            select(MealLog).where(MealLog.user_id == user.id, MealLog.logged_at >= start, MealLog.logged_at < end)
        ).all()
    )
    c = p = cb = f = 0.0
    for log in logs:
        t = (log.structured or {}).get("totals") or {}
        c += float(t.get("calories", 0))
        p += float(t.get("protein_g", 0))
        cb += float(t.get("carbs_g", 0))
        f += float(t.get("fat_g", 0))
    goal = user.daily_calorie_goal
    remaining = max(goal - c, 0)
    return TodayAnalytics(
        date_label=date.today().isoformat(),
        goal_calories=goal,
        consumed_calories=round(c, 1),
        kcal_remaining=round(remaining, 1),
        protein_g=round(p, 1),
        protein_goal_g=user.daily_protein_goal_g,
        carbs_g=round(cb, 1),
        carbs_goal_g=user.daily_carbs_goal_g,
        fat_g=round(f, 1),
        fat_goal_g=user.daily_fat_goal_g,
        water_goal_ml=user.water_goal_ml,
    )


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    period: str = "7d",
) -> AnalyticsSummary:
    days_count = 7 if period == "7d" else 30
    if period not in ("7d", "30d"):
        days_count = 7
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days_count - 1)
    start_dt = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    end_dt = datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)

    logs = list(
        db.scalars(
            select(MealLog).where(MealLog.user_id == user.id, MealLog.logged_at >= start_dt, MealLog.logged_at < end_dt)
        ).all()
    )

    by_day: dict[str, dict[str, float]] = {}
    for log in logs:
        d = log.logged_at.date().isoformat()
        by_day.setdefault(d, {"calories": 0, "protein_g": 0})
        t = (log.structured or {}).get("totals") or {}
        by_day[d]["calories"] += float(t.get("calories", 0))
        by_day[d]["protein_g"] += float(t.get("protein_g", 0))

    day_points: list[DaySeriesPoint] = []
    cur = start
    while cur <= end:
        ds = cur.isoformat()
        agg = by_day.get(ds, {"calories": 0, "protein_g": 0})
        day_points.append(
            DaySeriesPoint(
                date=ds,
                calories=round(agg["calories"], 1),
                target_calories=user.daily_calorie_goal,
                protein_g=round(agg["protein_g"], 1),
            )
        )
        cur = cur + timedelta(days=1)

    total_cal = sum(p.calories for p in day_points)
    avg_cal = total_cal / days_count if days_count else 0
    protein_avg = sum(p.protein_g for p in day_points) / days_count if days_count else 0

    hits = 0
    for p in day_points:
        if p.protein_g >= user.daily_protein_goal_g:
            hits += 1

    return AnalyticsSummary(
        period=f"{days_count}d",
        average_daily_calories=round(avg_cal, 1),
        days=day_points,
        protein_daily_avg_g=round(protein_avg, 1),
        protein_goal_hits=hits,
        protein_days_in_period=days_count,
    )
