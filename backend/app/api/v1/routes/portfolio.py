import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas.schemas import PortfolioIn, PortfolioOut

router = APIRouter(prefix="/portfolios", tags=["portfolio"])


@router.get("", response_model=list[PortfolioOut])
def list_portfolios(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(models.Portfolio)
        .options(selectinload(models.Portfolio.holdings))
        .filter(models.Portfolio.owner_id == current_user.id)
        .all()
    )


@router.post("", response_model=PortfolioOut, status_code=201)
def create_portfolio(
    payload: PortfolioIn,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = models.Portfolio(owner_id=current_user.id, name=payload.name)
    portfolio.holdings = [models.Holding(**h.model_dump()) for h in payload.holdings]
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio(
    portfolio_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = (
        db.query(models.Portfolio)
        .options(selectinload(models.Portfolio.holdings))
        .filter(models.Portfolio.id == portfolio_id, models.Portfolio.owner_id == current_user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(
    portfolio_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = (
        db.query(models.Portfolio)
        .filter(models.Portfolio.id == portfolio_id, models.Portfolio.owner_id == current_user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(portfolio)
    db.commit()
