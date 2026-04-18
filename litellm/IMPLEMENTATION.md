# LiteLLM Langfuse Integration - Implementation

Implementation status: **Phase 1-2 Scaffolding Complete**

## Project Structure

```
litellm/
├── config/
│   ├── __init__.py
│   ├── langfuse_schema.py          # Pydantic trace schema definitions
│   ├── metadata_extractor.py       # HTTP header parsing for X-Team-Id, X-User-Id, etc.
│   ├── correlation_id.py           # UUID v4 generation and validation
│   ├── token_extractor.py          # Parse token counts from vLLM response
│   ├── latency_tracker.py          # Measure queue/inference/total latency
│   ├── json_logger.py              # Structured JSON logging
│   ├── api_key_validator.py        # API key validation and authentication
│   ├── trace_client.py             # Async HTTP client for Langfuse API
│   ├── trace_buffer.py             # File-based JSONL trace buffering
│   ├── trace_buffer_flusher.py     # Async periodic buffer flushing
│   ├── litellm_langfuse_callback.py # Main callback executor
│   ├── error_handler.py            # Standardized error responses
│   ├── litellm_config.yaml         # LiteLLM gateway configuration
│   ├── .env.example                # Environment variable template
│   └── api_keys.json               # Sample API keys for testing
│
├── data/
│   └── trace_buffer/               # Directory for persisted trace buffer (JSONL)
│
└── tests/
    ├── conftest.py                 # Pytest configuration and fixtures
    ├── contract/
    │   ├── test_trace_schema.py     # Langfuse trace schema validation
    │   └── test_api_key_validation.py
    ├── integration/
    │   ├── test_e2e_request_tracing.py      # End-to-end flow tests
    │   ├── test_trace_fidelity.py           # Trace completeness tests
    │   ├── test_metadata_propagation.py     # Metadata flow tests
    │   ├── test_gateway_only_access.py      # Access control tests
    │   └── test_langfuse_resilience.py      # Resilience tests
    └── unit/
        ├── test_metadata_extraction.py
        ├── test_correlation_id.py
        ├── test_trace_submission.py
        └── test_callback_extraction.py

requirements.txt                    # Python dependencies
```

## Core Modules

### 1. langfuse_schema.py
Pydantic models for trace validation:
- `TokenUsage`: Input/output/total token counts
- `LatencyBreakdown`: Queue/inference/total latency in ms
- `TraceMetadata`: Team/user/model attribution
- `LangfuseTraceRequest`: Complete trace schema
- `VLLMResponse`: vLLM OpenAI-compatible response format
- `TracingContext`: Context passed through callback

### 2. metadata_extractor.py
Extracts and validates HTTP headers:
- `X-Team-Id` (required): Team identifier
- `X-User-Id` (required): User identifier
- `X-Api-Key` (required): API key for authentication
- `X-Correlation-Id` (optional): UUID v4 for tracing
- `X-Use-Case` (optional): Use case label

### 3. token_extractor.py
Parses token counts from vLLM OpenAI-compatible response:
```python
response = {
    "usage": {
        "prompt_tokens": 42,
        "completion_tokens": 18,
        "total_tokens": 60
    }
}
```

### 4. latency_tracker.py
Measures request latency breakdown:
- Queue time: Time waiting for inference
- Inference time: Model execution time
- Total time: End-to-end latency
- Supports context manager for automatic timing

### 5. api_key_validator.py
Validates API keys against stored credentials:
- Loads API keys from JSON file
- Hashes API key using SHA-256
- Validates key status (active/revoked/expired)
- Returns team_id and user_id on successful validation

### 6. trace_client.py
Async HTTP client for Langfuse trace submission:
- Submits traces to `POST /api/public/traces`
- Implements exponential backoff retry (100ms, 200ms, 400ms + jitter)
- Max 3 retry attempts
- Returns (success, error_message) tuple

### 7. trace_buffer.py
File-based JSONL trace buffering for resilience:
- Appends failed traces to `trace_buffer.jsonl`
- Maintains max 100MB buffer size
- Implements FIFO cleanup of oldest entries
- Stores entry metadata: buffered_at, retry_count, next_retry_at

### 8. trace_buffer_flusher.py
Async background task for retrying buffered traces:
- Runs every 60 seconds
- Attempts to resubmit buffered traces
- Removes successfully submitted traces from buffer
- Respects exponential backoff schedule for retries

### 9. litellm_langfuse_callback.py
Main callback executor invoked after vLLM response:
```python
async def __call__(
    kwargs: Dict,      # Original request parameters
    response: Dict,    # vLLM response
    start_time: float, # Request timestamp
    end_time: float,   # Response timestamp
) -> None
```

Flow:
1. Extract metadata from kwargs
2. Parse tokens from response
3. Calculate latency breakdown
4. Build LangfuseTraceRequest
5. Attempt submission to Langfuse
6. Buffer on failure if enabled
7. Log outcome

### 10. error_handler.py
Standardized error responses:
- `error_invalid_api_key()` → HTTP 401
- `error_missing_header(name)` → HTTP 400
- `error_rate_limit_exceeded()` → HTTP 429
- `error_authentication_failed()` → HTTP 401
- `error_service_unavailable()` → HTTP 503
- `error_internal_error()` → HTTP 500

## Configuration

### litellm_config.yaml
```yaml
model_list:
  - model_name: mistral-7b
    litellm_params:
      model: openai/mistral-7b-instruct
      api_base: http://vllm:8000/v1

langfuse_config:
  enabled: true
  public_key: "${LANGFUSE_PUBLIC_KEY}"
  host: "http://langfuse:3000"
  callback: "litellm_langfuse_callback"
  trace_buffer_dir: "/app/data/trace_buffer"
  trace_buffer_max_size_mb: 100
  flush_interval_seconds: 60
```

### .env.example
```bash
LITELLM_PORT=4000
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=http://langfuse:3000
TRACE_BUFFER_DIR=/app/data/trace_buffer
```

## Test Coverage

### Contract Tests
- Trace schema validation (Pydantic models)
- API key contract compliance
- Metadata header validation

### Integration Tests
- End-to-end request tracing (pending full implementation)
- Trace fidelity (all fields present)
- Metadata propagation (headers → trace)
- Gateway-only access (direct vLLM blocked)
- Langfuse resilience (buffering on failure)

### Unit Tests
- Metadata extraction from headers
- Correlation ID generation and validation
- Trace submission retry logic
- Callback data extraction

## Next Steps

1. **Phase 2 Completion**:
   - Implement missing core functionality
   - Fix import paths and dependencies
   - Validate schemas

2. **Phase 3+ Implementation**:
   - Implement integration endpoints in LiteLLM
   - Create E2E tests with mocked vLLM/Langfuse
   - Performance and load testing

3. **Production Readiness**:
   - Docker image with dependencies
   - Prometheus metrics for observability
   - Load testing and throughput benchmarks
   - Documentation and deployment guide

## Architecture

```
Client Request
    ↓
[X-Team-Id, X-User-Id, X-Api-Key, X-Correlation-Id headers]
    ↓
LiteLLM Gateway
    ├─ Validate metadata headers
    ├─ Validate API key
    ├─ Route to vLLM
    └─ Invoke Langfuse callback (async, non-blocking)
    ↓
vLLM Model Execution
    ↓
LiteLLM Langfuse Callback
    ├─ Extract tokens, latency, metadata
    ├─ Build LangfuseTraceRequest
    ├─ Attempt POST to Langfuse
    ├─ On failure: Buffer to disk
    └─ Log outcome
    ↓
Langfuse API
    ├─ Success: Store trace
    └─ Unavailable: Will retry from buffer
    ↓
Buffer Flusher (periodic)
    ├─ Read buffered traces
    ├─ Retry failed submissions
    └─ Clean up successfully submitted traces
```

## Key Design Decisions

1. **Gateway-level tracing**: No SDK in application code
2. **Async callbacks**: Non-blocking trace submission
3. **File-based buffering**: Simple, scalable, debuggable
4. **Exponential backoff**: Handles transient failures gracefully
5. **Correlation ID propagation**: UUID v4 for distributed tracing
6. **Structured JSON logging**: All logs include metadata for correlation

See `specs/001-automatic-request-tracing/research.md` for full rationale.
