import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models import RiskTolerance


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- Risk profile ----------
class RiskProfileIn(BaseModel):
    tolerance: RiskTolerance
    time_horizon_years: int = Field(ge=1, le=60)
    monthly_investment_capacity: float = Field(ge=0)
    questionnaire_score: int = Field(ge=0, le=100)


class RiskProfileOut(RiskProfileIn):
    model_config = ConfigDict(from_attributes=True)
    updated_at: datetime


# ---------- Portfolio ----------
class HoldingIn(BaseModel):
    ticker: str
    asset_class: str
    quantity: float = Field(gt=0)
    avg_cost: float = Field(ge=0)
    current_price: float = Field(ge=0)


class HoldingOut(HoldingIn):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class PortfolioIn(BaseModel):
    name: str = "My Portfolio"
    holdings: list[HoldingIn] = []


class PortfolioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    created_at: datetime
    holdings: list[HoldingOut]


# ---------- Chat / Agents ----------
class ChatRequest(BaseModel):
    session_id: Optional[uuid.UUID] = None
    message: str = Field(min_length=1)


class AgentStepOut(BaseModel):
    agent: str
    summary: str
    detail: Optional[dict] = None


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    reply: str
    agent_trace: list[AgentStepOut]
    citations: list[str] = []
