from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
from datetime import datetime

router = APIRouter(prefix="/safety", tags=["Safety"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------
# REPORT SOMETHING (user/event/post)
# ------------------------------------------------------------
@router.post("/report", response_model=schemas.Report)
def create_report(report: schemas.ReportBase, reporter_id: int, db: Session = Depends(get_db)):
    new_report = models.Report(
        reporter_id=reporter_id,
        target_type=report.target_type,
        target_id=report.target_id,
        reason=report.reason,
        details=report.details,
        created_at=datetime.utcnow()
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


# ------------------------------------------------------------
# GET ALL REPORTS (admin dashboard)
# ------------------------------------------------------------
@router.get("/reports", response_model=list[schemas.Report])
def get_all_reports(db: Session = Depends(get_db)):
    reports = db.query(models.Report).order_by(models.Report.created_at.desc()).all()
    return reports


# ------------------------------------------------------------
# GET REPORTS FOR SPECIFIC TARGET
# ------------------------------------------------------------
@router.get("/reports/{target_type}/{target_id}", response_model=list[schemas.Report])
def get_reports_for_target(target_type: str, target_id: int, db: Session = Depends(get_db)):
    reports = db.query(models.Report).filter(
        models.Report.target_type == target_type,
        models.Report.target_id == target_id
    ).order_by(models.Report.created_at.desc()).all()

    return reports


# ------------------------------------------------------------
# BLOCK USER
# ------------------------------------------------------------
@router.post("/block/{user_id}/{blocked_id}")
def block_user(user_id: int, blocked_id: int, db: Session = Depends(get_db)):
    if user_id == blocked_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    existing = db.query(models.BlockedUser).filter(
        models.BlockedUser.user_id == user_id,
        models.BlockedUser.blocked_user_id == blocked_id
    ).first()

    if existing:
        return {"message": "User already blocked"}

    block = models.BlockedUser(
        user_id=user_id,
        blocked_user_id=blocked_id,
        created_at=datetime.utcnow()
    )

    db.add(block)
    db.commit()
    return {"message": "User blocked"}


# ------------------------------------------------------------
# UNBLOCK USER
# ------------------------------------------------------------
@router.delete("/block/{user_id}/{blocked_id}")
def unblock_user(user_id: int, blocked_id: int, db: Session = Depends(get_db)):
    block = db.query(models.BlockedUser).filter(
        models.BlockedUser.user_id == user_id,
        models.BlockedUser.blocked_user_id == blocked_id
    ).first()

    if not block:
        raise HTTPException(status_code=404, detail="User not blocked")

    db.delete(block)
    db.commit()
    return {"message": "User unblocked"}


# ------------------------------------------------------------
# GET USER BLOCK LIST
# ------------------------------------------------------------
@router.get("/block/{user_id}", response_model=list[schemas.BlockedUser])
def get_block_list(user_id: int, db: Session = Depends(get_db)):
    blocks = db.query(models.BlockedUser).filter(
        models.BlockedUser.user_id == user_id
    ).order_by(models.BlockedUser.created_at.desc()).all()

    return blocks


# ------------------------------------------------------------
# ADMIN: MARK REPORT AS RESOLVED
# ------------------------------------------------------------
@router.post("/resolve/{report_id}")
def resolve_report(report_id: int, admin_id: int, db: Session = Depends(get_db)):
    # In future: check admin privileges
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Soft delete or mark resolved
    report.details += "\n\n[RESOLVED]"
    db.commit()

    return {"message": "Report marked as resolved"}
