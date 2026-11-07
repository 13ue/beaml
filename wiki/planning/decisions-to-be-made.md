---
id: planning-decisions-to-be-made
kind: planning
status: active
updated: 2026-11-07
---

# Offene Fragen / Decisions to be made

Record open R&D decisions with a stable ID, owner, evidence and next check.
Keep each decision OPEN until the owner records a choice and its reason.
See [specification gaps](specification-gaps.md) for the historical specification review.

## D001 — Enum or type declarations

- **Status** CLOSED 2026-11-06 (still CLOSED on 2026-11-07): `type` for records, `enum` for variants. See [DL-061](decision-log.md) (supersedes DL-060).
- **Decision owner** Repository owner
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** Before selecting a canonical declaration grammar or migrating the fixture.

**[Requirement]** The owner asks whether `type` should replace `enum` and requests an open decision record. [Selected conversation capture](../../raw/requirements/2026-11-05-enum-or-type.md)

**[Verified]** EXPERIMENT 0001 declares `enum OrderError` and `enum OrderResult`. `OrderResult` has `Ok(Order)` and `Error(OrderError)` variants. The compiler parses `enum` for variants and `interface` for exact records. [Fixture](../../experiments/0001-syntax-to-beam/example.beaml), [parser](../../experiments/0001-syntax-to-beam/src/main.rs), [retained run](../../experiments/0001-syntax-to-beam/results/20261105T202319485083Z/result.json)

**[Proposal]** Compare these declaration forms:

| Option | Meaning | Trade-off |
|---|---|---|
| Keep `enum` | `enum` declares tagged variants. `interface` declares exact records in the current subset. | The keyword identifies a variant declaration immediately. An alias would need a separate form if adopted. |
| Use `type` | `type` introduces a named declaration. Distinct forms identify tagged variants, records and aliases. | One keyword can cover several kinds of TYPE declarations. The form must make each kind clear. |

**[Proposal]** Candidate variant syntax for the second option. EXPERIMENT 0001 has no parser support for this form.

```beaml
type OrderResult = Ok(Order) | Error(OrderError)
```

**[Inference]** `type` fits if BEAML wants one keyword for several declaration kinds. The variants can keep their constructor identity, payload checks and exhaustive matching. The keyword by itself leaves those semantics open.

**[Proposal]** Compare the forms on five criteria:

| Criterion | Check |
|---|---|
| Readability | Identify variants, records and aliases from short declarations. |
| Semantics | Preserve constructor identity, payload checks and match coverage. Distinguish tagged variants from aliases and structural unions. |
| Grammar | Parse each form unambiguously. Include a single variant, a zero-argument variant and a named alias. |
| Migration | Account for fixture and documentation changes. Identify any source compatibility needs. |
| Tooling parity | Compare diagnostics and editor highlighting. Include formatting if it is in scope for the grammar check. |

**[Proposal]** First compare two small grammar sketches against the same order fixture. Add one record, one alias and the two variant edge cases. Use the current fixture as the control. Record what each form means and where it fails before the owner selects a form. **[Unknown]** The candidate has no retained test result.

## D002 — Scope of the replay artifact identity

- **Status** OPEN
- **Decision owner** Repository owner
- **Scope** EXECUTION/REPLAY RUN
- **Decision trigger** Before a REPLAY RUN claims that it reproduced the exact Orders code path.

**[Verified]** In EXPERIMENT 0003, the Orders `artifact_id` is the SHA-256 of the `OrdersBeamlSpike` BEAM only. It covers preparation and finish. It does not cover the host JSON decode or the `valid_payment!` validation. [Capture review, A3](../../experiments/0003-source-linked-replay/workflow/2026-11-05/capture/review.md#advisory-items)

**[Requirement]** On 2026-11-06 the owner chose not to solve this now and to keep it as an open decision. [Owner decisions](../../experiments/0003-source-linked-replay/workflow/2026-11-05/capture/notes.md#owner-decisions-after-review), [EXPERIMENT 0003](../../experiments/0003-source-linked-replay/README.md#evidence-and-limits)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| Keep the BEAML module hash | The REPLAY RUN binds only the generated module. | Simple. A changed host decode or validation is not detected. |
| Add a module-set digest | The identity also covers the host decode and validation modules. | Detects host changes. Needs a defined module set per operation. |

**[Unknown]** No test shows how often host decode or validation changes without a BEAML change.

**[Proposal]** Next check: in the gate 4 REPLAY RUN, change only the host decode in a derivative build. Record whether replay detects the change with each option.

## D003 — Trace sampling and retained response records

- **Status** OPEN
- **Decision owner** Repository owner
- **Scope** EXECUTION/OBSERVATORY
- **Decision trigger** Before CAPTURE runs with trace sampling or at large volume.

**[Requirement]** On 2026-11-06 the owner chose no timestamp in the response record. The reason is data economy at large volume. The time comes from the span through `trace_id` and `client_span_id`. The span has start and end in Unix nanoseconds since the lookup repair. [Owner decisions](../../experiments/0003-source-linked-replay/workflow/2026-11-05/capture/notes.md#owner-decisions-after-review)

**[Inference]** At volume, traces are often sampled. A response record that gets its time from its trace loses the time when the trace is dropped.

**[Proposal]** Candidate rule: a retained response record implies that its trace is retained.

**[Inference]** The JSON-lines record format is EXPERIMENT scaffolding, not a product format. Larger byte savings lie in a per-run `artifact_id`, a derived hash and length, and a binary format.

**[Unknown]** No run uses sampling. No byte measurement exists for the record.

**[Proposal]** Next check: drop one trace in a derivative copy of a CAPTURE run. Record whether the lookup reports the missing time as a specific evidence error. [EXPERIMENT 0003](../../experiments/0003-source-linked-replay/README.md#evidence-and-limits), [capture review](../../experiments/0003-source-linked-replay/workflow/2026-11-05/capture/review.md)

## D004 — Redacted fields in an EFFECT output and the stored body (Q6B-4)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Answer: a stored PII value cannot be taken back.
- **Scope** LANGUAGE/COMPILATION and EXECUTION/REPLAY RUN
- **Decision trigger** Before an EFFECT output TYPE can hold a redacted field, or before a production store keeps RESPONSE RECORDS.

**[Verified]** The RESPONSE RECORD stores the raw response body (`body_base64`, `body_sha256`) and the full EFFECT input. DL-089 states that spans, logs and records never hold the value. DL-029 makes privacy the highest goal. [Q6B-4](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-plan/decisions.md#q6b-4--answer--redacted-fields-in-an-effect-output-and-the-stored-body)

**[Inference]** The compiler cannot see undeclared keys. A service that echoes a redacted value in an undeclared key puts it into the stored raw body. The key name also goes into `unknown_keys`. A compile error on declared fields therefore does not protect the stored body. [Plan review, O2](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-plan/plan-review.md#o2--high--step-6-can-pass-while-response-records-hold-a-redacted-value)

**[Verified]** Interim: D6B-34 rejects a redacted field in any EFFECT output TYPE at any depth.

**[Proposal]** Options:

| Option | Meaning | Challenge |
|---|---|---|
| A, compile error stays | A redacted field in an EFFECT output TYPE stays a compile error. | Blocks real responses with PII. Does not protect against echoed undeclared keys. |
| B, store the cut body | The RESPONSE RECORD stores the body without redacted keys, with a digest of the cut body. The replay decode knows a value that is absent because it is redacted. | Changes the RESPONSE RECORD contract and the replay check. Needs a new TYPE state for that absent value. |

**[Proposal]** Independent rule, with A or B: unknown keys are stored as names only, never with values.

**[Unknown]** Whether a later production store keeps RESPONSE RECORDS. No recommendation (Answer class).

**[Proposal]** Next check: a loopback stub echoes the full request body. Assert that a marker value is in no file of the run directory.

## D005 — Forged constructor values at the generated public wrapper (Q6B-6)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION, host call boundary
- **Decision trigger** Before a host calls a generated wrapper with a TYPE that has a record constructor.

**[Inference]** The public wrapper checks the shape only. A host can call `BeamlSpike.keep(%{"value" => 0})` and get a NonZeroInt that never went through `fn NonZeroInt`. DL-092 ("the only way in") covers source code, not host calls. A struct success value alone does not close the gap. [RED review](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-type-constructor/red-review.md), [review](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-type-constructor/review.md)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, out of scope | DL-092 binds generated BEAML code only. | No work. A host can forge a checked value. |
| B, wrapper is the only entry | The generated constructor wrapper is the only entry. A guard on every public wrapper rejects a nominal value that did not come from the constructor. | Closes the gap. Needs a value mark and a guard per wrapper. |

**[Unknown]** Not built. No test calls a wrapper with a forged value.

**[Proposal]** Next check: one host test calls `keep` with `%{"value" => 0}`. Record the result for each option.

## D006 — Spans for a pipe that reaches an EFFECT through a fn (Q6B-7)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** EXECUTION/OBSERVATORY, D6B-28
- **Decision trigger** Before a trace must show a pipe that calls an EFFECT through another fn.

**[Verified]** D6B-28 gives spans only to a whole-body pipe with an EFFECT step. In `indirect order = order |> place`, `place` calls the EFFECT, but `place` is not an EFFECT step. `indirect` has no span now. No fixture has this shape. [Review, G13](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-type-constructor/review.md#g13-spans-per-pipe-observed-old-and-new-compiler-compared)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, keep | A span only where the EFFECT step is visible in the pipe. | Current output. A trace does not show the outer pipe. |
| B, every pipe in an EFFECT module | Every pipe in a module that has an EFFECT gets a span. | Simple rule. Spans also on pure pipes. |
| C, transitive reach | A pipe gets a span when a called fn reaches an EFFECT transitively. | Precise. Needs a call graph check. |

**[Unknown]** The `indirect` case was only compiled, not run against a host.

**[Proposal]** Next check: compile and run the `indirect` probe under each option. Count the spans.

## Answered 2026-11-07

- [DL-099](decision-log.md): Q6B-1, enum constructor inputs come from the field's own value.
- [DL-100](decision-log.md): Q6B-2, an enum constructor is the decode path only.
- [DL-101](decision-log.md): Q6B-3, the decode of outside data calls the record constructor.
- [DL-102](decision-log.md): replay rule, a stored record that fails a new rule blocks the build until a MIGRATE STEP declares its fate.
- [DL-103](decision-log.md): replay rule, a mapping change that only resolves Unknown values needs no MIGRATE STEP.
- [DL-104](decision-log.md): Q6B-5, `beaml fmt` never changes the TYPE VERSION.
