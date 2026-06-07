-- Latest 1-minute metrics
SELECT
    window_start,
    argMax(gmv, version) AS gmv,
    argMax(order_count, version) AS order_count,
    argMax(conversion_rate, version) AS conversion_rate,
    argMax(refund_rate, version) AS refund_rate
FROM commerce.metric_1m
GROUP BY window_start
ORDER BY window_start DESC
LIMIT 100;

-- GMV trend
SELECT
    window_start,
    argMax(gmv, version) AS gmv
FROM commerce.metric_1m
GROUP BY window_start
ORDER BY window_start;
