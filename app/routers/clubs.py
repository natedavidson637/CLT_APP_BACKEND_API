from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
from datetime import datetime

router = APIRouter(prefix="/clubs", tags=["Clubs"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------
# CREATE CLUB
# ------------------------------------------------------------
@router.post("/", response_model=schemas.Club)
def create_club(club: schemas.ClubCreate, db: Session = Depends(get_db)):
    new_club = models.Club(
        creator_id=club.creator_id,
        name=club.name,
        description=club.description,
        school=club.school,
        visibility=club.visibility,
        created_at=datetime.utcnow()
    )

    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    # Add creator as admin
    admin = models.ClubMember(
        club_id=new_club.id,
        user_id=club.creator_id,
        role="admin",
        joined_at=datetime.utcnow()
    )
    db.add(admin)
    db.commit()

    return new_club


# ------------------------------------------------------------
# GET CLUB
# ------------------------------------------------------------
@router.get("/{club_id}", response_model=schemas.Club)
def get_club(club_id: int, db: Session = Depends(get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


# ------------------------------------------------------------
# UPDATE CLUB
# ------------------------------------------------------------
@router.patch("/{club_id}")
def update_club(club_id: int, update: schemas.ClubBase, admin_id: int, db: Session = Depends(get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check admin
    admin = db.query(models.ClubMember).filter(
        models.ClubMember.club_id == club_id,
        models.ClubMember.user_id == admin_id,
        models.ClubMember.role == "admin"
    ).first()

    if not admin:
        raise HTTPException(status_code=403, detail="Not an admin")

    for key, value in update.dict(exclude_unset=True).items():
        setattr(club, key, value)

    db.commit()
    return {"message": "Club updated"}


# ------------------------------------------------------------
# JOIN CLUB
# ------------------------------------------------------------
@router.post("/{club_id}/join/{user_id}")
def join_club(club_id: int, user_id: int, db: Session = Depends(get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    existing = db.query(models.ClubMember).filter(
        models.ClubMember.club_id == club_id,
        models.ClubMember.user_id == user_id
    ).first()

    if existing:
        return {"message": "Already a member"}

    member = models.ClubMember(
        club_id=club_id,
        user_id=user_id,
        role="member",
        joined_at=datetime.utcnow()
    )

    db.add(member)
    db.commit()
    return {"message": "Joined club"}


# ------------------------------------------------------------
# LEAVE CLUB
# ------------------------------------------------------------
@router.delete("/{club_id}/leave/{user_id}")
def leave_club(club_id: int, user_id: int, db: Session = Depends(get_db)):
    member = db.query(models.ClubMember).filter(
        models.ClubMember.club_id == club_id,
        models.ClubMember.user_id == user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Not a member")

    db.delete(member)
    db.commit()
    return {"message": "Left club"}


# ------------------------------------------------------------
# PROMOTE MEMBER TO ADMIN
# ------------------------------------------------------------
@router.post("/{club_id}/promote/{user_id}")
def promote_member(club_id: int, user_id: int, admin_id: int, db: Session = Depends(get_db)):
    # Check admin
    admin = db.query(models.ClubMember).filter(
        models.ClubMember.club_id == club_id,
        models.ClubMember.user_id == admin_id,
        models.ClubMember.role == "admin"
    ).first()

    if not admin:
        raise HTTPException(status_code=403, detail="Not an admin")

    member = db.query(models.ClubMember).filter(
        models.ClubMember.club_id == club_id,
        models.ClubMember.user_id == user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = "admin"
    db.commit()
    return {"message": "Member promoted to admin"}


# ------------------------------------------------------------
# LIST CLUB MEMBERS
# ------------------------------------------------------------
@router.get("/{club_id}/members", response_model=list[schemas.ClubMember])
def list_members(club_id: int, db: Session = Depends(get_db)):
    return db.query(models.ClubMember).filter(models.ClubMember.club_id == club_id).all()


# ------------------------------------------------------------
# CREATE CLUB EVENT (links to Events table)
# ------------------------------------------------------------
@router.post("/{club_id}/event/{event_id}")
def add_club_event(club_id: int, event_id: int, admin_id: int, db: Session = Depends(get_db)):
    # Check admin
    admin = db.query(models.ClubMember).filter(
        models.ClubMember.club_id == club_id,
        models.ClubMember.user_id == admin_id,
        models.ClubMember.role == "admin"
    ).first()

    if not admin:
        raise HTTPException(status_code=403, detail="Not an admin")

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    link = models.ClubEvent(club_id=club_id, event_id=event_id)
    db.add(link)
    db.commit()
    return {"message": "Event added to club"}


# ------------------------------------------------------------
# GET CLUB EVENTS
# ------------------------------------------------------------
@router.get("/{club_id}/events", response_model=list[schemas.Event])
def get_club_events(club_id: int, db: Session = Depends(get_db)):
    links = db.query(models.ClubEvent).filter(models.ClubEvent.club_id == club_id).all()
    event_ids = [l.event_id for l in links]

    events = db.query(models.Event).filter(models.Event.id.in_(event_ids)).all()
    return events


# ------------------------------------------------------------
# CREATE CLUB CHAT ROOM (REST side)
# ------------------------------------------------------------
@router.post("/{club_id}/chat-room")
def create_club_chat_room(club_id: int, db: Session = Depends(get_db)):
    room = models.EventChatRoom(event_id=None)  # club chat uses same model
    db.add(room)
    db.commit()
    db.refresh(room)

    return {"room_id": room.id}
