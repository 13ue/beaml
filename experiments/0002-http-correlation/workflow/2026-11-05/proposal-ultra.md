# Ponytail ULTRA proposal: HTTP correlation EXPERIMENT

**[Proposal]** Implement the approved H01-H05 contract with two release processes and one fixed evidence checker.
Keep the EXPERIMENT 0001 compiler unchanged. Do not add replay or reconsider the product premise.

## Remove unnecessary machinery

- Use OTP `:json` and `:httpc`. Add no JSON or HTTP client dependency.
- Use one synchronous local SDK exporter. Add no Collector, OTLP exporter, batch processor or export queue.
- Use one bounded capture process per service for both observation files. Add no file-writer abstraction or storage backend interface.
- Use explicit fixture descriptors and one fixed six-span contract table. Add no source-map system or graph library.
- Put each business request directly in its router. Add no service, repository or HTTP-client wrapper layer.
- Use `:atomics` for the Payments request counter. It must not depend on the capture writer or tracing.
- Keep `run.py` and `query.py` separate. Do not add a workflow framework, query language, Python dependency or shared tool package.
- Reuse EXPERIMENT 0001's action-event shape locally. Do not refactor its compiler or runner to share a helper.
- Keep runtime settings explicit and fixed. Add no environment discovery or configurable backend selection.

These cuts preserve the required error boundaries, separation, evidence limits and negative controls.

## Inspected basis

**[Verified]** The planner inspected cached OTel SDK 1.7.0 and API 1.5.0 contracts; see [plan](plan.md).
The current exporter is `otel_exporter_traces`, with `init/1`, `export/3` over ETS, and `shutdown/1`.
Do not implement the older `export/4` callback.
The simple processor ends spans synchronously through `gen_statem:call`.
Its `force_flush/1` uses an asynchronous cast; a flush call alone cannot establish complete evidence.
Use the cached `OpenTelemetry.Tracer.with_span` macros and `otel_propagator_text_map` injection/extraction APIs.
Restore attached contexts with the returned detach token on every handled path.

**[Verified]** I read EXPERIMENT 0001's runner, fixture, runtime tests and compiler emission/action references.
The compiler emits `BeamlSpike`; its exact-interface guards already reject missing, extra and incorrectly typed fields.
The runner retains command outputs and hashes, and appends safe action records without raising on write failure.
Copy these small patterns; do not import an experiment runner as a library.

**[Unknown]** Cached APIs do not establish successful dependency resolution, Logger ordering or runtime integration.
The implementer must check those contracts while building the EXPERIMENT.

## Tests first

1. Create the checker callable with an incomplete result, then assert complete evidence succeeds. Retain this semantic failure.
2. Add one table-driven corruption test for missing logs, wrong log links, broken parents and duplicate span IDs.
3. Add wrong service/kind/descriptor/hash and malformed-JSONL cases to the same table.
4. Check two complete traces for the same order remain separate. Check a split trace cannot acquire an inferred parent.
5. Compile the two fixtures separately. Check exact-interface rejection and accepted transformations in separate BEAM invocations.
6. Add host checks for changed downstream order/status and fixed 400/502 errors before wiring success behavior.
7. Add a forced post-start runner failure. Check retained failure evidence and termination of both owned process groups.
8. Add capture overflow/write-failure checks. Business responses must survive; evidence must become incomplete.
9. Run H01-H05 against real release processes. Retain the first acceptance failure and every subsequent run.

Import errors and missing executables do not count as the intended failing assertions.
Synthetic checker fixtures test its logic; label them as synthetic, never as executed HTTP evidence.

## Minimal implementation

### Release and request boundary

Create the three umbrella applications from the plan. Give each release an explicit application list.
Orders depends on support and `:inets`; Payments depends on support. Neither depends on the sibling business application.
Compile each `.beaml` fixture into its own service's generated build input before release compilation.
Retain exact fixture, generated-source and compiled BEAM hashes in the run evidence.

Bind Cowboy to `{127, 0, 0, 1}` with port zero. Publish the actual port in fixed startup metadata.
Use unobserved health/control routes for readiness, process/application evidence, capture status, flush and Payments count.
Do not expose arbitrary module inspection or generic control execution.

Bound the request body and read deadline. Decode JSON with OTP and call the generated guards.
Convert only expected boundary failures into fixed safe responses; retain no exception text or request payload.
Orders checks the downstream status, exact response shape, matching order reference and `authorized` value.
Use explicit `:httpc` connection/request deadlines and no retries.
Increment Payments' counter at business-route entry, including invalid requests, before observation logic.

### Observation

Configure fixed service resources, always-on sampling and the W3C propagator. Disable unneeded resource detectors.
Start six spans with the exact plan names, kinds and parents. Use `with_span` around handled business operations.
Inject context inside `orders.payment_http`; extract before starting `payments.request`.
Orders starts a fresh root for each driver request. Never derive trace identity from the order reference.

Emit the two approved events through Elixir Logger while their internal BEAML spans are current.
The Logger handler accepts only those event names and copies an explicit safe-field allowlist.
The exporter normalizes real SDK span records into the same fixed evidence schema.
Retain actual OTel IDs, parent IDs, service/kind, outcomes and explicit fixture descriptors.

Use synchronous bounded writes through the capture process. Keep byte totals and sticky loss reasons there.
Reject writes exceeding each file's 1 MiB cap. Convert writer errors into loss state without raising into business handling.
Catch handler/exporter call failures at their boundaries; a dead capture process is incomplete evidence through control/readiness failure.
Do not acknowledge capture completeness after writer failure or timeout.

After each serial case, wait for the HTTP response, flush Logger/SDK and cross a capture-writer barrier.
Check sticky loss state and required record counts with deadlines. SDK force-flush alone is insufficient.
Health and control requests produce no business spans or approved application logs.

### Checker and runner

Read bounded JSONL files and validate records before graph construction.
Build a dictionary keyed by trace/span identity, reject duplicates, and check the fixed six-span contract.
Select exact order references, but establish edges only from actual trace/parent identities.
Verify log service, operation, trace/span identity and descriptor hashes against retained build inputs.
Keep split traces visible. Return structured gaps and nonzero CLI exit for incomplete evidence.
Reject capture-loss state independently of whether enough records appear to exist.

Run H01, H02 and H05 serially in one normal process pair. Snapshot Payments count immediately around H05.
Run H03 in a new process pair with one explicit outbound-context-drop setting.
Do not weaken the checker for H03: the runner expects its missing-causal-edge result.
After a flush, create H04's separate evidence copy and remove exactly one required log.
Check its CLI failure and original-file hashes. Do not mutate original captures or relabel negative results as complete.

Use Python 3.9 standard-library subprocess, urllib, json and hashlib facilities.
Use `start_new_session=True`, owned process handles, bounded TERM/KILL cleanup and an outer `finally`.
Retain command outputs, command lists, versions, process/application/module evidence, inputs, hashes and actual case results.
Create a unique UTC result directory for each invocation, including setup failures.
Append runner/query actions and H01-H05 start/step/pass/fail events; record no source text, input paths or typed values.

## Expected change scope and size

**[Proposal]** Estimates exclude generated source, dependency locks and retained run evidence.
File paths below are relative to `experiments/0002-http-correlation/`, except explicit repository paths.

| Scope | Files | Estimated lines |
|---|---|---:|
| Umbrella, app manifests and fixed config | `mix.exs`, three `apps/*/mix.exs`, `config/*.exs` | 100–150 |
| Two startups and routers | `apps/{orders_api,payments_api}/lib/*/{application,router}.ex` | 220–300 |
| Two exact String fixtures | `apps/*/priv/*.beaml` | 20–35 |
| Support, exporter, Logger handler, bounded capture | `apps/probe_support/lib/probe_support.ex`, `probe_support/{exporter,logger_handler,capture}.ex` | 220–300 |
| Runner and checker | `run.py`, `query.py` | 380–500 |
| Focused tests | `tests/test_query.py`, `tests/test_runner.py`, `tests/fixture_test.exs` | 170–240 |
| Current evidence documentation | `README.md`, repository `.gitignore`, three wiki files | 35–60 changed |

Target roughly 1,150–1,585 authored lines. This is an estimate, not a reason to omit a required check.
Keep the planner's four support files only where each separates an actual OTP callback or capture state owner.
Do not split router branches or runner steps into additional classes/modules.
Update `wiki/planning/research-and-development.md`, `wiki/index.md`, and append `wiki/log.md` after actual results exist.
Preserve raw captures and earlier results. Add no new wiki concept page.

## Verification and tradeoff

Run focused Python tests, generated-entry checks, Mix format/compile with warnings as errors, H01-H05, and wiki link checks.
Verify runtime application/module lists, separate PIDs, no distribution, loopback listeners and unchanged EXPERIMENT 0001 compiler hashes.
Check action-log records without copying source text or paths into events.
Record actual failures, setup limits and unexecuted checks explicitly.

Skipped implementation, package setup and test execution in this proposal phase.
Tradeoff: fixed fixture contracts minimize code; they establish this integration only, without production durability or general instrumentation claims.
