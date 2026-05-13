from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth_dependency import get_current_user
from models import User, Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])

class AlertCreate(BaseModel):
    field: str
    operator: str
    threshold: float

@router.post("/")
def create_alert(alert: AlertCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_alert = Alert(
        user_id=current_user.id,
        field=alert.field,
        operator=alert.operator,
        threshold=alert.threshold
    )
    db.add(new_alert)
    db.commit()
    return {"message": "Alert created successfully"}

@router.get("/")
def view_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alerts = db.query(Alert).filter(Alert.user_id == current_user.id).all()
    return [{"id": a.id, "field": a.field, "operator": a.operator, "threshold": a.threshold} for a in alerts]
