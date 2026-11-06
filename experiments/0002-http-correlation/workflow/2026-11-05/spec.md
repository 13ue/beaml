---
id: experiment-0002-http-correlation-plan
kind: experiment-plan
status: proposed-awaiting-discussion
updated: 2026-11-05
---

# EXPERIMENT 0002 plan: HTTP correlation

**[Requirement]** Produce an exact plan for discussion before implementation.
Origin: owner conversation, 2026-11-05. [Selected capture](../../../../raw/requirements/2026-11-05-http-probe-plan.md).
This file is a proposed plan. No code, dependency lock, HTTP service or EXPERIMENT RUN exists for 0002.

## Question and hypothesis

**[Proposal]** Question: can an order reference locate a verified causal path and its logs across two independent BEAM processes using HTTP?
Hypothesis: explicit HTTP propagation and a small shared observation adapter can preserve this relationship around compiled BEAML functions.
This is an integration test, not yet evidence that BEAML requires less author effort than idiomatic Elixir.

Candidate owners:

- LANGUAGE/COMPILATION: existing compiler, checked application functions and artifact/function references.
- EXECUTION: HTTP boundaries, fixed test behavior and observed outcomes.
- OBSERVATORY: permitted trace/log projection and correlation checks.

## Fixed scope

**[Proposal]** One umbrella repository, two application releases and two separate operating-system processes.
Use loopback HTTP only. Each release starts only its own business application and common runtime dependencies.
No Erlang distribution, sibling business-code dependency or direct cross-application function call is allowed.
The shared probe-support application may provide observation helpers; it owns no order or payment logic.
No Inventory application, database, actual payment, LLM, retry, broker, dashboard, Collector or replay engine is included.

Each service compiles its own `.beaml` fixture with the unchanged compiler from EXPERIMENT 0001.
The generated module name may remain `BeamlSpike`: the modules load in different processes.
Generated source and artifact hashes identify what each process executes.

## Application flow and wire contract

**[Proposal]** The test driver sends `POST /orders` to Orders with this synthetic JSON body:

```json
{"order_id":"order-1"}
```

Orders performs these operations:

1. Decode and check the exact request shape.
2. Call a compiled BEAML `prepare` function to construct a payment request.
3. Send one `POST /payments/authorize` request to Payments.
4. Decode the response and call a compiled BEAML `finish` function to check its shape and read its status.
5. Return the checked response to the driver.

Payments decodes and checks the payment request, then calls compiled BEAML `authorize`.
That function returns a fixed synthetic response. It performs no payment mutation.

```json
{"order_id":"order-1","status":"authorized"}
```

Use only the current String and exact-interface subset. No new language syntax, EFFECT system or foreign-function syntax is required.
The host adapters own JSON decoding, HTTP and tracing. BEAML owns the fixture's typed transformations and generated entry checks.
The adapter checks matching order references and the expected fixed status; String typing alone does not prove these values.
Reject malformed JSON, missing/extra fields and wrong field TYPEs with HTTP 400 and a fixed safe error body.
Unexpected downstream responses or transport failures produce a fixed HTTP 502 response.
There are no automatic retries.

## Trace, log and source contract

**[Proposal]** Use real OpenTelemetry API/SDK spans with W3C `traceparent` injection and extraction at HTTP boundaries.
Start a fresh root for each driver request. A client-supplied order reference is not a trace identity or authorization token.
Do not use baggage for the order reference. The order reference comes from the checked synthetic request body.

For each successful driver request, require exactly these six spans:

| Span | Kind | Parent |
|---|---|---|
| `orders.request` | server | none in this controlled test |
| `orders.prepare` | internal | `orders.request` |
| `orders.payment_http` | client | `orders.request` |
| `payments.request` | server | remote `orders.payment_http` |
| `payments.authorize` | internal | `payments.request` |
| `orders.finish` | internal | `orders.request` |

All six share one trace identity and have distinct span identities.
End all started spans on handled success and failure paths. Health endpoints are excluded from observation capture.
Use an always-on sampler only for this bounded fixture test; do not infer production sampling policy.

Emit two named structured application logs: `payment_request_prepared` and `payment_stub_returned`.
Each carries its service, trace/span identity, approved synthetic order reference and fixed operation name.
These are OBSERVATION EVENTS, not committed DOMAIN EVENTS or proof of payment.
The logs use Elixir Logger with a small structured output handler. An OTel logs exporter is not required.

Each internal BEAML span carries a fixture descriptor: relative source path, function name and source artifact hash.
Generate descriptors from the two explicit fixture entries, not from arbitrary stack guessing.
These are manually configured fixture references, not general compiler-generated source maps or automatic instrumentation.
The plan deliberately makes that limitation visible.

## Local evidence and search

**[Proposal]** A local SDK exporter writes normalized span records per service.
The Logger handler writes separate structured log records. Both use append-only JSONL within the new run directory.
Record original W3C trace/span values, parent references, service, kind, safe attributes and outcomes.
Do not export payloads or scan environment variables. Only the fixed synthetic fixture identifiers are allowed.
Cap each observation file at 1 MiB. On overflow, expose capture loss and fail the evidence checks.
Observation-write failure must not crash application business handling; the test runner independently marks evidence incomplete.
Explicitly flush SDK and Logger output before checking or stopping each process.

A small query script reads the two services' retained files and filters by the exact synthetic order reference.
It returns matching traces, verified parent edges, correlated application logs, fixture references and explicit gaps.
It must not fabricate a causal edge solely because two records share an order reference.
No timestamp-only ordering or free-text search engine is needed.

Proposed manual query after a run:

```sh
python3 experiments/0002-http-correlation/query.py --run RUN_DIRECTORY --order-id order-1
```

This command is a planned interface, not an available tool.

## Acceptance cases

**[Proposal]** The runner executes five bounded cases:

| Case | Action | Required result |
|---|---|---|
| H01 | Submit one valid order | HTTP 200; checked response; six connected spans; both named logs linked to their actual spans |
| H02 | Submit the same order again as a new request | A second trace; order query returns both; no false parent edge between requests |
| H03 | Deliberately remove outbound trace context in a dedicated fixture run | Payments starts a different trace; order search finds the records but reports the missing cross-service causal link |
| H04 | Remove one required log from a separate derivative evidence copy | Checker reports incomplete evidence and exits nonzero; original run files remain unchanged |
| H05 | Submit an extra input field | HTTP 400; no payment HTTP request or Payments operation for that request |

H03 is an expected negative control, not a successful propagation case.
The suite passes only if H03 and H04 produce their specified gap results.
H05's no-call assertion uses independent Payments request counting, not absence of sampled spans alone.
No acceptance case depends on searching raw error-message strings.

## Proposed components and dependency handling

**[Proposal]** Use Plug.Cowboy for HTTP servers and OTP `:httpc` for the synchronous client.
Use the OpenTelemetry API/SDK and W3C propagator; do not implement a private tracing protocol.
Use the local OTP JSON encoder/decoder if supported by the recorded toolchain; verify its API before implementation.
The [planning capture](../../../../raw/requirements/2026-11-05-http-probe-plan.md) lists the selected official references.
Dependency compatibility is not yet tested. Resolve it once during implementation and retain `mix.lock` with exact versions.
The local exporter must implement the installed SDK's documented callback contract.
Do not add OTLP transport or a network collector merely to persist this bounded evidence.
After dependency setup, the fixture run must need no public network access.

## Planned files and command

**[Proposal]** Create only the files needed under this experiment directory:

- `mix.exs`, `mix.lock`, `config/`: umbrella, two release definitions and explicit probe configuration.
- `apps/orders_api/`: startup, router, HTTP client adapter and `priv/orders.beaml`.
- `apps/payments_api/`: startup, router and `priv/payments.beaml`.
- `apps/probe_support/`: small shared context, span export and structured Logger helpers.
- `run.py`: compile fixtures, build releases, start processes, exercise HTTP, flush, check and stop.
- `query.py`: file-based correlation and explicit gap reporting.
- `tests/`: correlation checks and derivative missing-evidence fixture.
- `results/<UTC-id>/`: commands, versions, hashes, generated source, records, check results and captured process output.

Do not edit EXPERIMENT 0001 source unless an actual blocking defect is found and recorded separately.
Exclude builds, dependency trees and release binaries from Git; retain text evidence and exact build inputs.

Proposed repeatable command:

```sh
python3 experiments/0002-http-correlation/run.py
```

The command is not implemented. It must use bounded readiness and HTTP timeouts, loopback-only listeners and guaranteed process cleanup.
Use available ports selected at startup and record them in nonsecret run metadata.
Record separate process identities and release application lists to verify the separation.
CLI actions and H01-H05 start/step/pass/fail events append to the project's `.beaml/actions.jsonl`.
Keep this action log distinct from application traces/logs and omit typed input text and input paths from action events.

## Implementation sequence after discussion

**[Proposal]** Complete the following steps in order:

1. Verify the toolchain and dependency/exporter APIs. Lock the compatible versions.
2. Add both fixtures and HTTP applications. Verify the response and separate processes.
3. Add real context propagation, six-span capture and two structured logs.
4. Add the order query and parent/log/source checks.
5. Add H01-H05, clean shutdown and separate immutable run evidence.
6. Run once, inspect actual output and record passed, failed or inconclusive against each criterion.

## Interpretation and later work

**[Proposal]** Passing establishes observed HTTP correlation for the recorded fixture and two independent processes.
It does not establish product superiority, automatic language instrumentation, production durability, arbitrary process propagation or full replay.
No latency budget or performance claim is attached to this functional probe.

After evaluating this evidence, propose one separate HTTP-boundary replay experiment.
That later experiment would record the observed response and substitute it during Orders execution with no live Payments call.
Payment timeout uncertainty, retries, committed DOMAIN EVENTS, Inventory and composed service replay remain later scopes.
Do not add them to 0002 while implementing correlation.

**[Unknown]** Owner acceptance of this exact plan remains pending. No implementation has started.
