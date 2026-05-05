from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    yandex_gpt_api_key: str
    yandex_gpt_folder_id: str
    yandex_gpt_model: str = "yandexgpt-lite"
    yandex_gpt_url: str = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()