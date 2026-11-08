# RED output: fates-a2a (record format draft 4)

**[Verified]** Runs of 2026-11-08 at HEAD `6427262f` with the RED test changes uncommitted. By: Opus (RED fates-a2a).
Toolchain: the 0001 debug build of `cargo build --offline` at HEAD (`target/debug/beaml-spike`); elixir/mix of the host.
Plan: [red-plan.md](red-plan.md). Raw logs stayed in the session scratchpad; the counts and reasons below are copied.

## Run 1: a2a tests at HEAD

```
python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py FatesA2a
Ran 8 tests in 4.5s  FAILED (failures=39)
```

40 subtests: 39 fail, 1 passes (the V4i guard). Reasons:

| Test | Subtests failing | Actual at HEAD | Planned reason |
|---|---|---|---|
| V4a, V4b | 6 of 6 | every record `{version, type.nested} == {3, nil}` | writers are v3, no `nested` |
| V4c | 5 of 6 | `{3, nil}`; head `{"Order", 1}` | same; the mark does not reach the record |
| V4i | 0 of 1 (guard) | PASS: `value_sha256` is the value digest | guard, passes before and after |
| V4d | 5 of 5 | v3 records: exit 0, module built; draft 4 controls: `stored ROW has record version 4; this build reads record version 3 only (DL-143)` | v3 is accepted, v4 refused |
| V4e | 8 of 8 | `record version 4 ... version 3 only` | v4 refused (see Run 2 for the depth) |
| V4f, V4f2 | 5 of 5 | `record version 4 ... version 3 only` | same |
| V4g | 8 of 8 | `record version 4 ... version 3 only` | same |
| V4h | 2 of 2 | `record version 4 ... version 3 only` | same |

## Run 2: RED depth probe (the stored tests past the version gate)

At HEAD the stored tests stop at the version gate. To show they fail for the planned reason beyond it, a scratch copy
of HEAD (`git archive HEAD experiments/0001-syntax-to-beam`, scratchpad) changed only `if n == "3" => None` to
`if n == "4" => None` at the three readers (3 sites, `sed`), built with `cargo build --offline`.

```
BEAML_SPIKE=<scratch>/target/debug/beaml-spike python3 -B .../slice6_fates_test.py \
  FatesA2a.test_V4d_... FatesA2a.test_V4e_... FatesA2a.test_V4f_... FatesA2a.test_V4f2_... FatesA2a.test_V4g_... FatesA2a.test_V4h_...
FAILED (failures=20)
```

28 subtests: 20 fail, all 8 controls pass (V4d draft 4 rows and records build; V4f nested 2 builds; V4g three v1
quarantine controls and the v1 map control print the a1 fate and stop lines; V4h v1 `"web"` keeps the moved block).

| Test | Actual with the probe | Planned reason |
|---|---|---|
| V4d ROW / RESPONSE / ENTRY | v3 refused with `... version 3; this build reads record version 3 only (DL-143)` | the text must say `version 4 only (DL-168)` |
| V4e (8) | exit 0; ROW counted `1 checked, 0 not decodable` | `nested` is not read; no malformed check |
| V4f ROW / ENTRY / LIST item | exit 0, module built | no SQUASH block |
| V4f2 | exit 0, module built | no newer-version block |
| V4g ROW / LIST item / ENTRY at `amount` 2 | `fate: 1 stored ... quarantined by migrate Amount v1 -> v2 (quarantine value)` + a1 stop line | the fate line acts on a v2 value (no version selection) |
| V4g map v2 `"app"` | `fate: 1 stored ROW of table records mapped by migrate Channel v1 -> v2 ...` | the map line acts on a v2 value |
| V4h v2 `"web"` | `error: TYPE Order v1: 1 stored ROW ... "web" ... which was Web in enum Channel v1 and is App now (DL-140)` | the swap check reads the v1 table for a v2 value (GF-02) |

## Run 3: 0005 N16 at HEAD

```
cd experiments/0005-prototype-fullstack/app
BEAML_SPIKE=<repo>/experiments/0001-syntax-to-beam/target/debug/beaml-spike BEAML_RUN_DIR=<scratch> MIX_ENV=test \
  mix test test/prototype/stored_test.exs --only use_case:N16 --seed 0
6 tests, 1 failure, 5 excluded
left:  {0, ["rows: 1 rows, 1 checked, 0 not decodable"], {3, nil}, {3, nil}}
right: {0, ["rows: 1 rows, 1 checked, 0 not decodable"], {4, %{"amount" => 1, "channel" => 1}}, {4, %{...}}}
```

Planned reason: the live row core and its ROW SNAPSHOT line are v3 without `nested`. The build part already passes.
The local Postgres of `app/.pgsock` was running; the test truncates `records` (moduletag `committed: :truncate`).
`run.py run` was not run in RED: with N16 in `EXPECTED` it fails at HEAD by design.

## Run 4: guards at HEAD

```
python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py Fates
Ran 37 tests in 33.2s  OK
python3 -B experiments/0004-generated-replay/workflow/2026-11-08/fates-a2/convert_v4.py --check
files 26, records 53
```

The a1 / a1b tests keep passing with the new class in the file. The converter dry run reads all 26 v3 fixtures, its
digest asserts hold, and it writes nothing. V4h two-step probe: see red-plan.md (exit 1 for each form).

## Limits

- **[Inference]** V4e to V4h fail at HEAD at the version gate first; Run 2 is the evidence that they also fail for
  their own reason. The probe is a scratch build, not a GREEN.
- **[Unknown]** The order of the SQUASH line against other blocks in one build (S3 with SQUASH) is GREEN's choice; V4f
  holds one row only.
- Not run: full 0004 `run.py`, 0005 `run.py run`, cargo checks (no production change).

## Decisions
See red-plan.md "RED decisions" (RA-01 to RA-09, By: Opus (RED fates-a2a)).
