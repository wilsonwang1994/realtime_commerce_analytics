from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventType(StrEnum):
    ORDER = "order"
    PAYMENT = "payment"


class OrderStatus(StrEnum):
    CREATED = "created"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class BaseEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    event_type: EventType
    event_time: datetime
    schema_version: int = 1

    @field_validator("event_time")
    @classmethod
    def normalize_event_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class OrderEvent(BaseEvent):
    event_type: Literal[EventType.ORDER] = EventType.ORDER
    order_id: str
    user_id: str
    status: OrderStatus
    amount: float = 0.0
    currency: str = "USD"
    coupon_amount: float | None = None


class PaymentEvent(BaseEvent):
    event_type: Literal[EventType.PAYMENT] = EventType.PAYMENT
    payment_id: str
    order_id: str
    status: PaymentStatus
    amount: float = 0.0
    currency: str = "USD"
    provider: str | None = None


Event = OrderEvent | PaymentEvent


def parse_event(payload: dict[str, Any]) -> Event:
    event_type = payload.get("event_type")
    if event_type == EventType.ORDER:
        return OrderEvent.model_validate(payload)
    if event_type == EventType.PAYMENT:
        return PaymentEvent.model_validate(payload)
    raise ValueError(f"Unsupported event_type: {event_type}")
