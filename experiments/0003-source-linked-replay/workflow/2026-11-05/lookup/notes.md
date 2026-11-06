# Record live trace lookup RED (0003)

**[Requirement]** The owner replied “nice go” after compiler verification and the proposed lookup step. This authorized the lookup test. Follow the [acceptance contract](../spec.md), [plan](../plan.md) and [selected proposal](../notes.md). Keep the [compiler gate](../result.json) separate.

## Test decision

**[Proposal]** Reuse the production 0002 releases, loopback HTTP helper and public query with its supported arguments. Put the selected artifact and SOURCE ID in the run manifest. Attach the current revision as separate build evidence. Keep both build archives within the run. The lookup test asserts one original function summary. It also checks both exported spans carry the selected build and source. The test does not construct a summary.

Compile the original Payments source with the checked compiler and hash the actual deployed BEAM. Compile a second Payments source with the same declaration name and a different output. Run its function as a build control. Keep the revised build outside the live window. Remove only the original Payments source from a derivative of the run.

## Run

Run from the repository root with an offline Mix cache and permission to bind loopback TCP.

```sh
python3 -B experiments/0003-source-linked-replay/tests/trace_lookup_test.py
```

**[Verified]** [The test](../../../tests/trace_lookup_test.py) sent two sequential HTTP requests to separate, fresh releases. Both returned HTTP 200 and the expected authorized order. The [first baseline](../../../results/20261105T230852203515Z/baseline-call-1.stdout) found one trace. The [second baseline](../../../results/20261105T230852203515Z/baseline-call-2.stdout) found two traces, ten parent edges and four logs. Payments reported a request delta of two with no capture loss. Both release processes exited with code 0. The runtime BEAM hashes matched the archived builds.

**[Verified]** The original checked declaration range is `[91,193)`. The separately compiled [current revision](../../../results/20261105T230852203515Z/current-revision/manifest.json) has the same qualified function name and different source and BEAM hashes. The revised function returned `revised` in a separate VM. The control supplied no live spans.

| Assertion | Expected | Actual |
| --- | --- | --- |
| Two Payments spans | Selected artifact and source on both completed spans | Both source hashes match. Both artifact IDs are absent. |
| Query with current revision | 2/2 receipts, two successful outcomes, first receipt trace and original declaration | Exit 0 with complete correlation. The result has no function summary. |
| Query without original source | Exit 1 with `missing_source` and no summary | Exit 1 with generic `invalid_evidence` and no summary. |

**[Verified]** The test exited 1 at its behavior assertions. The 0002 observation has the short function name and source hash. The current query checks the causal graph and fixture integrity. It does not select a function by artifact and SOURCE ID or resolve the checked declaration. Its general file error handler reports the missing source as invalid evidence. Both lookup controls reached the public query.

See the [assertion output](red-output.log), [result](../../../results/20261105T230852203515Z/result.json), [commands](../../../results/20261105T230852203515Z/commands.json), [toolchain](../../../results/20261105T230852203515Z/toolchain.json), [input hashes](../../../results/20261105T230852203515Z/input-hashes.json), [output hashes](../../../results/20261105T230852203515Z/output-hashes.json) and [action events](action-events.jsonl). The [first RED run](../../../results/20261105T230743107625Z/result.json) records the two query failures before the direct span assertion was added.

## GREEN checks after review

**[Requirement]** After review of all three reached RED assertions, the owner replied “ok go! let's get it green”. This approves GREEN for the live lookup gate. Capture, transport observation and REPLAY RUN retain their separate RED review gates.

## Lookup GREEN

**[Verified]** The Payments host sets the release BEAM SHA-256 on the function span before it calls the generated function. The existing span descriptor supplies the function name and source hash. The query uses the existing causal graph check and adds the function summary when a run declares `function_lookup`. It checks the two ordered receipts, both span identities, the archived BEAM hash and the compiler's declaration reference. It resolves the byte range in the original source archive. [Payments router](../../../../0002-http-correlation/apps/payments_api/lib/payments_api/router.ex), [BEAM hash](../../../../0002-http-correlation/apps/probe_support/lib/probe_support.ex), [query](../../../../0002-http-correlation/query.py)

**[Verified]** The same command and test bytes passed after implementation. The formatted run had two HTTP 200 receipts, two correlated traces, ten edges, four logs and a Payments request delta of two. Both releases exited 0. The revised function ran in a separate VM and supplied no live observations.

| Assertion | RED | GREEN |
| --- | --- | --- |
| Live span artifact and SOURCE ID | Both artifact IDs absent | Both spans matched the archived artifact and source |
| Exact source with the current revision present | Complete trace graph, summary absent | 2/2 receipts, two successes, first receipt trace, original declaration at `[91,193)` |
| Original source removed from derivative | `invalid_evidence` | `missing_source`, exit 1, summary absent |
| Unchanged test exit | 1 | 0 |

See the [GREEN output](green-output.log), [run result](../../../results/20261105T232308384268Z/result.json), [commands](../../../results/20261105T232308384268Z/commands.json), [toolchain](../../../results/20261105T232308384268Z/toolchain.json), [input hashes](../../../results/20261105T232308384268Z/input-hashes.json), [output hashes](../../../results/20261105T232308384268Z/output-hashes.json) and [GREEN action events](green-action-events.jsonl). The [first GREEN run](../../../results/20261105T232238778158Z/result.json) passed before the formatter correction. The changed Elixir files passed the formatting check. The 0002 Python discovery ran eight tests and passed.

**[Verified]** The unchanged acceptance command used automatic approval for local loopback TCP. The BEAM hash uses the fixed release files. This gate covers the synthetic two-receipt lookup and its negative control. Capture, transport observation and REPLAY RUN are separate gates.

## Lookup repair RED

**[Verified]** The [repair RED](repair-red.md) reproduced the receipt order and window coverage findings. The original live test still passed. [Owner review is pending](repair-red-status.json).

## Lookup repair GREEN

**[Requirement]** The owner reviewed the repair RED and replied “Okay, lass uns weitermachen.” This approves GREEN for this repair gate only. The owner chose fresh Claude (Opus 5.5) subagents for this phase. GPT-6.1 Sol is not available in Claude Code.

**[Verified]** The query now compares the receipt order with the start order of the two Orders root spans. Both roots must have integer VM times and must not overlap. The query then requires `window` with UTC `start_utc` and `end_utc`. Both Orders roots must lie in that window. [Query receipt and window check](../../../../0002-http-correlation/query.py#L52)

**[Verified]** The span exporter now writes `start_time_unix_nano` and `end_time_unix_nano`. The VM converts its own monotonic times with `opentelemetry:timestamp_to_nano/1`. The raw monotonic times stay unchanged. [Span exporter](../../../../0002-http-correlation/apps/probe_support/lib/probe_support/exporter.ex#L22)

**[Verified]** The retained archive has no wall-clock span times. The default repair command therefore exits 1. The unchanged and outside-window cases report `missing_clock`. The swapped and missing-window cases report the expected gaps. This run is kept as a failed run. [Retained-archive run](../../../results/20261106T061716341141Z/result.json)

**[Verified]** The unchanged live test made a fresh archive and exited 0. Both calls returned HTTP 200. Both releases exited 0. The lookup returned 2/2 and the missing-source control returned `missing_source`. The repair test with `--source-run` on that archive exited 0. [Fresh live run](../../../results/20261106T061721787131Z/result.json), [fresh repair run](../../../results/20261106T061748414219Z/result.json), [output](green-repair-output.log)

| Case | RED (retained archive) | GREEN (fresh archive) |
| --- | --- | --- |
| Unchanged copy | Exit 0, 2/2, first trace | Exit 0, 2/2, first trace |
| Swap the receipt trace IDs | Exit 0, 2/2, wrong first trace | Exit 1, `receipt_coverage`, no summary |
| Remove the window | Exit 0, 2/2 | Exit 1, `missing_window`, no summary |
| Window in 2000 | Exit 0, 2/2 | Exit 1, `outside_window`, no summary |
| Repair test exit | 1 | 0 |

**[Verified]** Both test files kept their SHA-256 values. The eight 0002 Python unit tests passed. The changed Elixir file passed the format check. Manifests without `function_lookup` skip the new checks. The live baseline queries use that path.

**[Inference]** The first Orders root started 0.4 ms after the window start. The margin is small but follows from the order of events in the runner. A wall-clock step in the OS during a run can move the converted times.

**[Unknown]** No independent TEST of this repair has run. The malformed `service` parser crash, CAPTURE, transport and REPLAY RUN stay out of scope.

**[Proposal]** Run an independent TEST with `--source-run` on a fresh archive. Decide if the default `--source-run` should point to a fresh archive.

## Lookup repair TEST, review and owner decision

**[Verified]** A fresh Claude Opus 5.5 subagent ran the independent TEST. The fresh live test exited 0. The repair test with `--source-run` on that archive exited 0 and passed 4/4 cases. Both test files kept their SHA-256 values. The eight 0002 unit tests and four legacy 0002 manifests passed. [TEST record](repair-test-result.json), [fresh live run](../../../results/20261106T061910678622Z/result.json), [fresh repair run](../../../results/20261106T061936773705Z/result.json)

**[Verified]** The default repair command on the retained archive exited 1 with `missing_clock`. The TEST records this as a known deviation, not as a pass. [Retained-archive run](../../../results/20261106T061940807027Z/result.json)

**[Verified]** The independent review gave the verdict PASS. No repair is necessary. Findings 1 and 2 of the [lookup review](review.md) are closed for fresh archives. [Repair review](repair-review.md)

**[Requirement]** On 2026-11-06 the owner chose option B in conversation: “Ja, dann lass uns doch mal hier den Weg B gehen für die Experimente.” Always run the repair test with `--source-run <fresh live result dir>`. Keep the test file and its default unchanged. The retained archive has no wall-clock span times. It stays as evidence that the query rejects a recording without a clock with `missing_clock`. The archive and the default are EXPERIMENT scaffolding, not a BEAML language feature.

Run from the repository root. Run the live test first. Then give its new result directory to the repair test.

```sh
python3 -B experiments/0003-source-linked-replay/tests/trace_lookup_test.py
python3 -B experiments/0003-source-linked-replay/tests/trace_lookup_repair_test.py \
  --source-run experiments/0003-source-linked-replay/results/<fresh live result dir>
```

**[Unknown]** The acceptance test has only one disjoint window, in 2000. The review checked partial windows only in scratch derivatives. These cases are not retained. The 0002 `run.py` input hashes change for new runs, because `query.py` and `exporter.ex` changed. Retained 0002 results keep their old hashes. An OS clock step during a run was not tested.

**[Proposal]** Add the partial-window cases to a retained test only if the owner asks for them. The malformed `service` parser crash stays open as review finding 3.
