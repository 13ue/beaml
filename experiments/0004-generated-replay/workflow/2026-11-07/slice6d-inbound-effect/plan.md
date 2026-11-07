# Plan: slice 6d, inbound EFFECT: a declared entry point

**[Proposal]** PLAN phase, 2026-11-07. Task records only. No production file, no test, no commit, no `run.py` run.
Decision: DL-128 (option b) in [the decision log](../../../../../wiki/planning/decision-log.md). Also read: DL-092, DL-101, DL-105, DL-106, DL-108, DL-117, DL-119, DL-120, DL-126, DL-127; D018 in [decisions to be made](../../../../../wiki/planning/decisions-to-be-made.md) (inward view); the step 12 GREEN notes ([slice6b-effect-reach/notes.md](../slice6b-effect-reach/notes.md), D6B-114, D6B-127); the record contract ([slice6b-records-v2/spec.md](../slice6b-records-v2/spec.md)); the `effect_declaration` rule in `integrations/zed-beaml/grammar.js`; `experiments/0001-syntax-to-beam/src/main.rs` at HEAD fccb7941 (read from `git show HEAD:`; another worker edits the working copy); the design principle in [vertical-integration.md](../../../../../wiki/concepts/vertical-integration.md).
Design decisions that DL-128 does not settle: [decisions.md](decisions.md) (D6B-128 to D6B-142, OWNER questions Q6D-1 to Q6D-3). Machine form: [plan.json](plan.json).
By: Opus (PLAN, slice6d-inbound-effect) for every proposal in this file (DL-107).

Proposed terms (D6B-141, glossary entry in the docs phase before GREEN prose uses them): ENTRY LINE (the declaration), ENTRY RECORD (one stored line of one inbound event). UI EVENT is in the glossary already.

## Facts the slice builds on (observed at HEAD fccb7941)

- **[Verified]** The parser takes top-level words in `program()`. An unknown word gives `expected type, enum, effect, migrate, retire or fn` (main.rs line 748). `slice5_syntax_test.py` F02 asserts this text; `cli.rs` line 208 asserts its absence.
- **[Verified]** `validate` allows one outbound EFFECT (`slice 1 supports one effect`). `flow(effect)` is the one pipe that `Replay.run/3` replays. The EFFECT failure TYPE must have `reason: String`.
- **[Verified]** The outbound decode `__beaml_decode_<type>(bytes)` JSON-decodes bytes, then applies the literal map, `__beaml_from_T` for constructor fields (DL-101) and the shape check. It is emitted inside `emit_effect` for the EFFECT output TYPE only.
- **[Verified]** `Replay.record/3` writes `ProbeSupport.Capture.write("responses", %{version: 2, ...})`. `select/2` needs exactly one record per `trace_id` in the list it gets. `body/1` and `digest/3` check and re-encode a version 2 projection.
- **[Verified]** `ProbeSupport.Capture.write(kind, record)` appends to `<kind>.jsonl` for any kind (0002 `capture.ex`).
- **[Verified]** `ProbeSupport.span/5` reads `order["order_id"]`; `nil["order_id"]` is `nil`. `ProbeSupport.event/2` writes `"none"` with no open span (D6B-127).
- **[Verified]** The span name is `<service>.<name>`; the service is the source file stem.
- **[Observed]** Probe with a HEAD build in the scratch directory: the fixture types below (record constructor `Amount`, enum `Channel { Web = "web"  Unknown(String) }`, `PlaceOrder` with both as fields, `place` as the EFFECT flow) compile today without the ENTRY LINE (`--stored stored/empty.jsonl`). The pure fixture compiles without `--stored`.

## Syntax (Q6D-1, default A)

- **A (default).** `on ui "place" PlaceOrder -> place`. Keyword `on`, transport `ui`, the UI EVENT name as a string, the input TYPE, the target fn.
- **B.** `effect ui.place PlaceOrder -> Payment ! PaymentError = ui.event("place") |> place`.
- **C.** `entry ui.place PlaceOrder -> place`.
- Reason for A: it is the DL-128 sketch. One line holds shape and policy (DL-126). The output and the failure TYPE come from the fn, so no second place can drift. Details: [decisions.md](decisions.md#q6d-1--migrate--the-form-of-the-entry-line).

## Change (defaults, each in decisions.md)

1. **Parse** (D6B-128). `on <transport> "<event>" <Type> -> <fn>` becomes an `Entry` in `Program.entries`, apart from `effects`. The "one effect" check does not count it.
2. **Checks** (D6B-129, D6B-130). One ENTRY LINE per source. Transport `ui` only. Event `[a-z][a-z0-9_]*`. The target is a lower-case fn with one parameter of the declared TYPE, never a constructor (DL-120). With an outbound EFFECT the target must be its flow. The input TYPE is a plain record: no own constructor, no MIGRATE CHAIN. Its fields may hold constructor TYPES and enums. An ENTRY LINE alone needs no `--stored` (D6B-139).
3. **Generated entry function** (D6B-131, Q6D-2). `def ui_place(params)` in `BeamlSpike` (`ui_<event>`, like `payments_authorize`). The host calls `Orders.ui_place(params)` from `handle_event("place", params, socket)`. It never raises for outside data. It returns `{:ok, result}` or `{:error, failure}`; a fn without `!` gives `{:ok, result}` too.
4. **Decode** (D6B-132). The DL-101 decode of the input TYPE, the same code path as the outbound decode, run on `:json.encode(params)`. Constructors run; a keep-value variant (`Unknown`) takes another String. Reject reasons: `decode` (not a map, a non-String top-level key, a value that JSON cannot encode, a wrong shape) and `constructor`. The reject is `{:error, %BeamlSpike.Rejected{reason: r}}` (Q6D-3).
5. **Root span** (D6B-133). `ProbeSupport.span("<service>.ui.<event>", :server, nil, nil, fn -> ... end)`. The decode, the record write and the fn call run inside it. So the prepared event and the EFFECT span have the root as parent (closes the D6B-127 follow-up for a declared entry). A reject raises inside the span (outcome `error`, attribute `reason`) and returns outside it.
6. **Reach** (D6B-134, DL-119). The entry is a root, not a pipe step. The target fn has no span of its own. Its steps follow S unchanged. A pure target gives one span, the root.
7. **ENTRY RECORD** (D6B-135). Before the decode, inside the root span: `ProbeSupport.Capture.write("entries", %{version: 2, trace_id, server_span_id, artifact_id, operation: "ui.place", attempt: 1, value, redacted: [], unknown_keys, value_sha256, type})`. `value` is the DL-105 projection of the params under the declared keys of the input TYPE (nested by DL-099, D6B-49); `unknown_keys` the other names, dotted. Never the raw params. Also for a reject. Only in a source with an outbound EFFECT (D6B-136).
8. **REPLAY RUN from the entry** (D6B-137). `Replay.entry(record, records)`: `:operation_mismatch` for another operation; the digest check through `body/1` (`:body_digest_mismatch`); the entry decode on the re-encoded `value` (a reject gives the same `Rejected`); then `run(decoded, record["trace_id"], records)`.
9. **Names** (D6B-138). A fn named `ui_<event>`, or a TYPE named `Rejected` next to an ENTRY LINE, is a compile error.
10. **fmt** (D6B-140). `fmt` keeps the ENTRY LINE bytes and does not align it with clauses.
11. **Grammar** (D6B-142). Rule `entry_declaration` in `grammar.js`, `"on"` in `highlights.scm`, target `@function`; `tree-sitter generate`; corpus and highlight cases.

## Fixtures

- `slice6/inbound/orders.beaml`: the probe source above plus `on ui "place" PlaceOrder -> place`; `fn to_order PlaceOrder { order_id } -> Order = Order { order_id: order_id }`; `fn place p: PlaceOrder -> Payment ! PaymentError = p |> to_order |> payments.authorize`.
- `slice6/inbound/echo.beaml`: the same types without the outbound EFFECT, `fn echo p: PlaceOrder -> PlaceOrder = p`, `on ui "echo" PlaceOrder -> echo`. It makes the decoded value visible.
- Params used below: `good = %{"order_id" => "order-1", "amount" => %{"value" => "12.50", "currency" => "EUR"}, "channel" => "web"}`.

## First failing test: `tests/slice6_inbound_test.py`

Harness: the step 12 runtime harness (`slice6_effect_reach_test.py`: span stack stub, TCP payments stub, `elixirc --warnings-as-errors`). Changes: the span stub also logs `kind`; `Capture.write/2` appends `{kind, record}`. Expected values come from this plan and DL-128, never from the new compiler.

- **N1 (first RED).** `orders.beaml` compiles (exit 0) and the output has `def ui_place(`. Today: exit 1 with the fallback text. The new declaration is the behaviour, so this parse reject is a genuine RED.
- **N2 (decode through the constructor).** `BeamlSpike.ui_echo(good) == {:ok, %{"order_id" => "order-1", "amount" => %BeamlSpike.Amount{value: "12.50", currency: "EUR"}, "channel" => {"Channel", "Web", []}}}`.
- **N3 (`Unknown` applies).** `"channel" => "app"` gives `{"Channel", "Unknown", ["app"]}` in the result.
- **N4 (typed reject, never a raise).** Each gives `{:error, %BeamlSpike.Rejected{reason: R}}`: currency `""` gives `"constructor"`; no `order_id`, `nil`, a list, `%{order_id: "order-1", ...}` (atom keys) and `"order_id" => {:a}` give `"decode"`.
- **N5 (root span).** `ui_place(good)` returns `{:ok, %{"order_id" => "order-1", "status" => "authorized"}}`. The log is exactly `[{:span, "orders.ui.place", :server, nil, nil}, {:event, "payment_request_prepared", "to_order", "orders.ui.place"}, {:span, "orders.payments.authorize", :client, "order-1", "orders.ui.place"}]`. `ui_echo(good)` logs only the root span.
- **N6 (reject inside the root span).** `ui_place(nil)` logs the root span and no child, and sets the attribute `reason` to `"decode"`.
- **N7 (domain failure passes).** With `:payments_port` on a closed port: `ui_place(good) == {:error, %BeamlSpike.PaymentError{reason: "transport"}}`.
- **N8 (ENTRY RECORD shape).** After `ui_place(Map.put(good, "_csrf_token", "t"))`: one `"entries"` record with exactly the keys of item 7, `operation: "ui.place"`, `value` equal to `good` (no token value), `unknown_keys: ["_csrf_token"]`, `value_sha256` equal to the digest that the test computes by the D6B-58 rule. One `"responses"` record as before. `ui_echo` writes no record.
- **N9 (REPLAY RUN from the entry).** The two records through `:json` encode and decode (String keys, as read from JSONL). `Replay.entry(entry, [response]) == {:ok, %{"order_id" => "order-1", "status" => "authorized"}}`. A changed `value` gives `{:error, :body_digest_mismatch}`; another `operation` gives `{:error, :operation_mismatch}`. The ENTRY RECORD of a currency `""` call replays to `{:error, %BeamlSpike.Rejected{reason: "constructor"}}`.
- **N10 (compile rejects).** Each exits non-zero with its message (texts in D6B-129, D6B-130, D6B-138): two ENTRY LINES; `on http "place" ...`; event `"place-order"`; target `Amount` (constructor, DL-120); TYPE `Order` against the parameter `PlaceOrder`; a target with two parameters; target `checkout` that reaches the EFFECT but is not its flow; a fn `ui_place`; a TYPE `Rejected`; an input TYPE with a constructor; an input TYPE with a MIGRATE CHAIN.
- **N11 (fmt).** `beaml fmt` on both fixtures changes nothing (exit 0, empty stdout). A source with the ENTRY LINE between two alignable clauses keeps the ENTRY LINE bytes.
- **N12 (events).** Every compile keeps the harness check: no source text, no path in `.beaml/actions.jsonl`.
- **N13 (byte guard, passes before and after).** Every tracked source without an ENTRY LINE compiles byte-equal against the HEAD compiler (`git archive` build, as steps 5, 8, 11). `payments.generated.snapshot` stays equal.
- **N14 (grammar).** `integrations/zed-beaml`: a corpus case `test/corpus/entry.txt` with the tree `(entry_declaration transport: (identifier) event: (string) input: (type) target: (identifier))`; a highlight line in `test/highlight/forms.beaml` (`on` keyword, `"place"` string, `PlaceOrder` type, `place` function). `tree-sitter test --rebuild` and `tree-sitter test --wasm --rebuild` pass.

## Existing assertions that change (each by name)

| File | Assertion | Today | After 6d |
|---|---|---|---|
| `tests/slice5_syntax_test.py` | `FALLBACK` (used by `test_F02_fallback_error_names_every_declaration_word`) | `expected type, enum, effect, migrate, retire or fn` | `expected type, enum, effect, on, migrate, retire or fn` |
| `experiments/0001-syntax-to-beam/tests/cli.rs` | line 208, absence of the fallback text in `assert_rejected` | old text | new text. **Must change with main.rs**: an old text makes the absence check pass always (false pass). |

- **[Inference]** No other test asserts the fallback text (grep over `tests/`, `cli.rs`, `main.rs`). No tracked `.beaml` source has a top-level `on` (grep).

## Byte changes

- **Change:** none for existing sources (N13). The GREEN may move the decode emit out of `emit_effect` for reuse; N13 proves the move keeps bytes.
- **New:** the outputs of the two fixtures and of the N10 inline sources.

## Checks

- 0001: `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings`. New unit test `entry_line_parses` (parse and the checks of D6B-129).
- 0004: `tests/slice6_inbound_test.py`, every `slice6_*_test.py`, `slice5_syntax_test.py`, the compile-level test files; `python3 -B experiments/0004-generated-replay/run.py` once at the TEST phase, not before.
- `integrations/zed-beaml`: `tree-sitter generate`, `tree-sitter test --rebuild`, `tree-sitter test --wasm --rebuild`.

## Order

- **[Proposal]** After the step 13 GREEN (`slice6b-stored-elixir`, writes `main.rs` now). One code-writing worker at a time. Before EXPERIMENT 0005 (DL-128 effect).

## Exclusions

- HTTP route entries (`on http ...`). They follow later in the same form (DL-128).
- LiveView itself and any Phoenix code. That is EXPERIMENT 0005. 0004 calls the generated function from `elixir`.
- More than one ENTRY LINE per source; a target that reaches the EFFECT but is not its flow.
- An input TYPE with its own constructor, with a MIGRATE CHAIN, or with `redacted` fields (not in the 0001 compiler).
- An ENTRY RECORD and a REPLAY RUN for a source without an outbound EFFECT (D6B-136).
- `--stored` reads no ENTRY RECORD (D6B-139). No retention or RETIRE LINE for an entry.
- The OBSERVATORY settings of D018. The root span gives the tree its level 0 only.

## Limits

- **[Inference]** Nested atom keys (`"amount" => %{value: ...}`) pass the JSON round trip as String keys. Only the top level is checked (N4). Host code, not outside data, writes atom keys.
- **[Inference]** One JSON encode per event (D6B-132). Fine for UI events; a value-level decode can follow when a measure shows a need.
- **[Unknown]** Whether Elixir 1.18.1 with `--warnings-as-errors` reports a host call to a deleted `ui_<event>` as an error. Q6D-2 option A relies on it; the RED worker probes it once and records the result.
- **[Inference]** `on` becomes a keyword in tree-sitter, so a parameter named `on` no longer highlights as an identifier. The 0001 parser reads `on` only as a top-level word.
- **[Inference]** The test stubs do not run the real `ProbeSupport` and OTel exporter. `run.py` has no ENTRY LINE source.
