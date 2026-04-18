# Feature Specification: Automatic Request Tracing via LiteLLM → Langfuse Integration

**Feature Branch**: `001-automatic-request-tracing` <br>
**Created**: 2026-04-18 <br>
**Status**: Draft <br>
**Input**: Developer instrumentation currently required for Langfuse tracing; goal is automatic tracing at the LiteLLM gateway layer.

## User Scenarios & Testing

### User Story 1 - Automated Trace Capture (Priority: P1)
A LiteLLM client request is routed through LiteLLM and automatically appears in Langfuse without any developer instrumentation.

**Why this priority**: This fixes the core observability gap and enforces the constitution requirement that all requests be traced automatically through the gateway.

**Independent Test**: Send a valid LiteLLM request and verify the request trace appears in Langfuse with prompt, response, token usage, latency, model, and metadata.

**Acceptance Scenarios**:
1. **Given** a valid API key and team/user metadata, **when** a client sends a request through LiteLLM, **then** Langfuse receives and records a complete trace for that request.
2. **Given** a request routed through LiteLLM, **when** the request completes successfully, **then** the Langfuse trace includes prompt, response, model name, input/output/total tokens, and latency breakdown.
3. **Given** a request routed through LiteLLM, **when** the request is dropped or rejected, **then** the failure is logged and trace metadata still includes team_id, user_id, api_key, and use_case.

---

### User Story 2 - Enforced Gateway-only Access (Priority: P2)
All clients must access vLLM indirectly through LiteLLM; no direct vLLM calls are permitted.

**Why this priority**: This enforces the constitution’s API gateway governance and model serving isolation principles.

**Independent Test**: Attempt a direct vLLM call and verify it is blocked or cannot be reached when the system is configured for production.

**Acceptance Scenarios**:
1. **Given** a client knows the internal vLLM endpoint, **when** they attempt a direct request, **then** the request is rejected or fails because the endpoint is not exposed publicly.
2. **Given** LiteLLM is available, **when** a request is sent using the client API, **then** the request flows through LiteLLM and not directly to vLLM.

---

### User Story 3 - Metadata Propagation and Structured Logs (Priority: P3)
Metadata including team_id, user_id, api_key, and use_case propagate through LiteLLM into Langfuse traces and structured logs.

**Why this priority**: Accurate metadata is essential for cost tracking, audit, and observability consistency.

**Independent Test**: Send a request with metadata and verify Langfuse stores the exact metadata values in the trace and logs.

**Acceptance Scenarios**:
1. **Given** a request includes team_id and user_id, **when** the request is traced, **then** Langfuse trace attributes contain the same metadata values.
2. **Given** a request includes a use_case label, **when** tracing is performed, **then** the use_case appears in the trace metadata.

---

### Edge Cases
- What happens when Langfuse is unavailable? The gateway must continue handling requests and retry trace submission without blocking the client path.
- What happens if metadata is missing? LiteLLM should reject requests missing required API gateway metadata or default to safe tracing metadata rules.
- What happens when a request is retried? The trace must preserve correlation IDs and avoid duplicate primary request records.

## Requirements

### Functional Requirements
- **FR-001**: LiteLLM MUST automatically generate a Langfuse trace for every request that passes through the gateway.
- **FR-002**: LiteLLM MUST collect prompt, response, model name, input tokens, output tokens, total tokens, queue latency, inference latency, and total latency for every request.
- **FR-003**: LiteLLM MUST attach metadata fields `team_id`, `user_id`, `api_key` (required) and `use_case` (optional) to every trace.
- **FR-004**: Langfuse integration MUST be configured at the LiteLLM layer using callbacks or gateway-level hooks, not in downstream application code.
- **FR-005**: Client code MUST remain unchanged beyond sending requests through LiteLLM with standard metadata headers.
- **FR-006**: Direct client access to vLLM endpoints MUST be disallowed in the deployment architecture.
- **FR-007**: LiteLLM MUST handle Langfuse failures gracefully by retrying trace submission and optionally buffering trace payloads without blocking the request path.
- **FR-008**: All logs and traces MUST use structured JSON format.
- **FR-009**: Correlation IDs MUST propagate from client to LiteLLM to Langfuse and be present in all gateway logs.

### Key Entities
- **LiteLLM Gateway Request**: Represents an incoming request with prompt, metadata, and routing information.
- **Langfuse Trace**: Represents the observability record containing prompt, response, token usage, latency, model, metadata, and correlation IDs.
- **API Key**: A unique credential tied to team_id and user_id used for authentication and tracing context.
- **vLLM Model Endpoint**: Internal-only backend model execution endpoint that receives routed requests from LiteLLM.

## Success Criteria

### Measurable Outcomes
- **SC-001**: 100% of production LiteLLM requests are captured as Langfuse traces without developer instrumentation.
- **SC-002**: 95% of traced requests include prompt, response, model name, token usage (input/output/total), latency breakdown (queue, inference, total per data-model.md), and required metadata.
- **SC-003**: No direct vLLM request path exists for clients in the configured deployment.
- **SC-004**: Langfuse trace submission failures do not cause client request failures for at least 99% of requests.
- **SC-005**: At least 90% of requests preserve a correlation ID from client through LiteLLM to Langfuse.

## Assumptions
- LiteLLM is already the central gateway and can be extended with callback or hook support for Langfuse.
- Clients are able to supply `team_id`, `user_id`, `api_key`, and optional `use_case` via request headers or request payload.
- vLLM is hosted internally and not exposed to external clients; network policy or firewall rules enforce this.
- Langfuse can accept traces asynchronously and supports retry semantics when unavailable.
- Custom dashboards and billing pipelines are out of scope for this feature.

## Deliverables
- LiteLLM configuration artifacts describing Langfuse callback or hook setup using YAML or environment variables.
- Updated client interaction pattern that uses standard Python SDK calls to LiteLLM with metadata headers and no Langfuse SDK usage.
- E2E test plan covering automatic tracing, gateway-only routing, metadata propagation, trace fidelity, and Langfuse failure behavior.
- Failure handling behavior specification for Langfuse unavailability, retry/backoff, and non-blocking request flow.

## Principles Alignment
- **API Gateway Governance**: Requires LiteLLM as the exclusive ingress, blocks direct vLLM access, and ensures all requests carry team and user metadata.
- **Observability**: Requires automatic, standardized Langfuse tracing with structured JSON telemetry for every request.
- **Model Serving Abstraction**: Keeps vLLM internal-only and routes all model execution through LiteLLM.
- **Cost & Usage Accountability**: Captures token usage and metadata in every trace for downstream cost and team attribution.
- **Reliability & Performance**: Defines graceful Langfuse failure handling, retry behavior, and non-blocking request success.
- **Security & Compliance**: Keeps tracing configuration in the gateway layer and removes developer-side SDK instrumentation from application code.
- **Developer Experience**: Simplifies client integration by requiring no additional observability code, only standard LiteLLM request usage.
