---
id: planning-decisions-to-be-made
kind: planning
status: active
updated: 2026-11-08
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

- **Status** CLOSED by [DL-122](decision-log.md): A, a stored value whose literal is removed blocks the build until a MIGRATE STEP declares the fate (interim block).
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

- **Status** CLOSED by [DL-115](decision-log.md): A, a REPLAY RUN shows a redacted field as the atom `:redacted`.
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

- **Status** CLOSED by [DL-116](decision-log.md): A, interim: `redacted` output only on String and Int fields without a constructor.
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

- **Status** CLOSED by [DL-117](decision-log.md): B with atom keys, `T.new/1` takes one map with atom keys, also for one parameter.
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

- **Status** CLOSED by [DL-119](decision-log.md): S as the default; the resolution becomes an OBSERVATORY setting, see D018.
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

- **Status** CLOSED by [DL-120](decision-log.md): a, a constructor is pure; reaching an EFFECT is a compile error.
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

## D017 — The `--stored` check and a constructor that fails in a pipe step (Q6B-19)

- **Status** CLOSED by [DL-121](decision-log.md): b, the build runs the generated Elixir constructor over the stored values.
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION, DL-101, DL-102
- **Decision trigger** Before slice 6b closes (review D1, RV1).

**[Observed]** The `--stored` check reads only the static body TYPE of the first matching constructor clause (G7). Review probe 6: `fn Amount value, c -> Amount ! NoCurrency = value |> cur |> Amount` with a stored record `amount: {"value":"","currency":"EUR"}` gives exit 0 and empty stderr. The runtime decode of the same body gives the reject `constructor`. The control record with a literal failure clause gives exit 1. **[Verified]** DL-102 says such a record blocks the build; DL-101 says the decode calls the constructor. The check therefore gives a false pass against DL-102. [review D1, probe 6](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-decode-constructor/review.md), [notes G7, P11](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6b-decode-constructor/notes.md)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| a, compiler evaluates | The compiler interprets constructor clause bodies for the `--stored` check: an evaluator in the compiler for the constructor subset. | No new build tool. A second semantics beside the generated Elixir; the two can drift. Grows with each new body form. |
| b, build runs the generated constructor | The build runs the generated Elixir constructor over the stored values. | One semantics: the check equals the REPLAY RUN. Needs an Elixir toolchain at build time; the tests already have one. Slower build. |
| c, restrict the forms | A constructor clause used in a decode may only use forms the static check understands (no failing pipe steps). Other forms are a compile error with help. | Smallest change; no false pass. Removes syntax that compiles today; each new form needs the check first. |

**[Unknown]** Not built. By: Opus (DOCS, Q6B-19).

**[Proposal]** Next check: review probe 6 as the RED test under the chosen option; it must give exit 1 or the compile error. By: Opus (DOCS, Q6B-19).

## D018 — Span resolution as an OBSERVATORY setting (notes for part 4)

- **Status** OPEN, not before the OBSERVATORY slice
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** EXECUTION/OBSERVATORY, DL-108, DL-119
- **Decision trigger** Before the first OBSERVATORY slice plans its settings.

**[Requirement]** From the OWNER walk-through of Q6B-17 (2026-11-07), to keep for the OBSERVATORY design:

- The trace is a tree. Spans nest by call, as the code nests. A dashboard shows level 0 (the public API or the inbound EFFECT) and opens deeper levels on demand.
- The span resolution is a setting, not a compiler rule. The compiler instruments every call; the setting decides which spans a run writes.
- Three settings are needed: a default resolution for the whole application; an opt-out per part ("write no data here"); an opt-in to full resolution per part, limited in time (for example one day, to measure one question in production).
- The default is the EFFECT path per step (DL-119, option S). P (every step of a reaching pipe), H (hybrid) and E (every call, also pure functions) are candidate settings, not defaults.
- Seen inward, every live function in a web application lies on a path from an inbound EFFECT (request, message, timer). A function on no such path is dead code. "Pure steps stay silent" (DL-108) therefore holds for the default only.
- Where outside callers enter BEAML (an inbound EFFECT, an entry point) is not defined yet; today the host calls an exported `fn`. The inward view needs that definition (OWNER, Q6B-18 walk-through, DL-120).
- A span carries name, duration, parent, result TYPE and failure TYPE. Never values, source text, paths or PII (DL-105 projection applies).

**[Proposal]** Open questions for that slice: the address of a setting (module, function, or subtree from an entry); the cost of one flag check per call when a part is off (`persistent_term` or a compile-time variant); hot pure loops under E (one span per call versus per recursion step, or sampling); how a time-limited opt-in expires; where the setting lives (BEAML source, deploy config, or a live command). By: Fable (walk-through, 2026-11-07).

**[Unknown]** Not built. No OBSERVATORY slice is planned yet beyond the roadmap row.

## D019 — Backend of the pure core: generated Elixir or Rust NIFs

- **Status** OPEN, research note from the Q6B-19 walk-through (2026-11-07)
- **Decision owner** OWNER
- **Class** Migrate (architecture, roadmap parts 1 and 2)
- **Scope** LANGUAGE/COMPILATION, EXECUTION, DL-120, D017
- **Decision trigger** When a build must run without an Elixir toolchain, or when constructor performance is measured as a problem. Not a precondition for D017 (Q6B-19).

**[Proposal]** The idea: the COMPILER emits the pure core (constructors and every function they reach; DL-120 makes that core pure) as Rust, loaded into the BEAM as a NIF (Rustler). The `--stored` check then runs the same Rust code inside the compiler process. One semantics, no Elixir at build time.

**[Inference]** Against it: two code generators in one compiler (Elixir for pipes and EFFECTs, Rust for the core), so every shared form needs two emitters; a NIF call costs about 1 to 3 µs for term marshalling, and small pattern-matching clauses are often faster in Elixir; a native library per target platform (rustler_precompiled builds a matrix of 8 targets by 2 NIF versions); hot code upgrade of NIF libraries needs extra lifecycle care; NIF code is dark to BEAM tracing, which matters under a full-resolution OBSERVATORY setting (D018); the BEAM cannot preempt native code, so the core must stay short per call. For it: one semantics for build check and runtime, a fast in-process build check, no Elixir toolchain at build, deterministic replay. By: Fable (research, 2026-11-07).

**[Verified]** Sources read on 2026-11-07: Dashbit, "Introducing Rustler Precompiled" (dashbit.co/blog/rustler-precompiled); rustler_precompiled precompilation guide (hexdocs.pm/rustler_precompiled/precompilation_guide.html); localize performance guide on NIF boundary cost (hexdocs.pm/localize/performance.html); otter-nif crate docs on NIF lifecycle (docs.rs/crate/otter-nif/0.3.1); Fly.io, "Elixir and Rust is a good mix". Numbers are third-party, not measured on BEAML output.

**[Unknown]** Not built. No spike exists. The smallest spike: one constructor TYPE emitted as a Rustler NIF, the `--stored` check calling the same Rust function, one benchmark of `new/1` against the generated Elixir.

**[Proposal]** Options when the trigger fires: (1) keep the generated Elixir as the one backend and run the build check with it (D017 option b); (2) Rust NIF for the pure core as sketched; (3) a third form not yet named. The OWNER chooses.

## D020 — Does a MIGRATE STEP govern BEAML-owned persistence, or only RESPONSE RECORDS

- **Status** CLOSED, [DL-137](decision-log.md): option A, one `migrate` block for both streams, By: 13ue, 2026-11-07
- **Decision owner** OWNER
- **Class** Migrate (roadmap part 3)
- **Scope** EXECUTION, MIGRATE CHAIN, DL-102, DL-125
- **Decision trigger** Before BEAML owns any persistent store (table, document store, state), or before the fate syntax (DL-125) is used for anything but RESPONSE RECORDS.

**[Verified]** Today every stored record is a RESPONSE RECORD: one line per EFFECT call, written for the REPLAY RUN. A database is an EFFECT (`db.get(...)`), outside BEAML. BEAML owns no persistence, and data in a database is migrated by the host. The fate operations of DL-125 (`quarantine`, `retire`, `redact`, `map`) apply to RESPONSE RECORDS.

**[Proposal]** When BEAML owns persistence, the same `migrate T vN -> vM` block could govern both: replay records and stored state, with the same fates (a quarantined row is parked, a retired row is deleted after the keep window). Options then: one syntax for both; separate syntax for state; no BEAML-owned persistence. Raised in the OWNER walk-through of the fate concept (2026-11-07). By: Fable.

**[Unknown]** Not built. No persistence design exists.

**[Verified]** DL-127 (2026-11-07): the PROTOTYPE stores BEAML records in one JSONB table that BEAML owns. For those rows a MIGRATE STEP governs stored state. The question stays open for any other persistence form.

## D021 — The form of the ENTRY LINE (Q6D-1)

- **Status** CLOSED, [DL-130](decision-log.md): option E' (register option B, inbound like outbound), By: 13ue, 2026-11-07
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION, grammar, DL-126, DL-128
- **Decision trigger** Before slice 6d closes, or before the first ENTRY LINE outside EXPERIMENT 0004.

**[Verified]** DL-128 gives a sketch, not grammar: `on ui "place" Order -> place`. DL-126: a declaration carries shape and policy; the COMPILER derives the rest. Every source and the grammar carry the form. [Q6D-1](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/decisions.md#q6d-1--migrate--the-form-of-the-entry-line)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, `on` (slice default) | `on ui "place" PlaceOrder -> place`. Output and failure TYPE come from the fn. | New keyword `on`; the record `operation` is derived. |
| B, `effect` with body | `effect ui.place PlaceOrder -> Payment ! PaymentError = ui.event("place") \|> place`. | Output and failure TYPE stand twice and can drift; `effect` gets two body meanings. |
| C, `entry` | `entry ui.place PlaceOrder -> place`. | The event name comes from the dotted name; `place-order` cannot be written. |
| D, `effect in` | `effect in ui "place" PlaceOrder -> place`. One keyword for both directions. | `effect` gets two line forms; `in` becomes a keyword word. By: Opus (PLAN REPAIR, slice6d-inbound-effect). |

**[Unknown]** Not built. RED and GREEN build A. By: Opus (PLAN, slice6d-inbound-effect).

**[Proposal]** Next check: N1 and N14 of slice 6d under the chosen form. By: Opus (PLAN REPAIR, slice6d-inbound-effect).

## D022 — The generated function that the host calls (Q6D-2)

- **Status** CLOSED, [DL-131](decision-log.md): option A, one function per ENTRY LINE, By: 13ue, 2026-11-07
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** host call boundary, EXPERIMENT 0005, DL-128
- **Decision trigger** Before EXPERIMENT 0005 writes host code that calls an entry.

**[Verified]** Generated EFFECT functions follow `<kind>_<name>` today (`payments_authorize`). The host calls the entry from `handle_event/3` in EXPERIMENT 0005. [Q6D-2](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/decisions.md#q6d-2--migrate--the-generated-function-that-the-host-calls)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, one function per entry (slice default) | `Orders.ui_place(params)`; one host clause per event. | A deleted entry fails the host build only if the probe holds. |
| B, one dispatch | `Orders.entry("place", params)`; unknown event gives `Rejected{reason: "unknown_event"}`. | A renamed event fails at runtime only. |

**[Unknown]** Whether Elixir 1.18.1 with `--warnings-as-errors` reports a call to a deleted `ui_<event>` as an error. The RED worker of slice 6d probes it. By: Opus (PLAN, slice6d-inbound-effect).

**[Proposal]** Next check: that probe result. By: Opus (PLAN REPAIR, slice6d-inbound-effect).

## D023 — The form of a decode reject at the host (Q6D-3)

- **Status** CLOSED, [DL-133](decision-log.md): option A, a generated `Rejected` struct, By: 13ue, 2026-11-07
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** host call boundary, DL-101, DL-128
- **Decision trigger** Before EXPERIMENT 0005 matches on an entry result.

**[Verified]** The outbound EFFECT gives a decode reject as the failure TYPE with `reason` (`%PaymentError{reason: "decode"}`). A fn without `!` has no failure TYPE. [Q6D-3](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/decisions.md#q6d-3--migrate--the-form-of-a-decode-reject-at-the-host)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, `Rejected` struct (slice default) | `{:error, %BeamlSpike.Rejected{reason: "decode" \| "constructor"}}`. | A generated TYPE name is reserved next to an entry (D6B-138). |
| B, failure TYPE of the fn | `%PaymentError{reason: "decode"}`. | The UI cannot tell a bad event from a bad response; fails for a fn without `!`. |
| C, plain tuple | `{:error, {:rejected, "decode"}}`. | Not a TYPE; a host pattern on structs misses it. |

**[Unknown]** Not built. RED and GREEN build A. By: Opus (PLAN, slice6d-inbound-effect).

**[Proposal]** Next check: N4 and N6 of slice 6d under the chosen form. By: Opus (PLAN REPAIR, slice6d-inbound-effect).

## D024 — Stored ENTRY RECORDS and the DL-102 build check (Q6D-4)

- **Status** CLOSED, [DL-134](decision-log.md): option A, `--stored` also checks ENTRY RECORDS, By: 13ue, 2026-11-07
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION, `--stored`, DL-102, DL-122, D020
- **Decision trigger** Before slice 6d closes, or before an input TYPE of an ENTRY LINE changes a constructor or an ENUM LITERAL while ENTRY RECORDS are stored.

**[Verified]** D6B-130 allows constructor TYPES and enums in the fields of the input TYPE. DL-102 and DL-122: a stored record that fails a new rule, or loses its literal, blocks the build. `--stored` reads only RESPONSE RECORDS. **[Inference]** A changed `Amount` constructor or a lost `Channel` literal makes a stored ENTRY RECORD fail at REPLAY RUN only; the build does not block (plan check O2). [Q6D-4](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/decisions.md#q6d-4--migrate--stored-entry-records-and-the-dl-102-build-check), [plan check](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/plan-review.md)

**[Proposal]** Options:

| Option | Meaning | Trade-off |
|---|---|---|
| A, `--stored` reads entries | `--stored` also reads `entries.jsonl` and runs the field constructors and literals of the input TYPE. DL-102 covers ENTRY RECORDS. | New build input; more GREEN work in 6d. |
| B, interim gap (slice default) | No build check over ENTRY RECORDS in 6d; the gap is labelled interim (D6B-146). | Against DL-102 until the answer; failures show at REPLAY RUN only. |

**[Unknown]** Not built. Evidence for the gap: the N9 constructor case of slice 6d. By: Opus (PLAN REPAIR, slice6d-inbound-effect).

**[Proposal]** Next check: under A, a stored ENTRY RECORD with currency `""` gives build exit 1; under B, the exclusion label stays. By: Opus (PLAN REPAIR, slice6d-inbound-effect).

## D025 — A second declaration form with `=` and `|` for `enum` and `type`

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION, grammar, formatter, DL-126
- **Decision trigger** Later; a pure syntax question with no slice behind it. Raised by the OWNER on 2026-11-07 after a main-agent sketch used `enum Channel = Web | App` and `type PlaceForm = { amount: Amount, channel: Channel }`.

**[Verified]** Today the grammar has one form: `enum Channel { Web  App  Unknown(String) }` and `type Amount { value: Int }`; whitespace separates variants and fields, commas are optional. The `=` and `|` forms came from the sketch, not from the language. DL-132 settled comments the same way.

**[Proposal]** Options: A, keep one form (today); B, allow the `=` and `|` form as a second spelling that `fmt` rewrites to the brace form; C, replace the brace form with the `=` and `|` form. A second spelling adds a grammar rule, a formatter rule and a second way to read every source; the OWNER weighs that against readability.

**[Unknown]** Not built, not asked in a slice. By: Fable (note for the OWNER).

## D026 — Absent-value form: `Option`-like TYPE, optional field or enum idiom

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** After the first example applications are built.
- **Next check** When the first example application is planned.

**[Proposal]** Question: Does BEAML need an absent-value form, and how does it meet the historical S06 "missing vs explicit null" requirement? Candidate from the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#8-candidate-open-decisions), accepted as an open question by the OWNER on 2026-11-07 ([DL-145](decision-log.md)). No option is recommended.

**[Verified]** Evidence: [hated row 1](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) (null references), [loved row 4](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) (ergonomic null handling).

**[Verified]** BEAML today: no `Option`, `nil` or optional field; `Unknown(String)` is the keep-value idiom ([checklist](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#5-feature-checklist), DL-062).

## D027 — Failure-list ripple: a new failure TYPE on a deep `effect`

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** After the first example applications are built.
- **Next check** When the first example application is planned.

**[Proposal]** Question: When a deep `effect` gains a failure TYPE, must every caller's `!` list change? Is that ripple accepted or softened (generic `-> T ! E`, failure groups)? Candidate from the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#8-candidate-open-decisions), accepted as an open question by the OWNER on 2026-11-07 ([DL-145](decision-log.md)). No option is recommended.

**[Verified]** Evidence: [hated row 11](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) (checked exceptions, versionability), [loved row 3](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) (errors as values).

**[Verified]** BEAML today: a failure not in the enclosing `!` list is a compile error (DL-015, DL-093); generic `-> T ! E` is "for later" (DL-093).

## D028 — String interpolation: `#{...}` stays literal text, or a checked form

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** After the first example applications are built.
- **Next check** When the first example application is planned.

**[Proposal]** Question: Does `#{...}` stay literal text permanently, or does BEAML get a checked interpolation form? What is the recorded reason either way? Candidate from the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#8-candidate-open-decisions), accepted as an open question by the OWNER on 2026-11-07 ([DL-145](decision-log.md)). No option is recommended.

**[Verified]** Evidence: [loved row 16](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) (string interpolation).

**[Verified]** BEAML today: `#{...}` stays data; concatenation with `+`, the only operator ([checklist](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#5-feature-checklist), EXPERIMENT 0001 acceptance 6). The reason is not recorded as a decision.

## D029 — Collection TYPES and literals: list, map

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** After the first example applications are built.
- **Next check** When the first example application is planned.

**[Proposal]** Question: Which collection TYPES and literals does BEAML get, and in what form, given DL-129 already needs a `List` TYPE? Candidate from the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#8-candidate-open-decisions), accepted as an open question by the OWNER on 2026-11-07 ([DL-145](decision-log.md)). No option is recommended.

**[Verified]** Evidence: [loved row 11](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) (comprehensions), [hated row 21](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) (missing sum types and `Option` in Go).

**[Verified]** BEAML today: no list or map TYPE or literal; DL-084 "lists later"; DL-129 needs a `List` for `Orders` ([checklist](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#5-feature-checklist)).

## D030 — Anonymous-function form

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** After the first example applications are built.
- **Next check** When the first example application is planned.

**[Proposal]** Question: Does BEAML get an anonymous-function form, or do top-level clauses remain the only functions? How are `map` and `filter` then written? Candidate from the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#8-candidate-open-decisions), accepted as an open question by the OWNER on 2026-11-07 ([DL-145](decision-log.md)). No option is recommended.

**[Verified]** Evidence: [loved row 10](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) (closures, lambdas, first-class functions).

**[Verified]** BEAML today: functions exist only as top-level clauses ([checklist](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#5-feature-checklist)). Depends on D029.

## D031 — BEAM concurrency in syntax: spawn, receive, task

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** After the first example applications are built.
- **Next check** When the first example application is planned.

**[Proposal]** Question: Does BEAML expose BEAM concurrency in syntax, and would such a form stay uncolored? Candidate from the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#8-candidate-open-decisions), accepted as an open question by the OWNER on 2026-11-07 ([DL-145](decision-log.md)). No option is recommended.

**[Verified]** Evidence: [loved row 13](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) (lightweight concurrency), [hated row 5](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) (async function coloring).

**[Verified]** BEAML today: no spawn, receive or task form; BEAM processes named only for termination (DL-025) ([checklist](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#5-feature-checklist)). The `!` and `effect` split is a deliberate two-color system (DL-120).

## D032 — Optional separators and zero-argument variant spelling

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** After the first example applications are built.
- **Next check** When the first example application is planned.

**[Proposal]** Question: Do optional separators between fields and variants stay? Is bare `Pending` next to `Approved()` one spelling or two? Candidate from the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#8-candidate-open-decisions), accepted as an open question by the OWNER on 2026-11-07 ([DL-145](decision-log.md)). No option is recommended.

**[Verified]** Evidence: [hated row 25](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) (silent adjacent concatenation), [profile gap list](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#6-gaps-noticed-in-the-kb-for-the-synthesis-worker).

**[Verified]** BEAML today: commas between fields and variants are optional; slice 6 fixtures write `Pending` and `Approved()` side by side with no decision ([profile 1.1, 1.3](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#1-what-beaml-looks-like-today)). **[Unknown]** whether a silent misparse exists.

## D033 — Budget for top-level forms: keywords, modifiers, mark kinds

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** After the first example applications are built.
- **Next check** When the first example application is planned.

**[Proposal]** Question: Is there a budget for top-level forms, and who counts against it when `on`, the FATE OPERATIONS and `effect` policies arrive? Set the budget before these forms land? Candidate from the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#8-candidate-open-decisions), accepted as an open question by the OWNER on 2026-11-07 ([DL-145](decision-log.md)). No option is recommended.

**[Verified]** Evidence: [hated row 4](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) (complexity creep, 28 % of Rust respondents), [loved row 22](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) (small language, one way).

**[Verified]** BEAML today: six top-level keyword forms (`type`, `enum`, `fn`, `effect`, `migrate`, `retire`) plus `redacted`, `with` release, `with ... do`, VERSION MARK; sketched: `on`, four FATE OPERATIONS, policy on `effect` lines, `where` rules (DL-125, DL-126, DL-128). No budget is recorded ([scorecard](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md#2-scorecard)). The conservative syntax minimum proposes a ceiling of 39 with one-in-one-out; see D050 and the [syntax minimum hub](syntax-minimum.md).

## D050 — Which syntax minimum does BEAML adopt

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** LANGUAGE/COMPILATION
- **Decision trigger** OWNER review of the syntax minimum hub; before the next syntax DL.
- **Next check** When the next syntax decision is proposed.

**[Proposal]** Question: Which syntax minimum does BEAML adopt: the agreed 39-item set (D032 only), the conservative set with growth rules, or the radical set that reopens DL-014, DL-015, DL-022, DL-055, DL-061? Raised by the OWNER on 2026-11-08 ("really only the minimum of syntax", [DL-169](decision-log.md)). Two independent proposals and one compare page exist; no option is recommended.

**[Verified]** Evidence: the [syntax minimum hub](syntax-minimum.md) (one inventory of 40 items, the agreed set, the differences, the OWNER questions), the [conservative minimum](syntax-minimum-conservative.md) (38 proposed, ceiling 39, six growth rules), the [radical minimum](syntax-minimum-radical.md) (29 proposed, four top-level forms, six reopened decisions), the [syntax sentiment concept](../concepts/syntax-sentiment.md) sections [1](../concepts/syntax-sentiment.md#1-question) to [10](../concepts/syntax-sentiment.md#10-terraform-hcl-as-the-declarative-precedent), and the open items D032 (separators, zero-argument variant) and D033 (form budget) above.

**[Verified]** BEAML today: 40 syntax items by the hub's unit, 6 top-level forms; the compiler and the grammar disagree on the comma between MIGRATE CHANGES ([hub section 6](syntax-minimum.md#6-what-both-pages-miss)). **[Unknown]** Token cost and error rate for agent-written code under each set; no measurement exists.

## D034 — Keep the name BEAML next to BAML, or change it

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** Positioning, repository name, package names, documentation
- **Decision trigger** Before the first public release or external announcement.
- **Next check** When a public repository, package or talk is planned.

**[Proposal]** Question: Keep the name BEAML next to BAML, or change it, given the name proximity and the shared design space? Raised by the OWNER on 2026-11-07 when BAML was taken up in the syntax sentiment research ([DL-146](decision-log.md)). No option is recommended.

**[Verified]** Evidence: the [name proximity facts](../../raw/research/2026-11-07-baml-syntax-sentiment/baml-reception.md#6-name-proximity-baml-and-beaml). BAML is "Basically A Made-up Language" per its README, "tongue-in-cheek" per the team; third parties expand it as "Boundary AI Markup Language"; BAML also named a bank brand until 2019 and a WPF markup format. No project, package or page named `beaml` exists on GitHub, PyPI, npm, Hex or in web search. BEAML is BAML plus one letter and contains "BEAM". Both are typed languages for agent software with a Rust toolchain, typed LLM functions, exhaustive `match`, typed errors and telemetry by default ([shared design space](../sources/baml-v1.md#beaml-relevance)).

**[Inference]** Search collision runs one way today: a search for BEAML returns BEAM and BAML results. Whether proximity reads as "a BAML fork" (cost) or "BAML, but on the BEAM" (positioning) is the OWNER's call ([scorecard of what BAML already chose](../../raw/research/2026-11-07-baml-syntax-sentiment/baml-reception.md#4-scorecard-against-the-loved-and-hated-rows)).

**[Unknown]** Pronunciation of BAML; trademark status of BAML and BEAML (no register searched); whether a reader confuses the two in practice. By: Fable (INGEST, baml-reception).

## D036 — RED TEAM 01 questions M3, M4, M5, M8, M9 (parked by the OWNER; M3 DL-160, M4 DL-152, M5 DL-163 answered 2026-11-08)

- **ID note** first written as D026 by mistake (D026 is the absent-value form); renamed D036 the same day, references in the 0005 and P2/P4 ledgers updated.
- **Status** OPEN, parked 2026-11-07 by the OWNER ("later, in detail"); M1, M2, M6, M7 are answered (DL-136, DL-140, DL-139, DL-135). M4 is answered (DL-152, 2026-11-08); M3, M5, M8, M9 stay open.
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** fate forms (DL-125, DL-137, DL-140), the DL-102 help text, the host value rule, block text size
- **Decision trigger** Before the fate slice starts (M3, M4, M5) and before the record format v3 step (M8, M9). The main agent opens each as its own question with a picture (DL-139 rule).

**[Verified]** Options and evidence: [red team report](../../experiments/0004-generated-replay/workflow/2026-11-07/red-team-01/report.md), Migrate list. M3 needs a fresh explanation of DL-116 for the OWNER (asked for on 2026-11-07).

**[Verified]** M4 answered by [DL-152](decision-log.md) (D6B-39 lifted, B2). Step 1 is built in [m4-lift-d6b39](../../experiments/0004-generated-replay/workflow/2026-11-08/m4-lift-d6b39/review.md), GREEN `26b73524`, TEST PASS: a chained TYPE holds enum and constructor fields, the MIGRATE STEPS run before the literal map and constructor checks. A MIGRATE STEP that names such a field stays an error until M3 (fate forms, DL-116) and the `map` step of DL-140. N9 now waits on M3 only (DL-153). By: Opus (m4-lift, docs).

## D035 — P2b: the DL-136 digest half for stored records

- **Status** CLOSED 2026-11-08: A, DL-164 (step P2b after fates-a1)
- **Decision owner** Fable and workers under DL-144 (free run)
- **Class** Repair
- **Scope** `--stored` over RESPONSE RECORDS and ENTRY RECORDS
- **Decision trigger** Before EXPERIMENT 0005 TEST.
- **Next check** At the record format v3 (P2) TEST commit.

**[Proposal]** Question: Build the second half of [DL-136](decision-log.md): a stored record with a bad `value_sha256` is counted and not checked, for both streams. P2 (record format v3) builds only the `outcome` half. Until P2b lands, the P2 count line is followed by `digest not verified (P2b)`. Ledger: [record-format-v3 plan repair](../../experiments/0004-generated-replay/workflow/2026-11-07/record-format-v3/plan.md#plan-repair-after-plan-check-2026-11-07) (RV3-07, RV3-15). By: Fable (ruling O3 under DL-144).
- **[Inference]** Carried from slice 6d TEST O3: R1, a captured reject that a looser rule accepts now, is not reported; one test covers both streams. Ledger: [slice 6d review](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/review.md) (O3). By: Fable (ruling O3 under DL-144).
- **[Observed]** Carried from slice 6d TEST O3: `check_entries` does not verify `value_sha256` of a stored ENTRY RECORD (the C5 gap of the ENTRY stream); `Replay.entry` rejects a bad digest. Ledger: [slice 6d review](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/review.md) (O3). By: Fable (ruling O3 under DL-144).

## D037 — EXPERIMENT 0005 built defaults (DL-144 walk-through)

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** every built default of EXPERIMENT 0005 and its prerequisites P2 to P5, P4c and slice 6d: 19 big lines in 9 groups, 35 other lines, 6 parked lines
- **Decision trigger** the walk-through on 2026-11-08
- **Next check** after each OWNER answer: one DL entry per signed-off line (DL-139 sign-off rule)

**[Proposal]** Walk through [the OWNER review list](../../experiments/0005-prototype-fullstack/workflow/2026-11-07/owner-review.md), big items first: M4 (D036, critical path), the host-called `Orders.__beaml_encode_order/1`, Q5-10, Q6E-1/Q6E-2, QDB-6b/QDB-8, QV3-1 to QV3-8, the count-line print rule, the row shape check P4c, G6D-03/G6D-04. Every default stays as built until the OWNER signs it off. D035 and D036 stay separate entries. By: Opus (docs exp0005).
**[Verified]** Evidence: 0005 TEST PASS ([review](../../experiments/0005-prototype-fullstack/workflow/2026-11-08/review.md), O1 to O3 medium, open) and [run 20261108T003740313204Z](../../experiments/0005-prototype-fullstack/results/20261108T003740313204Z/result.json).

## D038 — Line length and line breaks inside a clause

- **Status** OPEN
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** the clause table of DL-148: may a clause break across lines, or does the language set a maximum line length (the OWNER named 120 as an example) and forbid breaks inside a clause?
- **Decision trigger** the first EXPERIMENT with longer functions
- **Next check** when such a function appears

**[Proposal]** Raised by the OWNER on 2026-11-08 together with DL-148: a hard maximum would force a style of short clauses; a break rule keeps the table readable. Not decided; the current `fmt` keeps multi-line clauses as written (D6B-44).

**[Verified]** Evidence from the [fmt layout review](../../experiments/0004-generated-replay/workflow/2026-11-08/fmt-layout/review.md) (2026-11-08, By: Opus (fmt-layout, review)): the CLAUSE TABLE counts bytes, not characters. A row with the argument `"ä"` stands 1 column left on screen, `"äöü"` 3 columns (O2). No tracked source is affected today. One block-wide table also widens lines: 19 of 83 changed sources have a line over 120 characters after `fmt`, 17 before (O3). The width unit and the maximum line length belong to this decision.

## D039 — How a REDACTED FIELD is stored in the records

- **Status** OPEN (idea, raised by the OWNER on 2026-11-08 during the D037 walk-through)
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** the ENTRY RECORDS, RESPONSE RECORDS and STORED ROWS keep, beside the real state in the database, the values that led there; a REDACTED FIELD must not be readable there. A configuration with a safe default decides the form.
- **Decision trigger** the first REDACTED FIELD in an EXPERIMENT source, or the slice that builds DL-151 (live `--stored`)
- **Next check** when the redaction syntax (DL-127 wording) gets its first step

**[Proposal]** Two forms, by the OWNER:
- **Option 1, the default: hash.** The record keeps a hash of the value. A later check can confirm "this value was entered here" without anyone reading it. Note for the plan (Fable): a plain hash of a low-entropy value (an e-mail, a name) is guessable by a dictionary; the step needs a keyed or salted hash, with the key handled like every secret (inside a process only).
- **Option 2, not the default: encrypt.** The value is encrypted with a server secret and can be made readable for an emergency. The OWNER names this the form that does not respect privacy; it exists as an explicit setting only.
- Open points for the plan: the setting's place (source line, build flag or host config), whether `value_sha256` (record format v3) is computed over the redacted form, what `--stored` compares for such a field (DL-151 keeps it redacted), and what a REPLAY RUN does with it.

## D040 — Visibility: what a module hides from the host

- **Status** OPEN (idea, raised by the OWNER on 2026-11-08 with DL-154)
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** a BEAML module should be able to keep a TYPE, a field or the whole module internal, so that nothing of it reaches the host or leaves the module by accident. Open: is this declared on the TYPE, on the field, or on the module; what the default is (the OWNER wants a sensible default and explicit opt-in to expose); how it relates to the REDACTED FIELD (DL-059) and to the public projection of DL-154.
- **Decision trigger** the plan of the DL-154 step (public projection), at the latest the first EXPERIMENT with a second module
- **Next check** when that plan is written

**[Proposal]** Sketch for the plan, not decided: three levels to compare: module-level `private`, TYPE-level, field-level; and a default where nothing is projected unless the TYPE opts in. By: Fable (note of the OWNER's voice note).

## D041 — Remove the ENUM CONSTRUCTOR; enums decode by ENUM LITERALS only

- **Status** OPEN (language simplification team round, candidate 2, 2026-11-08)
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** today a `fn` named like an `enum` maps outside Strings to variants with logic (DL-082, DL-100). Proposal: only the literal table says which String is which variant; `fn <Capital>` always means a record constructor. Possibly a multi-literal form `Web = "web" | "WEB"` (sketch, not built).
- **Decision trigger** before the fate slice touches enum decoding, or when a real provider needs two spellings
- **Next check** the paper check in [synthesis.md](../../experiments/0005-prototype-fullstack/workflow/2026-11-08/language-simplification/synthesis.md) candidate 2

**[Proposal]** Options: A literals only, normalisation in the parent record constructor · B literals plus a multi-literal form · C keep DL-082. Lost under A/B: mapping with logic, Int to variant; 9 enums use a constructor today, all fixtures, none in 0005. Gain: DL-122 and DL-140 become a diff of two literal tables (DL-155). The OWNER saw the proposal on 2026-11-08 and asked for it to be shown; not decided.

## D042 — Lazy recheck of a rule over a REDACTED FIELD (M3 follow-up)

- **Status** OPEN, narrowed 2026-11-08: the "redacted only on versioned constructor TYPES" half is decided as DL-160; M3 closes as A; open here is only the form of the lazy recheck outcome
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** a redacted value is absent from records, so the build cannot check a stricter rule over it. With DL-155 the stricter rule is a new TYPE VERSION; old values are `T v1`. Idea: the check runs lazily where the value exists (the host app, on read or re-entry), declared by a fate line (`recheck f`, sketch). Totality end to end: the compiler lists every place the outcome "old value fails the new rule" can reach (ENTRY LINE, generated function, page, replay, records, observability) and the host must handle it.
- **Decision trigger** the first redacted field with a rule in an EXPERIMENT, or the fate slice plan
- **Next check** the fate slice plan

**[Proposal]** Open form of the outcome: A an own state in the TYPE, visible in every signature (`Stale(T)` or the version itself, `T v1 | T v2`) · B a reject reason in `! StoreError` per call (the list breaks, see DL-150). The OWNER's answer to "old row fails on read": value comes back with a mark, never a crash, never a silent skip (leans to A). Also open: whether `redact` may ever skip a rule (M3 D3): the OWNER leans to "no; DL-116 leaves the fate list" (A), to be confirmed.

## D043 — Build order: fate slice before or after live `--stored`

- **Status** CLOSED 2026-11-08: A, DL-156
- **Decision owner** OWNER
- **Class** Repair (order of work), listed because both slices need the compiler
- **Scope** A fate slice first (grammar for the four fate lines and `map`, the three blocks lifted by a fate line, REPLAY RUN skips quarantined values, 0005 N9 as the use case, DL-155 gate in `--stored`) · B live `--stored` (DL-151) first, then the fate slice.
- **Decision trigger** now
- **Next check** OWNER answer on the walk-through page "M3: Fate-Formen", card FATE-NEXT

## D044 — One contract construct instead of Protocols and Behaviours

- **Status** OPEN (roadmap, OWNER 2026-11-08)
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** a single, simple interface construct: a contract declared once, implemented by TYPES or modules; the compiler maps it to Elixir Protocol or Behaviour as needed. Open: dispatch, generics in contracts, naming.
- **Decision trigger** the first EXPERIMENT that needs two implementations of one operation
- **Next check** a concept page with three worked examples before any syntax

## D045 — Generics (type variables)

- **Status** OPEN (roadmap, OWNER 2026-11-08)
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** type variables after accepted standards; where they appear (TYPE, fn, EFFECT, contract), inference vs annotation, interaction with TYPE VERSIONS, the record format (`type: {name, version}` for a `List(Order)`?) and the LIST TYPE `[T]` already built.
- **Decision trigger** the first EXPERIMENT with a reusable container or operation
- **Next check** compare three standards on paper against `OrderList { items: [Order] }`

## D046 — Async compute: OTP and Oban from BEAML

- **Status** OPEN (roadmap, OWNER 2026-11-08)
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** processes, supervision, state and timers from BEAML; Oban as the job library (a job as an EFFECT with an `oban` transport, attempts as records, retries and uniqueness as declared lines). Open: BEAML vs host ownership, TYPE VERSION and trace on a job, replay of a job.
- **Decision trigger** the first EXPERIMENT that needs background work
- **Next check** a concept page; the register of transports (http, db, ui) gets a candidate row

## D047 — Totality and let it crash: the explanation

- **Status** OPEN (roadmap, OWNER 2026-11-08); concept page drafted as [Proposal]
- **Decision owner** OWNER
- **Class** Repair (documentation), Migrate if it changes a rule
- **Scope** how BEAML's totality over stored data sits beside the BEAM's let-it-crash. See [the concept page](../concepts/totality-and-let-it-crash.md).
- **Decision trigger** the first external reader; before the public pages claim either word
- **Next check** OWNER reads the page

## D048 — EXPERIMENT 0005 as the living REFERENCE APP and end-to-end desk

- **Status** CLOSED 2026-11-08: A, DL-158; the desk stages (telemetry, dashboard, CLI, bench) stay open sub-items here (OWNER idea, 2026-11-08, [capture](../../raw/requirements/2026-11-08-owner-ideas-reference-app.md))
- **Decision owner** OWNER
- **Class** Migrate (changes how experiments are run and reported)
- **Scope** 0005 is upgraded with every slice and stays the standing example; a local end-to-end desk covers database, BEAML module, LiveView, telemetry, live dashboard and CLI; the desk is used to try, feel and benchmark against the speed promises.
- **Decision trigger** now (the fate slice is the first that would land in it)
- **Next check** OWNER answer on the main agent's proposal (below)

**[Proposal]** (Fable) A: 0005 becomes the REFERENCE APP: every slice ends with its use case landed in the app (`run.py run` grows), the register marks it "living", results stay per run; telemetry = the records plus OpenTelemetry spans to a local collector and a live dashboard page; a `beaml` CLI wraps build, `--stored`, fmt and replay; a `bench` step records build time, decode time per row and page latency into the results. B: keep 0005 frozen as the slice-5 proof and start 0006 as the living app. Options for the OWNER.

## D049 — PubSub and sockets as hard-typed EFFECTS

- **Status** OPEN (roadmap, OWNER 2026-11-08, [capture](../../raw/requirements/2026-11-08-owner-ideas-pubsub-sockets.md))
- **Decision owner** OWNER
- **Class** Migrate
- **Scope** Phoenix.PubSub topics, channels and LiveView socket events as EFFECTS with typed messages: a topic carries one BEAML TYPE (or an enum of message TYPES), publish is an outbound EFFECT, subscribe/receive is an inbound ENTRY LINE like `ui.event`, socket pushes are outbound. Every message is a record in the streams (format v3), replayable; TYPE VERSIONS apply to messages in flight (an old subscriber reads a new message: the MIGRATE CHAIN on read, as for rows). Tackled with D046 (OTP, GenServer).
- **Decision trigger** the first EXPERIMENT with a second process or a live update on a page (the 0005 orders list updating on a new order would be the smallest case)
- **Research first (OWNER)** study Gleam: `gleam_otp` and `gleam_erlang` (typed `Subject(msg)`, actors, selectors, supervision) as the closest prior art for hard-typed messages on the BEAM; source page with excerpts and limits before any BEAML form.
- **Next check** a concept page sketch: `effect orders.changed Order -> Order ! PubError = pubsub.publish("orders")` and `effect ui.live Order -> Order ! … = pubsub.subscribe("orders") |> refresh` as forms to compare (sketch, not built)

**[Proposal]** Smallest 0005 case: `/orders` refreshes when another session places an order; one topic, one TYPE, records for publish and receive, the trace spans both. Open: what "hard typed" means for a topic shared by two modules (D040, D044), and backpressure (event-flows page).

## Answered 2026-11-07

- [DL-141](decision-log.md), [DL-142](decision-log.md), [DL-143](decision-log.md): ENTRY RECORD format signed off (two outcome keys, both unknown lists, one format for every stream with a later alignment step).
- [DL-140](decision-log.md): M2, a known-to-known variant change blocks; a `map` MIGRATE STEP is forced (A).
- [DL-139](decision-log.md): M6, a slice may build and pin a Migrate default, except syntax and record formats (B with a limit).
- [DL-137](decision-log.md): D020, one `migrate` block governs RESPONSE RECORDS and database rows (A).
- [DL-136](decision-log.md): M1, `--stored` checks only replayable records; non-200 and bad digest are counted (A).
- [DL-135](decision-log.md): M7, the DRIFT status pins classes; crash, build failure, open repair are fail (A).
- [DL-134](decision-log.md): Q6D-4, `--stored` also checks stored ENTRY RECORDS (A).
- [DL-133](decision-log.md): Q6D-3, a decode reject is a generated `Rejected` struct (A).
- [DL-131](decision-log.md): Q6D-2, the host calls one generated function per ENTRY LINE (A).
- [DL-130](decision-log.md): Q6D-1, the ENTRY LINE is an `effect` line with head TYPEs, inbound like outbound (E').
- [DL-099](decision-log.md): Q6B-1, enum constructor inputs come from the field's own value.
- [DL-100](decision-log.md): Q6B-2, an enum constructor is the decode path only.
- [DL-101](decision-log.md): Q6B-3, the decode of outside data calls the record constructor.
- [DL-102](decision-log.md): replay rule, a stored record that fails a new rule blocks the build until a MIGRATE STEP declares its fate.
- [DL-103](decision-log.md): replay rule, a mapping change that only resolves Unknown values needs no MIGRATE STEP.
- [DL-117](decision-log.md): Q6B-16, `T.new/1` takes one map with atom keys, also for one parameter.
- [DL-129](decision-log.md): PROTOTYPE, Postgres through three fixed transports `db.put`, `db.get`, `db.list` (T).
- [DL-128](decision-log.md): PROTOTYPE, the UI event enters BEAML through a declared inbound EFFECT (b).
- [DL-127](decision-log.md): PROTOTYPE, Postgres holds BEAML records in one JSONB table, BEAML owns the rows (J).
- [DL-125](decision-log.md): fate concept, declarative fate operations in the MIGRATE STEP; expressions only on a real case.
- [DL-122](decision-log.md): Q6B-8, a removed or changed ENUM LITERAL with stored values blocks the build (interim).
- [DL-121](decision-log.md): Q6B-19, the `--stored` check runs the generated Elixir constructor over the stored values.
- [DL-120](decision-log.md): Q6B-18, a constructor is pure; reaching an EFFECT is a compile error.
- [DL-119](decision-log.md): Q6B-17, span default is the EFFECT path per step (S); the resolution becomes an OBSERVATORY setting (D018).
- [DL-104](decision-log.md): Q6B-5, `beaml fmt` never changes the TYPE VERSION.
