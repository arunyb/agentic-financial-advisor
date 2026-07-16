from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas.schemas import RiskProfileIn, RiskProfileOut, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/me/risk-profile", response_model=RiskProfileOut)
def read_risk_profile(current_user: models.User = Depends(get_current_user)):
    return current_user.risk_profile


@router.put("/me/risk-profile", response_model=RiskProfileOut)
def update_risk_profile(
    payload: RiskProfileIn,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = current_user.risk_profile
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
