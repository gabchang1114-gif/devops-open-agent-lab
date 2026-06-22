from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    service_name: str = "devops-open-agent"
    version: str = "0.1.0"

    llm_provider: str = "openai"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-latest"

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    llm_timeout: int = 120

    kubeconfig_path: str = ""

    kube_api_host_rewrite: str = ""

    aws_profile: str = ""
    aws_default_region: str = "us-east-1"

    log_level: str = "INFO"

    multi_cluster_enabled: bool = True
    topology_graph_enabled: bool = False
    memory_enabled: bool = False

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    database_path: str = "data/investigations.db"

    postgres_url: str = "postgresql+asyncpg://kda:kda@localhost:5432/kda"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    seed_default_admin: bool = True
    default_admin_email: str = "admin"
    default_admin_password: str = ""

    github_token: str = ""
    github_webhook_secret: str = ""
    github_api_base_url: str = "https://api.github.com"
    github_app_id: str = ""
    github_private_key: str = ""
    github_installation_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
