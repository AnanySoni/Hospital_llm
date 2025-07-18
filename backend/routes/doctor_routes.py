from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.models import Doctor  # assuming your model is here

router = APIRouter()

@router.get("/doctors")
def read_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()
