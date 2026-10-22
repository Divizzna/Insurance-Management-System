from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.schemas.claim import ClaimCreate, ClaimUpdate, ClaimResponse


router = APIRouter(
    prefix="/api/v1/claims",
    tags=["Claims"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


CLAIM_COLUMNS = """
    claim_id,
    claim_number,
    policy_id,
    incident_date,
    claim_amount,
    description,
    status,
    decision_reason,
    submitted_at
"""


@router.get("", response_model=list[ClaimResponse])
def list_claims(db: Session = Depends(get_db)):
    rows = db.execute(
        text(f"""
            SELECT {CLAIM_COLUMNS}
            FROM claims
            ORDER BY claim_id
        """)
    ).mappings().all()

    return [dict(row) for row in rows]


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text(f"""
            SELECT {CLAIM_COLUMNS}
            FROM claims
            WHERE claim_id = :claim_id
        """),
        {"claim_id": claim_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    return dict(row)


@router.post("", response_model=ClaimResponse, status_code=201)
def create_claim(
    claim: ClaimCreate,
    db: Session = Depends(get_db),
):
    policy = db.execute(
        text("""
            SELECT policy_id
            FROM policies
            WHERE policy_id = :policy_id
        """),
        {"policy_id": claim.policy_id},
    ).first()

    if policy is None:
        raise HTTPException(
            status_code=400,
            detail="The referenced policy does not exist",
        )

    try:
        result = db.execute(
            text("""
                INSERT INTO claims (
                    claim_number,
                    policy_id,
                    incident_date,
                    claim_amount,
                    description,
                    status,
                    decision_reason
                )
                VALUES (
                    :claim_number,
                    :policy_id,
                    :incident_date,
                    :claim_amount,
                    :description,
                    :status,
                    :decision_reason
                )
            """),
            claim.model_dump(),
        )

        claim_id = result.lastrowid
        db.commit()

        row = db.execute(
            text(f"""
                SELECT {CLAIM_COLUMNS}
                FROM claims
                WHERE claim_id = :claim_id
            """),
            {"claim_id": claim_id},
        ).mappings().one()

        return dict(row)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Claim conflicts with a database constraint. "
                "Check that the claim number is unique and the policy exists."
            ),
        ) from exc


@router.put("/{claim_id}", response_model=ClaimResponse)
def update_claim(
    claim_id: int,
    claim: ClaimUpdate,
    db: Session = Depends(get_db),
):
    existing = db.execute(
        text("""
            SELECT claim_id
            FROM claims
            WHERE claim_id = :claim_id
        """),
        {"claim_id": claim_id},
    ).first()

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    db.execute(
        text("""
            UPDATE claims
            SET incident_date = :incident_date,
                claim_amount = :claim_amount,
                description = :description,
                status = :status,
                decision_reason = :decision_reason
            WHERE claim_id = :claim_id
        """),
        {
            **claim.model_dump(),
            "claim_id": claim_id,
        },
    )

    db.commit()

    row = db.execute(
        text(f"""
            SELECT {CLAIM_COLUMNS}
            FROM claims
            WHERE claim_id = :claim_id
        """),
        {"claim_id": claim_id},
    ).mappings().one()

    return dict(row)


@router.delete("/{claim_id}")
def delete_claim(
    claim_id: int,
    db: Session = Depends(get_db),
):
    existing = db.execute(
        text("""
            SELECT claim_id
            FROM claims
            WHERE claim_id = :claim_id
        """),
        {"claim_id": claim_id},
    ).first()

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    try:
        db.execute(
            text("""
                DELETE FROM claims
                WHERE claim_id = :claim_id
            """),
            {"claim_id": claim_id},
        )
        db.commit()

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "This claim cannot be deleted because another database "
                "record depends on it."
            ),
        ) from exc

    return {
        "message": "Claim deleted successfully",
        "claim_id": claim_id,
    }