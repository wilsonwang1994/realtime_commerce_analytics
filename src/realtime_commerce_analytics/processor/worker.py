from __future__ import annotations

import json
import signal
import sys
from datetime import timezone

from confluent_kafka import Consumer, KafkaException

from realtime_commerce_analytics.config import settings
from realtime_commerce_analytics.events.models import parse_event
from realtime_commerce_analytics.processor.metrics import MetricAggregator
from realtime_commerce_analytics.storage.clickhouse import (
    get_client,
    init_db,
    insert_metric_rows,
    insert_raw_event,
    is_processed,
    mark_processed,
)

running = True


def stop(*_: object) -> None:
    global running
    running = False


def main() -> None:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    client = get_client()
    init_db(client)
    aggregator = MetricAggregator()

    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": settings.consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
    )
    consumer.subscribe([settings.order_topic, settings.payment_topic])

    print(
        f"Listening to topics {settings.order_topic}, {settings.payment_topic} "
        f"on {settings.kafka_bootstrap_servers}",
        flush=True,
    )

    try:
        while running:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            payload_raw = msg.value().decode("utf-8")
            payload = json.loads(payload_raw)
            event = parse_event(payload)

            if is_processed(client, event.event_id):
                continue

            insert_raw_event(
                client,
                event_id=event.event_id,
                event_type=str(event.event_type),
                event_time=event.event_time.astimezone(timezone.utc),
                payload=payload_raw,
            )
            bucket = aggregator.process(event)
            mark_processed(client, event.event_id)

            if bucket is not None:
                insert_metric_rows(client, [bucket.as_row()])
                print(f"processed {event.event_id} -> {bucket.window_start.isoformat()}", flush=True)
    finally:
        consumer.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"worker failed: {exc}", file=sys.stderr, flush=True)
        raise
