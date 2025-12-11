"""Pydantic models for the PR summarizer service."""

from typing import List, Optional

from pydantic import BaseModel, Field


class PRPayload(BaseModel):
    repo: str = Field(..., description="Repository full name owner/repo")
    number: int = Field(..., description="Pull request number")
    title: str
    body: Optional[str] = None
    state: str
    merged: bool
    merged_at: Optional[str] = None
    created_at: str
    author: str
    files: List[str] = Field(default_factory=list, description="Changed file paths")
    reviews: List[str] = Field(default_factory=list, description="Review texts or states")
    additions: Optional[int] = None
    deletions: Optional[int] = None
    commits: Optional[int] = None
    url: str
    labels: List[str] = Field(default_factory=list)
    base_branch: Optional[str] = None
    head_branch: Optional[str] = None


class SummaryResponse(BaseModel):
    summary: str


class SummaryFullResponse(BaseModel):
    summary: str
    pr: PRPayload


class GitHubPRRequest(BaseModel):
    repo: str = Field(..., description="Repository full name owner/repo")
    number: int = Field(..., description="Pull request number")


