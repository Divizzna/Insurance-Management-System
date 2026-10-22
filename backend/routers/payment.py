
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(
    prefix="/api/v1/payments",
    tags=["Payments"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


PAYMENT_COLUMNS = """
    payment_id,
    policy_id,
    amount,
    payment_date,
    payment_method,
    status,
    transaction_reference
"""


@router.get("", response_model=list[PaymentResponse])
def list_payments(db: Session = Depends(get_db)):
    rows = db.execute(
        text(f"""
            SELECT {PAYMENT_COLUMNS}
            FROM payments
            ORDER BY payment_id
        """)
    ).mappings().all()

    return [dict(row) for row in rows]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(f"""
            SELECT {PAYMENT_COLUMNS}
            FROM payments
            WHERE payment_id = :payment_id
        """),
        {"payment_id": payment_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return dict(row)


@router.post("", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
):
    policy = db.execute(
        text("""
            SELECT policy_id
            FROM policies
            WHERE policy_id = :policy_id
        """),
        {"policy_id": payment.policy_id},
    ).first()

    if policy is None:
        raise HTTPException(
            status_code=400,
            detail="The referenced policy does not exist",
        )

    try:
        result = db.execute(
            text("""
                INSERT INTO payments (
                    policy_id,
                    amount,
                    payment_date,
                    payment_method,
                    status,
                    transaction_reference
                )
                VALUES (
                    :policy_id,
                    :amount,
                    :payment_date,
                    :payment_method,
                    :status,
                    :transaction_reference
                )
            """),
            payment.model_dump(),
        )

        payment_id = result.lastrowid
        db.commit()

        row = db.execute(
            text(f"""
                SELECT {PAYMENT_COLUMNS}
                FROM payments
                WHERE payment_id = :payment_id
            """),
            {"payment_id": payment_id},
        ).mappings().one()

        return dict(row)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Payment conflicts with a database constraint. "
                "Check the transaction reference and allowed values."
            ),
        ) from exc
