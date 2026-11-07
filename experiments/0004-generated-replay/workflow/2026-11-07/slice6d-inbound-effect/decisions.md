# Decisions: slice 6d (inbound EFFECT: a declared entry point)

**[Proposal]** PLAN phase, 2026-11-07. Design decisions that DL-128 and the decision log do not settle.
Classes follow Decision4. Undo and Repair entries give the default that the step worker takes. Migrate entries are OWNER questions.
Every entry carries a `By:` line (DL-107). The worker records each taken default again in its `notes.md` (DL-097). A Repair that changes language behaviour gets a decision-log entry at the end of its phase.
ID check: the highest D6B number in `experiments/` and `wiki/` was D6B-127 at this plan. The main agent checks for a collision again before the commit.

## OWNER questions

### Q6D-1 · Migrate · The form of the ENTRY LINE

- **Context.** **[Verified]** DL-128 gives a sketch, not grammar: `on ui "place" Order -> place`. DL-126: a declaration carries shape and policy; the COMPILER derives the rest.
- **Option A (default).** `on ui "place" PlaceOrder -> place`. The event name is a string, as LiveView sends it. The input TYPE is the shape that the decode checks. Output and failure TYPE come from the fn. Challenge: a new keyword `on`; the record `operation` (`ui.place`) is derived, not written.
- **Option B.** `effect ui.place PlaceOrder -> Payment ! PaymentError = ui.event("place") |> place`. It reuses the `effect` keyword and its `kind("path")` parser. Challenges: output and failure TYPE stand twice (in the line and in the fn), so they can drift; `effect` then has two directions with two body meanings; `|> place` in an EFFECT body is a new form.
- **Option C.** `entry ui.place PlaceOrder -> place`. The dotted name is the operation, as in `effect` and `retire` lines. Challenge: the event name comes from the dotted name, so a UI EVENT such as `place-order` cannot be written.
- **Why Migrate.** Every source and the grammar carry the form. A change later rewrites every ENTRY LINE.
- **Interim.** RED and GREEN build A. B or C change the parser, the grammar cases and N10; the generated code stays.
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6d-inbound-effect).

### Q6D-2 · Migrate · The generated function that the host calls

- **Option A (default).** One function per ENTRY LINE: `Orders.ui_place(params)`. The host writes `def handle_event("place", params, socket)` and calls it. Because: a deleted or renamed entry is an undefined remote call in the host build ([Unknown] for `--warnings-as-errors`, probe in RED), not a runtime surprise. Challenge: one host clause per event.
- **Option B.** One dispatch function: `Orders.entry("place", params)`. One host clause `handle_event(event, params, socket)` forwards every event. An unknown event gives `{:error, %Rejected{reason: "unknown_event"}}`. Challenge: a renamed event fails at runtime only.
- **Why Migrate.** Host code calls it in EXPERIMENT 0005.
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6d-inbound-effect).

### Q6D-3 · Migrate · The form of a decode reject at the host

- **Option A (default).** `{:error, %BeamlSpike.Rejected{reason: "decode" | "constructor"}}`, a generated struct apart from domain failures. Because: the host can tell a bad UI EVENT from a failed flow; it works when the fn has no `!`.
- **Option B.** The failure TYPE of the fn with `reason`, as the outbound EFFECT does (`%PaymentError{reason: "decode"}`). Challenge: `reason: "decode"` then means a bad UI EVENT or a bad payments response; the UI cannot tell them apart. It fails for a fn without a failure TYPE.
- **Option C.** A plain tuple `{:error, {:rejected, "decode"}}`. Challenge: not a TYPE; a host pattern on structs misses it.
- **Why Migrate.** Host code matches on it.
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6d-inbound-effect).

## Undo and Repair defaults

Format: **ID · class · decision.** Chose / Over / Because. Commits us to (Repair only).

**D6B-128 · Repair · The ENTRY LINE is its own declaration, not an `Effect`.**
Chose: `struct Entry { transport, event, input, target, source_range }` in `Program.entries`; the parser branch `"on"`; the fallback text becomes `expected type, enum, effect, on, migrate, retire or fn`. Over: an `Effect` with a direction flag. Because: the outbound checks (`http.post`, one EFFECT, `reason: String`) do not apply; a flag would make every EFFECT check branch. Commits us to: two lists for EFFECTS; the reach analysis treats an entry as a root, not a node.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-129 · Repair · Supported subset of the line.**
Chose: compile errors, each one line with the place: `slice 6d supports one entry`; `entry on <t>: slice 6d supports the transport ui only (HTTP route entries come later)`; `entry ui "<e>": the event name must match [a-z][a-z0-9_]*`; `entry ui "<e>": <T> is a constructor; an entry calls a fn (DL-120)`; `entry ui "<e>": <fn> takes <P>, not <T>`; `entry ui "<e>": <fn> must take one parameter`; `entry ui "<e>": <fn> reaches <effect> but is not its flow; slice 6d replays the flow only`. Over: several entries; any reaching fn. Because: `Replay.run/3` replays one flow (`flow(effect)`); the generated name needs an Elixir identifier. Commits us to: a page with several events waits for a later step.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-130 · Undo · The input TYPE is a plain record.**
Chose: errors `entry ui "<e>": <T> has a constructor; slice 6d decodes a plain record` and `entry ui "<e>": <T> has a MIGRATE CHAIN; slice 6d decodes the newest TYPE only`. Its fields may be constructor TYPES and enums (the DL-101 path). Over: a top-level `__beaml_from_T`. Because: the field path covers DL-101 with existing code; params carry no TYPE VERSION.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-131 · Repair · `def ui_<event>(params)` is the host entry.**
Chose: a public function in `BeamlSpike` that accepts any term, never raises for outside data, and returns `{:ok, result}` or `{:error, failure}`. It calls the public wrapper of the target, so the output check stays. Over: `entry/2` (Q6D-2 B). Because: the same naming as `payments_authorize`. Commits us to: one public name per event; Q6D-2 can change it.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-132 · Repair · The decode is the DL-101 decode of the input TYPE on `:json.encode(params)`.**
Chose: the same emit path as the outbound decode, for the input TYPE; a guard before it: not a map, a non-String top-level key, or a JSON encode raise give `decode`. Constructor failure gives `constructor`. Over: a second, value-level decode. Because: one decode for the live call and the REPLAY RUN, which reads JSON-encoded `value` (D6B-137); outside data stays on the String-key path (DL-117). Commits us to: one encode round trip per event (ponytail: value-level decode when a measure needs it); nested atom keys are not rejected (limit).
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-133 · Repair · The entry opens the root span.**
Chose: `ProbeSupport.span("<service>.ui.<event>", :server, nil, nil, fn -> ... end)` around record write, decode and call. Span input `nil`: no attribute from undecoded data. `function` `nil`: no source file read. `unknown_keys` and `reason` as root attributes, as on the EFFECT span. A reject raises `BeamlFailure` inside, `__beaml_attempt__` returns it outside (outcome `error`). A domain failure returns through the span. Over: the decoded value as span input; a root span around the call only. Because: the root must also show a rejected event; D6B-127 `"none"` then stays only for an undeclared host call. Commits us to: a root span with outcome `ok` for a failed flow (the failing child span carries `error`).
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-134 · Undo · Reach: the entry is a root, not a step.**
Chose: the target fn gets no span of its own; its steps keep DL-119 S. A pure target gives the root span only. DL-120 is unchanged; an entry cannot target a constructor (D6B-129). Over: a span for the target fn. Because: the root span already names the call; a second span adds a level with no new fact.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-135 · Repair · The ENTRY RECORD.**
Chose: `ProbeSupport.Capture.write("entries", %{version: 2, trace_id, server_span_id, artifact_id, operation: "ui.<event>", attempt: 1, value, redacted: [], unknown_keys, value_sha256, type})`, written before the decode, also for a reject. `value` and `unknown_keys` follow the D6B-54/D6B-56 projection of the input TYPE; `value_sha256` the D6B-58 digest. Over: the key `request` for the projection; the same `responses` stream. Because: `value`, `body/1` and `digest/3` already mean "the projection of outside data" and are reused unchanged; `select/2` needs one `responses` record per `trace_id`. Commits us to: a second JSONL stream (`entries.jsonl`); no `status` and no `request` key in an ENTRY RECORD.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-136 · Undo · No ENTRY RECORD without an outbound EFFECT.**
Chose: a source with an ENTRY LINE and no outbound EFFECT writes no record and has no `Replay` module. Over: a `Replay` module in a pure source. Because: a pure flow from the same params is the same call; `digest/3` lives in `Replay`.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-137 · Repair · `Replay.entry(record, records)` is the REPLAY RUN from the entry.**
Chose: `:operation_mismatch` for another operation; `body(record)` for the digest (`:body_digest_mismatch`); the entry decode on the re-encoded `value` (a reject gives the same `Rejected`); then `run(decoded, record["trace_id"], records)`. Over: a host-side replay that decodes itself. Because: the REPLAY RUN covers the whole flow from the entry with the existing checks. Commits us to: the caller passes the ENTRY RECORD and the RESPONSE RECORDS of one trace.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-138 · Undo · Name collisions are compile errors.**
Chose: `entry ui "<e>": the generated name ui_<e> is taken by fn ui_<e>` and `entry ui "<e>": the TYPE name Rejected is reserved next to an entry`. Over: renaming. Because: silent renames break the host call.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-139 · Undo · An ENTRY LINE needs no `--stored`; `--stored` reads no ENTRY RECORD.**
Chose: the `--stored` rule keeps its trigger (an outbound EFFECT or a RETIRE LINE). Over: `--stored` for entries. Because: the ENTRY RECORD has no build check yet; a build check of stored params against a changed input TYPE is a later step (D020).
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-140 · Undo · `fmt` keeps the ENTRY LINE bytes.**
Chose: the entry is not a row of the column alignment. Over: aligning `->` with clauses. Because: one line with no peer; nothing to align.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-141 · Undo · New glossary terms ENTRY LINE and ENTRY RECORD.**
Chose: the docs phase adds them to `GLOSSARY.md` (owner LANGUAGE/COMPILATION and EXECUTION; aliases Eintrittszeile, Eintrittsdatensatz) before GREEN prose uses them. Over: reuse of RESPONSE RECORD. Because: an ENTRY RECORD holds no response.
By: Opus (PLAN, slice6d-inbound-effect)

**D6B-142 · Repair · Grammar rule `entry_declaration`.**
Chose: `seq("on", field("transport", $.identifier), field("event", $.string), field("input", $.type), "->", field("target", $.identifier))` in `source_file`; `"on"` in the keyword list of `highlights.scm`; `(entry_declaration target: (_) @function)`; regenerate `src/` with `tree-sitter generate`. Over: a generic rule for B and C. Because: Q6D-1 default A; B or C replace this one rule. Commits us to: `on` is a keyword word in tree-sitter.
By: Opus (PLAN, slice6d-inbound-effect)
