from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


# Auth
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    is_active: bool


# Match
class TeamBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int
    name: str
    logo_url: str | None = None


class CompetitionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str | None = None
    country_code: str | None = None
    logo_url: str | None = None


class CompetitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int
    name: str
    country: str | None = None
    country_code: str | None = None
    country_flag_url: str | None = None
    flag_emoji: str | None = None
    logo_url: str | None = None
    season: str | None = None
    season_year: int | None = None
    league_type: str | None = None
    status: str
    odds_sport_key: str | None = None
    synced_at: datetime | None = None


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int
    status: MatchStatus
    kickoff_at: datetime | None
    minute: int | None
    home_score: int
    away_score: int
    is_monitored: bool
    home_team: TeamBrief
    away_team: TeamBrief
    competition: CompetitionBrief | None = None


class LiveStatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    minute: int
    possession_home: float | None
    possession_away: float | None
    shots_home: int
    shots_away: int
    shots_on_target_home: int
    shots_on_target_away: int
    xg_home: float
    xg_away: float
    dangerous_attacks_home: int
    dangerous_attacks_away: int
    corners_home: int
    corners_away: int
    momentum_home: float
    momentum_away: float
    offensive_pressure_home: float
    offensive_pressure_away: float
    recorded_at: datetime


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    minute: int
    event_type: str
    detail: str | None
    extra_data: dict | None = None


class OddResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    market: str
    selection: str
    bookmaker: str
    odds_value: float
    implied_probability: float | None


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    market: str
    probability: float
    model_name: str
    minute: int


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    market: str
    selection: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    probability: float
    expected_value: float | None
    odds_at_creation: float | None
    reasons: list[str] | None
    positive_points: list[str] | None
    negative_points: list[str] | None
    model_contributions: dict | None
    explanation: str | None
    minute: int
    is_active: bool
    created_at: datetime


class MatchDetailResponse(MatchResponse):
    live_stats: list[LiveStatResponse] = []
    events: list[EventResponse] = []
    odds: list[OddResponse] = []
    predictions: list[PredictionResponse] = []
    recommendations: list[RecommendationResponse] = []


class MonitorMatchRequest(BaseModel):
    match_id: int


class UserPreferencesUpdate(BaseModel):
    sound_alerts: bool | None = None
    push_notifications: bool | None = None
    min_confidence_score: float | None = Field(default=None, ge=0, le=100)
    favorite_leagues: list[int] | None = None
