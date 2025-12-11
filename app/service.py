"""Service layer combining GitHub fetching and LLM summarization."""

from typing import Optional

from fastapi import HTTPException, status

from .config import get_settings, Settings
from .github_client import fetch_pr_payload, GitHubClientError
from .llm import summarize_pr
from .models import GitHubPRRequest, PRPayload, SummaryFullResponse, SummaryResponse


def summarize_payload(payload: PRPayload, settings: Settings | None = None) -> SummaryResponse:
    settings = settings or get_settings()
    try:
        summary = summarize_pr(payload, settings)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM error: {exc}",
        ) from exc
    return SummaryResponse(summary=summary)


def summarize_from_github(
    request: GitHubPRRequest,
    token_override: Optional[str] = None,
    settings: Settings | None = None,
) -> SummaryFullResponse:
    settings = settings or get_settings()
    try:
        pr_payload = fetch_pr_payload(
            repo=request.repo,
            number=request.number,
            settings=settings,
            token_override=token_override,
        )
    except GitHubClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    summary = summarize_payload(pr_payload, settings).summary
    return SummaryFullResponse(summary=summary, pr=pr_payload)


