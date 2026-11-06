# Ponytail LITE proposal: EXPERIMENT 0002

**[Proposal]** Build the approved H01-H05 probe with two releases and one fixed evidence contract.
The [plan](plan.md) supplies the scope. The [specification snapshot](spec.md) supplies the accepted behavior.
Its pending-approval wording is historical; the root task reports approval.

Smaller option: combine the observation helper modules, but retain separate exporter and Logger callbacks for clarity.
No additional user decision is needed for this authorized implementation.

## Concrete implementation

1. Create the planned umbrella with `orders_api`, `payments_api` and `probe_support`.
   Define two releases with explicit application lists. Neither release starts the sibling business application.
   Build each fixture into only its own business application. Keep both generated module names as `BeamlSpike`.
   Do not change EXPERIMENT 0001 or introduce another compiler integration layer.
2. Keep three compiled functions: Orders `prepare/1`, Orders `finish/1`, and Payments `authorize/1`.
   Use exact String interfaces and ordinary generated maps. Keep the fixed response synthetic.
   Use the existing compiler command and generated boundary checks. Add host checks for matching order references and `authorized` status.
   A generated String check cannot establish either value.
3. Use one router and application module per service. Keep the Orders HTTP client in its router.
   Use Plug.Cowboy, native OTP JSON, and synchronous `:httpc` with explicit connection/request timeouts.
   Bound request-body reads. Reject malformed JSON and wrong interface shapes with fixed HTTP 400 responses.
   Convert transport errors and invalid downstream results to fixed HTTP 502 responses. Do not retry.
   Increment an independent Payments counter before processing every business request, regardless of trace state or request validity.
   Exclude health, count and flush controls from that counter and business spans.
4. Start real OTel spans around the six specified operations.
   Start Orders with a detached fresh root; do not accept driver context as its parent.
   Inject W3C TRACE CONTEXT inside `orders.payment_http`; extract it before `payments.request`.
   Attach/detach extracted context within `try/after`, and use `with_span` so handled failures also end spans.
   H03 uses a dedicated process pair with one explicit context-drop switch. All other behavior stays identical.
5. Emit `payment_request_prepared` inside `orders.prepare` and `payment_stub_returned` inside `payments.authorize`.
   Use actual Logger structured metadata and the current SDK span identity, rather than copying IDs into a separate fake logger.
   Capture only these approved events, their service, operation, checked synthetic reference and actual trace/span IDs.
   Read each fixture descriptor from an explicit manifest: relative source path, function and source hash.
   Retain generated-source and BEAM hashes separately. Do not present a fixture hash as the executable hash.
6. Use one serialized capture process per service for span and log files.
   Keep a separate byte count per file and a sticky loss state. Reject writes above 1 MiB.
   Expose loss and writer completion through an unobserved local control response.
   Catch observation failures at callback boundaries; mark loss without changing business responses.
   Avoid restarting the writer into an apparently healthy state that erases earlier loss.
7. Keep the checker independent from runtime generation.
   Read normalized JSONL, run metadata, retained source bytes and explicit service process evidence.
   Filter by exact order reference, then group by trace ID. Never group a causal graph by order reference alone.
   Check the exact six-span shape, unique identities, service/kind ownership, parent edges, ended outcomes and source descriptors.
   Verify each required log against its actual internal span and operation.
   Reject malformed records, duplicate span identities, unknown parents, altered descriptors/hashes and capture-loss flags.
   Return structured gap codes and nonzero CLI status whenever completeness is not established.
   For H03, report separate trace fragments and the missing cross-service edge without joining them by timestamp.
8. Extend the EXPERIMENT 0001 runner pattern locally, without refactoring its files.
   Retain the existing best-effort action-event shape. Events omit input paths, source bytes and typed text.
   Give runner/query CLI actions and each H01-H05 case start, step and pass/fail events.
   Use Python 3.9 standard-library modules: subprocess, urllib, json, hashlib, pathlib, unittest and time.
   Own foreground release process groups. Use bounded readiness, HTTP, flush, shutdown and forced-stop deadlines.
   Always write a terminal result and clean owned children in `finally`, including setup and post-start failures.
   Retain command outputs, tool versions, hashes, generated source, process IDs and started application/module lists.
   Never inspect the full environment or secret files.

## Installed API choices

**[Verified]** These facts come from the planner's cached-package inspection, not a new runtime check here.

→ OTP 27 exports `:json.encode/1` and `:json.decode/1`; encode output needs `IO.iodata_to_binary/1`.

→ SDK 1.7.0 requires API `~> 1.5.0`. Resolve once and retain the actual `mix.lock`.

→ Implement `otel_exporter_traces`: `init/1`, `export/3` over its ETS table, and `shutdown/1`.

→ Use the simple processor's synchronous `on_end` behavior. Its asynchronous `force_flush/1` cast does not prove completion.

→ Use `OpenTelemetry.Tracer.with_span`, `otel_propagator_text_map` injection/extraction, and `otel_ctx` attach/detach.

**[Proposal]** Flush SDK and Logger explicitly, then check a synchronous capture barrier and expected record counts.
Configure fixed service resources and disable unnecessary detectors. Do not export automatic environment metadata.
Dependency resolution and callback integration remain implementation checks; cached packages alone do not establish success.

## First meaningful failing test

**[Proposal]** Start with `tests/test_query.py` and a callable `query.check_run` entry point.
Use a temporary synthetic six-span graph with two span-linked logs and retained fixture files.
Give it a valid manifest so the baseline assertion can establish completeness.
Delete only `payment_stub_returned`; require `complete=false` and a structured missing-log gap identifying its trace and span.
Invoke the CLI on that derivative and require nonzero status.
Record an assertion failure after a minimally callable API exists. A missing import is not the useful failure.
Label these records synthetic checker fixtures; never retain them as a successful HTTP EXPERIMENT RUN.

Next add table-driven corruptions: wrong parent, duplicate identity, wrong service/kind, bad hash, malformed JSONL and unlinked log.
Test two successful traces sharing `order-1`; require two independent roots and no false edge.
Test H03-shaped fragments; require a causal gap rather than a fabricated connected trace.

Run generated-entry tests in separate Elixir invocations for Orders and Payments to avoid the `BeamlSpike` collision.
Check valid values, missing/extra fields, wrong TYPEs and invalid UTF-8. Check changed downstream order/status separately in the host adapter.
Add one writer-cap/failure check and one runner post-start failure check. Prove retained failure evidence and child cleanup.
Check action-event append failure does not replace the real CLI outcome.

## Acceptance execution

→ H01: check real HTTP 200, exact response, six connected SDK spans, two linked Logger events and three source descriptors.

→ H02: repeat the request; check two roots and exact-order query results without inter-request edges.

→ H05: compare independent Payments counts before and after extra-field rejection; require HTTP 400 and unchanged count.

→ Flush and stop the normal pair only after capture barriers and loss checks pass.

→ H03: start a dedicated context-drop pair; require different traces and the specific missing-edge gap.

→ H04: copy flushed evidence to a named derivative, remove one required log, and require the specific nonzero checker result.

Hash the original evidence before and after H04. Preserve it unchanged, and record the derivative's declared mutation.
Check actual process/application/module evidence, loopback listener configuration and disabled Erlang distribution for each pair.
Run focused Python and Elixir checks, Mix formatting/compilation, existing compiler checks and `python3 scripts/lint_wiki.py`.
Update README, register, existing index entry and append-only wiki log with the actual result and limitations.
Do not revise raw captures or convert planned outcomes into verified claims.

## Required scope and size

**[Proposal]** Keep the planner's explicit file scope, including the generated `mix.lock`.
The generated per-run evidence and service-local generated modules are additional outputs, not hand-written abstractions.

| Area | Estimated nonblank lines |
|---|---:|
| Mix/configuration and fixtures | 120–180 |
| Two applications and routers | 220–300 |
| Shared helper, exporter, Logger and capture | 260–360 |
| Runner and query checker | 450–600 |
| Focused tests | 220–300 |
| README/wiki updates | 50–80 |

These are planning estimates, not a size budget. Boundary validation and retained evidence cannot be removed to meet them.
The shared capture owner is justified by serialization, file caps and loss state. Exporter and Logger modules follow external callback contracts.
No client wrapper, middleware framework, universal event model, schema engine or generalized source-map system is needed.

## Limits

No installs, tests or runtime checks were performed in this proposal phase. No implementation files were changed.
Replay, production claims, performance work and a product-premise review remain excluded.
The main integration risk is SDK/Logger completion ordering; require observed record completion, not a flush call alone.
