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

- **Status** CLOSED 2026-11-07: option O2, the RESPONSE RECORD holds the typed projection, never the raw body. See [DL-105](decision-log.md); step 6 replan in [slice6b-redacted](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-redacted/plan.md).
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

- **Status** CLOSED 2026-11-07 by [DL-106](decision-log.md) (Q6B-6, B: the generated wrapper is the only entry). Record kept below.
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

- **Status** CLOSED 2026-11-07 by [DL-108](decision-log.md) (Q6B-7, C: a span follows the EFFECT, transitively). Record kept below.
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

## D007 — Removed or changed ENUM LITERAL in stored records (Q6B-8)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** EXECUTION, DL-102, DL-103
- **Decision trigger** Before a deploy removes an ENUM LITERAL or changes its String.

**[Inference]** When an ENUM LITERAL is removed, or its String changes, old stored records replay as the KEEP-VALUE VARIANT `Unknown`. Example: remove `Pending = "pending"`, and a stored `"pending"` replays as `Unknown("pending")`. DL-102 does not fire, so the build does not fail. DL-103 covers only `Unknown` to known, so no count occurs. Today a deploy changes the replay result with no block and no count. [RED review, N1](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-decode-literals/red-review.md)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, block | Treat it as a hit under DL-102. Block until a MIGRATE STEP. | Safe. In slice 6b no MIGRATE STEP is possible for this TYPE (D6B-39). |
| B, count | Count and report the records. Do not block. | Visible. The replay result still changes. |
| C, no check | The `Unknown` promise covers it. | No work. The change stays silent. |

**[Unknown]** No fixture has a stored value whose literal is removed.

**[Proposal]** Next check: a fixture with a stored value whose literal is removed, run with `--stored`. Record the exit and the stderr.

## D008 — GEN arm and the 0003 RESPONSE RECORD contract (Q6B-10)

- **Status** CLOSED 2026-11-07 by [DL-110](decision-log.md) (Q6B-10, B: the GEN against LIB comparison ends before the projection records). Record kept below.
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** EXPERIMENT 0004 evidence base, GEN against LIB comparison
- **Decision trigger** Before the 6a GEN copy run and `overlay_diff_test.py` run with the projection record.

**[Inference]** DL-105 removes the raw body from every GEN record. The GEN copies of the 0003 tests read the raw body, and LIB is frozen on the raw body. [Q6B-10](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-redacted/decisions.md#q6b-10--migrate--the-gen-arm-and-the-0003-response-record-contract-blocks-6a)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, new GEN rows | GEN copies get projection rows. LIB stays frozen on the raw body. | The arms store different contracts. a1 gets a new meaning. |
| B, stop the comparison | The arm comparison stops at 6a. Slice 1 to 5 results stay evidence. | Cheap. The GEN against LIB claim ends. |
| C, outcomes and counts only | LIB stays its own record version. Record-byte lines become "not applicable". | Cheaper than A, keeps more than B. Loses the byte checks. |

**[Verified]** Blocks only the GEN copy run and `overlay_diff_test.py`. 6a RED and GREEN can start. By: Opus (PLAN REPAIR, slice6b-redacted).

**[Proposal]** Next check: list the GEN copy lines that each option changes. Count them.

## D009 — A field that becomes redacted while stored records hold its value (Q6B-11)

- **Status** CLOSED 2026-11-07 by [DL-111](decision-log.md) (Q6B-11, 1A + 2A: a new TYPE VERSION, eager removal). Record kept below.
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** EXECUTION/REPLAY RUN, stored records, DL-029, DL-102
- **Decision trigger** Before 6b GREEN of R7 and R8, or before a deploy marks a stored field as `redacted`.

**[Inference]** Input case: the value is in the record `request`. The record has no fingerprint of the input TYPE, so the build passes and every old record gives `:request_mismatch`. Output case: the value is in `value`. [Plan check, O2](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-redacted/plan-review.md#o2--high--an-input-field-that-becomes-redacted-does-not-block-and-leaves-the-value-in-stored-request-d6b-66-q6b-11)

**[Proposal]** Interim D6B-72: `--stored` counts stored values under a now-redacted field in `request` and `value`, and blocks. No exit in 6b. By: Opus (PLAN REPAIR, slice6b-redacted).

**[Proposal]** Options, Part 1 (detection, was D6B-66) and Part 2 (exit):

| Option | Meaning | Trade-off |
|---|---|---|
| 1A, in the fingerprint | The field TYPE text is `redacted String`. | A new TYPE VERSION. The input case still needs D6B-72. |
| 1B, not in the fingerprint | Only the D6B-72 value check blocks (D6B-30). | The TYPE VERSION does not show the change. |
| 2A, MIGRATE CHANGE `redact f` | The REPLAY RUN removes and marks the old value at read. | The old value stays until a `retire` keep window ends. |
| 2B, DL-102 fates only | `retire` with a keep window, or `quarantine`. | An input field has no TYPE VERSION in the record. |

**[Unknown]** Not built. No test runs today.

**[Proposal]** Next check: 6b R8, a stored `request` with `card_holder` against a source that marks it `redacted`.

## D010 — Direct copy of a redacted value into a non-failure TYPE (Q6B-12)

- **Status** CLOSED 2026-11-07 by [DL-112](decision-log.md) (Q6B-12, A: a direct copy is a compile error everywhere). Record kept below.
- **Decision owner** OWNER
- **Class** Answer
- **Scope** LANGUAGE/COMPILATION, DL-105 failure TYPE rule
- **Decision trigger** Before a flow copies a redacted field into a non-redacted field of a TYPE that an EFFECT takes.

**[Inference]** `Receipt { holder: card_holder }` with a non-redacted `holder` sends the value on the wire without `with`. DL-105 names only failure TYPES. [Q6B-12](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-redacted/decisions.md#q6b-12--answer--a-direct-copy-of-a-redacted-value-into-a-non-redacted-field-of-a-non-failure-type-does-not-block)

| Option | Meaning | Challenge |
|---|---|---|
| A, every TYPE | The 6c compile error applies to every record literal and variant payload. | Stricter than the OWNER text. A legal copy needs a `redacted` mark. |
| B, failure TYPES only | DL-105 text now. Other copies wait for the flow check. | A one-step copy bypasses DL-089 until then. |

**[Unknown]** How many real flows copy a PII field on purpose. No recommendation (Answer class).

**[Proposal]** Next check: 6c F1 to F6, plus one non-failure copy case compiled under each option.

## D011 — Redacted input field and same-named plain output field (Q6B-13)

- **Status** CLOSED 2026-11-07 by [DL-113](decision-log.md) (Q6B-13, C: the declaration decides). Record kept below.
- **Decision owner** OWNER
- **Class** Answer
- **Scope** LANGUAGE/COMPILATION, DL-089, DL-105
- **Decision trigger** Before 6b GREEN of R4c, or before an EFFECT returns an input PII field under the same name.

**[Inference]** An output TYPE with a plain `card_holder: String` puts an echoed value into the record `value`. No compile signal. The same name does not prove the same value. [Plan check, O3](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-redacted/plan-review.md#o3--high--the-echo-test-misses-one-leak-path-and-two-channels-r4-d6b-70), [Q6B-13](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-redacted/decisions.md#q6b-13--answer--a-redacted-input-field-and-a-same-named-plain-output-field-of-the-same-effect-blocks-6b-green-of-r4c)

| Option | Meaning | Challenge |
|---|---|---|
| A, compile error | The build fails. | Blocks a legal display field. A different name bypasses it. |
| B, warning | The build passes with a warning. | A stored value cannot be taken back (DL-029). |
| C, allowed | The OWNER declares the output plain. | The record holds a value that the input marks as PII. |

**[Unknown]** How many real EFFECTS return an input PII field under the same name. No recommendation (Answer class). By: Opus (PLAN REPAIR, slice6b-redacted).

**[Proposal]** Next check: 6b R4c with the echo stub, scan of the RUN DIRECTORY.

## D012 — Replay marker for a redacted field (Q6B-14)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** EXECUTION/REPLAY RUN, DL-105
- **Decision trigger** Before 6b GREEN of R5, or before host replay code reads a redacted field.

**[Inference]** DL-105: a redacted field replays "as absent and marked". An atom in a String field takes another host branch than live (`is_binary`). [Q6B-14](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-redacted/decisions.md#q6b-14--migrate--how-a-replay-run-shows-a-marked-field-was-d6b-62-blocks-6b-green-of-r5)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, atom `:redacted` | The field holds `:redacted`. `__beaml_valid__` accepts it only for a redacted field. | Host code sees a value that live never gives. A pure step that computes with it may raise. |
| B, absent key plus list | The key is absent; the result carries the `redacted` list. | The result is not TYPE-valid by today's `__beaml_valid__`. Host code needs a second check. |

**[Unknown]** Not built. By: Opus (PLAN REPAIR, slice6b-redacted).

**[Proposal]** Next check: 6b R5, replay of the R4 record under each option.

## D013 — `redacted` output only on a top-level String field (Q6B-15)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION, DL-102, DL-105, DL-106
- **Decision trigger** Before 6b GREEN of R6, or before an EFFECT output marks an enum, constructor or record field `redacted`.

**[Inference]** DL-102 cannot run a rule over a value that the record does not have, and a constructor would get the marker as input. [Q6B-15](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-redacted/decisions.md#q6b-15--migrate--interim-limit-redacted-output-only-on-a-top-level-string-field-was-d6b-63-blocks-6b-green-of-r6)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, String fields only | Compile error for every other redacted output field (slice 6b). | A new interim compile error on a basic feature. |
| B, any field TYPE | The REPLAY RUN and the DL-102 check skip the rules of a marked field. | A constructor or enum rule over that field is not checked at replay. |

**[Unknown]** Not built. By: Opus (PLAN REPAIR, slice6b-redacted).

**[Proposal]** Next check: 6b R6, the reject texts under option A; one enum field case under option B.

## D014 — Form of `T.new` for several parameters or signatures (Q6B-16)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION, host call boundary, DL-106
- **Decision trigger** Before step 11 GREEN of H9, or before a host builds a constructor TYPE with more than one parameter.

**[Verified]** DL-106 names `new/1`. `NonZeroInt` has one parameter; `Pair` and `Amount` have two. A record constructor can have several signatures; a host call has no static TYPE. [Q6B-16](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-host-structs/decisions.md#q6b-16--migrate--the-form-of-tnew-for-a-constructor-with-more-than-one-parameter-or-more-than-one-signature-blocks-h9-only)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, positional | `T.new/n` with the parameters in order; the first accepting signature wins. | `new/1` holds only for one parameter. |
| B, one map | Always `T.new/1`; several parameters as a map with the parameter names as String keys, as in the decode (DL-099). | One-parameter and several-parameter signatures read the argument differently. |
| C, keyword list | `Pair.new(x: "x", y: "y")`; named and order-free. | Atom names at the host; differs from the String-key decode form (DL-099). By: Opus (PLAN REPAIR, slice6b-host-structs). |

**[Unknown]** Not built. By: Opus (PLAN, slice6b-host-structs).

**[Proposal]** Next check: step 11 H9, `Pair.new` under each option.

## D015 — Which steps of a reaching pipe get a span (Q6B-17)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** EXECUTION/OBSERVATORY, DL-108, D6B-28
- **Decision trigger** Before step 12 GREEN of E2.

**[Verified]** DL-108: "Pure steps stay silent; steps on a path to an EFFECT get a span". Today every step of a direct EFFECT pipe has a span; the GEN arm query expects `orders.prepare` and the log inside it. [Q6B-17](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-effect-reach/decisions.md#q6b-17--migrate--which-steps-of-a-reaching-pipe-get-a-span-blocks-e2-and-the-green-of-e2-only)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| P, per pipe | Every step of a pipe in which any step is or reaches an EFFECT. | No byte change. Pure work next to an EFFECT has spans. |
| S, per step | Only steps that are or reach an EFFECT. | About 50 EFFECT sources, the hash guards and the GEN query change. |
| H, hybrid | Direct EFFECT pipes keep today's spans; indirect pipes span only reaching steps. | No existing byte changes. Two span rules in one compiler. By: Opus (PLAN REPAIR, slice6b-effect-reach). |

**[Unknown]** Not built. By: Opus (PLAN, slice6b-effect-reach).

**[Proposal]** Next check: step 12 E2, span count of `checkout` under each option.

## D016 — A constructor that reaches an EFFECT (Q6B-18)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION, DL-092, DL-101, DL-108
- **Decision trigger** Before step 12b RED. 12b is blocked until the answer.

**[Observed]** An enum constructor can be the EFFECT flow today, and it compiles. **[Verified]** DL-092, DL-100, DL-101 and DL-108 do not restrict what a constructor calls. [Q6B-18](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-effect-reach/decisions.md), [plan check O1](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-effect-reach/plan-review.md)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| a, reject all | Every constructor that reaches an EFFECT is a compile error. | Removes syntax that compiles today. |
| b, reject where the compiler calls it | Reject only in a decode field, the step 8 `--stored` check and the host `T.new`. | Keeps source use; two contexts for one constructor. |
| c, allow | Spans on the constructor; the REPLAY RUN substitutes the inner EFFECT. | A decode can call an EFFECT. |

**[Unknown]** Not built. By: Opus (PLAN REPAIR, slice6b-effect-reach).

**[Proposal]** Next check: 12b RED, `fn Settled order: Order -> Settled ! PaymentError = order |> payments.authorize |> Done` under the chosen option.

## Answered 2026-11-07

- [DL-099](decision-log.md): Q6B-1, enum constructor inputs come from the field's own value.
- [DL-100](decision-log.md): Q6B-2, an enum constructor is the decode path only.
- [DL-101](decision-log.md): Q6B-3, the decode of outside data calls the record constructor.
- [DL-102](decision-log.md): replay rule, a stored record that fails a new rule blocks the build until a MIGRATE STEP declares its fate.
- [DL-103](decision-log.md): replay rule, a mapping change that only resolves Unknown values needs no MIGRATE STEP.
- [DL-104](decision-log.md): Q6B-5, `beaml fmt` never changes the TYPE VERSION.
