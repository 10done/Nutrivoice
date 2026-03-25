from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import Settings, get_settings
from app.db import get_db
from app.models.meal_log import MealLog
from app.models.user import User
from app.schemas.meal import MealItem, MealListItem, MealListResponse, MealResponse, MealTextRequest, MealTotals
from app.services.agent_service import run_meal_agent, title_from_structured
from app.services.speech_transcription import TranscriptionError, transcribe_audio

router = APIRouter(prefix="/meals", tags=["meals"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def _meal_to_response(log: MealLog) -> MealResponse:
    s = log.structured
    raw_items = s.get("items") or []
    items = [MealItem.model_validate(x) for x in raw_items]
    totals = MealTotals.model_validate(s.get("totals") or {})
    return MealResponse(
        meal_id=log.id,
        transcript=log.raw_transcript,
        title=log.title,
        items=items,
        totals=totals,
        meal_type=s.get("meal_type"),
        tags=s.get("tags") or [],
        review_status=log.review_status,
        logged_at=log.logged_at,
    )


@router.post("/text", response_model=MealResponse)
def create_meal_from_text(
    body: MealTextRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MealResponse:
    structured = run_meal_agent(body.text, settings)
    title = title_from_structured(structured)
    log = MealLog(
        user_id=user.id,
        source="text",
        raw_transcript=body.text,
        title=title,
        review_status="needs_review" if structured.needs_review else "verified",
        structured=structured.model_dump(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _meal_to_response(log)


@router.post("/voice", response_model=MealResponse)
async def create_meal_from_voice(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    file: UploadFile = File(...),
) -> MealResponse:
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    filename = file.filename or "audio.webm"
    try:
        transcript = transcribe_audio(content, filename, settings)
    except TranscriptionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    structured = run_meal_agent(transcript, settings)
    title = title_from_structured(structured)
    log = MealLog(
        user_id=user.id,
        source="voice",
        raw_transcript=transcript,
        title=title,
        review_status="needs_review" if structured.needs_review else "verified",
        structured=structured.model_dump(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _meal_to_response(log)


@router.get("", response_model=MealListResponse)
def list_meals(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
    q: str | None = None,
) -> MealListResponse:
    limit = min(max(limit, 1), 100)
    cond = MealLog.user_id == user.id
    if q and q.strip():
        pat = f"%{q.strip()}%"
        cond = cond & (or_(MealLog.title.ilike(pat), MealLog.raw_transcript.ilike(pat)))
    stmt = select(MealLog).where(cond).order_by(MealLog.logged_at.desc()).limit(limit + 1)
    rows = list(db.scalars(stmt).all())
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = rows[-1].id if rows else None
    items: list[MealListItem] = []
    for log in rows:
        s = log.structured
        t = s.get("totals") or {}
        title = log.title or "Meal"
        items.append(
            MealListItem(
                id=log.id,
                logged_at=log.logged_at,
                title=title,
                calories=float(t.get("calories", 0)),
                protein_g=float(t.get("protein_g", 0)),
                carbs_g=float(t.get("carbs_g", 0)),
                fat_g=float(t.get("fat_g", 0)),
                meal_type=s.get("meal_type"),
                review_status=log.review_status,
            )
        )
    return MealListResponse(items=items, next_cursor=next_cursor)


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    log = db.get(MealLog, meal_id)
    if log is None or log.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    db.delete(log)
    db.commit()
