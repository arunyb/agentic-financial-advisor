from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health/live")
def liveness():
    """Process is up. Used by Docker HEALTHCHECK / k8s livenessProbe."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Process can serve traffic (DB reachable). Used by k8s readinessProbe."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
