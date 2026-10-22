
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PaymentStatus = Literal["paid", "pending", "failed"]


class PaymentCreate(BaseModel):
    policy_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_date: datetime | None = None
    payment_method: str = Field(min_length=2, max_length=50)
    status: PaymentStatus = "pending"
    transaction_reference: str = Field(min_length=3, max_length=100)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    policy_id: int
    amount: Decimal
    payment_date: datetime | None
    payment_method: str
    status: str
    transaction_reference: str
