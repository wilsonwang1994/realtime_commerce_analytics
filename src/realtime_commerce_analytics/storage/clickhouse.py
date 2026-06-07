from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from realtime_commerce_analytics.config import settings


DDL = [
    "CREATE DATABASE IF NOT EXISTS commerce",
    """
    CREATE TABLE IF NOT EXISTS commerce.raw_events (
        event_id String,
        event_type LowCardinality(String),
        event_time DateTime64(3, 'UTC'),
        ingest_time DateTime64(3, 'UTC'),
        payload String
    ) ENGINE = MergeTree
    ORDER BY (event_type, event_time, event_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS commerce.metric_1m (
        window_start DateTime('UTC'),
        gmv Float64,
        order_count UInt64,
        paid_order_count UInt64,
        refund_count UInt64,
        refund_amount Float64,
        payment_success_count UInt64,
        payment_failed_count UInt64,
        conversion_rate Float64,
        refund_rate Float64,
        version UInt64
    ) ENGINE = ReplacingMergeTree(version)
    ORDER BY window_start
    """,
    """
    CREATE TABLE IF NOT EXISTS commerce.processed_event_ids (
        event_id String,
        processed_at DateTime64(3, 'UTC')
    ) ENGINE = MergeTree
    ORDER BY event_id
    """,
]


def get_client() -> Client:
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_username,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


def init_db(client: Client | None = None) -> None:
    client = client or get_client()
    for stmt in DDL:
        client.command(stmt)


def insert_raw_event(client: Client, *, event_id: str, event_type: str, event_time: datetime, payload: str) -> None:
    client.insert(
        "raw_events",
        [[event_id, event_type, event_time, datetime.now(timezone.utc), payload]],
        column_names=["event_id", "event_type", "event_time", "ingest_time", "payload"],
    )


def is_processed(client: Client, event_id: str) -> bool:
    result = client.query("SELECT count() FROM processed_event_ids WHERE event_id = %(event_id)s", {"event_id": event_id})
    return bool(result.result_rows[0][0])


def mark_processed(client: Client, event_id: str) -> None:
    client.insert(
        "processed_event_ids",
        [[event_id, datetime.now(timezone.utc)]],
        column_names=["event_id", "processed_at"],
    )


def insert_metric_rows(client: Client, rows: Iterable[dict]) -> None:
    rows = list(rows)
    if not rows:
        return
    client.insert(
        "metric_1m",
        [
            [
                r["window_start"],
                r["gmv"],
                r["order_count"],
                r["paid_order_count"],
                r["refund_count"],
                r["refund_amount"],
                r["payment_success_count"],
                r["payment_failed_count"],
                r["conversion_rate"],
                r["refund_rate"],
                r["version"],
            ]
            for r in rows
        ],
        column_names=[
            "window_start",
            "gmv",
            "order_count",
            "paid_order_count",
            "refund_count",
            "refund_amount",
            "payment_success_count",
            "payment_failed_count",
            "conversion_rate",
            "refund_rate",
            "version",
        ],
    )


def reset_tables(client: Client | None = None) -> None:
    client = client or get_client()
    init_db(client)
    for table in ["raw_events", "metric_1m", "processed_event_ids"]:
        client.command(f"TRUNCATE TABLE IF EXISTS {table}")
