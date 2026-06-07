from realtime_commerce_analytics.storage.clickhouse import init_db

if __name__ == "__main__":
    init_db()
    print("ClickHouse schema initialized")
