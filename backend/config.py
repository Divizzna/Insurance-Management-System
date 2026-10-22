from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsureFlow AI"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "insurance_db"
    mysql_user: str = "insurance_user"
    mysql_password: str = ""

    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()