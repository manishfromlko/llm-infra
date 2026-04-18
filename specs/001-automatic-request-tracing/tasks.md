---
description: "Task list for Automatic Request Tracing via LiteLLM → Langfuse Integration"
---

# Tasks: Automatic Request Tracing via LiteLLM → Langfuse Integration

**Input**: Design documents from `/specs/001-automatic-request-tracing/`
**Prerequisites**: plan.md (✓), spec.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓), quickstart.md (✓)

**Tests**: End-to-end tests are included and critical for this feature (automatic tracing and resilience). Tests are organized by user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase Mapping Note

Phase numbering in this document (1-6) corresponds to execution phases:
- **Phase 1 (Setup)** + **Phase 2 (Foundational)** = plan.md research and core infrastructure scaffolding
- **Phases 3-5** = user story implementation (can run in parallel after Phase 2 completes)
- **Phase 6** = cross-cutting concerns, polish, and production readiness

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Repository root: `/Users/manish/mount/spec-kit/llm-infra`
LiteLLM config: `litellm/config/`
Tests: `litellm/tests/{contract,integration,unit}/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create LiteLLM config directory structure: `litellm/config/`, `litellm/data/trace_buffer/`, `litellm/tests/{contract,integration,unit}/`
- [ ] T002 Create LiteLLM callback scaffold in `litellm/config/litellm_langfuse_callback.py` with async function signature
- [ ] T003 [P] Create Langfuse trace schema validator in `litellm/config/langfuse_schema.py` (Pydantic model)
- [ ] T004 [P] Create trace submission client in `litellm/config/trace_client.py` with HTTP methods and retry logic
- [ ] T005 Create trace buffer manager in `litellm/config/trace_buffer.py` for JSONL file persistence
- [ ] T006 [P] Create metadata extractor in `litellm/config/metadata_extractor.py` for header parsing and validation
- [ ] T007 [P] Create correlation ID generator in `litellm/config/correlation_id.py` (UUID v4 + fallback generation)
- [ ] T008 Create structured JSON logger in `litellm/config/json_logger.py` for gateway logging
- [ ] T009 [P] Update `litellm/docker-compose.yaml` with environment variables for Langfuse integration
- [ ] T010 Create `litellm/config/.env.example` with Langfuse credentials and LiteLLM config templates

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 Implement LiteLLM callback registration in `litellm/config/litellm_config.yaml` (add langfuse_config section)
- [ ] T012 Implement async callback executor in `litellm/config/litellm_langfuse_callback.py` with proper exception handling
- [ ] T013 Implement API key validation in `litellm/config/api_key_validator.py` (hash comparison, status check)
- [ ] T014 [P] Implement metadata extraction from headers in `litellm/config/metadata_extractor.py` (X-Team-Id, X-User-Id, X-Api-Key, X-Correlation-Id)
- [ ] T015 [P] Implement correlation ID generation and propagation in `litellm/config/correlation_id.py` (UUID fallback if missing from headers)
- [ ] T016 [P] Implement trace schema validation in `litellm/config/langfuse_schema.py` (Pydantic models for request/response/trace)
- [ ] T017 Implement trace submission client with exponential backoff in `litellm/config/trace_client.py` (retry up to 3 times, 100/200/400ms delays + jitter)
- [ ] T018 [P] Implement JSONL trace buffer in `litellm/config/trace_buffer.py` (write, read, flush, size management)
- [ ] T019 Implement async buffer flusher in `litellm/config/trace_buffer_flusher.py` (periodic retry of failed traces)
- [ ] T020 [P] Implement token extraction from vLLM response in `litellm/config/token_extractor.py` (parse usage field from OpenAI-format response)
- [ ] T021 Implement latency measurement (queue + inference + total) in `litellm/config/latency_tracker.py`
- [ ] T022 [P] Implement structured JSON logging in `litellm/config/json_logger.py` with metadata fields
- [ ] T023 Update `litellm/config/api_keys.json` with sample API keys for testing; reference schema in contracts/README.md; include test keys for team1/user1, team2/user2
- [ ] T024 Create environment configuration in `.env` with required variables: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST, LITELLM_PORT, LITELLM_MASTER_KEY; reference litellm/config/.env.example template

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Trace Capture (Priority: P1) 🎯 MVP

**Goal**: Every LiteLLM request automatically generates a Langfuse trace with complete prompt, response, tokens, latency, model, and metadata.

**Independent Test**: Send a valid LiteLLM request through the gateway and verify the trace appears in Langfuse with all required fields populated.

### Tests for User Story 1 (End-to-End) ⚠️

> **NOTE: Write tests FIRST, ensure they FAIL before implementation**

- [ ] T025 [P] [US1] Contract test for Langfuse trace schema in `litellm/tests/contract/test_trace_schema.py` (validate all required fields)
- [ ] T026 [P] [US1] Contract test for callback invocation in `litellm/tests/contract/test_langfuse_callback.py` (async execution, non-blocking)
- [ ] T027 [US1] Integration test for E2E request tracing in `litellm/tests/integration/test_e2e_request_tracing.py` (request → LiteLLM → vLLM → Langfuse)
- [ ] T028 [US1] Integration test for trace fidelity in `litellm/tests/integration/test_trace_fidelity.py` (prompt, response, tokens match)

### Implementation for User Story 1

- [ ] T029 Implement trace object creation in LiteLLM callback in `litellm/config/litellm_langfuse_callback.py` (combine request + response + metadata)
- [ ] T030 [P] Implement token count attachment to trace in `litellm/config/token_extractor.py` (input, output, total from vLLM response)
- [ ] T031 [P] Implement latency breakdown attachment to trace (queue time, inference time, total latency)
- [ ] T032 Implement trace submission to Langfuse in `litellm/config/trace_client.py` with success/failure handling
- [ ] T033 Implement error handling in callback: on Langfuse submission failure, buffer trace to disk without blocking request path
- [ ] T034 [P] Implement retry logic in `litellm/config/trace_client.py` (exponential backoff, max 3 retries)
- [ ] T035 Implement trace buffering on submission failure in `litellm/config/trace_buffer.py` (persist to JSONL, enable async recovery)
- [ ] T036 Implement buffer flushing mechanism in `litellm/config/trace_buffer_flusher.py` (periodic retry of buffered traces)
- [ ] T037 [P] Add logging for trace submission status in `litellm/config/json_logger.py` (success, retry, buffered, error)
- [ ] T038 Implement E2E test execution and validation in `litellm/tests/integration/test_e2e_request_tracing.py`
- [ ] T039 Verify trace capture with request rate testing in `litellm/tests/integration/test_trace_throughput.py` (100+ req/s)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Every request generates a trace in Langfuse.

---

## Phase 4: User Story 2 - Enforced Gateway-only Access (Priority: P2)

**Goal**: All clients must access LLMs through LiteLLM; direct vLLM access is blocked.

**Independent Test**: Attempt a direct vLLM call and verify it fails or cannot be reached.

### Tests for User Story 2

- [ ] T040 [P] [US2] Contract test for API key authentication in `litellm/tests/contract/test_api_key_validation.py` (valid key accepted, invalid/missing key rejected)
- [ ] T041 [P] [US2] Contract test for metadata header requirement in `litellm/tests/contract/test_metadata_validation.py` (missing X-Team-Id / X-User-Id rejected)
- [ ] T042 [US2] Integration test for gateway-only routing in `litellm/tests/integration/test_gateway_only_access.py` (direct vLLM call fails, LiteLLM call succeeds)
- [ ] T043 [US2] Integration test for request rejection in `litellm/tests/integration/test_invalid_credentials.py` (invalid API key, missing headers → 400/401 responses)

### Implementation for User Story 2

- [ ] T044 Update `litellm/docker-compose.yaml` to hide vLLM from external network (internal network only)
- [ ] T045 [P] Implement API key validation in `litellm/config/api_key_validator.py` (check against store, verify status)
- [ ] T046 [P] Implement metadata header validation in `litellm/config/metadata_extractor.py` (reject requests missing X-Team-Id, X-User-Id, X-Api-Key)
- [ ] T047 Implement gateway authentication middleware in LiteLLM config (enforce before routing to vLLM)
- [ ] T048 [P] Add error responses for authentication failures (HTTP 401, 400) in `litellm/config/error_handler.py`
- [ ] T049 Implement network policy or docker-compose configuration to isolate vLLM from public access
- [ ] T050 Create integration test that verifies direct vLLM access fails in `litellm/tests/integration/test_gateway_only_access.py`
- [ ] T051 Document network isolation in `specs/001-automatic-request-tracing/quickstart.md` (already done in Phase 1 planning)

**Checkpoint**: Direct vLLM access is blocked. All requests must flow through LiteLLM.

---

## Phase 5: User Story 3 - Metadata Propagation and Structured Logs (Priority: P3)

**Goal**: Metadata (team_id, user_id, api_key, use_case) flows from client headers through LiteLLM to Langfuse traces and logs.

**Independent Test**: Send requests with different metadata values and verify Langfuse traces contain exact metadata values.

### Tests for User Story 3

- [ ] T052 [P] [US3] Unit test for metadata extraction in `litellm/tests/unit/test_metadata_extraction.py` (extract from headers correctly)
- [ ] T053 [P] [US3] Unit test for correlation ID handling in `litellm/tests/unit/test_correlation_id.py` (generate UUID if missing, propagate if present)
- [ ] T054 [US3] Integration test for metadata propagation in `litellm/tests/integration/test_metadata_propagation.py` (headers → trace attributes)
- [ ] T055 [US3] Integration test for multi-team scenarios in `litellm/tests/integration/test_multi_team_isolation.py` (team-a traces isolated from team-b)
- [ ] T056 [US3] Integration test for use_case tracking in `litellm/tests/integration/test_use_case_labels.py` (use_case label appears in traces)
- [ ] T057 [US3] Integration test for structured JSON logs in `litellm/tests/integration/test_structured_logging.py` (all logs contain metadata fields)

### Implementation for User Story 3

- [ ] T058 [P] Implement metadata extraction from headers in `litellm/config/metadata_extractor.py` (X-Team-Id, X-User-Id, X-Api-Key, X-Use-Case, X-Correlation-Id)
- [ ] T059 [P] Implement metadata attachment to trace object in LiteLLM callback (include in Langfuse trace payload)
- [ ] T060 [P] Implement metadata inclusion in structured JSON logs in `litellm/config/json_logger.py` (every log entry includes team_id, user_id, request_id)
- [ ] T061 Implement API key hashing in `litellm/config/metadata_extractor.py` (store hash in traces, not plain key)
- [ ] T062 [P] Implement correlation ID propagation through layers (request → LiteLLM → vLLM → callback → Langfuse)
- [ ] T063 Implement trace metadata enrichment with all required fields (team_id, user_id, use_case, correlation_id, model, request_id)
- [ ] T064 Create integration test for multi-team isolation in `litellm/tests/integration/test_multi_team_isolation.py`
- [ ] T065 Create integration test for use_case analytics in `litellm/tests/integration/test_use_case_labels.py`
- [ ] T066 Implement metadata field validation (team_id/user_id non-empty, correlation_id valid UUID if provided)

**Checkpoint**: Metadata flows from client headers through all layers and appears in traces and logs. Multi-team isolation verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories and production readiness

- [ ] T067 [P] [US1] E2E resilience test for Langfuse unavailability in `litellm/tests/integration/test_langfuse_resilience.py` (stop Langfuse, verify requests succeed, traces buffered, Langfuse restart flushes buffer)
- [ ] T068 [US1] E2E test for buffer overflow handling in `litellm/tests/integration/test_buffer_overflow.py` (buffer >100MB triggers oldest-first cleanup)
- [ ] T069 [P] [US1] E2E test for retry behavior in `litellm/tests/integration/test_retry_behavior.py` (transient failures retried with backoff)
- [ ] T070 [P] Implement comprehensive error logging in all modules (callbacks, trace submission, buffer management)
- [ ] T071 Create example client implementation in `litellm/examples/example_client.py` (demonstrates metadata header usage)
- [ ] T072 Create API key provisioning guide in `docs/API_KEY_PROVISIONING.md` (how to create and manage API keys)
- [ ] T073 Update docker-compose configurations with all Langfuse integration settings
- [ ] T074 Create environment variable reference in `litellm/.env.example` (all configurable parameters documented)
- [ ] T075 [P] Add metrics/observability for callback execution (trace submission latency, retry counts, buffer size)
- [ ] T076 Create troubleshooting guide in `docs/TROUBLESHOOTING.md` (missing traces, high latency, buffer overflow, Langfuse failures)
- [ ] T077 [P] Run all unit tests in `litellm/tests/unit/` with >80% coverage
- [ ] T078 Run all contract tests in `litellm/tests/contract/` with all scenarios passing
- [ ] T079 Run all integration tests in `litellm/tests/integration/` with full E2E scenarios
- [ ] T080 [P] Documentation updates in `specs/001-automatic-request-tracing/quickstart.md` (already created, verify correctness)
- [ ] T081 Create deployment runbook in `docs/DEPLOYMENT.md` (step-by-step instructions for production deployment)
- [ ] T082 Code review checklist in `docs/CODE_REVIEW_CHECKLIST.md` (verify all principles, test coverage, error handling)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✓ MVP
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 and US3 ✓
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1 and US2 ✓

### Within Each User Story

- Tests (contract) MUST be written and FAIL before implementation
- Implementation tasks must follow dependency order (metadata extraction before attachment, etc.)
- Integration tests can run after implementation complete

### Parallel Opportunities

**Phase 1 Setup**:
- T002, T003, T004, T005, T006, T007, T008, T009, T010 can run in parallel (independent files)

**Phase 2 Foundational**:
- T014, T015, T016, T020, T021, T022 can run in parallel (independent modules)
- T012 must complete before T017 (callback executor before trace client)
- T018 must complete before T019 (buffer implementation before flusher)

**Phase 3 (US1)**:
- T025, T026, T027, T028 can run in parallel (write tests first)
- T030, T031, T032 can run in parallel (token extraction, latency, submission)
- Tests must pass before moving to Phase 4

**Phase 4 (US2)**:
- T040, T041, T042, T043 can run in parallel (tests first)
- T044, T045, T046 can run in parallel (isolation and validation)

**Phase 5 (US3)**:
- T052, T053, T054, T055, T056, T057 can run in parallel (tests first)
- T058, T059, T060, T062 can run in parallel (metadata extraction and propagation)

**Phase 6 Polish**:
- T067, T068, T069, T075 can run in parallel (resilience E2E tests)
- T070, T071, T072, T073, T074 can run in parallel (documentation)
- T077, T078, T079 can run in parallel (test suite runs)

---

## Parallel Example: User Story 1

```bash
# Launch all Phase 1 setup tasks together (independent modules):
Task: T002 - Create callback scaffold
Task: T003 - Create trace schema validator
Task: T004 - Create trace submission client
Task: T006 - Create metadata extractor
Task: T007 - Create correlation ID generator

# After Phase 2 Foundational complete:
# Launch all US1 tests together (contract tests):
Task: T025 - Contract test for trace schema
Task: T026 - Contract test for callback invocation
Task: T027 - Integration test for E2E tracing

# After tests written (failing):
# Launch implementation tasks together:
Task: T029 - Implement trace object creation
Task: T030 - Implement token attachment
Task: T031 - Implement latency breakdown
Task: T032 - Implement trace submission

# Verify tests pass, then move to US2/US3
```

---

## Parallel Example: All User Stories (After Foundational)

```bash
# After Phase 2 Foundational complete, launch all three stories in parallel:

### US1 Stream (Team A):
Start → US1 Tests (T025-T028) → US1 Implementation (T029-T039) → Complete

### US2 Stream (Team B):
Start → US2 Tests (T040-T043) → US2 Implementation (T044-T051) → Complete

### US3 Stream (Team C):
Start → US3 Tests (T052-T057) → US3 Implementation (T058-T066) → Complete

# Once all three complete, run Phase 6 Polish/E2E in parallel:
Task: T067 - Resilience tests
Task: T071 - Example client
Task: T077-T079 - Full test suites
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

Recommended for fast validation:

1. ✓ Complete Phase 1: Setup
2. ✓ Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. ✓ Complete Phase 3: User Story 1 (Automated Trace Capture)
4. **STOP and VALIDATE**: Deploy to dev environment
   - Send test request via LiteLLM
   - Verify trace appears in Langfuse within 2 seconds
   - Verify token counts and latency breakdown correct
5. ✓ Gather feedback before proceeding to US2/US3
6. ✓ Demo to stakeholders: "Every request is now traced automatically"

**Time estimate for MVP**: ~2-3 weeks (assuming 1 team of 2 engineers)

### Full Feature (All User Stories)

Proceed after MVP validation:

7. ✓ Complete Phase 4: User Story 2 (Gateway-only Access)
   - Verify direct vLLM calls fail
   - Verify all traffic routes through LiteLLM
8. ✓ Complete Phase 5: User Story 3 (Metadata Propagation)
   - Verify team isolation in Langfuse
   - Verify use_case labels for analytics
9. ✓ Complete Phase 6: Polish & Cross-Cutting
   - Run full E2E resilience tests
   - Deploy to production with monitoring
   - Gather production telemetry

**Time estimate for full feature**: ~4-5 weeks total

---

## Quality Gates

### Before Phase 2 Completion

- [ ] All Phase 1 setup tasks complete and verified
- [ ] LiteLLM config structure in place
- [ ] Environment configuration documented

### Before User Story 1 Completion

- [ ] All Phase 2 foundational tasks complete and tested
- [ ] US1 tests all passing (contract + integration)
- [ ] Dev environment deployment successful
- [ ] Manual trace validation in Langfuse

### Before User Story 2 Completion

- [ ] US2 tests all passing (contract + integration)
- [ ] Network isolation verified (direct vLLM access blocked)
- [ ] Authentication and authorization verified

### Before User Story 3 Completion

- [ ] US3 tests all passing (contract + integration)
- [ ] Multi-team isolation verified
- [ ] Structured logging verified

### Before Production Deployment

- [ ] Phase 6 Polish tasks complete
- [ ] All E2E resilience tests passing (Langfuse downtime, buffer overflow, retries)
- [ ] Full test suite coverage >80%
- [ ] Documentation complete and reviewed
- [ ] Runbooks and troubleshooting guide finalized
