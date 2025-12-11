"""LLM wrapper using Hugging Face Inference (no LangChain)."""

from functools import lru_cache

from huggingface_hub import InferenceClient

from .config import get_settings, Settings
from .models import PRPayload


SUMMARY_PROMPT = """
You summarize pull requests for tracking tasks. Be concise and specific.
Repo: {repo}
PR: {number} - {title}
State: {state}, Merged: {merged}, Created: {created_at}, MergedAt: {merged_at}
Author: {author}
Base/Head: {base_branch} <- {head_branch}
Labels: {labels}
Body:
{body}
Files:
{files}
Reviews:
{reviews}
Adds/Deletes: {additions}/{deletions}, Commits: {commits}
PR URL: {url}

Return 3-6 bullet sentences that cover the change, risks/tests, and any review signals.
"""


@lru_cache(maxsize=1)
def get_client(settings: Settings | None = None) -> InferenceClient:
    settings = settings or get_settings()
    return InferenceClient(
        model=settings.hf_model_id,
        token=settings.hf_api_token,
        timeout=settings.http_timeout_seconds,
    )


def render_prompt(payload: PRPayload) -> str:
    return SUMMARY_PROMPT.format(
        repo=payload.repo,
        number=payload.number,
        title=payload.title,
        state=payload.state,
        merged=payload.merged,
        created_at=payload.created_at,
        merged_at=payload.merged_at or "n/a",
        author=payload.author,
        base_branch=payload.base_branch or "n/a",
        head_branch=payload.head_branch or "n/a",
        labels=", ".join(payload.labels) if payload.labels else "none",
        body=payload.body or "n/a",
        files="\n".join(payload.files) if payload.files else "n/a",
        reviews="\n".join(payload.reviews) if payload.reviews else "n/a",
        additions=payload.additions or 0,
        deletions=payload.deletions or 0,
        commits=payload.commits or 0,
        url=payload.url,
    ).strip()


def summarize_pr(payload: PRPayload, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    client = get_client(settings)
    prompt = render_prompt(payload)
    # Using text-generation; ensure your model supports it (e.g., Mixtral instruct).
    result = client.text_generation(
        prompt,
        max_new_tokens=settings.llm_max_new_tokens,
        temperature=settings.llm_temperature,
        top_p=0.9,
        do_sample=True,
        repetition_penalty=1.05,
    )
    # InferenceClient returns str directly for text_generation
    return result.strip()

