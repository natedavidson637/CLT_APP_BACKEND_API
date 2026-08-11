from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
from datetime import datetime
import uuid
import os

router = APIRouter(prefix="/feed", tags=["Feed"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------
# UPLOAD VIDEO + THUMBNAIL
# ------------------------------------------------------------
@router.post("/upload")
def upload_video(
        user_id: int,
        event_id: int | None = None,
        caption: str = "",
        tags: list[str] | None = None,
        video: UploadFile = File(...),
        thumbnail: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    # Save video
    video_ext = video.filename.split(".")[-1]
    video_name = f"{uuid.uuid4()}.{video_ext}"
    video_path = f"uploads/feed/videos/{video_name}"

    os.makedirs("uploads/feed/videos", exist_ok=True)
    with open(video_path, "wb") as f:
        f.write(video.file.read())

    # Save thumbnail
    thumb_ext = thumbnail.filename.split(".")[-1]
    thumb_name = f"{uuid.uuid4()}.{thumb_ext}"
    thumb_path = f"uploads/feed/thumbnails/{thumb_name}"

    os.makedirs("uploads/feed/thumbnails", exist_ok=True)
    with open(thumb_path, "wb") as f:
        f.write(thumbnail.file.read())

    # Create feed post
    post = models.FeedPost(
        user_id=user_id,
        event_id=event_id,
        video_url=video_path,
        thumbnail_url=thumb_path,
        caption=caption,
        tags=tags or [],
        created_at=datetime.utcnow()
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return {"message": "Post uploaded", "post_id": post.id}


# ------------------------------------------------------------
# GET GLOBAL FEED (TikTok-style)
# ------------------------------------------------------------
@router.get("/global", response_model=list[schemas.FeedPost])
def global_feed(db: Session = Depends(get_db)):
    posts = db.query(models.FeedPost).order_by(models.FeedPost.created_at.desc()).limit(50).all()
    return posts


# ------------------------------------------------------------
# GET USER FEED
# ------------------------------------------------------------
@router.get("/user/{user_id}", response_model=list[schemas.FeedPost])
def user_feed(user_id: int, db: Session = Depends(get_db)):
    posts = db.query(models.FeedPost).filter(
        models.FeedPost.user_id == user_id
    ).order_by(models.FeedPost.created_at.desc()).all()

    return posts


# ------------------------------------------------------------
# GET EVENT FEED (Event recap videos)
# ------------------------------------------------------------
@router.get("/event/{event_id}", response_model=list[schemas.FeedPost])
def event_feed(event_id: int, db: Session = Depends(get_db)):
    posts = db.query(models.FeedPost).filter(
        models.FeedPost.event_id == event_id
    ).order_by(models.FeedPost.created_at.desc()).all()

    return posts


# ------------------------------------------------------------
# LIKE POST
# ------------------------------------------------------------
@router.post("/like/{post_id}")
def like_post(post_id: int, user_id: int, db: Session = Depends(get_db)):
    existing = db.query(models.FeedLike).filter(
        models.FeedLike.post_id == post_id,
        models.FeedLike.user_id == user_id
    ).first()

    if existing:
        return {"message": "Already liked"}

    like = models.FeedLike(
        post_id=post_id,
        user_id=user_id,
        created_at=datetime.utcnow()
    )

    db.add(like)
    db.commit()
    return {"message": "Post liked"}


# ------------------------------------------------------------
# VIEW POST (increments view count)
# ------------------------------------------------------------
@router.post("/view/{post_id}")
def view_post(post_id: int, user_id: int | None = None, db: Session = Depends(get_db)):
    view = models.FeedView(
        post_id=post_id,
        user_id=user_id,
        created_at=datetime.utcnow()
    )

    db.add(view)
    db.commit()
    return {"message": "View recorded"}


# ------------------------------------------------------------
# COMMENT ON POST
# ------------------------------------------------------------
@router.post("/comment/{post_id}", response_model=schemas.FeedComment)
def comment_post(post_id: int, user_id: int, text: str, db: Session = Depends(get_db)):
    comment = models.FeedComment(
        post_id=post_id,
        user_id=user_id,
        text=text,
        created_at=datetime.utcnow()
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


# ------------------------------------------------------------
# GET COMMENTS
# ------------------------------------------------------------
@router.get("/comments/{post_id}", response_model=list[schemas.FeedComment])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.FeedComment).filter(
        models.FeedComment.post_id == post_id
    ).order_by(models.FeedComment.created_at.asc()).all()

    return comments


# ------------------------------------------------------------
# TRENDING FEED (simple algorithm)
# ------------------------------------------------------------
@router.get("/trending", response_model=list[schemas.FeedPost])
def trending_feed(db: Session = Depends(get_db)):
    # Trending score = likes * 2 + views
    trending = db.query(models.FeedPost).all()

    scored = []
    for post in trending:
        likes = db.query(models.FeedLike).filter(models.FeedLike.post_id == post.id).count()
        views = db.query(models.FeedView).filter(models.FeedView.post_id == post.id).count()
        score = likes * 2 + views

        scored.append((score, post))

    scored.sort(reverse=True, key=lambda x: x[0])
    top_posts = [p for _, p in scored[:50]]

    return top_posts


# ------------------------------------------------------------
# RECOMMENDED FEED (starter version)
# ------------------------------------------------------------
@router.get("/recommended/{user_id}", response_model=list[schemas.FeedPost])
def recommended_feed(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    interests = user.interests or []

    if not interests:
        return db.query(models.FeedPost).order_by(models.FeedPost.created_at.desc()).limit(50).all()

    posts = db.query(models.FeedPost).filter(
        models.FeedPost.tags.overlap(interests)
    ).order_by(models.FeedPost.created_at.desc()).limit(50).all()

    return posts
