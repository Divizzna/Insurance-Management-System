
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.schemas.customer import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT customer_id, full_name, email, phone, date_of_birth
            FROM customers
            ORDER BY customer_id
        """)
    ).mappings().all()

    return [dict(row) for row in rows]


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT customer_id, full_name, email, phone, date_of_birth
            FROM customers
            WHERE customer_id = :customer_id
        """),
        {"customer_id": customer_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return dict(row)


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):
    result = db.execute(
        text("""
            INSERT INTO customers
                (full_name, email, phone, date_of_birth)
            VALUES
                (:full_name, :email, :phone, :date_of_birth)
        """),
        customer.model_dump(),
    )

    customer_id = result.lastrowid
    db.commit()

    row = db.execute(
        text("""
            SELECT customer_id, full_name, email, phone, date_of_birth
            FROM customers
            WHERE customer_id = :customer_id
        """),
        {"customer_id": customer_id},
    ).mappings().one()

    return dict(row)
