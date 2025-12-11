# PR Summarizer Service

FastAPI service that fetches PR details from GitHub and summarizes them via Hugging Face Inference. Intended to be called from n8n to populate task trackers (e.g., Notion) and send notifications.

## Architecture (at a glance)
- API: FastAPI (`/summarize` and `/summarize/github`)
- LLM: Hugging Face Inference (no LangChain; direct `huggingface_hub`)
- Fetch: GitHub REST (files, reviews, PR metadata)
- Orchestration: n8n HTTP node calls `/summarize/github`, then Notion + email
- Optional tunnel: ngrok sidecar in docker-compose to expose the service publicly

## Endpoints
- `GET /health` — health check
- `POST /summarize` — summarize a PR when you already have the PR payload (see `app/models.py`)
- `POST /summarize/github` — fetches PR details from GitHub (requires token) and returns `{ summary, pr }`

## Environment variables (`.env`)
- `HF_API_TOKEN` (required): Hugging Face Inference token.
- `HF_MODEL_ID` (optional): defaults to `mistralai/Mixtral-8x7B-Instruct-v0.1`.
- `LLM_TEMPERATURE` (optional): default `0.2`.
- `LLM_MAX_NEW_TOKENS` (optional): default `512`.
- `GITHUB_TOKEN` (optional): GitHub PAT if you want the service to fetch PRs without passing `x-github-token` from n8n.
- `GITHUB_API_BASE` (optional): defaults to `https://api.github.com`.
- `HTTP_TIMEOUT_SECONDS` (optional): default `20`.
- `NGROK_AUTHTOKEN` (optional, for the tunnel sidecar).

## Local run (no Docker)
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
export HF_API_TOKEN=...  # Windows: set HF_API_TOKEN=...
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker / Compose
1) Copy env: `cp env.example .env` and fill tokens (HF_API_TOKEN required; NGROK_AUTHTOKEN if using ngrok sidecar).
2) Run: `docker compose up --build`
3) Health: `curl http://localhost:8000/health`

### ngrok sidecar (compose)
The compose file includes an `ngrok` service. With `NGROK_AUTHTOKEN` set, it will publish a tunnel to `pr-summarizer:8000`.
- View the public URL from logs: `docker compose logs ngrok --tail 50`
- Or via inspector: `http://localhost:4040/api/tunnels` (4040 is exposed)
Use `https://<public>.ngrok-free.dev/summarize/github` in n8n.

## n8n HTTP Request node (minimal config)
- Method: POST
- URL: `https://<public-url>/summarize/github`
- Headers:
  - `Content-Type: application/json`
  - `x-github-token: <PAT>` (omit if service has GITHUB_TOKEN)
- Body (JSON):
```json
{
  "repo": "{{$json.repo}}",
  "number": {{$json.number}}
}
```
Response: `{ "summary": "...", "pr": { ... } }`

## Typical n8n flow
1) Webhook (GitHub PR + review events)
2) Set core fields (repo, number)
3) HTTP Request → `POST /summarize/github` (ngrok/public URL)
4) Set derived fields (Month, TaskName, StoryPoints=null, ExternalKey, summary, pr)
5) Notion Create/Update Page (map fields; e.g., LLMDescription=summary, PRInfo=details)
6) Email (SMTP/Gmail) notification

## Testing the API
- Health: `curl http://localhost:8000/health`
- Summarize with GitHub fetch (requires token):
```bash
curl -X POST http://localhost:8000/summarize/github \
  -H "Content-Type: application/json" \
  -H "x-github-token: $GITHUB_TOKEN" \
  -d '{"repo":"owner/repo","number":123}'
```
- Summarize with payload: see `app/models.py` for `PRPayload` fields.

## Troubleshooting
- 405 Method Not Allowed: ensure you POST, not GET.
- 401/403 from GitHub: token missing/insufficient; set `x-github-token` or `GITHUB_TOKEN`.
- n8n can’t reach service: use ngrok public URL; ensure container is up and HF_API_TOKEN is set.
- Ngrok URL changes on restart (free plan): update n8n HTTP node accordingly or use a reserved domain.

## Security notes
- Keep tokens in `.env` (gitignored). Do not commit secrets.
- Prefer passing GitHub tokens via headers or env, not hardcoding in flows.
- If exposing publicly, use HTTPS (ngrok provides this) and avoid leaving admin ports open.

