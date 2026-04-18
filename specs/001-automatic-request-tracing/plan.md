# Implementation Plan: Automatic Request Tracing via LiteLLM → Langfuse Integration

**Branch**: `001-automatic-request-tracing` | **Date**: 2026-04-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-automatic-request-tracing/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Enable automatic, transparent tracing of every LiteLLM request in Langfuse without requiring developer instrumentation. This feature enforces API gateway governance by capturing all traffic at the LiteLLM layer and streaming structured traces to Langfuse with full prompt, response, token, latency, and business metadata. Implementation uses LiteLLM's callback mechanisms to intercept requests and a dedicated Langfuse trace submission service that handles retries and failures gracefully without blocking the request path.

## Technical Context

**Language/Version**: Python 3.8+ (LiteLLM and observability stack support)  
**Primary Dependencies**: LiteLLM (gateway), Langfuse (observability platform), vLLM (model serving), pydantic (data validation)  
**Storage**: Configuration files (YAML/env), Langfuse PostgreSQL backend, optional trace buffer (Redis or file-based for resilience)  
**Testing**: pytest for unit tests, requests/httpx for integration tests, docker-compose for E2E testing  
**Target Platform**: Linux server (containerized via docker-compose with RTX 3060 GPU node)
**Project Type**: Web-service configuration and integration layer (glue between gateway and observability)  
**Performance Goals**: <200ms p95 latency for trace submission, 99%+ request capture rate, <100MB memory for trace buffer  
**Constraints**: No direct vLLM client access permitted, structured JSON logs mandatory, correlation IDs must be propagable, Langfuse unavailability must not block requests  
**Scale/Scope**: Single RTX 3060 node initially with team-level quotas and per-API-key metrics ready for multi-node scaling

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance Review

| Principle | Requirement | Plan Status |
|-----------|-------------|-------------|
| API Gateway Governance | LiteLLM as exclusive ingress, team_id/user_id metadata required | ✓ PASS - Spec enforces gateway-only access and metadata propagation |
| Observability & Traceability | Every request traced with structured JSON, correlation IDs propagated | ✓ PASS - Automatic tracing via callbacks, correlation IDs in design |
| Model Serving Abstraction | vLLM internal-only, no direct client access | ✓ PASS - Architecture isolates vLLM behind LiteLLM |
| Cost & Usage Accountability | Token usage and cost tracked in traces | ✓ PASS - Token counts captured in Langfuse traces |
| Reliability & Performance | Graceful failure handling, timeouts, retries with backoff | ✓ PASS - Langfuse failures non-blocking, retry strategy in spec |
| Security & Compliance | Secure key storage, audit logging, redaction support | ✓ PASS - Tracing layer handles sensitive data, audit logs via traces |
| Developer Experience | Simple, modular, minimal dependencies | ✓ PASS - Gateway-level integration avoids application-code instrumentation |
| Infrastructure Constraints | Docker Compose deployment, LiteLLM/Langfuse integration | ✓ PASS - Configuration-driven setup via docker-compose |

**Gate Result**: ✅ **PASS** - Feature aligns with all constitutional principles. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-automatic-request-tracing/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command) - design decisions
├── data-model.md        # Phase 1 output (/speckit.plan command) - entities and schemas
├── quickstart.md        # Phase 1 output (/speckit.plan command) - integration guide
├── contracts/           # Phase 1 output (/speckit.plan command) - API and callback contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
litellm/
├── docker-compose.yaml          # Existing LiteLLM deployment config
├── config/
│   ├── litellm_config.yaml       # LiteLLM configuration with Langfuse callbacks
│   ├── litellm_langfuse_callback.py  # Custom callback for Langfuse trace submission
│   └── langfuse_schema.json      # Langfuse trace payload schema
└── tests/
    ├── contract/
    │   ├── test_langfuse_callback.py       # Contract tests for callback behavior
    │   └── test_trace_schema.py            # Trace payload schema validation
    ├── integration/
    │   ├── test_e2e_request_tracing.py     # E2E test: request → trace in Langfuse
    │   ├── test_metadata_propagation.py    # Metadata flow through layers
    │   ├── test_gateway_only_access.py     # Verify no direct vLLM access
    │   └── test_langfuse_resilience.py     # Langfuse failure handling
    └── unit/
        ├── test_callback_extraction.py     # Token/latency extraction logic
        ├── test_correlation_id.py          # Correlation ID generation/propagation
        └── test_trace_submission.py        # Retry logic and buffering

langfuse/
├── docker-compose.yml            # Existing Langfuse deployment config
└── [no changes required - observability endpoint]

client-examples/
└── example_client.py             # Example Python client showing metadata headers
```

**Structure Decision**: Single configuration and integration point at the LiteLLM layer (litellm/config/) with comprehensive tests covering gateway behavior, metadata propagation, tracing accuracy, and failure resilience. No changes required to Langfuse deployment; no SDK required in client code.

## Phase 0: Research & Design Decisions

**Goal**: Resolve technical unknowns and design decisions for Langfuse integration, trace schema, and failure handling.

### Research Areas

1. **LiteLLM Callback Architecture** - How does LiteLLM support custom callbacks? What are the lifecycle hooks available (pre-request, post-request, on-error)?
2. **Trace Schema Definition** - What is the Langfuse trace payload schema? Which fields are required vs optional for cost tracking and debugging?
3. **Metadata Propagation Pattern** - How should team_id, user_id, api_key, and use_case flow from client headers through LiteLLM to Langfuse?
4. **Correlation ID Strategy** - How to generate and propagate correlation IDs? Should UUIDs or request hashes be used?
5. **Retry & Backoff Policy** - What retry strategy is appropriate for Langfuse trace submission? Exponential backoff or fixed delay?
6. **Buffering & Resilience** - Should failed traces be buffered to disk/Redis, or re-attempted with a queue?
7. **Token Extraction from vLLM** - How to capture input/output token counts from vLLM responses?
8. **Industry Best Practices** - What are best practices for observability integration in API gateways (reference: Kong, API7, Tyk)?

### Outputs

This phase produces `research.md` documenting each design decision, rationale, and any alternative approaches considered.

---

## Phase 1: Design & Contracts

**Goal**: Define data models, API contracts, and integration interfaces.

### Deliverables

1. **data-model.md** - Entities and relationships:
   - LiteLLM Request (prompt, model, metadata, timing)
   - Langfuse Trace (structure, required fields, metadata)
   - API Key / Team context
   - Correlation ID context

2. **contracts/** - Define interfaces:
   - LiteLLM callback contract (input/output signatures)
   - Langfuse trace submission API contract (JSON schema)
   - Client metadata header contract (required headers/fields)
   - Error/retry response contract

3. **quickstart.md** - Integration guide:
   - How to enable tracing in LiteLLM config
   - How to supply metadata headers from client
   - How to verify traces appear in Langfuse
   - Troubleshooting guide

### Re-Check Constitution

After Phase 1 design, verify:
- ✓ Observability layer captures all required fields
- ✓ API gateway governance enforced at callback level
- ✓ Failure handling aligns with reliability principle
- ✓ No Langfuse SDK required in client code (developer experience)

---

## Next Steps

1. Complete Phase 0 research (→ research.md)
2. Complete Phase 1 design (→ data-model.md, contracts/, quickstart.md)
3. Run `/speckit.tasks` to generate task list (→ tasks.md)
4. Begin implementation work per tasks.md
