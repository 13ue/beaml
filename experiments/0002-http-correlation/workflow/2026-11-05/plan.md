# EXPERIMENT 0002 implementation ledger

**[Proposal]** One bounded step: implement the accepted two-process HTTP correlation EXPERIMENT with H01-H05.

Root task reports owner approval. Existing pending-approval prose is historical. Do not reopen the product premise.

## Scope and exact files

- `.gitignore`: Ignore only EXPERIMENT 0002 dependencies, builds and release binaries.
- `experiments/0002-http-correlation/README.md`: Record accepted scope, commands, actual results and limits.
- `experiments/0002-http-correlation/mix.exs`: Umbrella and explicit orders/payments release application lists.
- `experiments/0002-http-correlation/mix.lock`: Exact compatible dependency resolution, retained after setup.
- `experiments/0002-http-correlation/config/config.exs`: Always-on sampler, W3C propagator and local simple span processor.
- `experiments/0002-http-correlation/config/runtime.exs`: Explicit nonsecret probe settings; no environment enumeration.
- `experiments/0002-http-correlation/apps/orders_api/mix.exs`: Only own service and shared support dependencies; include inets.
- `experiments/0002-http-correlation/apps/orders_api/lib/orders_api/application.ex`: Loopback server startup and own generated BEAML module.
- `experiments/0002-http-correlation/apps/orders_api/lib/orders_api/router.ex`: Orders boundary, prepare/finish spans, synchronous :httpc call and safe errors.
- `experiments/0002-http-correlation/apps/orders_api/priv/orders.beaml`: Exact String-only request/response interfaces; prepare and finish.
- `experiments/0002-http-correlation/apps/payments_api/mix.exs`: Only own service and shared support dependencies.
- `experiments/0002-http-correlation/apps/payments_api/lib/payments_api/application.ex`: Loopback server startup and independent request counter.
- `experiments/0002-http-correlation/apps/payments_api/lib/payments_api/router.ex`: Payments boundary, authorize span, fixed response and count/health/flush control.
- `experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml`: Exact String-only payment interfaces; authorize fixed response.
- `experiments/0002-http-correlation/apps/probe_support/mix.exs`: Plug.Cowboy, OTel API/SDK dependencies; no business application dependency.
- `experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex`: Shared observation/context helpers, safe JSON boundary and fixed descriptors.
- `experiments/0002-http-correlation/apps/probe_support/lib/probe_support/exporter.ex`: Installed SDK exporter callback; normalized span JSONL.
- `experiments/0002-http-correlation/apps/probe_support/lib/probe_support/logger_handler.ex`: Logger handler for only two approved structured application events.
- `experiments/0002-http-correlation/apps/probe_support/lib/probe_support/capture.ex`: Serialized append-only bounded observation writer and explicit capture-loss state.
- `experiments/0002-http-correlation/run.py`: Compile fixtures, build/start releases, H01-H05, immutable evidence and guaranteed cleanup.
- `experiments/0002-http-correlation/query.py`: Exact order query, independently checked graph/log/source links, structured gaps and nonzero incomplete result.
- `experiments/0002-http-correlation/tests/test_query.py`: Synthetic positive and corrupted-evidence checks; no stored hand-built trace masquerades as a run.
- `experiments/0002-http-correlation/tests/test_runner.py`: Focused process cleanup/failure and action-event checks.
- `experiments/0002-http-correlation/tests/fixture_test.exs`: Generated exact-entry guards and semantic matching/status boundary checks.
- `wiki/planning/research-and-development.md`: Update EXPERIMENT 0002 state and link actual result.
- `wiki/index.md`: Update existing EXPERIMENT 0002 entry; no new concept page.
- `wiki/log.md`: Append observed evidence and limits; preserve history.

Generated per-run files remain under `results/<UTC-id>/` and derivatives below that new run. Retain failed runs.

Retain `result.json`, command outputs, versions, process/application evidence, fixture/generated source and BEAM hashes, observation JSONL and case checks.

Only the solver may create generated sources inside each service build input. Exclude dependency/build/release trees from Git.

## Callers, fixtures and configuration

- run.py calls the unchanged EXPERIMENT 0001 compiler with one fixture path per invocation; compiler emits Elixir to stdout and logs compile events itself.
- run.py places generated source in each own service build input, retaining byte-identical copies and hashes in the new result directory.
- Orders router calls BeamlSpike.prepare/1 and BeamlSpike.finish/1. Payments router calls its separate BeamlSpike.authorize/1. Shared support cannot call business functions.
- Orders uses :httpc only over loopback to Payments. Client carrier injection occurs inside orders.payment_http; Payments extracts before payments.request.
- run.py invokes query.py for exact order query and H04 process exit checks. tests import query API. Query also remains a logged standalone CLI.
- Release definitions include only own business app and shared runtime dependencies; use explicit app selection and verify actual started apps, not only configuration.
- Both server trees expose unobserved local health/flush controls. Payments count covers every business HTTP request independently of tracing.

## First meaningful failing tests

- **Q01** — `experiments/0002-http-correlation/tests/test_query.py`: A complete synthetic six-span graph and two actual span-linked logs yields complete=true. Deleting or mismatching a required log yields structured gaps and nonzero CLI exit. First failure: Missing query implementation; require the semantic assertion to fail after import/API exists, rather than treating ImportError as meaningful evidence.
- **Q02** — `experiments/0002-http-correlation/tests/test_query.py`: Two traces sharing order-1 remain separate. A broken outbound context creates no inferred cross-service parent. Duplicate IDs, missing parents, wrong kind/service/descriptor/hash and malformed JSONL are incomplete. First failure: Checker cannot yet establish or reject these relationships.
- **B01** — `experiments/0002-http-correlation/tests/fixture_test.exs`: Compiled prepare/authorize/finish accept their exact interfaces. Missing/extra fields, wrong TYPEs and invalid UTF-8 are rejected. Host semantic checks reject a changed order reference or status. First failure: Generated modules and host checks do not yet exist; retain the first real assertion failures after wiring fixtures.
- **R01** — `experiments/0002-http-correlation/tests/test_runner.py`: A forced post-start failure retains a fail result and stops every owned child; event logging failures never change the business/CLI outcome. First failure: Runner has no bounded process lifecycle or fail evidence yet.
- **H01-H05** — `experiments/0002-http-correlation/run.py`: Execute the accepted five real two-process HTTP cases. Negative controls succeed only when the required structured gap is detected. First failure: Record the first actual acceptance failure in a fresh result directory; never overwrite it.

## Minimal implementation sequence

1. Lock cached compatible dependencies and verify installed SDK contracts. Use native OTP JSON. Retain setup commands. Do not add OTLP or JSON dependencies.
2. Write minimal checker assertions first; create query API, then retain actual assertion failures. Add exact BEAML fixtures and generated-entry checks.
3. Implement the two release application trees and bounded HTTP boundaries. Generate each BeamlSpike module into only its own business application before release build.
4. Add real OTel spans, W3C propagation and structured Logger capture. Use fixed descriptors, synchronous export and capture-loss reporting.
5. Implement query graph/log/source checks and the bounded runner. Execute H01/H02/H05 in a normal process pair, then H03 in a separate context-drop process pair.
6. Create H04 as a separate derivative copy after flush. Remove exactly one required log. Check nonzero exit and verify original evidence hashes remain unchanged.
7. Run focused Python and generated-entry checks, full H01-H05, release separation assertions and wiki link checks. Record all commands, failures, versions and hashes.
8. Update README, register, index wording and append wiki log. Report the actual result and limits without production or replay claims.

## Done criteria

- H01 returns checked HTTP 200 and exactly six spans with correct names, kinds, service ownership, distinct IDs, one trace, exact parents and ended outcomes.
- H01 has both named Logger records linked to the actual internal spans. Three internal spans have fixture path, function and source artifact hash verified against retained inputs.
- H02 makes a second independent root trace; exact order query returns both and no false inter-request edges.
- H03 omits only outbound trace context in a dedicated run. Payments has a different trace; query reports a missing causal edge with structured gap evidence.
- H04 derivative lacks one required log; checker exits nonzero with a structured gap. Original files and hashes stay unchanged.
- H05 returns fixed HTTP 400. Independent Payments request count is unchanged; absence of spans alone is insufficient.
- Malformed JSON, missing/extra fields and wrong TYPEs return fixed 400; changed downstream order/status, transport errors and unexpected downstream responses return fixed 502; no retries.
- Two OS processes execute separate releases. Runtime application/module evidence proves no sibling business app or module; distribution is not started; listeners bind only loopback.
- Bounded readiness, request, flush and process-stop deadlines exist. All handled spans end. Health/control endpoints create no business observation spans.
- Each observation file is capped at 1 MiB; write/overflow loss is explicit and fails evidence completeness without failing business handling. Logger and SDK are explicitly flushed before checking/stopping.
- Every run has a new UTC directory retaining commands, versions, input/output hashes, generated sources, observations, process identities/application lists, checks and stdout/stderr. Failed runs remain.
- Compiler, runner and query CLI actions plus H01-H05 start/step/pass/fail events append to .beaml/actions.jsonl. Events contain no source text, typed text or input paths.
- Focused checks and python3 scripts/lint_wiki.py pass. EXPERIMENT 0001 compiler source remains unchanged.

## Local nonsecret availability

**[Verified]** Read-only inspection on 2026-11-05 found OTP 27, Elixir/Mix 1.18.1, Python 3.9.6 and Rust/Cargo 1.94.0.

**[Verified]** Native OTP `:json.encode/1` and `:json.decode/1` exports exist. No JSON dependency is needed.

**[Verified]** Cached tarballs include Plug.Cowboy 2.8.1, Cowboy 2.15.0, OTel SDK 1.7.0 and API 1.5.0.

**[Verified]** Version-scoped Hex 2.4.1 and rebar3 files exist for Elixir 1.18.1-otp-27. No install was attempted.

- **[Verified]** SDK 1.7.0 requires API ~> 1.5.0.
- **[Verified]** Current exporter behavior is otel_exporter_traces with init/1, export/3 over an ETS table, shutdown/1; older export/4 is legacy.
- **[Verified]** Simple processor on_end uses synchronous gen_statem:call; force_flush/1 uses an asynchronous cast. Flush alone is not proof of completion.
- **[Verified]** API provides OpenTelemetry.Tracer.with_span macros, otel_propagator_text_map inject/extract, and otel_ctx attach/detach semantics.

**[Unknown]** Dependency resolution, full transitive cache coverage and runtime integration remain untested.

## Risks and resolutions

- Both generated modules use BeamlSpike. Build/load each only inside its own release and record separate process/module evidence; never run both generated fixtures in one VM.
- Capture races or asynchronous flush can hide missing records. Prefer simple synchronous span export, Logger.flush plus writer barrier, and bounded explicit completion checks.
- Automatic OTel resource detectors may inspect environment metadata. Configure explicit fixed service resources and disable unneeded detectors; do not enumerate environment variables or export payloads.
- Cap or writer failure must not crash business requests. Keep a separate in-process loss state exposed by unobserved control/status and make runner evidence incomplete.
- Exact order reference is a search key only. Parent IDs, trace IDs, service/kind and source descriptors establish edges; timestamps and order equality cannot establish them.
- Port selection has a reservation race. Bind port zero and publish actual port or retry a bounded failed start; retain only owned PID handles and clean process groups.
- Python is 3.9.6. Avoid Python 3.10-only annotation unions and newer subprocess conveniences.
- Existing wiki text says approval pending. Update current state with the user authorization reported in the root task, preserving original raw captures.
- New dependency setup may need public package access despite cached tarballs. Report an actual setup failure, retain it, and do not silently substitute fake OTel or a different architecture.

## Exclusions

- Replay and replay proposals in implementation
- Inventory, database, real payments, broker, Collector, OTLP, dashboard
- Retries, performance claims, production durability, generalized instrumentation/source maps
- Compiler syntax/semantics changes and EXPERIMENT 0001 refactors
- Secrets, environment scans, arbitrary payload export, automatic commits/pushes

## Limits and blockers

No known hard blocker. Dependency/API integration remains a solver check.

Planner wrote only this ledger and `plan.json`. No package installs, test execution or implementation edits occurred.

Skipped runtime verification. Cached packages do not prove a working release.
