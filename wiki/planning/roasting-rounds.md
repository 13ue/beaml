---
id: planning-roasting-rounds
kind: review-record
status: open-objections
updated: 2026-11-07
---

# BEAML roasting rounds

The [conversation source](../sources/roasting-rounds.md) records provenance and coverage limits.
These are architecture challenges, not release gates or findings of proven implementation failure.
Human dispositions remain pending unless an explicit decision is recorded below.

## Round 1: reduce the first slice

**[Inference]** The initial slice risked combining too many unsettled concerns before producing useful evidence.
The review also questioned syntax readiness and missing evidence against a plain Elixir-library alternative.
The original full response is unavailable here; no exact severity or complete objection list is reconstructed.

**[Requirement]** The owner then selected a minimal syntax spike and later adopted the initial Elixir backend.
The [syntax source](../sources/syntax-spike-requirement.md) records those separate decisions.
**[Verified]** [EXPERIMENT 0001](../../experiments/0001-syntax-to-beam/README.md) provides evidence for that smaller subset.
It does not establish a workflow benefit over an Elixir library.

**[Proposal]** Resolve the remaining value question with a shared workflow and explicit comparison criteria.
Compare prevented failures and authoring effort. Do not assume either implementation is superior.
Disposition of the broader language-value objection: pending. Disposition rationale: null.

## Round 2: one guarantee across the boundary

**[Proposal]** Central question: which concrete error does BEAML prevent from foreign input to the first domain effect?
Does that guarantee justify the cost of a separate language?

Category: premise and scope. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The POC checks exact shapes and nested patterns and executes generated code on the BEAM.
Its [documented limits](../../experiments/0001-syntax-to-beam/README.md#evidence-and-limits) exclude EFFECT support, provider calls and full typed replay.
The [product CONTRACT](../concepts/product-contract.md#trust-transitions-are-explicit) requires rejected input to cause no domain effects.

**[Inference]** More syntax could extend the compiler without testing that cross-boundary requirement.
This is a gap between current evidence and the product target, not a failure of EXPERIMENT 0001's criteria.

### Proposed invariant and smallest resolving test

**[Proposal]** Within a declared controlled boundary, no domain effect occurs before all required input checks pass.
A VALIDATED VALUE certifies only its named checks. Shape alone proves neither authority nor factual truth.

Use one simulated effect with a call counter:

1. Valid input produces exactly one call.
2. Nested invalid input produces zero calls.
3. The public Elixir entry point preserves both results.
4. Prevent a known bypass or explicitly exclude it from the declared guarantee.

Passing these cases would provide scoped evidence, not a general proof or a language-value comparison.
**[Unknown]** This proposed EXPERIMENT has not been adopted, implemented or run.
Its controlled boundary and required checks still need definition.

### Deliberately not challenged

The accepted syntax and initial Elixir backend remain in place. The review supplied no new reason to reopen them.
No complete code audit or new runtime test was performed during this round.

## Follow-up

### Round 2 clarification: product value is a separate question

**[Verified]** In follow-up discussion, the AUTHORING AGENT corrected its framing of the boundary invariant.
That test alone cannot justify a language; an Elixir library could provide boundary checks too.
The original review remains above as history. No human disposition is inferred from this correction.

**[Requirement]** The owner asks for a concrete product-benefit test and describes a BAML talk about instrumentation growth.
The [follow-up source](../sources/roasting-rounds.md) records the description and its limits.
**[Proposal]** Compare small application functions with equivalent typed failure evidence and source-linked observations.
The [product-benefit probe](product-benefit-probe.md) defines a bounded workflow, fair Elixir comparison and change test.
The proposal is not adopted or executed. The product-value objection remains pending.

**[Proposal]** Select the next EXPERIMENT through the [R&D register](research-and-development.md).
Keep the proposed invariant, executed results and owner decisions separate.
Add later rounds as new records; preserve the original conversation capture.

## Round 3 — Test the competitive claim (2026-11-05)

Spec mode. Target: BEAML's current evidence, the proposed first REPLAY RUN and the claim of a 3–8× advantage over BAML.
The strongest case for BEAML is one checked CONTRACT across a model result, an HTTP boundary and failure evidence.
It could reduce repeated work in Elixir applications that use model output for domain decisions.
See the [conversation and research capture](../../raw/requirements/2026-11-05-roasting-round-3.md).

| Evidence | LANGUAGE/COMPILATION | Host and OBSERVATORY | Result |
|---|---|---|---|
| [0001](../../experiments/0001-syntax-to-beam/results/20261105T202319485083Z/result.json) | Generate Elixir checks for exact shapes and nested patterns | Compile and run the output on the BEAM | Compiler, CLI and BEAM tests passed |
| [0002](../../experiments/0002-http-correlation/results/20261105T221134010042Z/result.json) | Generate three checked fixture functions | Orders → HTTP → Payments. Elixir propagates context, records observations and serves a fixed payment response. | H01–H05 passed, including missing context and missing log controls |
| Proposed next test | Derive validation, typed outcome and capture/replay metadata from one declared boundary | Elixir performs HTTP and capture. A test runner substitutes captured outcomes and counts calls. | Pending |

### 1. The 3–8× claim has no denominator

Category: premise, scope and specification quality. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The [owner's thesis](../../raw/requirements/2026-11-05-roasting-round-3.md) includes breadth in the comparison.
The [R&D register](research-and-development.md) reports no head-to-head result.
**[Inference]** Counting compiler, provider and operations features rewards inventory. It can hide slower changes and more integration work.
A team can add scope and still lose its most important task against a smaller tool.
**[Proposal]** Name the user, workflow and primary measure before the test. Keep coverage and correctness separate from the time ratio.

### 2. BAML is a moving baseline with overlapping features

Category: premise and alternatives. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The established BAML v0 changelog records 0.226.3 on 2026-10-27. Its documentation covers typed structured output and streaming, retries and fallback, tests and per-attempt observations.
The newer language line separately documents typed errors, concurrent tasks and SQL queries over recorded telemetry.
GitHub lists the 0.23.1 nightly series. These are separate observations about docs and release lines.
See the [versioned source details](../../raw/requirements/2026-11-05-roasting-round-3.md#baml-evidence).

**[Inference]** Comparing BEAML to a prompt wrapper would ignore those capabilities. Typed failures and searchable traces alone do not differentiate the tools.
**[Proposal]** Use BAML for one typed extraction and an idiomatic Elixir host for the domain operation. Give the host the same shared tools as the BEAML case.
Pin the BAML build and verify its capabilities in the fixture. Test the newer line separately if it fits the same workflow.

**[Verified]** Evidence update 2026-11-06, after the round. The disposition stays pending. The newer line is BAML v1, a general-purpose language with its own release line. It moved from the 0.23.1 nightlies to `baml-language-0.25.1` in two days. No 1.0 tag exists, and the workspace version says beta. The v0 docs now call v0 "the legacy DSL". This supports the objection: the baseline moves fast and overlaps more. A comparison must pin one toolchain build. [BAML v1 source page](../sources/baml-v1.md#versions-and-release-lines)

### 3. OTP restarts processes. It cannot settle an uncertain payment

Category: implementation and risk. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** OTP supplies lightweight processes and monitoring. EXPERIMENT 0002 ran separate local BEAM processes with Erlang distribution disabled.
The [Orders](../../experiments/0002-http-correlation/apps/orders_api/lib/orders_api/router.ex) and [Payments](../../experiments/0002-http-correlation/apps/payments_api/lib/payments_api/router.ex) host routers call the observation helper around the generated functions. Payments performs no business mutation.
See the [OTP process reference](https://www.erlang.org/doc/system/ref_man_processes.html) and [independent verification](../../experiments/0002-http-correlation/workflow/2026-11-05/result.json).

**[Inference]** Ordinary Elixir can use the same OTP features. A caller timeout can occur after a remote commit. Restarting or correlating a trace cannot settle that outcome.
TYPE checks also cannot establish who authorized the operation or whether a model result is true.
**[Proposal]** Commit once to an independent test ledger and then lose the HTTP response. Require the caller to preserve the uncertain outcome.
Report the recorded commit separately. An isolated REPLAY RUN must issue zero live requests and make zero live mutations.

### 4. Fixture replay can leave the language claim untested

Category: scope and alternatives. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The [distributed order proposal](distributed-order-probe.md#replay-is-more-than-a-joined-search-result) limits its first replay to Orders decisions with captured HTTP outcomes. It already calls for gap detection and isolation.
EXPERIMENT 0002 covers fixed loopback correlation and bounded local files.
**[Inference]** A hand-written recorder and fixture player can meet that replay scope. This would answer a useful EXECUTION question and leave the language-value question open.
**[Proposal]** Derive the boundary identity, checks and capture/replay descriptor from one BEAML declaration. Compare a response SCHEMA change and an incident task against Elixir with equivalent helpers.
Reject the language claim for this slice if the advantage disappears when the host baseline uses a shared helper.

### Proposed smallest comparison

**[Proposal]** Use one synthetic model extraction and one HTTP effect in the two existing releases.
Feed each implementation the same raw synthetic model response. Require the same extracted result and downstream decisions.
Use a fixed valid result and one invalid result. Add the response-loss case in objection 3 and a missing-capture control.

Compare BEAML with a generated boundary adapter, idiomatic Elixir with reusable validation and OpenTelemetry helpers, and pinned BAML plus the Elixir host.
Use the documented REST preview or a small supported-SDK bridge for BAML. Record the chosen integration cost. Avoid dependence on the community Elixir binding.
Give each case the same test ledger, replay runner contract and shared dependencies when applicable.
Use no third service. Keep production durability and composed replay outside this test.

1. **Correctness gate.** The valid case has one test commit. Invalid input has zero downstream calls. The lost response yields a TYPED ERROR for the uncertain outcome.
   Replay reproduces the error and the intended operation/attempt sequence with no live calls or mutations. Missing required evidence fails explicitly.
2. **Derivation gate.** Change the response SCHEMA once. Regenerate the checks and source-linked capture metadata, with no manual metadata edits.
   The original artifact must remain usable for the original REPLAY CAPSULE. Reject an incompatible capsule explicitly if its original artifact is absent.
3. **Value gate.** Give independent operators the same brief and fixed incident artifact. Measure active time from receiving the artifact to locating the source and reproducing the typed failure.
   Use a counterbalanced order and report individual times. A small pilot is directional. A 3× result on that task requires the fastest qualifying baseline median divided by the BEAML median to be at least 3.
   Separately record manual change sites and initial compiler, runtime and bridge work. Keep the engineering budget equal. Stop an arm at its time limit and report it as incomplete.
   If correctness holds but there is no repeatable task advantage, keep replay as infrastructure evidence and defer new language scope.
   A task win justifies a wider test. It does not establish a product-wide multiplier.

### Deliberately not challenged

**[Verified]** The initial Elixir backend and the two passed EXPERIMENTS answer their bounded questions.
**[Unknown]** This review did not run a competitor, measure performance, test security or inspect all BAML features. No owner disposition on these objections is recorded.

## Round 4 — RED TEAM 01 over the compiler and EXPERIMENT 0004 (2026-11-07)

Target: git HEAD `7ee5c89e`: the BEAML compiler (EXPERIMENT 0001), EXPERIMENT 0004 slices 1 to 6b, the tree-sitter grammar, the decision log and the Pages site.
Method: a lead (Fable) and three Opus workers (correctness, boundary, design), two rounds, scratch builds only, no full `run.py` run, no code or test changed.
See the [consolidated report](../../experiments/0004-generated-replay/workflow/2026-11-07/red-team-01/report.md) and the [capture](../../raw/requirements/2026-11-07-roasting-round-4-red-team-01.md).
Counts: high 6, medium 13, low 4, critical 0. Every disposition below is pending. No OWNER decision is inferred.

### 1. The `--stored` check and the REPLAY RUN read different records

Category: implementation. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** `check_stored` never reads `status`; `Replay.run` stops at `status_mismatch` before it reads `value`. A 503 record beside valid records gives exit 1 with the DL-102 text and the MIGRATE STEP help ([C2](../../experiments/0004-generated-replay/workflow/2026-11-07/red-team-01/rt-correctness.md)). DL-121 claims "the check result equals the REPLAY RUN result".
**[Verified]** The same gap: a tampered `value_sha256` passes the check and never replays (C5).
**[Inference]** One recorded Payments outage blocks every later build; nothing changed, so no MIGRATE STEP helps.
Resolving test: a mixed snapshot (200, 503, 503 without `value`, bad digest); the `--stored` verdict equals the `Replay.run` class per record.

### 2. An enum constructor with a failure TYPE breaks the Elixir pass for valid records

Category: implementation. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The DRIVER matches only `{:ok, %{__struct__: ^ok}}`; an enum constructor returns a tuple; the child exits 1 and the build blocks with the run error (C1, [B1](../../experiments/0004-generated-replay/workflow/2026-11-07/red-team-01/rt-boundary.md)). A non-record failure TYPE gives the run error instead of the DL-102 text (B2). No test covers the DRIVER; `elixir_results_are_strict` tests the Rust line parser only.
**[Verified]** P9 in the step 8 ledger named the case and nobody closed it.
Resolving test: one DRIVER test per return shape (record, enum, scalar failure), with one valid and one failing record.

### 3. The DRIFT status ignores outcome classes; a crash run is `pass`

Category: evidence quality. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** `run.py:609` sets the status from the freeze only; `drift_test.py` is not in the STEPS and asserts no expected class. The retained run `results/20261107T171545190446Z` has `untyped_crash` on R, N and Q with `status: pass` and is named nowhere (C3).
**[Verified]** "Recorded, not asserted" is the slice 1 Undo D12 and README line 1561 states the limit for 6a. The full `run.py` runs no slice 6 file (C4); "full suite 14 of 14" stands beside slice 6 results without a limit line in the log, the register and the README ([D10](../../experiments/0004-generated-replay/workflow/2026-11-07/red-team-01/rt-design.md)).
**[Inference]** A compiler regression that crashes the generated flow gives `pass`. **[Unknown]** The cause of the crash in that run.
Resolving test: pin the observed classes per derivative; fail `run.py drift` on a build failure or `repaired_all` false; add the slice 6 files to `run.py`.

### 4. A swapped ENUM LITERAL passes `--stored` and replays as another variant

Category: specification gap. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** `main.rs:3851` blocks only a String that is no current literal. The swap `Authorized = "pending"  Pending = "ok"` gives exit 0; `Replay.run` flips the variants (D1, confirmed by rt-correctness R2-1). The same for an enum constructor, with and without `!`.
**[Verified]** The DL-103 limit ("moves a value from one known variant to another ... stays open until a case shows up") and README line 1770 (D6B-109) have no register entry.
Resolving test: the swap fixture with `--stored`, expect exit 1 with the DL-122 text, or a counted note, by OWNER choice.

### 5. The DL-102 help line names an exit that the compiler refuses

Category: agent trap. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The help says "declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION"; a MIGRATE STEP on that TYPE gives the D6B-39 error, because every DL-102 hit sits on a TYPE with an enum or constructor field (D2, confirmed by rt-correctness R2-2 and rt-boundary). D6B-39 is a plan default with no DL entry and no line in the fate concept.
Resolving step: the help names the slice 6b exit as the DL-122 help does; the fate concept names "lift D6B-39" as a prerequisite.

### 6. DL-125 misstates DL-116; a FATE OPERATION cannot lift it

Category: decision consistency. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** DL-125 names "a redacted field without a constructor (DL-116)"; DL-116 blocks the redacted field on a constructor TYPE. [The fate concept](../concepts/migrate-fates.md) says `redact` lifts DL-116 because "the rule does not run over an absent value"; that is DL-116 option B, which the OWNER rejected ("B would make a replay silently skip a rule") (D3).
Resolving step: DL-116 leaves the DL-125 list; a new OWNER question on a rule over an absent value.

### Noted (medium and low)

**[Verified]** Medium: the slice 6d entry REPLAY RUN diverges from live on every failure and input TYPE change (D4); `retire` means delete in the concept and leave the replay set in DL-125 (D5); `vertical-integration.md` lines 60 and 69 contradict DL-102, DL-121, DL-122 (D6); slice 6d plans to build Migrate defaults before the OWNER answers (D7); RESPONSE RECORD covers the ENTRY RECORD by definition, ENTRY LINE, ENTRY RECORD and OBSERVATORY have no glossary row (D8); `.beaml/actions.jsonl` loses events under parallel runs, 396 of 13203 lines invalid (B3); one TYPE has two host shapes, failure struct against String-key map (B4); `%{s | value: 0}` and a forged `__struct__` map pass the host check (B5); DL-032 "counts, not identities" against DL-124 per-record lines (B6); `docs/index.html` sample does not compile and shows built items as not built (B7, D9).
Low: tampered digest (C5), byte guard hashes edited by hand pass the count guard (R2-5), the grammar reserves `with` that the compiler accepts (B8), `--stored` trusts the first `elixir` on PATH (B9).

### Checked and sound

**[Verified]** Nominal checks, constructor bypass, DL-120 reach reject, `T.new/1` key cases, the Elixir child failure modes (absent, endless, crash, partial output), `value_sha256` writer and reader, step 12 byte guard derivation and span assertions, exact stderr assertions, no stored value in any error text, span attribute or event, 68 accepted sources parse with 0 ERROR nodes, DL-108 against DL-119, DL-106 against DL-117, DL-105 against DL-124, DL-120 against DL-128.

### Open questions for the OWNER (Migrate, pending)

M1 replayable records in `--stored`; M2 known-to-known literal remap; M3 DL-125 scope; M4 D6B-39 against the DL-102 help; M5 `retire` semantics; M6 slice 6d defaults; M7 DRIFT status and coverage claims; M8 failure struct at the host; M9 record lines against DL-032. Options in the [report](../../experiments/0004-generated-replay/workflow/2026-11-07/red-team-01/report.md#decisions-decision4).

### Deliberately not challenged

**[Unknown]** The redacted-fields work in progress was not read. No full `run.py` run. No competitor, no performance and no security test. The `"none"` span ids in 0002 host code were not probed.
