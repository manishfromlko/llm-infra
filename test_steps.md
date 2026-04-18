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

## 2. Run the local Python tests

### Unit tests
```bash
uv run pytest litellm/tests/unit/ -q
```

### Contract tests
```bash
uv run pytest litellm/tests/contract/ -q
```

### Integration smoke test
```bash
uv run pytest litellm/tests/integration/test_e2e_request_tracing.py -q
```

These commands verify the core trace schema, metadata handling, correlation IDs, and the callback flow.

## 3. Run the real runtime stack with Docker Compose

Start Langfuse and LiteLLM together so the full trace path is live:

```bash
docker compose -f litellm/docker-compose.yaml -f langfuse/docker-compose.yml up --build
```

Adjust compose file paths if your repository uses a different local setup.

## 4. Send a real request through LiteLLM

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Team-Id: team-1" \
  -H "X-User-Id: user-1" \
  -H "X-Api-Key: sk-test-key" \
  -H "X-Correlation-Id: $(uuidgen)" \
  -d '{
    "model": "qwen-3b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

Verify:
- LiteLLM returns a valid OpenAI-compatible response
- `response.usage` is present
- the request is authenticated and not blocked

## 5. Verify trace delivery in Langfuse

### Option A: Langfuse UI
- Open the Langfuse dashboard
- Confirm a new trace arrived
- Check metadata fields: `team_id`, `user_id`, `correlation_id`, token usage, latency

### Option B: Buffer fallback verification
If Langfuse is unavailable:
- stop the Langfuse service
- send another request
- confirm LiteLLM still returns successfully
- inspect `litellm/data/trace_buffer/trace_buffer.jsonl`

If the trace is buffered, the offline resilience path is working.

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