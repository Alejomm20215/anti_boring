"""HTTP routes for the PR summarizer service."""

from fastapi import APIRouter, Header

from .models import GitHubPRRequest, PRPayload, SummaryFullResponse, SummaryResponse
from .service import summarize_from_github, summarize_payload

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/summarize", response_model=SummaryResponse)
def summarize(payload: PRPayload) -> SummaryResponse:
    return summarize_payload(payload)


@router.post("/summarize/github", response_model=SummaryFullResponse)
def summarize_github(
    request: GitHubPRRequest,
    x_github_token: str | None = Header(default=None, convert_underscores=False),
) -> SummaryFullResponse:
    return summarize_from_github(request, token_override=x_github_token)


