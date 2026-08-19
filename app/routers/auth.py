from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
from ..utils.auth import hash_password, verify_password, create_token
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.options("/register")
async def register_options():
    return Response(status_code=200)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        password_hash=hashed,
        age=user.age,
        gender=user.gender,
        bio=user.bio,
        interests=user.interests,
        profile_visibility=user.profile_visibility,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/{user_id}/token")
def update_fcm_token(user_id: int, token: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.fcm_token = token
    db.commit()
    return {"message": "FCM token updated"}
