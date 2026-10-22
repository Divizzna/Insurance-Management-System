
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.db import SessionLocal

router = APIRouter(
    prefix="/api/v1/policies",
    tags=["Policies"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_policies(db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT
                policy_id,
                policy_number,
                customer_id,
                product_id,
                start_date,
                end_date,
                coverage_amount,
                premium_amount,
                status
            FROM policies
            ORDER BY policy_id
        """)
    ).mappings().all()

    return [dict(row) for row in rows]


@router.get("/{policy_id}")
def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("""
            SELECT
                policy_id,
                policy_number,
                customer_id,
                product_id,
                start_date,
                end_date,
                coverage_amount,
                premium_amount,
                status
            FROM policies
            WHERE policy_id = :policy_id
        """),
        {"policy_id": policy_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Policy not found",
        )

    return dict(row)


from fastapi import Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.schemas.policy import (
    PolicyCreate,
    PolicyUpdate,
    PolicyResponse,
)

# Reuse your existing router if it is already defined:
# router = APIRouter(prefix="/api/v1/policies", tags=["Policies"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


POLICY_SELECT = """
    SELECT policy_id, policy_number, customer_id, product_id,
           start_date, end_date, coverage_amount,
           premium_amount, status
    FROM policies
"""


def validate_references(db: Session, customer_id: int, product_id: int):
    customer = db.execute(
        text("SELECT customer_id FROM customers WHERE customer_id = :id"),
        {"id": customer_id},
    ).first()

    if customer is None:
        raise HTTPException(status_code=400, detail="Customer does not exist")

    product = db.execute(
        text("""
            SELECT product_id
            FROM insurance_products
            WHERE product_id = :id
        """),
        {"id": product_id},
    ).first()

    if product is None:
        raise HTTPException(status_code=400, detail="Insurance product does not exist")


def read_policy(db: Session, policy_id: int):
    row = db.execute(
        text(POLICY_SELECT + " WHERE policy_id = :id"),
        {"id": policy_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    return dict(row)


@router.post("", response_model=PolicyResponse, status_code=201)
def create_policy(
    policy: PolicyCreate,
    db: Session = Depends(get_db),
):
    if policy.end_date < policy.start_date:
        raise HTTPException(
            status_code=422,
            detail="End date cannot be earlier than start date",
        )

    validate_references(db, policy.customer_id, policy.product_id)

    try:
        result = db.execute(
            text("""
                INSERT INTO policies (
                    policy_number, customer_id, product_id,
                    start_date, end_date, coverage_amount,
                    premium_amount, status
                )
                VALUES (
                    :policy_number, :customer_id, :product_id,
                    :start_date, :end_date, :coverage_amount,
                    :premium_amount, :status
                )
            """),
            policy.model_dump(),
        )
        policy_id = result.lastrowid
        db.commit()
        return read_policy(db, policy_id)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Policy number may already exist or a database constraint failed",
        ) from exc


@router.put("/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: int,
    policy: PolicyUpdate,
    db: Session = Depends(get_db),
):
    read_policy(db, policy_id)

    if policy.end_date < policy.start_date:
        raise HTTPException(
            status_code=422,
            detail="End date cannot be earlier than start date",
        )

    validate_references(db, policy.customer_id, policy.product_id)

    try:
        db.execute(
            text("""
                UPDATE policies
                SET policy_number = :policy_number,
                    customer_id = :customer_id,
                    product_id = :product_id,
                    start_date = :start_date,
                    end_date = :end_date,
                    coverage_amount = :coverage_amount,
                    premium_amount = :premium_amount,
                    status = :status
                WHERE policy_id = :policy_id
            """),
            {**policy.model_dump(), "policy_id": policy_id},
        )
        db.commit()
        return read_policy(db, policy_id)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Policy update conflicts with a database constraint",
        ) from exc


@router.delete("/{policy_id}", status_code=204)
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
):
    read_policy(db, policy_id)

    try:
        db.execute(
            text("DELETE FROM policies WHERE policy_id = :id"),
            {"id": policy_id},
        )
        db.commit()
        return Response(status_code=204)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This policy has related payments or claims and cannot be deleted",
        ) from exc
