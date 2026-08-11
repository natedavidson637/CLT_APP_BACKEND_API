from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/users", tags=["Users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}")
def update_user(user_id: int, update: schemas.UserBase, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in update.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    return {"message": "Profile updated"}


@router.post("/{user_id}/follow/{target_id}")
def follow_user(user_id: int, target_id: int, db: Session = Depends(get_db)):
    if user_id == target_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    existing = db.query(models.Follower).filter(
        models.Follower.follower_id == user_id,
        models.Follower.following_id == target_id
    ).first()

    if existing:
        return {"message": "Already following"}

    follow = models.Follower(follower_id=user_id, following_id=target_id)
    db.add(follow)
    db.commit()
    return {"message": "Followed"}


@router.delete("/{user_id}/follow/{target_id}")
def unfollow_user(user_id: int, target_id: int, db: Session = Depends(get_db)):
    follow = db.query(models.Follower).filter(
        models.Follower.follower_id == user_id,
        models.Follower.following_id == target_id
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="Not following")

    db.delete(follow)
    db.commit()
    return {"message": "Unfollowed"}
