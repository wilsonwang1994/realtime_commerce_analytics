from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore")

    kafka_bootstrap_servers: str = Field("localhost:19092")
    order_topic: str = Field("order-events")
    payment_topic: str = Field("payment-events")
    consumer_group: str = Field("commerce-analytics-worker")

    clickhouse_host: str = Field("localhost")
    clickhouse_port: int = Field(8123)
    clickhouse_username: str = Field("default")
    clickhouse_password: str = Field("")
    clickhouse_database: str = Field("commerce")


settings = Settings()
