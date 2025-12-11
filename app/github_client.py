"""GitHub client helpers to materialize PR data for summarization."""

from typing import List, Optional

import httpx

from .config import Settings
from .models import PRPayload


class GitHubClientError(RuntimeError):
    pass


def _auth_headers(token: Optional[str]) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_json(client: httpx.Client, url: str) -> dict:
    resp = client.get(url)
    if resp.status_code >= 400:
        raise GitHubClientError(f"GitHub API error {resp.status_code}: {resp.text}")
    return resp.json()


def _fetch_list(client: httpx.Client, url: str) -> List[dict]:
    resp = client.get(url)
    if resp.status_code >= 400:
        raise GitHubClientError(f"GitHub API error {resp.status_code}: {resp.text}")
    return resp.json()


def fetch_pr_payload(
    repo: str,
    number: int,
    settings: Settings,
    token_override: Optional[str] = None,
) -> PRPayload:
    token = token_override or settings.github_token
    if not token:
        raise GitHubClientError("GitHub token is required (set GITHUB_TOKEN or pass header)")

    base_url = settings.github_api_base.rstrip("/")
    with httpx.Client(
        headers=_auth_headers(token),
        timeout=settings.http_timeout_seconds,
    ) as client:
        pr_url = f"{base_url}/repos/{repo}/pulls/{number}"
        files_url = f"{pr_url}/files"
        reviews_url = f"{pr_url}/reviews"

        pr = _fetch_json(client, pr_url)
        files = _fetch_list(client, files_url)
        reviews = _fetch_list(client, reviews_url)

    file_paths = [f.get("filename", "") for f in files]
    review_texts = [
        f"{r.get('state')} by {r.get('user', {}).get('login')}: {r.get('body') or ''}".strip()
        for r in reviews
    ]

    return PRPayload(
        repo=repo,
        number=number,
        title=pr.get("title", ""),
        body=pr.get("body"),
        state=pr.get("state", "unknown"),
        merged=pr.get("merged", False),
        merged_at=pr.get("merged_at"),
        created_at=pr.get("created_at", ""),
        author=pr.get("user", {}).get("login", "unknown"),
        files=file_paths,
        reviews=review_texts,
        additions=pr.get("additions"),
        deletions=pr.get("deletions"),
        commits=pr.get("commits"),
        url=pr.get("html_url", ""),
        labels=[lbl.get("name", "") for lbl in pr.get("labels", [])],
        base_branch=pr.get("base", {}).get("ref"),
        head_branch=pr.get("head", {}).get("ref"),
    )


