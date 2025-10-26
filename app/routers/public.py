from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Reason

router = APIRouter()

@router.get("/reasons")
def get_public_reasons(db: Session = Depends(get_db)):
    reasons = db.query(Reason).all()
    return [{"id": r.id, "name": r.name} for r in reasons]