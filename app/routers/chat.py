from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
from datetime import datetime
import uuid
import os

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------
# CREATE CHAT ROOM FOR EVENT
# ------------------------------------------------------------
@router.post("/room/{event_id}", response_model=schemas.EventChatRoom)
def create_chat_room(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    existing = db.query(models.EventChatRoom).filter(models.EventChatRoom.event_id == event_id).first()
    if existing:
        return existing

    room = models.EventChatRoom(event_id=event_id)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


# ------------------------------------------------------------
# GET CHAT HISTORY
# ------------------------------------------------------------
@router.get("/room/{room_id}/messages", response_model=list[schemas.EventChatMessage])
def get_messages(room_id: int, db: Session = Depends(get_db)):
    messages = db.query(models.EventChatMessage).filter(
        models.EventChatMessage.room_id == room_id,
        models.EventChatMessage.is_deleted == False
    ).order_by(models.EventChatMessage.timestamp.asc()).all()

    return messages


# ------------------------------------------------------------
# SEND TEXT MESSAGE
# ------------------------------------------------------------
@router.post("/message", response_model=schemas.EventChatMessage)
def send_message(data: schemas.EventChatMessageBase, db: Session = Depends(get_db)):
    room = db.query(models.EventChatRoom).filter(models.EventChatRoom.id == data.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    message = models.EventChatMessage(
        room_id=data.room_id,
        sender_id=data.sender_id,
        message_text=data.message_text,
        media_url=data.media_url,
        timestamp=datetime.utcnow()
    )

    db.add(message)
    db.commit()
    db.refresh(message)
    return message


# ------------------------------------------------------------
# SEND MEDIA MESSAGE (Image/Video Upload)
# ------------------------------------------------------------
@router.post("/message/media")
def send_media_message(
    room_id: int,
    sender_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    room = db.query(models.EventChatRoom).filter(models.EventChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    # Save file locally or to S3 later
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = f"uploads/chat/{filename}"

    os.makedirs("uploads/chat", exist_ok=True)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    message = models.EventChatMessage(
        room_id=room_id,
        sender_id=sender_id,
        media_url=filepath,
        timestamp=datetime.utcnow()
    )

    db.add(message)
    db.commit()
    db.refresh(message)
    return {"message": "Media uploaded", "media_url": filepath}


# ------------------------------------------------------------
# PIN MESSAGE
# ------------------------------------------------------------
@router.post("/pin/{message_id}")
def pin_message(message_id: int, admin_id: int, db: Session = Depends(get_db)):
    message = db.query(models.EventChatMessage).filter(models.EventChatMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Check admin
    admin = db.query(models.EventChatAdmin).filter(
        models.EventChatAdmin.room_id == message.room_id,
        models.EventChatAdmin.user_id == admin_id
    ).first()

    if not admin:
        raise HTTPException(status_code=403, detail="Not an admin")

    message.is_pinned = True
    db.commit()
    return {"message": "Message pinned"}


# ------------------------------------------------------------
# DELETE MESSAGE
# ------------------------------------------------------------
@router.delete("/message/{message_id}")
def delete_message(message_id: int, admin_id: int, db: Session = Depends(get_db)):
    message = db.query(models.EventChatMessage).filter(models.EventChatMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    admin = db.query(models.EventChatAdmin).filter(
        models.EventChatAdmin.room_id == message.room_id,
        models.EventChatAdmin.user_id == admin_id
    ).first()

    if not admin:
        raise HTTPException(status_code=403, detail="Not an admin")

    message.is_deleted = True
    db.commit()
    return {"message": "Message deleted"}


# ------------------------------------------------------------
# ADD CHAT ADMIN
# ------------------------------------------------------------
@router.post("/admin/add")
def add_chat_admin(room_id: int, user_id: int, db: Session = Depends(get_db)):
    room = db.query(models.EventChatRoom).filter(models.EventChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    admin = models.EventChatAdmin(room_id=room_id, user_id=user_id)
    db.add(admin)
    db.commit()
    return {"message": "Admin added"}
