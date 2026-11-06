# BAML debugging and replay: selected research capture

Date and access: 2026-11-06. Publisher: BoundaryML. Researcher: fresh worker for the BEAML knowledge base.
Coverage: selected paraphrases, short identifiers and researcher notes. Not a full copy of any upstream page or file.
Question: how does BAML support the debugging and replay of a recorded call?
Limits: no BAML package installed or run. No playground or Boundary Studio session opened. Code read, not executed.

License: the BAML repository root is Apache License 2.0 (see [license note](../../../wiki/sources/baml-license.md)).
Documentation pages keep their own terms. No upstream implementation is copied into BEAML.

## Commits

- Default branch: `canary`. Head `6a3eb3dfb2908bac750ad0e4cd9d6a086a72f211`, committer date 2026-11-06T03:47:16Z.
- Existing pin: `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`, committer date 2026-11-05T05:58:34Z.
- The first three files below have the same Git blob at both commits. The test file was read at `canary` only.

| Path at both commits | Git blob | Local SHA-256 of fetched bytes |
|---|---|---|
| `skills/baml-core/SKILL.md` | `e2dd238bbf94f91e3d6704979ed3d4fb4a21b502` | `c41d36faacb330c54a73fef565bb6e1972bd208a1fe0f66e0dd1420b040477bb` |
| `baml_language/crates/baml_query_btel/src/catalog.rs` | `4e69e102c6ce6f404976d2f66ec7f6f2f0b47a4f` | `e7065bffa84a8127a17506d6aa86aa9ee848e7bcff802ef37028bea3edcee2df` |
| `baml_language/crates/btel_bcs/README.md` | `5756585d3038e3228064a9fb13686a904b6d72c1` | `7dc45bd87ec98d5f135053524be1f2b7eaecefaf7a2709b7b12f2ae3b9dfd621` |
| `baml_language/crates/baml_query_btel/tests/network.rs` (canary) | not recorded | `490677a6593bf348a11cbe7cd39dd178ffb84252c2e06410f2f2bfb125460ad9` |

## Established documentation track (BAML v0 pages)

Each page now carries a notice: it documents BAML v0, the legacy DSL. BAML v1 is a separate language in public beta.

- https://docs.boundaryml.com/guide/boundary-cloud/observability/tracking-usage — Boundary Studio.
  `@trace` / `traceSync` / `traceAsync` show function input and output in the dashboard. Custom tags per call.
  Logs reach the dashboard only with `BOUNDARY_API_KEY`. No re-run, replay or "open in playground" text found.
- https://docs.boundaryml.com/guide/baml-advanced/collector-track-tokens — Collector.
  FunctionLog: `id`, `function_name`, `log_type`, `timing`, `usage`, `calls`, `raw_llm_response`, `tags`.
  LLMCall: `http_request`, `http_response` (null for streaming), `selected`. LLMStreamCall: `chunks` ("API coming soon").
  HTTP bodies give `text()` and `json()`. No replay or re-parse text found.
- https://docs.boundaryml.com/guide/baml-advanced/modular-api — modular API.
  `b.request` builds the HTTP request; `b.parse.<Fn>(text)` and `b.parse_stream.<Fn>(text)` parse a reply string.
  Examples extract the message content from the provider envelope first, then call `b.parse`.
  The batch example parses saved batch output. The page does not state whether `b.parse` performs I/O.
- https://docs.boundaryml.com/ref/baml/test and https://docs.boundaryml.com/guide/baml-basics/testing-functions — test blocks.
  Components: `functions`, `args`, `type_builder`, `@@check`, `@@assert`. Run from the playground.
  No mocked or recorded model response is documented.
- https://docs.boundaryml.com/ref/baml-cli/test — `baml-cli test`.
  Include/exclude filters, `--list`, `--parallel` (default 10), exit codes 0–4.
  Examples set provider API keys. No mock, cache, record or replay flag is documented.

## Code track (`baml_language`, BAML v1) at the commits above

- `skills/baml-core/SKILL.md`, sections "Running AI functions", "Debugging a recorded call" and "Tests".
  `F@spec(args)` is an unrun `ai.FunctionSpec<Out>`: `.call`, `.build_request` (no I/O), `.parse(reply)`, `.prompt()`.
  `on_event` receives `ModelCall` with usage, timing and the raw HTTP request and response.
  Replay, caching and metering are user code: a class that implements `ai.Runner`, or a fake `ai.Client`.
  Runs record calls by default. AI functions record inputs, output, error and type arguments.
  `baml query` runs SQL over the recordings. The documented debugging flow has three queries:
  find the failed span, render its type arguments as BAML code, read the raw HTTP response of the child network span.
  The user then writes a test that calls `F@parse` on the recorded reply text. The test does not call the model.
  A test with a live client makes a real request.
- `baml_query_btel/src/catalog.rs`, relation `spans`.
  Columns include `span_id`, `span_type` (function, future, network_span), `span_name`, `parent_span_id`, `status`,
  start/end time, `duration`, `type_args`, `input_args`, `output_value`, `network_event_values`, `error_value`, usage.
  A network span stores the request (`method`, `url`, `headers`, `body`) in `input_args`.
  Its events hold `connection` (status, headers) and `data` (whole body or one SSE event). `data` is null when bodies are not recorded.
  Relation `processes` has `baml_source_code_content_id`: a CAS id of the BAML sources that ran, null when not recorded.
- `baml_query_btel/tests/network.rs`, test `network_spans_are_spans_with_their_request_and_events`.
  The fixture stores the response body as a JSON string value in CAS.
- `btel_bcs/README.md`, "Automatic function observation" and "Transport".
  `BAML_TELEMETRY` levels `low`, `medium` (default), `high`, `off`. At `medium`, auto LLM functions produce spans with default captures.
  `baml run`, `baml test` and native SDKs record to the cloud with credentials, else locally. Its "replay" means metadata re-delivery, not call replay.

## Code search on the default branch

`gh search code` (default branch index only) on 2026-11-06:
- `cassette`, `ReplayHttp`, `record_replay`: no hits.
- `replay`: telemetry metadata re-delivery (`btel_bcs`), REPL session source (`bex_vm/src/compile_artifact.rs`), playground UI and website animation, a design note, the skill above.
- Open pull request #3336, "feat: add record-replay system for playground HTTP calls". Not merged.
  Base `canary`, head `01fc300611e09dcd129ce3e1eefb26fba3a7fb81`, created 2026-04-07, updated 2026-04-08.
  Its description: playground records HTTP responses; a user pins one; matching requests (SHA-256 of method, URL, sorted headers, body) get the cached response.
  Only the pull request description was read, not its code.

## Researcher notes

- Two tracks: v0 docs (generated client, Collector, Studio) and v1 code (`baml query`, `F@parse`). Do not merge them.
- No built-in replay runner was found in either track. Offline re-parse of a stored reply exists in both.
- Search index coverage and recording-body policy defaults are not established.
