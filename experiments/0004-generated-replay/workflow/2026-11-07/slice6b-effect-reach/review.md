# TEST and review: slice 6b steps 12 and 12b (spans on the EFFECT path, a pure constructor)

**[Observed]** TEST and REVIEW phase, 2026-11-07. Fresh context. Normal review, not a Devil's Advocate. Git HEAD 5120bb5b (step 12 compiler 237a4578, PIN re-pin f3a52261, step 13 on top). No source, test or fixture changed. No commit.
Read: [SKILL.md](../../../../../skills/implement-step/SKILL.md) (TEST, review), [plan.md](plan.md), [plan-review.md](plan-review.md), [spec.md](spec.md), [notes.md](notes.md) (RED, GREEN, GREEN follow-up), [red-review.md](red-review.md), DL-108, DL-119, DL-120 in [the decision log](../../../../../wiki/planning/decision-log.md), `git show --stat` of 237a4578, f3a52261, 5120bb5b.
Limit: the task allows this one file per ledger. So the test results are in this file, not in a separate `test-output.log` and summary (SKILL.md step 6).
By: Opus (TEST/review, slice6b-effect-reach) for every judgement in this file.

## Verdict

- **PASS. No block.** No critical or high objection. Two medium notes (N1, N2). By: Opus (TEST/review, slice6b-effect-reach)

## TEST (one run for steps 12 and 13)

| Check | Result |
|---|---|
| `python3 -B experiments/0004-generated-replay/run.py` | pass, 14 of 14 steps, 13 min 03 s (18:04:01 to 18:17:04 UTC); [result dir](../../../results/20261107T180401517724Z/result.json) |
| previous full run (step 11 TEST) | pass, 14 of 14, 13 min 26 s; `results/20261107T165145154357Z` |
| `slice6_*_test.py` (unittest, 13 files) | 172 of 172 OK: constructor 25, decode_ctor 8, decode 10, effect_reach 8, enum 20, failure 22, fmt 25, host_struct 3, int 16, pipe 12, record 5, stored_elixir 15, struct_order 3 |
| `drift_test.py` | 5 of 5 OK (99 s) |
| `python3 -B experiments/0001-syntax-to-beam/run.py` | pass; `experiments/0001-syntax-to-beam/results/20261107T182003249036Z/result.json` |
| `cargo fmt --check`, `cargo clippy -- -D warnings` | clean (exit 0, 0 warnings) |
| `cargo test` | unit 21 of 21, `cli.rs` 14 of 14 |
| `python3 scripts/lint_wiki.py` | 0 errors, 82 files |

- **[Observed]** The full run drift step: `results/20261107T180431928222Z`. By: Opus (TEST/review, slice6b-effect-reach)

## Probes by hand (scratch build of HEAD, `git archive`)

- **Three-level reach.** `top = o |> pa |> pz |> c`, `c = o |> helper`, `helper = o |> payments.authorize`, `pa`, `pz` pure. **[Observed]** `top`: one span, on `c`; `pa`, `pz` are plain calls. `c`: one span, on `helper`. `helper`: the direct EFFECT call, its `:client` span inside `payments_authorize`. A pure pipe `purepipe = o |> pa |> pz` beside it: no `ProbeSupport` line. This follows DL-119 S: `helper` is a step that reaches an EFFECT through a fn, so it has a span too. By: Opus (TEST/review, slice6b-effect-reach)
- **D6B-127.** Real `ProbeSupport.event/2` (scratch copy of 0002, `mix run`, no open span): `current_span_ctx()` is `:undefined`, the record has `trace_id: "none"`, `span_id: "none"`, the call returns `:ok`, nothing raises. By: Opus (TEST/review, slice6b-effect-reach)
- **12b record, two helpers, shortest path.** `Ticket o = o |> l1 |> s1 |> Ticket`, `l1 -> l2 -> l3 -> place`, `s1 -> place`. **[Observed]** exit 1, no stdout, `error: fn Ticket: a constructor cannot reach an EFFECT: Ticket -> s1 -> place -> payments.authorize (DL-120)` and the D6B-112 help line. The shorter path wins over the first step. By: Opus (TEST/review, slice6b-effect-reach)
- **12b enum, two helpers.** `Settled = order |> l2 |> Done`, `l2 -> l3 -> place`. **[Observed]** exit 1, `Settled -> l2 -> l3 -> place -> payments.authorize`, D6B-112 text. By: Opus (TEST/review, slice6b-effect-reach)
- **12b through a constructor.** `Box = o |> Ticket |> Held`, `Ticket` reaches. **[Observed]** exit 1; only `fn Ticket` is named. `Box` is pure once `Ticket` is pure, so no wrong outcome (dropped, low). By: Opus (TEST/review, slice6b-effect-reach)
- **Guard.** `settle = order |> h |> status_of |> Receipt` (h reaches) and `settle2 = order |> place |> Done`: exit 0, spans on `h` and `place` only. By: Opus (TEST/review, slice6b-effect-reach)
- **Slice 5 PIN diff proof.** PIN `0747c315` build against HEAD build, `--stored stored/empty.jsonl`. **[Observed]** `arms/gen/orders.beaml`: exit and stderr equal; hunks `35/35-36` (the `prepare` span becomes the call and the `_ =` event clause) and `37/38` (the `finish` span becomes the call). `drift/Q/orders.beaml`: `36/36-37`, `38/39`. Both equal notes.md. HEAD holds step 13 too, so this also shows no step 13 byte change for these sources. By: Opus (TEST/review, slice6b-effect-reach)
- **GEN query in the full run.** **[Observed]** In the drift run dir, the baseline and the six N, Q, R `new_live` and `repaired` logs each hold one `payment_request_prepared` with operation `prepare`, and its `span_id` is the `orders.request` span. The baseline spans are `orders.request` and `orders.payments.authorize`; no `orders.prepare`, no `orders.finish`. By: Opus (TEST/review, slice6b-effect-reach)

## Gate check

- RED genuine (5 of 8 fail on missing behaviour), RED review PASS with O1 to O3, all three applied in GREEN (`cli.rs` edit, count asserts, `enum_equal_paths`). GREEN follow-up decisions D6B-127 and the re-pin are recorded with `By:`. By: Opus (TEST/review, slice6b-effect-reach)

## Notes (medium, no block)

**N1 · medium · D6B-127 changes a shared host file with no direct test.**
- Evidence: `probe_support.ex` `event/2` (experiment 0002) now writes `"none"` ids. Only `arms_test` (HARNESS call of `place`) covers it, indirectly. No 0002 test calls `event/2` without a span.
- Consequence: a later edit of `event/2` that raises again is seen only through the eval HARNESS. A log row with `"none"` has no span link; a consumer that joins on `span_id` drops it silently.
- Smallest test: one 0002 unit case: `event/2` with no span returns `:ok` and the record holds `"none"`.
- By: Opus (TEST/review, slice6b-effect-reach)

**N2 · medium · A reaching step span carries the pipe head, not the step input (D6B-88).**
- Evidence: in the three-level probe, the span on `c` gets `p0`, while `c` receives `p2` after two pure steps that can change `order_id`.
- Consequence: the span attribute `order_id` can show the head value, not the value that went into the step. Known by design (plan check O3); not a step 12 defect.
- Smallest test: a pipe whose pure step changes `order_id` before a reaching step; assert which value the span records.
- By: Opus (TEST/review, slice6b-effect-reach)

## Docs defects (listed, not fixed)

- `experiments/0004-generated-replay/README.md` has no step 12 or 12b section: the DL-119 span rule, the D6B-114 event clause, the DL-120 error text and D6B-127 are missing. Line 1617 (step 11 section) says the DL-120 reject "is not in this step"; that is true for step 11, but no later line names where it is now.
- `wiki/planning/research-and-development.md` and `wiki/log.md` have no step 12 or 12b GREEN or TEST entry.
- The 0002 README does not state the `"none"` ids of D6B-127.
- By: Opus (TEST/review, slice6b-effect-reach)

## Limits

- **[Observed]** One host (macOS, Elixir 1.18.1, OTP 27). Probes use a scratch build of HEAD.
- **[Inference]** The real OTel exporter is covered only for the GEN orders source through `run.py`; that source has no indirect pipe.
