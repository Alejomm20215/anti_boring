# PR Summarizer Service

FastAPI service that fetches PR details from GitHub and summarizes them using Hugging Face Inference. Intended to be called from n8n to create/update tasks (e.g., Notion) and send notifications.

## Endpoints
- `GET /health` — health check
- `POST /summarize` — summarize a PR when you already have the PR payload (see `app/models.py`)
- `POST /summarize/github` — fetches PR details from GitHub (requires token) and returns `{ summary, pr }`

## Environment variables
Set in `.env`:
- `HF_API_TOKEN` (required): Hugging Face Inference token.
- `HF_MODEL_ID` (optional): defaults to `mistralai/Mixtral-8x7B-Instruct-v0.1`.
- `LLM_TEMPERATURE` (optional): default `0.2`.
- `LLM_MAX_NEW_TOKENS` (optional): default `512`.
- `GITHUB_TOKEN` (optional): GitHub PAT if you want the service to fetch PRs without passing `x-github-token` from n8n.
- `GITHUB_API_BASE` (optional): defaults to `https://api.github.com`.
- `HTTP_TIMEOUT_SECONDS` (optional): default `20`.
- `NGROK_AUTHTOKEN` (for tunnel sidecar in docker-compose).

## Local run (no Docker)
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
export HF_API_TOKEN=...  # on Windows: set HF_API_TOKEN=...
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker / Compose
1) Copy env: `cp env.example .env` and fill tokens (HF_API_TOKEN required, NGROK_AUTHTOKEN if using ngrok sidecar).
2) Run: `docker compose up --build`
3) Health: `curl http://localhost:8000/health`

### ngrok sidecar (compose)
The compose file includes an `ngrok` service. With `NGROK_AUTHTOKEN` set, it will publish a tunnel to `pr-summarizer:8000`.
- View the public URL from logs: `docker compose logs ngrok --tail 50`
- Or inspector: `http://localhost:4040/api/tunnels` (4040 is exposed in compose)
Use the `https://<public>.ngrok-free.dev/summarize/github` URL in n8n.

## n8n HTTP Request node config
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
3) HTTP Request → `POST /summarize/github` (ngrok URL)
4) Set derived fields (Month, TaskName, StoryPoints=null, ExternalKey, summary, pr)
5) Notion Create/Update Page (map fields; include LLMDescription = summary, PRInfo = details)
6) Email (SMTP/Gmail) notification

## Testing the API
- Health: `curl http://localhost:8000/health`
- Summarize with GitHub fetch (requires token):  
  `curl -X POST http://localhost:8000/summarize/github -H "Content-Type: application/json" -H "x-github-token: $GITHUB_TOKEN" -d '{"repo":"owner/repo","number":123}'`
- Summarize with payload: see `app/models.py` for `PRPayload` fields.

## Notes
- If you change the ngrok URL (free plan), update the n8n HTTP node URL accordingly.
- If n8n cannot reach your host, use the ngrok URL or deploy the service where n8n has network access.

