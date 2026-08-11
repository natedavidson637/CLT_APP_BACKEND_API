from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import SessionLocal
from .. import models, schemas
from datetime import datetime

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------
# CREATE REVIEW
# ------------------------------------------------------------
@router.post("/", response_model=schemas.Review)
def create_review(review: schemas.ReviewBase, user_id: int, db: Session = Depends(get_db)):
    new_review = models.Review(
        user_id=user_id,
        target_type=review.target_type,
        target_id=review.target_id,
        rating=review.rating,
        text=review.text,
        created_at=datetime.utcnow()
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


# ------------------------------------------------------------
# GET REVIEWS FOR TARGET (event/location/restaurant)
# ------------------------------------------------------------
@router.get("/target/{target_type}/{target_id}", response_model=list[schemas.Review])
def get_reviews_for_target(target_type: str, target_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).filter(
        models.Review.target_type == target_type,
        models.Review.target_id == target_id
    ).order_by(models.Review.created_at.desc()).all()

    return reviews


# ------------------------------------------------------------
# GET REVIEWS BY USER
# ------------------------------------------------------------
@router.get("/user/{user_id}", response_model=list[schemas.Review])
def get_reviews_by_user(user_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).filter(
        models.Review.user_id == user_id
    ).order_by(models.Review.created_at.desc()).all()

    return reviews


# ------------------------------------------------------------
# UPDATE REVIEW
# ------------------------------------------------------------
@router.patch("/{review_id}")
def update_review(review_id: int, update: schemas.ReviewBase, user_id: int, db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your review")

    for key, value in update.dict(exclude_unset=True).items():
        setattr(review, key, value)

    db.commit()
    return {"message": "Review updated"}


# ------------------------------------------------------------
# DELETE REVIEW
# ------------------------------------------------------------
@router.delete("/{review_id}")
def delete_review(review_id: int, user_id: int, db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your review")

    db.delete(review)
    db.commit()
    return {"message": "Review deleted"}


# ------------------------------------------------------------
# GET AVERAGE RATING FOR TARGET
# ------------------------------------------------------------
@router.get("/average/{target_type}/{target_id}")
def get_average_rating(target_type: str, target_id: int, db: Session = Depends(get_db)):
    avg = db.query(func.avg(models.Review.rating)).filter(
        models.Review.target_type == target_type,
        models.Review.target_id == target_id
    ).scalar()

    return {"average_rating": round(avg or 0, 2)}


# ------------------------------------------------------------
# GET RATING DISTRIBUTION (1–5 stars)
# ------------------------------------------------------------
@router.get("/distribution/{target_type}/{target_id}")
def get_rating_distribution(target_type: str, target_id: int, db: Session = Depends(get_db)):
    distribution = {}

    for rating in range(1, 6):
        count = db.query(models.Review).filter(
            models.Review.target_type == target_type,
            models.Review.target_id == target_id,
            models.Review.rating == rating
        ).count()

        distribution[rating] = count

    return distribution
