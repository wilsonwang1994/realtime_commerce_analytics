from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from confluent_kafka import Producer

from realtime_commerce_analytics.config import settings


def topic_for(event: dict) -> str:
    if event["event_type"] == "order":
        return settings.order_topic
    if event["event_type"] == "payment":
        return settings.payment_topic
    raise ValueError(f"unknown event_type: {event.get('event_type')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay JSONL events into Kafka.")
    parser.add_argument("--file", default="sample-data/events.jsonl")
    parser.add_argument("--sleep-ms", type=int, default=20)
    args = parser.parse_args()

    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    path = Path(args.file)

    sent = 0
    with path.open() as f:
        for line in f:
            event = json.loads(line)
            producer.produce(
                topic_for(event),
                key=event.get("event_id", ""),
                value=json.dumps(event).encode("utf-8"),
            )
            sent += 1
            producer.poll(0)
            if args.sleep_ms:
                time.sleep(args.sleep_ms / 1000)

    producer.flush()
    print(f"replayed {sent} events from {path}")


if __name__ == "__main__":
    main()
