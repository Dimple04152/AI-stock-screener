from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import yfinance as yf

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
        
    # Check if user already owns this company
    existing_item = db.query(PortfolioItem).filter(
        PortfolioItem.user_id == current_user.id,
        PortfolioItem.company_id == company.id
    ).first()

    if existing_item:
        # Calculate new weighted average purchase price
        # New Price = ((Old Qty * Old Price) + (New Qty * New Price)) / (Total Qty)
        total_cost = (existing_item.quantity * existing_item.purchase_price) + (item.quantity * item.purchase_price)
        new_total_quantity = existing_item.quantity + item.quantity
        
        existing_item.purchase_price = round(total_cost / new_total_quantity, 2)
        existing_item.quantity = new_total_quantity
        
        db.commit()
        return {"message": "Updated existing position (Weighted Average Applied)"}
    else:
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
    
    # We can batch fetch or fetch individually. For simple on-demand, individual is easier but slower.
    # Let's try individual for now.
    for item in items:
        try:
            ticker = yf.Ticker(item.company.symbol)
            # Fetch current price from yfinance
            # ticker.fast_info is faster than ticker.info
            current_price = ticker.fast_info['last_price']
            
            if current_price is None:
                # Fallback if fast_info fails
                current_price = item.purchase_price
        except Exception:
            current_price = item.purchase_price # Fallback
            
        result.append({
            "id": item.id,
            "symbol": item.company.symbol,
            "company_name": item.company.company_name,
            "sector": item.company.sector,
            "quantity": item.quantity,
            "purchase_price": item.purchase_price,
            "current_price": current_price,
            "total_value": current_price * item.quantity,
            "profit_loss": (current_price - item.purchase_price) * item.quantity,
            "pl_percent": ((current_price - item.purchase_price) / item.purchase_price) * 100 if item.purchase_price > 0 else 0
        })
    return result
