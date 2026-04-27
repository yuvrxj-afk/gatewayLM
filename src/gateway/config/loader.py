from pathlib import Path

import yaml
from pydantic import BaseModel


class RateLimits(BaseModel):
    requests_per_minute: int
    tokens_per_minute: int


class Budget(BaseModel):
    monthly_usd: float
    warning_threshold: float


class Team(BaseModel):
    id: str
    name: str
    api_key: str
    allowed_models: list[str]
    rate_limits: RateLimits
    budget: Budget
    priority: str
    system_prompt: str | None = None


class FallbackEntry(BaseModel):
    provider: str
    model: str


class GatewayConfig(BaseModel):
    teams: list[Team]
    fallback_chains: dict[str, list[FallbackEntry]]


def load_config(path: str = "config/teams.yaml") -> GatewayConfig:
    raw = Path(path).read_text()
    data = yaml.safe_load(raw)
    return GatewayConfig.model_validate(data)
