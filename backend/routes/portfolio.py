from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import get_db
from auth_dependency import get_current_user
from models import User, PortfolioItem, Symbol

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

class PortfolioItemCreate(BaseModel):
    symbol: str
    quantity: int
    purchase_price: float

@router.post("/")
def add_to_portfolio(item: PortfolioItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = db.query(Symbol).filter(Symbol.symbol == item.symbol.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Symbol not found")
        
    new_item = PortfolioItem(
        user_id=current_user.id,
        company_id=company.id,
        quantity=item.quantity,
        purchase_price=item.purchase_price
    )
    db.add(new_item)
    db.commit()
    return {"message": "Added to portfolio"}

@router.get("/")
def view_portfolio(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(PortfolioItem).filter(PortfolioItem.user_id == current_user.id).all()
    result = []
    for item in items:
        # Dummy current price logic, in a real scenario you fetch from an API
        current_price = item.purchase_price * 1.05  # just mock 5% profit
        result.append({
            "id": item.id,
            "symbol": item.company.symbol,
            "company_name": item.company.company_name,
            "quantity": item.quantity,
            "purchase_price": item.purchase_price,
            "current_price": current_price,
            "profit_loss": (current_price - item.purchase_price) * item.quantity
        })
    return result
