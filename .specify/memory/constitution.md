<!--
Sync Impact Report
Version change: N/A → 1.0.0
Modified principles: added 7 mandatory principle sections for API gateway governance, observability, model serving, cost tracking, reliability, security, and developer experience
Added sections: Infrastructure Constraints; Implementation & Test Requirements
Removed sections: none
Templates reviewed: .specify/templates/plan-template.md ✅ no change required; .specify/templates/spec-template.md ✅ no change required; .specify/templates/tasks-template.md ✅ no change required; .specify/templates/constitution-template.md ✅ no change required
Follow-up TODOs: none
-->

# LLM Infrastructure Constitution

## Core Principles

### API Gateway Governance
LiteLLM is the only public ingress for all client requests. Every request MUST be authenticated using a unique API key and MUST carry explicit `team_id` and `user_id` metadata.
- All requests MUST be routed through LiteLLM only.
- Direct client access to vLLM endpoints is forbidden.
- LiteLLM MUST log input tokens, output tokens, total tokens, and latency metrics for p50, p95, and p99.
- LiteLLM MUST enforce per-API key rate limits, quotas, retries, and fallback behavior.

### Observability & Traceability
Every request MUST be traced end-to-end across LiteLLM and vLLM with structured JSON telemetry.
- Traces MUST include prompt, response, model used, queue time, inference time, total latency, and business metadata including `team_id`, `api_key`, and `user_id`.
- Correlation IDs MUST be propagated across LiteLLM → vLLM and included in every request and log entry.
- Logs MUST be structured JSON and include all observability metadata required for debugging, audit, and cost attribution.
- Langfuse MUST capture request-level traces, model-level metrics, latency breakdowns, and prompt/response logs.

### Model Serving Abstraction
Model serving MUST be abstracted behind LiteLLM routing so clients never access vLLM directly.
- LiteLLM MUST perform routing to vLLM-hosted models, including model version selection and dynamic routing.
- vLLM endpoints MUST remain internal-only and inaccessible to clients.
- Model serving MUST support horizontal scaling, model versioning, and routing policy changes without client-side configuration changes.

### Cost & Usage Accountability
Token and cost accounting MUST be tracked at both the API key and team scope for every request.
- Usage data MUST include input tokens, output tokens, total tokens, and request cost estimate.
- Cost estimation logic MUST run per request and be available to dashboards and downstream billing workflows.
- Aggregated dashboards MUST be ready to report per-key, per-team, and per-use-case usage and cost trends.

### Reliability & Performance
The system MUST meet defined SLAs through explicit timeouts, retries, and circuit-breaking controls.
- Define and publish latency targets and uptime expectations before production deployment.
- Circuit breakers MUST protect downstream vLLM services from overload.
- Requests MUST use timeouts and retries with exponential backoff.
- Performance metrics MUST include throughput and latency distributions to prove SLA compliance.

### Security & Compliance
Secrets MUST never be stored in code. Security and audit controls are required for all production data and logs.
- API keys MUST be securely stored, hashed, and validated outside source code.
- Prompt and response logging MUST support redaction for sensitive data.
- Audit logging MUST capture authentication events, administrative changes, and request routing decisions.

### Developer Experience
The architecture MUST be simple, modular, and aligned with enterprise-grade self-hosted LLM operations.
- The design MUST maintain a clear separation between gateway, observability, and model serving layers.
- Dependencies MUST remain minimal and intentional.
- The solution MUST avoid over-engineering by keeping each layer focused on its core responsibility.

## Infrastructure Constraints
The deployment model MUST support the stated 5-layer architecture and self-hosted requirements.
- Infra Layer: single-node RTX 3060 GPU for vLLM inference.
- Serving Layer: vLLM as the model execution engine behind LiteLLM.
- Observability Layer: Langfuse for distributed tracing, metrics, evals, and prompt management.
- Routing Layer: LiteLLM MUST act as the API gateway, cost tracker, guardrail enforcer, load balancer, and request logger.
- Client Layer: standard Python SDK clients access only LiteLLM endpoints using issued API keys.
- Docker Compose definitions MUST be provided for Langfuse and LiteLLM deployments that follow industry standards for observability and secure configuration.

## Implementation & Test Requirements
End-to-end testing MUST validate the full LiteLLM → vLLM → Langfuse path independently from development tooling.
- Separate E2E tests MUST cover authentication, routing, observability, token accounting, retry behavior, and failure handling.
- Deployment artifacts MUST include docker-compose files for Langfuse and LiteLLM with secure environment configuration.
- Documentation MUST explicitly describe how to provision API keys, enable tracing, and enforce team-level policies.
- Every architectural decision MUST be justified by the principles in this constitution.

## Governance
This constitution is authoritative for self-hosted LLM infrastructure decisions and supersedes informal practices.
- All design and implementation work MUST be reviewed against this constitution before approval.
- Amendments MUST be documented, approved, and versioned with a clear rationale.
- Compliance reviews MUST verify API gateway governance, observability coverage, model serving isolation, cost tracking, reliability safeguards, security controls, and developer ergonomics.

**Version**: 1.0.0 | **Ratified**: 2026-04-18 | **Last Amended**: 2026-04-18
