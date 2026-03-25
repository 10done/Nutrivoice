from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.user import UserGoalsPatch, UserMeResponse, UserPreferencesPatch, UserProfilePatch

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserMeResponse)
def read_me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.patch("/goals", response_model=UserMeResponse)
def patch_goals(
    body: UserGoalsPatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/profile", response_model=UserMeResponse)
def patch_profile(
    body: UserProfilePatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/preferences", response_model=UserMeResponse)
def patch_preferences(
    body: UserPreferencesPatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
