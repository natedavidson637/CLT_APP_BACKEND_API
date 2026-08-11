from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
import stripe
import os
from datetime import datetime

router = APIRouter(prefix="/payments", tags=["Payments"])

stripe.api_key = os.getenv("STRIPE_SECRET")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------
# CREATE STRIPE CHECKOUT SESSION
# ------------------------------------------------------------
@router.post("/create-session")
def create_checkout_session(event_id: int, user_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not event.price:
        raise HTTPException(status_code=400, detail="Event is free")

    # Create Stripe checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": event.title},
                "unit_amount": event.price * 100,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="https://yourapp.com/payment-success",
        cancel_url="https://yourapp.com/payment-cancel",
    )

    # Save payment record
    payment = models.Payment(
        event_id=event_id,
        user_id=user_id,
        stripe_session_id=session.id,
        amount=event.price,
        status="pending",
        created_at=datetime.utcnow()
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {"checkout_url": session.url, "payment_id": payment.id}


# ------------------------------------------------------------
# VERIFY PAYMENT AFTER CHECKOUT
# ------------------------------------------------------------
@router.post("/verify")
def verify_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    session = stripe.checkout.Session.retrieve(payment.stripe_session_id)

    if session.payment_status == "paid":
        payment.status = "paid"
        db.commit()

        # Create ticket
        ticket = models.Ticket(
            payment_id=payment.id,
            event_id=payment.event_id,
            user_id=payment.user_id,
            qr_code_url=f"https://yourapp.com/ticket/{payment.id}",
            checked_in=False
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return {"message": "Payment verified", "ticket_id": ticket.id}

    return {"message": "Payment not completed yet"}


# ------------------------------------------------------------
# QR CHECK-IN
# ------------------------------------------------------------
@router.post("/check-in/{ticket_id}")
def check_in(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.checked_in = True
    ticket.checked_in_at = datetime.utcnow()
    db.commit()

    return {"message": "Check-in successful"}
