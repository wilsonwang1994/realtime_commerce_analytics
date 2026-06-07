from realtime_commerce_analytics.storage.clickhouse import reset_tables

if __name__ == "__main__":
    reset_tables()
    print("ClickHouse tables reset")
