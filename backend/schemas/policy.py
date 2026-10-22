
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PolicyStatus = Literal[
    "active",
    "pending",
    "expired",
    "cancelled",
]


class PolicyCreate(BaseModel):
    policy_number: str = Field(min_length=3, max_length=50)
    customer_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    start_date: date
    end_date: date
    coverage_amount: Decimal = Field(gt=0)
    premium_amount: Decimal = Field(gt=0)
    status: PolicyStatus = "pending"


class PolicyUpdate(PolicyCreate):
    pass


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    policy_id: int
    policy_number: str
    customer_id: int
    product_id: int
    start_date: date
    end_date: date
    coverage_amount: Decimal
    premium_amount: Decimal
    status: str
