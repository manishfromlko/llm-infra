# Data Model: Automatic Request Tracing

**Feature**: [spec.md](spec.md) | **Research**: [research.md](research.md)
**Date**: 2026-04-18

## Entities & Relationships

### 1. LiteLLM Request (Incoming Request)

Represents an incoming request from a client to LiteLLM.

**Fields**:
- `request_id` (string, UUID): Unique request identifier
- `correlation_id` (string, UUID): Client-supplied or generated trace correlation ID
- `timestamp_start` (ISO8601): Request arrival time
- `prompt` (string): User prompt or input text
- `model_name` (string): Model identifier (e.g., "mistral-7b-instruct")
- `max_tokens` (int, optional): Max output token limit
- `temperature` (float, optional): Sampling parameter
- `top_p` (float, optional): Nucleus sampling parameter
- `metadata` (object):
  - `team_id` (string): Team identifier from header
  - `user_id` (string): User identifier from header
  - `api_key` (string): API key hash from header
  - `use_case` (string, optional): Use case label from header

**Validation Rules**:
- `team_id` MUST be non-empty string
- `user_id` MUST be non-empty string
- `api_key` MUST be valid and hashed (not plain text in logs)
- `prompt` MUST be non-empty string
- `model_name` MUST match registered vLLM model

**State Transitions**:
1. QUEUED (received by LiteLLM)
2. ROUTING (routing to vLLM)
3. INFERENCE (executing in vLLM)
4. COMPLETE (response received)
5. TRACE_SUBMITTED (trace sent to Langfuse)
6. TRACE_BUFFERED (trace submission failed, buffered to disk)

---

### 2. vLLM Response (Model Execution Result)

Represents the response from vLLM after model inference.

**Fields**:
- `request_id` (string): Correlation to original LiteLLM request
- `response_text` (string): Generated response
- `model_name` (string): Model that executed request
- `finish_reason` (enum): "stop" | "length" | "error"
- `usage` (object):
  - `prompt_tokens` (int): Input token count
  - `completion_tokens` (int): Output token count
  - `total_tokens` (int): Sum
- `latency_ms` (object):
  - `queue_time` (int): Time spent in LiteLLM queue before vLLM
  - `inference_time` (int): vLLM inference time
  - `total_latency` (int): End-to-end latency from LiteLLM receipt
- `timestamp_end` (ISO8601): Response completion time
- `error` (string, optional): Error message if finish_reason = "error"

**Validation Rules**:
- `usage.total_tokens` MUST equal `usage.prompt_tokens + usage.completion_tokens`
- `latency_ms.inference_time` MUST be > 0
- If `finish_reason` = "error", `error` MUST be non-empty

---

### 3. Langfuse Trace (Observability Record)

Represents a single trace in Langfuse combining request, response, and metadata.

**Fields**:
- `trace_id` (string, UUID): Primary identifier in Langfuse
- `correlation_id` (string, UUID): Links trace to client request
- `timestamp_start` (ISO8601): Request start time
- `timestamp_end` (ISO8601): Response completion time
- `prompt` (string): Input text (may be redacted)
- `response` (string): Output text (may be redacted)
- `model_name` (string): Model used
- `tokens` (object):
  - `input` (int): Input token count
  - `output` (int): Output token count
  - `total` (int): Total token count
- `latency_ms` (object):
  - `queue` (int): Queue wait time
  - `inference` (int): Model inference time
  - `total` (int): End-to-end latency
- `metadata` (object):
  - `team_id` (string)
  - `user_id` (string)
  - `api_key` (string, hashed)
  - `use_case` (string, optional)
- `status` (enum): "success" | "error"
- `error` (string, optional): Error message if status = "error"

**Validation Rules**:
- All fields except optional ones MUST be present
- `tokens.total` MUST equal `tokens.input + tokens.output`
- `timestamp_end` MUST be >= `timestamp_start`
- `trace_id` MUST be unique in Langfuse database

**Relationships**:
- **1:1 with LiteLLM Request**: Each request produces exactly one trace
- **1:1 with vLLM Response**: Each trace corresponds to one model response
- **N:1 with Team**: Many traces belong to one team (via team_id)
- **N:1 with API Key**: Many traces belong to one API key

---

### 4. Trace Buffer Entry (Resilience)

Represents a trace that failed to submit to Langfuse and is buffered for retry.

**Fields**:
- `buffered_at` (ISO8601): Time buffered to disk
- `trace` (object): Complete Langfuse trace (as above)
- `retry_count` (int): Number of submission attempts
- `last_error` (string): Last submission error message
- `next_retry_at` (ISO8601): Scheduled next retry timestamp

**Validation Rules**:
- `trace` MUST be valid per Langfuse Trace schema
- `retry_count` MUST be non-negative
- `next_retry_at` MUST be in future

**Retention Rules**:
- Buffer file MUST NOT exceed 100MB
- Traces MUST be persisted as newline-delimited JSON (JSONL)
- Oldest entries SHOULD be flushed first if size limit approached

---

### 5. API Key (Authentication & Attribution)

Represents an API key used for authentication and cost attribution.

**Fields**:
- `key_id` (string, UUID): Primary identifier
- `team_id` (string, UUID): Team that owns this key
- `user_id` (string, UUID): User who created this key
- `key_hash` (string): Salted SHA-256 hash of actual key (not stored plain text)
- `created_at` (ISO8601): Key creation time
- `last_used_at` (ISO8601): Last successful authentication
- `status` (enum): "active" | "revoked" | "expired"
- `rate_limit_rpm` (int): Requests per minute quota
- `rate_limit_tokens_per_day` (int): Token quota per day
- `metadata` (object, optional): Custom attributes (e.g., environment, purpose)

**Validation Rules**:
- `key_hash` MUST never be the plain key
- `status` = "active" MUST be checked before allowing requests
- `rate_limit_rpm` and `rate_limit_tokens_per_day` MUST be positive

**Relationships**:
- **N:1 with Team**: Each API key belongs to one team
- **1:1 with User**: Each API key is associated with one user

---

## Relationships Diagram

```
┌─────────────────────────────────────────────────────┐
│ Client Request (HTTP Headers)                       │
│  - X-Team-Id, X-User-Id, X-Api-Key                 │
│  - X-Correlation-Id (optional)                      │
│  - Prompt in body                                   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ LiteLLM Request Entity      │
        │ - Extract headers/metadata │
        │ - Validate API key         │
        │ - Generate correlation ID  │
        └────────────┬───────────────┘
                     │
                     ▼ (route to vLLM)
        ┌────────────────────────────┐
        │ vLLM Response Entity        │
        │ - Execute inference        │
        │ - Generate response text   │
        │ - Extract tokens/latency   │
        └────────────┬───────────────┘
                     │
                     ▼ (callback trigger)
        ┌────────────────────────────┐
        │ Langfuse Trace Entity      │
        │ - Combine request/response │
        │ - Add metadata             │
        │ - Attempt submission       │
        └────────────┬───────────────┘
                     │
        ┌────────────┴────────────────┐
        │                             │
   Success?                      Failure?
        │                             │
        ▼                             ▼
  (Stored in              ┌───────────────────────┐
   Langfuse)              │ Trace Buffer Entry    │
                          │ - Persist to disk     │
                          │ - Schedule retry      │
                          │ - Track error reason  │
                          └───────────────────────┘
```

---

## Entities Summary

| Entity | Purpose | Primary Key | Storage |
|--------|---------|-------------|---------|
| LiteLLM Request | Incoming request context | request_id | In-memory (gateway) |
| vLLM Response | Model execution result | request_id | In-memory (callback) |
| Langfuse Trace | Observability record | trace_id | Langfuse database |
| Trace Buffer Entry | Failed trace resilience | trace_id | JSONL file (litellm/data/trace_buffer.jsonl) |
| API Key | Authentication & attribution | key_id | Configuration / external key store |

---

## Data Flow Summary

```
Request → LiteLLM
  ├─ Extract metadata from headers
  ├─ Validate API key
  ├─ Route to vLLM
  │
  └─ vLLM Response
      ├─ Generate response
      ├─ Extract tokens/latency
      │
      └─ LiteLLM Callback
          ├─ Combine request + response + metadata
          ├─ Create Langfuse trace
          ├─ Attempt submit (with retries)
          │
          ├─ Success → Trace in Langfuse
          │
          └─ Failure → Buffer to disk
              ├─ Async buffer flusher retries periodically
              └─ Eventually Success → Trace in Langfuse
```
