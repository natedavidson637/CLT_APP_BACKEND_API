from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/rsvp", tags=["RSVP"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.EventRSVP)
def rsvp(data: schemas.EventRSVPBase, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    count = db.query(models.EventRSVP).filter(models.EventRSVP.event_id == data.event_id).count()

    if event.capacity_limit and count >= event.capacity_limit:
        data.status = "waitlist"

    new_rsvp = models.EventRSVP(**data.dict())
    db.add(new_rsvp)
    db.commit()
    db.refresh(new_rsvp)
    return new_rsvp


@router.delete("/{rsvp_id}")
def cancel_rsvp(rsvp_id: int, db: Session = Depends(get_db)):
    rsvp = db.query(models.EventRSVP).filter(models.EventRSVP.id == rsvp_id).first()
    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")

    db.delete(rsvp)
    db.commit()
    return {"message": "RSVP cancelled"}
