---
id: planning-decisions-to-be-made
kind: planning
status: active
updated: 2026-11-06
---

# Offene Fragen / Decisions to be made

Record open R&D decisions with a stable ID, owner, evidence and next check.
Keep each decision OPEN until the owner records a choice and its reason.
See [specification gaps](specification-gaps.md) for the historical specification review.

## D001 — Enum or type declarations

- **Status** CLOSED 2026-11-06: `type` for records, `enum` for variants. See [DL-061](decision-log.md) (supersedes DL-060).
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
