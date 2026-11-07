# Slice 6b mini-step struct-order: spec

**[Proposal]** SOLVE / RED phase, 2026-11-07. A step 2 regression, found by the step 8 RED review ([../slice6b-decode-constructor/red-review.md](../slice6b-decode-constructor/red-review.md), objection 2). Decisions: [notes.md](notes.md). RED output: [red-output.log](red-output.log).

## Defect

- **[Observed]** Commit `c3e97430` (step 2 GREEN) added the order rule of D6B-07: `emit()` puts the failure struct modules first only when the module has no EFFECT. With an EFFECT, `emit_effect` puts them after the clauses.
- **[Observed]** An EFFECT module with a pure fn that fails with a record failure TYPE (`! Bad`) compiles with exit 0. Then `elixirc` fails: `BeamlSpike.Bad.__struct__/1 is undefined, cannot expand struct BeamlSpike.Bad`, at `defp __beaml_check(<<>>), do: {:error, %__MODULE__.Bad{}}`.
- **[Observed]** The existing EFFECT fixtures do not use a failure struct before its `defmodule` (RED review scan).

## Fix contract

- In every module, each struct module of a failure TYPE comes before its first use.
- The outputs of `arms/gen/orders.beaml` and `slice2/reuse/orders.beaml` (`--stored stored/empty.jsonl`) stay byte-identical (sha256 of the step 5 guard, D6B-07). The output of `payments.beaml` stays equal to `tests/payments.generated.snapshot`.
- A pure module keeps its output (step 2 tests).

## Behavior under test

| Case | Expected |
|---|---|
| Probe (EFFECT plus `fn check ... ! Bad`), `--stored stored/empty.jsonl` | exit 0, then `elixirc --warnings-as-errors` with the step 7 stubs gives exit 0 |
| Guard: the two EFFECT fixtures | the step 5 sha256 values |
| Guard: `payments.beaml` | equal to the snapshot |

## Exclusions

- No change to the struct texts or the clause texts.
- No runtime call of `check`. The fault is a compile fault.

## Files

- Test: `experiments/0004-generated-replay/tests/slice6_struct_order_test.py`. 2 tests (RED: 1 FAIL, 1 guard PASS).
