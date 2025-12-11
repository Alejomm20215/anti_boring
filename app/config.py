"""Configuration helpers for the PR summarizer service."""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass
class Settings:
    hf_api_token: str
    hf_model_id: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    llm_temperature: float = 0.2
    llm_max_new_tokens: int = 512

    github_token: Optional[str] = None
    github_api_base: str = "https://api.github.com"
    http_timeout_seconds: int = 20


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    hf_api_token = os.getenv("HF_API_TOKEN")
    if not hf_api_token:
        raise RuntimeError("HF_API_TOKEN is required")

    return Settings(
        hf_api_token=hf_api_token,
        hf_model_id=os.getenv("HF_MODEL_ID", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", 0.2)),
        llm_max_new_tokens=int(os.getenv("LLM_MAX_NEW_TOKENS", 512)),
        github_token=os.getenv("GITHUB_TOKEN"),
        github_api_base=os.getenv("GITHUB_API_BASE", "https://api.github.com"),
        http_timeout_seconds=int(os.getenv("HTTP_TIMEOUT_SECONDS", 20)),
    )

