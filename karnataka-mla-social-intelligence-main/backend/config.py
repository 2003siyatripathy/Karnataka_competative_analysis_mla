from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/mla_social"
    x_bearer_token: str = ""
    youtube_api_key: str = ""
    demo_mode: bool = True
    api_base_url: str = "http://localhost:8000"
    poll_interval_seconds: int = 300
    sentiment_model: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
