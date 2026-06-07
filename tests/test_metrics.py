from datetime import datetime, timezone

from realtime_commerce_analytics.events.models import OrderEvent, PaymentEvent
from realtime_commerce_analytics.processor.metrics import MetricAggregator


def test_dedup_event_id():
    agg = MetricAggregator()
    event = OrderEvent(
        event_id="e1",
        event_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        order_id="o1",
        user_id="u1",
        status="paid",
        amount=100,
    )

    assert agg.process(event) is not None
    assert agg.process(event) is None
    bucket = list(agg.buckets.values())[0]
    assert bucket.gmv == 100


def test_binary_payment_metrics():
    agg = MetricAggregator()
    success = PaymentEvent(
        event_id="p1",
        event_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        payment_id="p1",
        order_id="o1",
        status="success",
        amount=100,
    )
    refund = PaymentEvent(
        event_id="p2",
        event_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        payment_id="r1",
        order_id="o1",
        status="refunded",
        amount=100,
    )

    agg.process(success)
    agg.process(refund)
    bucket = list(agg.buckets.values())[0]
    assert bucket.payment_success_count == 1
    assert bucket.refund_count == 1
    assert bucket.refund_rate == 1.0
    assert bucket.refund_amount == 100


def test_event_time_bucket_for_out_of_order_events():
    agg = MetricAggregator()
    later = OrderEvent(
        event_id="e2",
        event_time=datetime(2026, 1, 1, 10, 5, 10, tzinfo=timezone.utc),
        order_id="o2",
        user_id="u1",
        status="created",
        amount=10,
    )
    earlier = OrderEvent(
        event_id="e3",
        event_time=datetime(2026, 1, 1, 10, 1, 5, tzinfo=timezone.utc),
        order_id="o3",
        user_id="u1",
        status="created",
        amount=20,
    )

    agg.process(later)
    agg.process(earlier)

    assert datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc) in agg.buckets
    assert datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc) in agg.buckets
