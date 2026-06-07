from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
random.seed(42)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def main() -> None:
    start = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    events = []

    for i in range(1, 101):
        order_id = f"order-{i:04d}"
        user_id = f"user-{random.randint(1, 40):03d}"
        amount = random.randint(20, 500)
        created_time = start + timedelta(seconds=random.randint(0, 600))
        paid_time = created_time + timedelta(seconds=random.randint(5, 120))

        created = {
            "schema_version": 1,
            "event_id": str(uuid4()),
            "event_type": "order",
            "event_time": iso(created_time),
            "order_id": order_id,
            "user_id": user_id,
            "status": "created",
            "amount": amount,
            "currency": "USD",
        }
        paid = {
            "schema_version": 2,
            "event_id": str(uuid4()),
            "event_type": "order",
            "event_time": iso(paid_time),
            "order_id": order_id,
            "user_id": user_id,
            "status": "paid",
            "amount": amount,
            "currency": "USD",
            "coupon_amount": random.choice([None, 5, 10]),
        }
        payment = {
            "schema_version": 1,
            "event_id": str(uuid4()),
            "event_type": "payment",
            "event_time": iso(paid_time + timedelta(seconds=random.randint(-30, 180))),
            "payment_id": f"pay-{i:04d}",
            "order_id": order_id,
            "status": "success" if random.random() > 0.08 else "failed",
            "amount": amount,
            "currency": "USD",
            "provider": random.choice(["stripe", "adyen", "paypal"]),
        }
        events.extend([created, paid, payment])

        if random.random() < 0.12:
            refund = {
                "schema_version": 1,
                "event_id": str(uuid4()),
                "event_type": "payment",
                "event_time": iso(paid_time + timedelta(minutes=random.randint(1, 30))),
                "payment_id": f"refund-{i:04d}",
                "order_id": order_id,
                "status": "refunded",
                "amount": amount,
                "currency": "USD",
                "provider": payment["provider"],
            }
            events.append(refund)

        if random.random() < 0.08:
            duplicate = dict(payment)
            events.append(duplicate)

    random.shuffle(events)

    out = ROOT / "events.jsonl"
    with out.open("w") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"wrote {len(events)} events to {out}")


if __name__ == "__main__":
    main()
