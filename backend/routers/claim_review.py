from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.services.claim_review_service import (
    review_claim,
    get_claim_reviews,
    get_all_audit_records,
    get_review_run,
)

router = APIRouter(
    prefix="/api/v1/claims",
    tags=["AI Claim Review & Audit"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/reviews/audit")
def list_ai_audit_records(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve all AI review audit trails and agent results across all claims."""
    return get_all_audit_records(db, limit=limit)


@router.get("/reviews/runs/{run_id}")
def get_ai_review_run_detail(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve detailed agent findings for a specific AI review run."""
    return get_review_run(run_id, db)


@router.post("/{claim_id}/review")
def run_claim_review(
    claim_id: int,
    db: Session = Depends(get_db),
):
    """Execute automated multi-agent AI claim review (ChatGPT + Rule validation)."""
    return review_claim(claim_id, db)


@router.get("/{claim_id}/reviews")
def get_reviews_for_claim(
    claim_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve historical AI review runs and audit findings for a specific claim."""
    return get_claim_reviews(claim_id, db)