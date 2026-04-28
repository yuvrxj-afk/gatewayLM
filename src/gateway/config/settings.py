from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    # App
    app_env: str = "development"
    log_level: str = "INFO"
    config_path: str = "config/teams.yaml"

    # Redis
    redis_url: str

    # providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # Optional overrides for tests / local mocks
    openai_base_url: str = "https://api.openai.com"
    anthropic_base_url: str = "https://api.anthropic.com"



settings = Settings()
