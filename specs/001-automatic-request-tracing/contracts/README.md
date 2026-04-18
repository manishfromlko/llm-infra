# Contracts: Automatic Request Tracing

**Feature**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)
**Date**: 2026-04-18

## 1. Client Metadata Header Contract

**Description**: HTTP headers that clients MUST send with requests to LiteLLM.

**Headers (Required)**:

| Header | Type | Example | Purpose |
|--------|------|---------|---------|
| `X-Team-Id` | string | `"acme-corp"` | Team identifier for cost/quota attribution |
| `X-User-Id` | string | `"user-42"` | User identifier for audit/tracing |
| `X-Api-Key` | string | `"sk-xxx...yyy"` | API key for authentication |
| `Content-Type` | string | `"application/json"` | Standard HTTP header |

**Headers (Optional)**:

| Header | Type | Example | Purpose |
|--------|------|---------|---------|
| `X-Correlation-Id` | string | `"550e8400-e29b-41d4-a716-446655440000"` | UUID for request correlation (generated if missing) |
| `X-Use-Case` | string | `"email-generation"` | Use case label for analytics |

**Request Body** (standard OpenAI format):

```json
{
  "model": "mistral-7b-instruct",
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 128
}
```

**Validation Rules**:
- `X-Team-Id` MUST be non-empty, alphanumeric + hyphens
- `X-User-Id` MUST be non-empty
- `X-Api-Key` MUST be valid (checked against stored API keys)
- `X-Correlation-Id` MUST be valid UUID v4 if provided; LiteLLM generates UUID if missing
- All metadata headers MUST be preserved in request context for downstream tracing

**Example Request**:

```bash
curl -X POST http://litellm:4000/v1/completions \
  -H "X-Team-Id: acme-corp" \
  -H "X-User-Id: user-42" \
  -H "X-Api-Key: sk-xxx...yyy" \
  -H "X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Use-Case: email-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b-instruct",
    "messages": [{"role": "user", "content": "Write an email..."}],
    "max_tokens": 256
  }'
```

---

## 2. LiteLLM Callback Contract

**Description**: Interface and lifecycle for Langfuse trace submission callback.

**Function Signature** (Python):

```python
async def langfuse_callback(
    kwargs: dict,
    response: dict,
    start_time: float,
    end_time: float
) -> None:
    """
    Callback invoked after LiteLLM receives response from vLLM.
    
    Args:
        kwargs: Original request parameters including metadata
        response: vLLM response dict (OpenAI format)
        start_time: Timestamp when request was received (seconds since epoch)
        end_time: Timestamp when response was received (seconds since epoch)
    
    Returns:
        None (async, non-blocking)
    
    Raises:
        Exceptions are caught and logged; callback failure does not block request path.
    """
```

**Input Contract** (kwargs):

```python
{
    "model": "mistral-7b-instruct",
    "messages": [{"role": "user", "content": "..."}],
    "temperature": 0.7,
    "max_tokens": 128,
    "metadata": {
        "team_id": "acme-corp",
        "user_id": "user-42",
        "api_key": "sk-xxx...yyy",
        "use_case": "email-generation",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

**Input Contract** (response):

```json
{
  "id": "chatcmpl-123456",
  "object": "text_completion",
  "created": 1234567890,
  "model": "mistral-7b-instruct",
  "choices": [
    {
      "index": 0,
      "text": "Paris is the capital of France.",
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 11,
    "completion_tokens": 8,
    "total_tokens": 19
  }
}
```

**Callback Behavior**:

1. **Extract data** from kwargs and response
2. **Create trace object** per Langfuse Trace schema
3. **Attempt submission** to Langfuse with retries:
   - Retry up to 3 times with exponential backoff (100ms, 200ms, 400ms)
   - If all retries fail, buffer to disk JSONL file
4. **Log submission result** (success or failure reason)
5. **Return immediately** without blocking request path

**Error Handling**:

| Error Scenario | Behavior |
|--------|----------|
| Langfuse API unavailable | Retry with backoff, then buffer |
| Invalid trace schema | Log error, skip submission |
| Disk buffer full (>100MB) | Drop oldest buffered traces, log warning |
| Callback exception | Catch and log, continue |

**Example Implementation Location**: `litellm/config/litellm_langfuse_callback.py`

---

## 3. Langfuse Trace Submission API Contract

**Description**: HTTP contract for submitting traces to Langfuse.

**Endpoint**: `POST /api/public/traces`

**Headers**:

```
Authorization: Bearer {LANGFUSE_PUBLIC_KEY}
Content-Type: application/json
```

**Request Body** (Langfuse trace schema):

```json
{
  "traceId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "acme-corp|user-42",
  "name": "llm_request",
  "input": {
    "prompt": "What is the capital of France?"
  },
  "output": {
    "response": "Paris is the capital of France.",
    "tokens": {
      "input": 11,
      "output": 8,
      "total": 19
    }
  },
  "metadata": {
    "team_id": "acme-corp",
    "user_id": "user-42",
    "api_key_hash": "sha256:...",
    "use_case": "email-generation",
    "model": "mistral-7b-instruct"
  },
  "latency": {
    "queue_ms": 10,
    "inference_ms": 850,
    "total_ms": 860
  },
  "startTime": "2026-04-18T10:30:00Z",
  "endTime": "2026-04-18T10:30:00.860Z"
}
```

**Response** (success - HTTP 200):

```json
{
  "traceId": "550e8400-e29b-41d4-a716-446655440000",
  "id": "trace-12345"
}
```

**Response** (error - HTTP 400/401/500):

```json
{
  "error": "Invalid trace schema: missing required field 'output'"
}
```

**Retry Contract**:
- Retry on HTTP 503 (Service Unavailable)
- Retry on network timeout (>5s)
- Do NOT retry on HTTP 400 (client error)
- Max 3 retries per trace + buffer for async retry

---

## 4. Configuration Contract

**Description**: LiteLLM configuration for enabling Langfuse tracing callbacks.

**File**: `litellm/config/litellm_config.yaml`

```yaml
model_list:
  - model_name: "mistral-7b"
    litellm_params:
      model: "openai/mistral-7b-instruct"
      api_base: "http://vllm:8000/v1"
      api_key: "not-needed"
  
  - model_name: "mistral-7b-instruct"
    litellm_params:
      model: "openai/mistral-7b-instruct"
      api_base: "http://vllm:8000/v1"
      api_key: "not-needed"

# Langfuse integration
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

# API key validation (external service or local store)
api_keys:
  store: "file"  # or "database", "external_service"
  file_path: "/app/config/api_keys.json"

# Logging
logging:
  level: "INFO"
  format: "json"
  output: "stdout"
```

**Environment Variables**:

```bash
LITELLM_PORT=4000
LITELLM_MASTER_KEY=sk-master-key
LANGFUSE_PUBLIC_KEY=pk-xxx...
LANGFUSE_SECRET_KEY=sk-xxx...
LANGFUSE_HOST=http://langfuse:3000
```

---

## 5. Error Response Contract

**Description**: Standard error responses for gateway failures.

**Error: Invalid API Key** (HTTP 401):

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": "invalid_api_key"
  }
}
```

**Error: Missing Metadata Header** (HTTP 400):

```json
{
  "error": {
    "message": "Missing required header: X-Team-Id",
    "type": "invalid_request_error",
    "code": "missing_header"
  }
}
```

**Error: Rate Limited** (HTTP 429):

```json
{
  "error": {
    "message": "Rate limit exceeded: 100 requests/minute",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded",
    "retry_after": 10
  }
}
```

**Error: vLLM Backend Error** (HTTP 503):

```json
{
  "error": {
    "message": "vLLM backend unavailable",
    "type": "server_error",
    "code": "backend_unavailable"
  }
}
```

---

## Summary

All contracts above define the boundaries between:
1. **Client → LiteLLM**: Metadata headers, request format
2. **LiteLLM → vLLM**: Model routing (existing contract)
3. **LiteLLM → Langfuse**: Trace submission, retries, buffering
4. **Configuration**: YAML schema for enablement and tuning

Each contract is independently testable via unit/integration tests (see tasks.md).
