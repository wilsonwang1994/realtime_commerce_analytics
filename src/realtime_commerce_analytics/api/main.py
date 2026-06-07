from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import FastAPI, Query

from realtime_commerce_analytics.storage.clickhouse import get_client, init_db

app = FastAPI(
    title="Realtime Commerce Analytics API",
    version="0.1.0",
    description="API for querying near real-time GMV, order, refund, and conversion metrics.",
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
def get_metrics(
    metric: Literal["gmv", "order_count", "refund_rate", "conversion_rate"] | None = None,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    client = get_client()

    where = []
    params: dict = {"limit": limit}
    if start is not None:
        where.append("window_start >= %(start)s")
        params["start"] = start
    if end is not None:
        where.append("window_start < %(end)s")
        params["end"] = end

    where_sql = "WHERE " + " AND ".join(where) if where else ""
    query = f"""
        SELECT
            window_start,
            argMax(gmv, version) AS gmv,
            argMax(order_count, version) AS order_count,
            argMax(paid_order_count, version) AS paid_order_count,
            argMax(refund_count, version) AS refund_count,
            argMax(refund_amount, version) AS refund_amount,
            argMax(payment_success_count, version) AS payment_success_count,
            argMax(payment_failed_count, version) AS payment_failed_count,
            argMax(conversion_rate, version) AS conversion_rate,
            argMax(refund_rate, version) AS refund_rate
        FROM metric_1m
        {where_sql}
        GROUP BY window_start
        ORDER BY window_start DESC
        LIMIT %(limit)s
    """
    result = client.query(query, params)
    columns = result.column_names
    rows = [dict(zip(columns, row)) for row in result.result_rows]

    if metric:
        rows = [{"window_start": row["window_start"], metric: row[metric]} for row in rows]

    return {"data": rows}
