# Quickstart: Automatic Request Tracing Integration

**Feature**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md) | **Contracts**: [contracts/README.md](../contracts/README.md)
**Date**: 2026-04-18

## Overview

This quickstart guide walks through enabling automatic tracing from LiteLLM to Langfuse using the gateway-level callback mechanism. No changes are required to application code—tracing is configured entirely at the LiteLLM deployment level.

## Prerequisites

- LiteLLM deployed and running on `http://litellm:4000`
- vLLM running on `http://vllm:8000` with a model loaded
- Langfuse deployed and running on `http://langfuse:3000`
- API keys provisioned (team_id, user_id, api_key)

## Step 1: Configure LiteLLM for Langfuse Tracing

### 1.1 Update LiteLLM Configuration

Edit `litellm/config/litellm_config.yaml`:

```yaml
model_list:
  - model_name: "mistral-7b-instruct"
    litellm_params:
      model: "openai/mistral-7b-instruct"
      api_base: "http://vllm:8000/v1"
      api_key: "not-needed"

langfuse_config:
  enabled: true
  public_key: "${LANGFUSE_PUBLIC_KEY}"
  secret_key: "${LANGFUSE_SECRET_KEY}"
  host: "http://langfuse:3000"
  callback: "litellm_langfuse_callback"
  trace_buffer_dir: "/app/data/trace_buffer"
  trace_buffer_max_size_mb: 100
  batch_size: 10
  flush_interval_seconds: 60
```

### 1.2 Set Environment Variables

Create or update `.env`:

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-xxx...
LANGFUSE_SECRET_KEY=sk-lf-xxx...
LANGFUSE_HOST=http://langfuse:3000
```

### 1.3 Provision API Keys

Create `litellm/config/api_keys.json`:

```json
{
  "sk-team1-user1-key1": {
    "team_id": "acme-corp",
    "user_id": "user-1",
    "rate_limit_rpm": 100,
    "rate_limit_tokens_per_day": 100000,
    "status": "active"
  },
  "sk-team1-user2-key2": {
    "team_id": "acme-corp",
    "user_id": "user-2",
    "rate_limit_rpm": 50,
    "rate_limit_tokens_per_day": 50000,
    "status": "active"
  }
}
```

### 1.4 Restart LiteLLM

```bash
docker-compose -f litellm/docker-compose.yaml restart litellm
```

Verify it starts without errors:

```bash
docker-compose -f litellm/docker-compose.yaml logs -f litellm
```

You should see:

```
litellm: Langfuse integration enabled
litellm: Callback registered: litellm_langfuse_callback
```

---

## Step 2: Update Client Code (Minimal Changes)

### 2.1 Python Client Example

Clients simply add metadata headers to their requests:

```python
import requests
import json

LITELLM_URL = "http://localhost:4000/v1/completions"
API_KEY = "sk-team1-user1-key1"
TEAM_ID = "acme-corp"
USER_ID = "user-1"

# Optional: Generate or provide correlation ID
CORRELATION_ID = "550e8400-e29b-41d4-a716-446655440000"

headers = {
    "X-Team-Id": TEAM_ID,
    "X-User-Id": USER_ID,
    "X-Api-Key": API_KEY,
    "X-Correlation-Id": CORRELATION_ID,
    "X-Use-Case": "email-generation",  # Optional
    "Content-Type": "application/json"
}

payload = {
    "model": "mistral-7b-instruct",
    "messages": [
        {
            "role": "user",
            "content": "Write a professional email confirming a meeting."
        }
    ],
    "temperature": 0.7,
    "max_tokens": 256
}

response = requests.post(LITELLM_URL, headers=headers, json=payload)
result = response.json()

print("Response:", result["choices"][0]["text"])
print("Tokens:", result["usage"])
# Trace is automatically submitted to Langfuse by LiteLLM callback
```

### 2.2 cURL Example

```bash
curl -X POST http://localhost:4000/v1/completions \
  -H "X-Team-Id: acme-corp" \
  -H "X-User-Id: user-1" \
  -H "X-Api-Key: sk-team1-user1-key1" \
  -H "X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Use-Case: email-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b-instruct",
    "messages": [{"role": "user", "content": "Write a professional email..."}],
    "temperature": 0.7,
    "max_tokens": 256
  }'
```

**Key Point**: No Langfuse SDK imports required in client code. Metadata is passed via HTTP headers.

---

## Step 3: Verify Traces in Langfuse

### 3.1 Access Langfuse Dashboard

Open browser to `http://localhost:3000` and sign in.

### 3.2 View Traces

1. Navigate to **Traces** tab
2. You should see traces appearing in real-time as requests are made
3. Each trace shows:
   - **Prompt**: Input text
   - **Response**: Model output
   - **Model**: "mistral-7b-instruct"
   - **Tokens**: Input, output, total counts
   - **Latency**: Queue time + Inference time breakdown
   - **Metadata**: team_id, user_id, use_case, correlation_id

### 3.3 Inspect a Trace

Click on a trace to see details:

```json
{
  "traceId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "acme-corp|user-1",
  "name": "llm_request",
  "input": {
    "prompt": "Write a professional email..."
  },
  "output": {
    "response": "Dear [Name],\n\nI'm writing to confirm our meeting...",
    "tokens": {
      "input": 15,
      "output": 42,
      "total": 57
    }
  },
  "metadata": {
    "team_id": "acme-corp",
    "user_id": "user-1",
    "use_case": "email-generation",
    "model": "mistral-7b-instruct"
  },
  "latency": {
    "queue_ms": 5,
    "inference_ms": 1200,
    "total_ms": 1205
  },
  "startTime": "2026-04-18T10:30:00Z",
  "endTime": "2026-04-18T10:30:01.205Z"
}
```

---

## Step 4: Verify Gateway-Only Access

### 4.1 Confirm vLLM is Not Directly Accessible

Attempt to access vLLM directly (should fail if network policy is enforced):

```bash
curl http://vllm:8000/v1/completions -X POST -d '...'
# Expected: Connection refused or timeout
```

Or verify via network policy:

```bash
kubectl get networkpolicies -n llm-infra
# Should show policy blocking direct vLLM access
```

### 4.2 Verify All Requests Route Through LiteLLM

Make a request with valid headers → Trace should appear in Langfuse
Make a request with invalid API key → Request rejected by LiteLLM (401)
Make a request missing X-Team-Id → Request rejected by LiteLLM (400)

---

## Step 5: Test Metadata Propagation

### 5.1 Test Different Teams

Make requests with different team_id values:

```bash
# Request 1: Team A
curl -X POST http://localhost:4000/v1/completions \
  -H "X-Team-Id: team-a" \
  -H "X-User-Id: user-alice" \
  -H "X-Api-Key: sk-team-a-alice" \
  ...

# Request 2: Team B
curl -X POST http://localhost:4000/v1/completions \
  -H "X-Team-Id: team-b" \
  -H "X-User-Id: user-bob" \
  -H "X-Api-Key: sk-team-b-bob" \
  ...
```

Verify in Langfuse:
- Traces for Team A show `metadata.team_id: "team-a"`
- Traces for Team B show `metadata.team_id: "team-b"`
- Dashboard can filter by team_id

### 5.2 Test Use Case Labels

Make requests with different use_case values:

```bash
# Use case: email-generation
curl ... -H "X-Use-Case: email-generation" ...

# Use case: code-generation
curl ... -H "X-Use-Case: code-generation" ...

# Use case: customer-support
curl ... -H "X-Use-Case: customer-support" ...
```

Verify in Langfuse:
- Traces show different use_case values in metadata
- Can create dashboards grouped by use_case

---

## Step 6: Test Failure Resilience

### 6.1 Simulate Langfuse Downtime

Stop Langfuse:

```bash
docker-compose -f langfuse/docker-compose.yml stop langfuse
```

Make a request to LiteLLM:

```bash
curl -X POST http://localhost:4000/v1/completions \
  -H "X-Team-Id: acme-corp" \
  ... (other headers) ...
```

Expected behavior:
- Request succeeds (returns response from vLLM)
- LiteLLM logs: "Langfuse trace submission failed, buffering to disk"
- Trace is written to `/app/data/trace_buffer/traces.jsonl`

Restart Langfuse:

```bash
docker-compose -f langfuse/docker-compose.yml up -d langfuse
```

Expected behavior:
- LiteLLM detects Langfuse is back online
- Buffered traces are submitted automatically
- Traces appear in Langfuse dashboard (check timestamps)

### 6.2 Inspect Buffer File

View buffered traces (human-readable JSONL):

```bash
docker exec litellm cat /app/data/trace_buffer/traces.jsonl | head -20
```

Each line is a JSON trace object.

---

## Step 7: Monitor Token & Cost Metrics

### 7.1 Query Langfuse for Usage Stats

In Langfuse dashboard, create a dashboard showing:
- Total tokens by team
- Total tokens by user
- Total tokens by use_case
- Average latency by model

Example Langfuse query:

```sql
SELECT 
  metadata.team_id,
  metadata.user_id,
  SUM(output.tokens.total) as total_tokens,
  AVG(latency.total_ms) as avg_latency_ms,
  COUNT(*) as request_count
FROM traces
GROUP BY metadata.team_id, metadata.user_id
```

### 7.2 Export Data for Billing

Langfuse API endpoint to fetch traces for billing:

```python
import requests

LANGFUSE_URL = "http://langfuse:3000/api/public/traces"
headers = {"Authorization": f"Bearer {LANGFUSE_PUBLIC_KEY}"}

params = {
  "filter": "metadata.team_id = 'acme-corp'",
  "limit": 1000
}

response = requests.get(LANGFUSE_URL, headers=headers, params=params)
traces = response.json()

# Process traces for billing
for trace in traces:
    tokens = trace["output"]["tokens"]["total"]
    model = trace["metadata"]["model"]
    cost = calculate_cost(model, tokens)
    # Insert into billing system
```

---

## Step 8: Run E2E Test Suite

### 8.1 Unit Tests

```bash
cd litellm/tests/unit
pytest test_callback_extraction.py -v
pytest test_correlation_id.py -v
pytest test_trace_submission.py -v
```

### 8.2 Integration Tests

```bash
cd litellm/tests/integration
pytest test_e2e_request_tracing.py -v
pytest test_metadata_propagation.py -v
pytest test_gateway_only_access.py -v
pytest test_langfuse_resilience.py -v
```

### 8.3 Contract Tests

```bash
cd litellm/tests/contract
pytest test_langfuse_callback.py -v
pytest test_trace_schema.py -v
```

All tests should pass ✅

---

## Troubleshooting

### Issue: Traces Not Appearing in Langfuse

**Checklist**:
1. ✓ LiteLLM config has `langfuse_config.enabled: true`
2. ✓ Environment variables set: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
3. ✓ LiteLLM restarted after config change
4. ✓ Langfuse is running and accessible at configured `host`
5. ✓ LiteLLM logs show: "Callback registered: litellm_langfuse_callback"
6. ✓ Request is being made with valid API key

**Debug**: Check LiteLLM logs:

```bash
docker-compose -f litellm/docker-compose.yaml logs litellm | grep -i langfuse
```

### Issue: Missing Metadata in Traces

**Checklist**:
1. ✓ Client sending X-Team-Id, X-User-Id headers
2. ✓ LiteLLM callback extracting from request metadata dict
3. ✓ Langfuse trace submission includes metadata fields

**Debug**: Check callback execution:

```bash
docker-compose -f litellm/docker-compose.yaml logs litellm | grep -i "metadata"
```

### Issue: High Latency in Trace Submission

**Possible causes**:
- Langfuse server is slow (check Langfuse logs)
- Network connectivity issue between LiteLLM and Langfuse
- Callback is synchronous (blocking request path)

**Solution**: Enable async callback processing in LiteLLM config:

```yaml
langfuse_config:
  callback_async: true
  callback_thread_pool_size: 10
```

### Issue: Out of Disk Space (Trace Buffer)

**Monitor buffer size**:

```bash
du -sh litellm/data/trace_buffer/
```

**Increase buffer limit** in config:

```yaml
langfuse_config:
  trace_buffer_max_size_mb: 500  # Increase from 100
```

**Or clean old buffered traces**:

```bash
find litellm/data/trace_buffer/ -mtime +7 -delete  # Delete traces older than 7 days
```

---

## Next Steps

1. **Monitoring**: Set up Grafana dashboard to visualize token usage, latency, error rates from Langfuse
2. **Cost Attribution**: Integrate with billing system to generate invoices based on token usage per team
3. **Alerting**: Configure alerts for high error rates, Langfuse unavailability, buffer overflow
4. **Documentation**: Add to runbooks and operational guides for the observability stack

---

## Resources

- LiteLLM Docs: https://docs.litellm.ai
- Langfuse Docs: https://langfuse.com/docs
- vLLM Docs: https://docs.vllm.ai
- Constitution: [../../.specify/memory/constitution.md](../../../.specify/memory/constitution.md)
