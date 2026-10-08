# JEV Network-Native Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe, testable capability-planned execution layer to JEV-Developer that can route bounded deterministic operations to supported network/storage targets and prove when host CPU/GPU execution was or was not used.

**Architecture:** Keep existing JEV typed-decision agent and guarded tools intact. Introduce a pure-Python specification/runtime first: typed operation envelopes, capability declarations, an explicit planner, deterministic simulator and structured execution evidence. Hardware adapters are opt-in implementations behind the same interface; no production routing/SAN mutations in MVP.

**Tech Stack:** Python >=3.10, existing pytest/ruff dev tooling, standard library dataclasses/enums/json/hashlib, optional hardware integrations only behind adapter interfaces. Context7 documentation: DPDK 25.11, SPDK, Linux AF_XDP/eBPF, FRRouting and P4 specifications.

**Spec:** `docs/research/NETWORK_NATIVE_JEV.md`

## Global Constraints

- Preserve current JEV-Developer CLI behavior, typed tool decisions and workspace security guards.
- Do not add runtime dependencies for the simulator MVP.
- No implicit CPU/GPU fallback in `strict_offload` mode.
- Never trust a request-provided tenant field as identity; use caller-authenticated context.
- No production route changes, SAN zoning, LUN changes or privileged hardware writes in MVP.
- Keep host CPU use, GPU use, offload selection and fallback explicit in every execution result.
- Hardware support is determined by actual adapter capability responses, not by protocol name alone.

## Review Focus

- Unknown opcode or missing target capability is rejected instead of silently falling back.
- A stale cache/state result is never returned as fresh.
- Duplicate/replayed mutating requests do not execute twice.
- Timeout/partial failure returns an indeterminate state and does not claim commit success.
- Cross-tenant or unauthenticated remote execution is rejected before dispatch.

---

### Task 1: Typed JEV operation contracts

**Files:**
- Create: `jev_developer/network_native.py`
- Test: `tests/test_network_native.py`

**Interfaces:**
- `Opcode(str, Enum)` for `MATCH`, `FILTER`, `COUNT`, `AGGREGATE`, `FETCH`, `ROUTE_HINT`, `VERIFY`, `COMMIT`, `ROLLBACK`.
- `TargetKind(str, Enum)` for `CACHE`, `P4`, `XDP`, `DPU`, `STORAGE`, `REMOTE`, `HOST`.
- `OperationRequest` dataclass: `request_id`, `opcode`, `inputs`, `tenant_id`, `strict_offload`, `allowed_targets`, `freshness_ms`, `idempotency_key`, `evidence_required`.
- `TargetCapability` dataclass: `target_id`, `kind`, `supported_opcodes`, `host_cpu_required`, `gpu_required`, `available`, `max_state_bytes`.
- `ExecutionResult` dataclass: `request_id`, `status`, `result`, `target_id`, `host_cpu_used`, `gpu_used`, `fallback_used`, `verified`, `evidence`, `error_code`.

- [ ] **Step 1: Write failing tests** for valid envelopes, unknown opcode rejection, missing tenant, invalid negative freshness, empty request IDs, and unsupported target declarations.
- [ ] **Step 2: Run** `python -m pytest tests/test_network_native.py -q`; confirm failures are caused by missing contracts.
- [ ] **Step 3: Implement** frozen/validated dataclasses and explicit input validation; avoid implicit coercions that hide malformed inputs.
- [ ] **Step 4: Re-run** `python -m pytest tests/test_network_native.py -q`; expected all tests pass.
- [ ] **Step 5: Commit** `feat: add typed JEV network operation contracts`.

### Task 2: Capability discovery and deterministic planner

**Files:**
- Modify: `jev_developer/network_native.py`
- Test: `tests/test_network_native.py`

**Interfaces:**
- `plan_execution(request: OperationRequest, capabilities: list[TargetCapability]) -> TargetCapability`.
- Deterministic target priority: permitted cache hit, eligible P4/XDP/DPU/storage, authorized remote, host only when allowed.

- [ ] **Step 1: Add tests** for target priority, target allow-list enforcement, unavailable targets, `strict_offload=True` rejecting host fallback, and normal fallback being explicitly marked.
- [ ] **Step 2: Run targeted tests** and confirm they fail before implementation.
- [ ] **Step 3: Implement** deterministic capability filtering and target selection; reject ambiguity or no eligible target with typed errors.
- [ ] **Step 4: Verify** targeted tests and add tests that host/GPU dependency comes from capability metadata, not guessed by the scheduler.
- [ ] **Step 5: Commit** `feat: plan JEV operations by explicit target capability`.

### Task 3: Deterministic simulator and verification contract

**Files:**
- Create: `jev_developer/network_simulator.py`
- Modify: `jev_developer/network_native.py`
- Test: `tests/test_network_native.py`

**Interfaces:**
- `execute_simulated(request: OperationRequest, target: TargetCapability, state: dict) -> ExecutionResult`.
- Implement only bounded `MATCH`, `FILTER`, `COUNT`, `AGGREGATE`, `FETCH`, and `VERIFY`; other mutating/route opcodes return `unsupported_in_simulator`.

- [ ] **Step 1: Write oracle tests** for all supported operations, duplicate events, empty input, malformed shapes, stale evidence and deterministic repeatability.
- [ ] **Step 2: Run** targeted tests; verify failing baseline.
- [ ] **Step 3: Implement** bounded, deterministic pure-Python semantics; enforce input item/byte limits.
- [ ] **Step 4: Verify** result matches reference oracle and output includes truthful `host_cpu_used=True` for software simulation.
- [ ] **Step 5: Commit** `feat: add deterministic JEV network simulator`.

### Task 4: Execution traces and audit-safe telemetry

**Files:**
- Modify: `jev_developer/network_native.py`
- Use: `jev_developer/logging_util.py`
- Test: `tests/test_network_native.py`

- [ ] **Step 1: Write tests** for target/fallback/result trace fields and redaction of keys, tokens, storage identifiers and payloads marked sensitive.
- [ ] **Step 2: Run** targeted tests and confirm failures.
- [ ] **Step 3: Implement** structured event records using existing JEV logging/tracing patterns; record timing/capability metadata but never raw secrets or unrestricted packet payloads.
- [ ] **Step 4: Verify** traces remain JSONL-parseable and sensitive fixture values do not appear.
- [ ] **Step 5: Commit** `feat: trace JEV target selection and offload evidence`.

### Task 5: CLI inspection and benchmark

**Files:**
- Modify: `jev_developer/cli.py`
- Modify: `jev_developer/agent.py` only if needed for a no-regression boundary; avoid wiring by default.
- Test: `tests/test_network_native.py`
- Docs: `docs/NETWORK_NATIVE_JEV.md`, `README.md`

- [ ] **Step 1: Write CLI tests** for `jev-dev network-plan --json` over declared sample capabilities and a benchmark subcommand that labels simulator results as simulation.
- [ ] **Step 2: Run** CLI tests to confirm failure.
- [ ] **Step 3: Implement** read-only `network-plan` and deterministic simulator benchmark; do not edit host routes or devices.
- [ ] **Step 4: Verify** `python -m pytest -q`, `ruff check .`, `jev-dev --help`, `jev-dev benchmark`.
- [ ] **Step 5: Commit** `feat: expose read-only JEV network planning diagnostics`.

### Task 6: Hardware-adapter conformance boundary

**Files:**
- Create: `jev_developer/network_adapters/__init__.py`
- Create: `jev_developer/network_adapters/base.py`
- Test: `tests/test_network_adapters.py`

- [ ] **Step 1: Test** adapter contract: capability advertisement, unsupported opcode rejection, timeout and connection failures, health status and no host fallback under strict mode.
- [ ] **Step 2: Confirm** failures before implementation.
- [ ] **Step 3: Implement** an abstract adapter interface only; no dependency on P4 SDK, DPDK, SPDK, RDMA libraries, physical SAN or vendor SDK in the base package.
- [ ] **Step 4: Verify** simulator adapter conforms; real adapters are gated on identified hardware, SDK version and lab access.
- [ ] **Step 5: Commit** `feat: define JEV hardware adapter conformance interface`.

### Task 7: Full regression, benchmark report and review

**Files:**
- Update: `docs/TEST_REPORT.md`
- Update: `docs/NETWORK_NATIVE_JEV.md`

- [ ] **Step 1:** Run `python -m pytest -q` and `ruff check .`.
- [ ] **Step 2:** Run CLI smoke tests and simulator benchmark, save raw outputs and environment metadata.
- [ ] **Step 3:** Confirm existing `test_policy.py`, `test_tools.py`, `test_loop.py` and `test_prod.py` pass unchanged.
- [ ] **Step 4:** Audit diff for accidental changes to tool allow-list, command execution, current agent default behavior or production networking.
- [ ] **Step 5:** Request code review before integration; open a PR from the research branch. Do not merge hardware-dependent behavior until physical-target conformance and failure tests exist.
