# Feature Test Steps

## 1. Set up the project for the first feature test
From the repository root:

```bash
cd /Users/manish/mount/spec-kit/llm-infra
```

Initialize the UV project and create the environment:

```bash
uv init --bare --name llm-infra --description "LiteLLM → Langfuse tracing feature"
uv venv .venv
uv pip install -r requirements.txt
```

If you want to use the virtual environment directly instead of `uv run`, activate it:

```bash
source .venv/bin/activate
```

## 2. Prepare environment files

Before starting the runtime stack, create a dedicated LitellM env file and a Langfuse env file.

```bash
cp litellm/.env.example litellm/.env
cp langfuse/.env.example langfuse/.env
```

Then edit `litellm/.env` and set:
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST`

Then edit `langfuse/.env` and set:
- `NEXTAUTH_SECRET`
- `LANGFUSE_INIT_USER_EMAIL`
- `LANGFUSE_INIT_USER_NAME`
- `LANGFUSE_INIT_USER_PASSWORD`
- `LANGFUSE_INIT_PROJECT_PUBLIC_KEY`
- `LANGFUSE_INIT_PROJECT_SECRET_KEY`
- `LANGFUSE_SERVICE_POSTGRES_USER`
- `LANGFUSE_SERVICE_POSTGRES_PASSWORD`
- `LANGFUSE_SERVICE_POSTGRES_DB`
- `LANGFUSE_SERVICE_DATABASE_URL`

Also verify the LiteLLM internal DB URL is set correctly:

```bash
DATABASE_URL=postgresql://postgres:password@litellm-postgres:5432/litellm
```

## 3. Run the real runtime stack with Docker Compose

Before starting, clean up any stale containers from previous runs:

```bash
docker compose -f litellm/docker-compose.yaml -f langfuse/docker-compose.yml down --remove-orphans
```

Start Langfuse and LiteLLM together so the full trace path is live:

```bash
docker compose -f litellm/docker-compose.yaml -f langfuse/docker-compose.yml up --build
```

This combined stack now uses separate Postgres services:
- `litellm-postgres` for LiteLLM (internal-only, no host port mapping)
- `postgres` for Langfuse (host port `127.0.0.1:5432`)

That means port `5432` on localhost is reserved for the Langfuse Postgres service, while LiteLLM connects to its own internal `litellm-postgres` service.

If you want to validate the merged compose before starting it:

```bash
docker compose -f litellm/docker-compose.yaml -f langfuse/docker-compose.yml config --services
```

If you see `litellm-postgres` and `postgres` both listed, the separation is correct. No `WARN` output should appear—all environment variables are now properly scoped.

Adjust compose file paths if your repository uses a different local setup.

## 4. Set up LiteLLM API keys and models (prerequisites before curl)

The curl request requires valid API keys and models to be configured in LiteLLM.

### Check model configuration

Verify that `qwen-3b` model is already configured in `litellm/config/litellm_config.yaml`:

```bash
grep -A3 "model_name: qwen-3b" litellm/config/litellm_config.yaml
```

If the model is defined, you should see it listed. The vLLM backend is configured to serve this model internally.

### Generate or verify API keys

The API keys are stored as SHA-256 hashes in `litellm/config/api_keys.json`. LiteLLM expects the `X-Api-Key` header to contain the plain API key; it hashes the key internally and compares that hash to the stored entries.

The current sample keys are:

- `sk-test-key-team1-user1-12345` → team-1 / user-1
- `sk-test-key-team2-user1-67890` → team-2 / user-1

Use one of those plain values in `X-Api-Key`.

If you want to verify the mappings, run:

```bash
uv run python3 << 'EOF'
import hashlib
import json

sample_keys = [
    "sk-test-key-team1-user1-12345",
    "sk-test-key-team2-user1-67890",
]

with open("litellm/config/api_keys.json") as f:
    api_keys = json.load(f)

for sample_key in sample_keys:
    hashed = hashlib.sha256(sample_key.encode()).hexdigest()
    print(sample_key)
    print("  hash:", hashed)
    print("  valid:", hashed in api_keys)
    if hashed in api_keys:
        info = api_keys[hashed]
        print("  team:", info["team_id"], "user:", info["user_id"])
    print()
EOF
```

This confirms the plain key and hash mapping, but the request header itself must remain plain text.

## 5. Send a real request through LiteLLM

Once you have determined a valid API key (from step 4), use the plain-text key in the curl request. Do not pass the SHA-256 hash from `api_keys.json`.

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Team-Id: team-1" \
  -H "X-User-Id: user-1" \
  -H "X-Api-Key: sk-test-key-team1-user1-12345" \
  -H "X-Correlation-Id: $(uuidgen)" \
  -d '{
    "model": "qwen-3b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

If you need team-2 instead, use `sk-test-key-team2-user1-67890`.

Verify:
- LiteLLM returns a valid OpenAI-compatible response
- `response.usage` is present (prompt_tokens, completion_tokens, total_tokens)
- the request is authenticated and not blocked with a 401 error

## 5. Verify trace delivery in Langfuse

After successfully sending a request via LiteLLM, you should see traces appear in Langfuse.

### Option A: Langfuse UI
- Open the Langfuse dashboard at `http://localhost:3000`
- Log in with credentials from `langfuse/.env`:
  - Email: `LANGFUSE_INIT_USER_EMAIL`
  - Password: `LANGFUSE_INIT_USER_PASSWORD`
- Navigate to the project: `LANGFUSE_INIT_PROJECT_NAME`
- Confirm a new trace arrived for your chat completion request
- Check metadata fields: `team_id`, `user_id`, `correlation_id`, token usage, latency

### Option B: Buffer fallback verification
If Langfuse is unavailable:
- Stop the Langfuse service: `docker compose stop langfuse-web`
- Send another request via LiteLLM (it should still succeed)
- Confirm LiteLLM returns a response (not blocked by trace failure)
- Inspect `litellm/data/trace_buffer/trace_buffer.jsonl` on the host
- If traces are buffered as JSONL, the offline resilience path is working
- Start Langfuse again: `docker compose up langfuse-web`
- Confirm the buffer flush task retries and moves traces to Langfuse

## 6. Test failure and retry behavior

1. Start LiteLLM with Langfuse down
2. Send a request
3. Confirm trace is written to the buffer
4. Start Langfuse again
5. Confirm the buffer flush task retries and removes buffered entries

## 7. Validate actual configuration

Check that the runtime settings are correct:
- `litellm/config/litellm_config.yaml`
- `litellm/config/.env.example`
- `API_KEYS_FILE`
- `LANGFUSE_HOST`
- `LANGFUSE_PUBLIC_KEY`

Ensure the gateway uses the real `trace_buffer_dir` and `trace_buffer_max_size_mb`.

## 8. Optional: Stronger real test

Run a short load test against the gateway while Langfuse is healthy and while it is down to confirm request throughput, trace capture rate, and request resilience.