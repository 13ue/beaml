# Slice 6b step 0: baseline hygiene

Step: [plan.md, Step 0](../slice6b-plan/plan.md#step-0-baseline-hygiene-slice6b-hygiene), `plan.json` step 0.
Review note: [plan-review.md (5), Step 0](../slice6b-plan/plan-review.md). Name the difflib parity test (DL-067).

- **Change.** Run `cargo fmt` on `experiments/0001-syntax-to-beam/src/main.rs`. Fix the two clippy lints (loop at 3039, TYPE at 3610). No behavior change.
- **Check instead of RED.** Test counts equal the baseline. Compiler output is byte-equal before and after (`capture.py`). Both `run.py` runs pass.
- **Exclusion.** No other refactor. Do not touch `integrations/zed-beaml/`.
