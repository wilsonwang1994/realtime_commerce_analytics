from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from realtime_commerce_analytics.events.models import OrderEvent, OrderStatus, PaymentEvent, PaymentStatus


def minute_bucket(ts: datetime) -> datetime:
    ts = ts.astimezone(timezone.utc)
    return ts.replace(second=0, microsecond=0)


@dataclass
class MetricBucket:
    window_start: datetime
    gmv: float = 0.0
    order_count: int = 0
    paid_order_count: int = 0
    refund_count: int = 0
    refund_amount: float = 0.0
    payment_success_count: int = 0
    payment_failed_count: int = 0
    version: int = 0

    @property
    def conversion_rate(self) -> float:
        if self.order_count == 0:
            return 0.0
        return self.paid_order_count / self.order_count

    @property
    def refund_rate(self) -> float:
        if self.payment_success_count == 0:
            return 0.0
        return self.refund_count / self.payment_success_count

    def as_row(self) -> dict:
        return {
            "window_start": self.window_start,
            "gmv": self.gmv,
            "order_count": self.order_count,
            "paid_order_count": self.paid_order_count,
            "refund_count": self.refund_count,
            "refund_amount": self.refund_amount,
            "payment_success_count": self.payment_success_count,
            "payment_failed_count": self.payment_failed_count,
            "conversion_rate": self.conversion_rate,
            "refund_rate": self.refund_rate,
            "version": self.version,
        }


@dataclass
class MetricAggregator:
    """Small event-time metric aggregator used by the local streaming worker.

    This intentionally keeps state in memory for local demo simplicity. In production,
    the same logic would live behind Flink keyed state and checkpoints.
    """

    buckets: dict[datetime, MetricBucket] = field(default_factory=dict)
    seen_event_ids: set[str] = field(default_factory=set)

    def get_bucket(self, ts: datetime) -> MetricBucket:
        key = minute_bucket(ts)
        if key not in self.buckets:
            self.buckets[key] = MetricBucket(window_start=key)
        return self.buckets[key]

    def process(self, event: OrderEvent | PaymentEvent) -> MetricBucket | None:
        if event.event_id in self.seen_event_ids:
            return None
        self.seen_event_ids.add(event.event_id)

        bucket = self.get_bucket(event.event_time)
        bucket.version += 1

        if isinstance(event, OrderEvent):
            if event.status == OrderStatus.CREATED:
                bucket.order_count += 1
            elif event.status == OrderStatus.PAID:
                bucket.paid_order_count += 1
                bucket.gmv += event.amount
            elif event.status == OrderStatus.CANCELLED:
                # Cancellation does not subtract GMV unless a refund event arrives.
                pass

        elif isinstance(event, PaymentEvent):
            if event.status == PaymentStatus.SUCCESS:
                bucket.payment_success_count += 1
            elif event.status == PaymentStatus.FAILED:
                bucket.payment_failed_count += 1
            elif event.status == PaymentStatus.REFUNDED:
                bucket.refund_count += 1
                bucket.refund_amount += event.amount
                bucket.gmv -= event.amount

        return bucket
