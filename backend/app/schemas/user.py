from pydantic import BaseModel, EmailStr, Field


class UserMeResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: str | None
    timezone: str
    daily_calorie_goal: int
    daily_protein_goal_g: int
    daily_carbs_goal_g: int
    daily_fat_goal_g: int
    fiber_goal_g: int
    water_goal_ml: int
    store_voice_audio: bool

    model_config = {"from_attributes": True}


class UserGoalsPatch(BaseModel):
    daily_calorie_goal: int | None = Field(None, ge=500, le=20000)
    daily_protein_goal_g: int | None = Field(None, ge=0, le=1000)
    daily_carbs_goal_g: int | None = Field(None, ge=0, le=2000)
    daily_fat_goal_g: int | None = Field(None, ge=0, le=500)
    fiber_goal_g: int | None = None
    water_goal_ml: int | None = None


class UserProfilePatch(BaseModel):
    display_name: str | None = Field(None, max_length=255)
    timezone: str | None = Field(None, max_length=64)


class UserPreferencesPatch(BaseModel):
    store_voice_audio: bool | None = None
