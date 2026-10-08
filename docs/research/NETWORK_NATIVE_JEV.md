# JEV Network-Native Execution Research

Status: research proposal; no dataplane implementation is claimed.

## Objective

Reduce host CPU/GPU involvement to zero on the steady-state path for a bounded class of deterministic operations, by placing work on supported switches, NICs/DPUs, associative-memory devices, storage engines, or trusted remote endpoints. The design does not claim zero physical computation or general-purpose intelligence without computation.

## Existing JEV-Developer boundary

JEV-Developer is an offline-first coding agent using typed decisions and guarded tools. Network-native execution is an optional, separate capability backend. It must not alter the current READ/SEARCH/EDIT/RUN policy, expand the shell allow-list, bypass human-gated EDIT, or enable privileged network mutation by default.

## Proposed architecture

```text
Typed JEV request
  -> schema + tenant/policy validation
  -> capability discovery
  -> target planner
       ├─ cache/state reuse
       ├─ P4 programmable dataplane
       ├─ NIC/DPU offload
       ├─ memory/storage-side operation
       ├─ explicitly authorized remote executor
       └─ host fallback (only if caller policy allows)
  -> execute bounded instruction
  -> verify output/evidence/freshness
  -> append redacted trace
  -> result + honest execution telemetry
```

### Execution tiers

1. **Cache/state reuse**: only return a cached result when identity, tenant, key, freshness and invalidation rules match.
2. **P4 switch**: bounded match/action, counters, meters and target-supported stateful operations. Reject programs exceeding parser, stage, register or target resource limits.
3. **XDP/eBPF**: kernel datapath optimization; hardware offload and AF_XDP zero-copy depend on NIC/driver/kernel. It is not automatically CPU-free.
4. **NIC/DPU**: offload only functions supported by device firmware, driver and SDK.
5. **RDMA/NVMe-oF**: use for data movement and storage I/O; do not claim that RDMA itself provides reasoning. Connection setup, control, completion/error paths and storage backends may still use host CPUs.
6. **FC SAN**: keep Fibre Channel identity and fabric controls separate from Ethernet identities. Model WWPN/WWNN, FCID, VSAN, zoning, LUN masking and multipath; initial phase read-only inventory/diagnostics only.
7. **Remote execution**: only an explicitly trusted endpoint, with authenticated mutual identity, scoped authorization, resource limits, replay protection and verifiable results.
8. **Host/GPU fallback**: default `deny` under strict-offload mode. If fallback is allowed, record that it occurred and report CPU/GPU use honestly.

## Draft instruction set

- `MATCH`: bounded pattern/rule lookup.
- `FILTER`: remove events that do not match policy.
- `COUNT`: use supported hardware counters.
- `AGGREGATE`: bounded aggregation supported by target.
- `FETCH`: retrieve existing state/data.
- `ROUTE_HINT`: produce a proposal, not direct mutation, in MVP.
- `VERIFY`: validate a result against explicit evidence and freshness requirements.
- `COMMIT`: state-changing action; requires authorization, idempotency key and approval policy.
- `ROLLBACK`: bounded compensating action; must be independently tested.

Every opcode must declare inputs/outputs, maximum state footprint, supported target classes, determinism/idempotency, time/resource budgets, authorization scope, evidence policy, failure semantics, and fallback policy. The planner must reject unknown or unsupported opcode/target combinations; no implicit fallback.

## Network optimization methods to evaluate

1. Baseline first: NIC RSS, IRQ affinity, NUMA placement, queue sizing, MTU and offload feature compatibility.
2. Path distribution: ECMP / weighted ECMP; flowlet/adaptive routing only when actual switch supports the mechanism. Avoid packet spraying for ordered stateful flows unless reordering is explicitly handled.
3. Congestion: ECN feedback, queue occupancy, supported DCTCP/RDMA congestion-control algorithms, PFC only where lossless transport requirements and deadlock analysis justify it.
4. Telemetry: device counters and in-band telemetry where supported; sample rather than export every event. Detect stale/lost/out-of-order observations.
5. Fast paths: XDP/eBPF for early classification/redirect; P4 for hardware match-action; DPDK as a CPU-based performance baseline and development option, not a zero-CPU claim.
6. Storage: compare supported NVMe/TCP vs NVMe/RDMA; evaluate SPDK only with explicit CPU-core accounting; keep FC validation in a lab fabric.
7. Recovery: health checks, circuit breakers, hysteresis and reversible routing proposals. Do not automatically mutate production routing or SAN zoning in the MVP.

## Benchmark protocol

Compare the *same workload and semantics* across: ordinary Linux socket path; XDP/eBPF where supported; DPDK software path; P4 software model; physical P4/NIC/DPU hardware where available; remote endpoint; and cache-hit path.

Record hardware/firmware/driver/kernel, topology, MTU, transport, offload settings, queue counts, workload inputs, warmup and steady-state duration, raw logs, host CPU cycles/percent, GPU utilization, interrupts/context switches, p50/p95/p99 latency, throughput, packet loss/reordering, bytes transferred, energy per successful operation when measurable, result correctness and failure recovery. Report host CPU separately from total infrastructure computation and energy.

## Success criteria

- Deterministic test oracle matches all outputs for supported operations.
- Strict-offload mode rejects unsupported targets and never silently falls back.
- Execution trace reports selected target, fallback, host CPU/GPU use and verification result.
- Security tests reject unauthenticated, cross-tenant, stale, replayed and over-budget requests.
- Hardware claims are made only from real target benchmarks; software-model results must be labelled as simulation.
- Performance must be compared to the same-workload baseline; no blanket speedup or zero-compute claim.

## Risks / non-goals

- The Internet is not an arbitrary remote compute API; execution requires a participating endpoint or programmable device.
- P4 pipelines have finite target-specific limits and are not suitable for arbitrary graph traversal or unbounded loops.
- DPUs, storage controllers, routers and memory controllers still perform physical computation.
- Remote execution expands the trust boundary and may increase latency, network cost and data exposure.
- FC SAN, RDMA and production route changes are excluded from automated changes until a lab target and rollback plan exist.

## Current documentation references used via Context7

- DPDK 25.11 guides: https://doc.dpdk.org/guides-25.11/ (poll-mode drivers, zero-copy ring operations, hardware flow features; DPDK still uses CPU polling cores).
- SPDK documentation: https://spdk.io/doc/ (NVMe-oF transports, RDMA prerequisites, polling and interrupt mode; target CPU cores need to be accounted for).
- Linux AF_XDP: https://docs.kernel.org/networking/af_xdp.html (XDP redirect and AF_XDP; zero-copy/offload vary by driver).
- FRRouting docs: https://docs.frrouting.org/ (BGP/EVPN/SRv6; deploy only in isolated lab first).
- P4 specifications: https://p4.org/specifications/ (language/target interfaces; validate architecture and resource limits per target).
- NVMe specifications: https://nvmexpress.org/specifications/ (NVMe-oF transport support; use exact device and spec revision in test reports).

Documentation was queried on 2026-10-09. Re-check current release versions and device-specific support before implementation; protocol support and documentation change over time.
