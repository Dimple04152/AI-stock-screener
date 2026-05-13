from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Symbol

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/")
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(Symbol).all()
    return [{"id": c.id, "symbol": c.symbol, "company_name": c.company_name, "sector": c.sector} for c in companies]
