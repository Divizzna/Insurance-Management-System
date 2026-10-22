from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ClaimCreate(BaseModel):
    claim_number: str = Field(min_length=3, max_length=30)
    policy_id: int = Field(gt=0)
    incident_date: date
    claim_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    description: str = Field(min_length=3)
    status: str = Field(default="submitted", max_length=30)
    decision_reason: str | None = None


class ClaimUpdate(BaseModel):
    incident_date: date
    claim_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    description: str = Field(min_length=3)
    status: str = Field(max_length=30)
    decision_reason: str | None = None


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: int
    claim_number: str
    policy_id: int
    incident_date: date
    claim_amount: Decimal
    description: str
    status: str
    decision_reason: str | None
    submitted_at: datetime | None