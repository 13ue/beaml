# Slice 6b step 6a: TEST and review (fresh context)

**[Observed]** TEST and normal fresh review, 2026-11-07, git HEAD `1bd1217b`, branch `main`. No source or test changed. Not committed.
By: Opus (TEST/review, slice6b-records-v2) for every entry in this file.

## Verdict

**BLOCK** on objection RV6A-1 (high). RV6A-2 is medium: note it. All checks pass.

## TEST results

Runner: `unittest` (no pytest in this Python). Commands from the repository root.

| Check | Command | Result |
|---|---|---|
| Full 0004 suite | `python3 -B experiments/0004-generated-replay/run.py` | **pass, 14 of 14 steps**, 12 min 20 s |
| Result dir | | `experiments/0004-generated-replay/results/20261107T155400927519Z` |
| DRIFT run dir of that suite | | `experiments/0004-generated-replay/results/20261107T155426933490Z` |

Steps of the full suite (all `pass`):

| Step | Tests |
|---|---|
| compiler (`cargo test`) | 18 + 14 |
| lib-freeze | freeze verified |
| arms | 11 |
| drift | `repaired_all` true |
| stored-types | 33 |
| slice2-replay | 21 |
| slice3-types | 69 |
| slice3-replay | 31 |
| slice4-retire | 87 |
| slice4-replay | 27 |
| slice5-syntax | 60 |
| slice5-squash | 24 |
| slice5-replay | 12 |
| slice5-rewrite | 5 |

**[Observed]** The full suite runs no `slice6_*` file and not `drift_test.py` (see RV6A-2). I ran them apart:

| File | Result |
|---|---|
| `slice6_record_test.py` | 5 OK |
| `slice6_decode_test.py` | 10 OK |
| `slice6_decode_ctor_test.py` | 8 OK |
| `slice6_pipe_test.py` | 12 OK |
| `slice6_struct_order_test.py` | 3 OK |
| `slice6_constructor_test.py` | 25 OK |
| `slice6_enum_test.py` | 20 OK |
| `slice6_failure_test.py` | 22 OK |
| `slice6_fmt_test.py` | 25 OK |
| `slice6_int_test.py` | 16 OK |
| `drift_test.py` | 5 OK, 96 s, run dir `results/20261107T160640532493Z` |

## Compiler and lint

| Check | Result |
|---|---|
| `python3 -B experiments/0001-syntax-to-beam/run.py` | pass, `experiments/0001-syntax-to-beam/results/20261107T155833108504Z/result.json` |
| `cargo fmt --check` (0001) | clean |
| `cargo clippy -- -D warnings` (0001) | clean |
| `cargo test` (0001) | 18 + 14 passed |
| `python3 -B scripts/lint_wiki.py` | 81 files, 0 errors. Limit: inline links only; workflow ledgers may be outside its scope. |

## Probes

Scratch source (not retained in the repository): `Payment { order_id: String note: String amount: Amount }`, `Amount` with a constructor. One live `Replay.record/3` with the release-free stubs of `slice6_decode_test.py`. Body: a non-ASCII `note` (2-, 3- and 4-byte UTF-8), a non-ASCII `currency`, the stray key `amount.extra`, and a stray nested object `zzz`.

**[Observed]** Record shape (no raw body shown):

- Keys: the 13 keys of D6B-53. No `body_base64`, `body_length`, `body_sha256`.
- `version` 2, `redacted` `[]`, `unknown_keys` `["amount.extra", "zzz"]`.
- `value` keys `amount, note, order_id`; `amount` keys `currency, value`. Non-ASCII values equal the input.
- The stray values are in no record byte.
- Python `stored_types_test.value_sha256` equals the record `value_sha256` (writer parity, D6B-58).
- The ASCII-escaped form and the unsorted form give another digest. So the writer does not escape and does sort.
- REPLAY RUN of the record: `{:ok, ...}` with the nested `value`. The reader recomputes the same digest after a JSON round trip.
- Tamper of a nested value, tamper of `unknown_keys`, and a version 1 shape (`body_base64`, no `value`): each gives `{:error, :body_digest_mismatch}`.

**[Observed]** `--stored` version check:

- `slice6/record/stored-v1.jsonl`: exit 1, the D6B-59 text with `record version 1` and `record source: ...:1 (line 1)`.
- The same file with `--remove-dead`: exit 1, the same text. That path goes through `check_stored` too.
- `version` `2.0`: exit 1, `record version 2.0`. `version` `"2"`: exit 1, `record version malformed`.

**[Observed]** Version 1 survivors (`rg`, generated code and tests):

- `main.rs`: none. Every `--stored` path calls `check_stored`; `body/1` accepts only the four projection keys.
- `run.py` `proxy` writes `body_base64` into the proxy exchange. That is a DRIFT diagnostic, not a RESPONSE RECORD. `body_json` falls back to it for exchanges.
- Test guards (`BODY_KEYS`) and the LIB and GEN 0003 copies under `arms/`. The copies are out of the check list (DL-110).

**[Observed]** DRIFT D6B-96, DRIFT run dir of the full suite:

| Row | `repaired` keys | `exit_code` | `argv` | record | report result | 0003 copy in `commands.json` |
|---|---|---|---|---|---|---|
| R | argv, exit_code, record, report | 0 | `.../bin/orders eval` | version 2, status 200 | `ok`, host `ok` | no |
| N | argv, exit_code, record, report | 0 | `.../bin/orders eval` | version 2, status 200 | `ok`, host `ok` | no |
| Q | argv, exit_code, record, report | 0 | `.../bin/orders eval` | version 2, status 400 | `error: status_mismatch`, host `nil` | no |

- `drift`, `baseline`, `sites` have only the key `gen`. No `*/lib` dir. `repaired_all` true.

## Objections

### RV6A-1 · high · The DRIFT-Q repair check passes without the repair

- **[Observed]** The Q repair (`arms/gen/repair/Q.json`) adds one `valid_order!/1` clause for `{"order_id", "channel" => "web"}`.
- **[Observed]** The repaired live call gives status 400 (`PaymentError{reason: "status"}`), as the drifted live call does.
- **[Observed]** The repaired replay input is `order: {"order_id": "order-1"}`. `valid_order!/1` takes the old first clause. The replay stops at `:status_mismatch`. `host_validation` is `nil`.
- **[Inference]** No line of the Q repair runs. Without the repair, the Q row gives the same report. `repaired_all` true is thus no evidence for Q.
- **[Inference]** The removed 0003 copy run replayed a status 200 record with `{**ORDER, "channel": "web"}`. That reached the decode and the host validation. 6a removed that coverage for Q.
- The RED repair accepted "a Q row may pass with `error`". It did not see that the error comes before the repaired code.
- **Smallest test that settles it:** in `drift_test.py`, a case that runs DRIFT with the Q repair minus the `valid_order!` hunk. Expect a Q report other than the repaired one, or `repaired_all` false. Today it gives the same report.
- **Repair options (main agent chooses; the class may be Migrate, because DL-118 names the check):**
  - A: the Q repair check replays a status 200 derivative (`st.with_value`, D6B-68) with the channel order. It must reach `valid_order!/1` with `channel` and host `ok`.
  - B: state in DL-118 and the README that DRIFT-Q has no repair evidence after 6a; `repaired_all` ignores Q.

### RV6A-2 · medium · A full suite pass does not run the 6a acceptance

- **[Observed]** `run.py` `STEPS` runs no `slice6_*_test.py` and not `drift_test.py`. The run.py `drift` step checks only `status` and `repaired_all`, not the D6B-96 shape.
- **[Inference]** A later change can break `slice6_record_test.py` or D6B-96 while `run.py` says `pass`. The GREEN counts and this TEST needed separate runs.
- **Smallest fix:** add the slice 6 files and `drift_test.py` to `SLICE_TESTS`, or say in the `run.py` docstring that they run apart.

## Docs defects for the docs phase (not fixed)

- `GLOSSARY.md` RESPONSE RECORD: "the body bytes". New text in [readme-change.md](readme-change.md).
- `GLOSSARY.md` ENUM LITERAL: "A wire value". Check the term against DL-105.
- README, the five "Pass and reject rule" headings and case (c): no DL-110 cut note yet ([readme-change.md](readme-change.md)).
- README line 299: "It reads no body bytes". After 6a the DL-102 checks read `value`.
- README case (f) DRIFT: "repair each arm until (d) or (e) passes". No GEN-only rows, no D6B-96 repair check (DL-118 commits this).
- README case (d2) R1: "`body_length` and `body_sha256` recomputed". Version 2 records have neither.
- README has no text on RESPONSE RECORD version 2 (`value`, `unknown_keys`, `value_sha256`, D6B-59 version check).
- `run.py` docstring: "the slice 2-5 test files" is true, but it does not say that slice 6 files and `drift_test.py` run apart (RV6A-2).
- `readme-change.md` "Open": says DRIFT (f) does not change in 6a. DL-118 and D6B-96 changed it.
- `repin.md` "Result": says the re-pin is not applied. Commit `1bd1217b` applied it (its message accepts the `Replay.run/3` hunk).
- `notes.md` O1: closed text is right; the GREEN counts table still shows the 37 byte-guard failures that the re-pin closed.

## Decisions

**Undo**
- → Ran the slice 6 files and `drift_test.py` apart, because `run.py` omits them. By: Opus (TEST/review, slice6b-records-v2)
- → Ran the 0001 cargo checks during the 0004 suite; cargo locks the target. By: Opus (TEST/review, slice6b-records-v2)
- → Probes with the release-free stubs, not a release; the DRIFT records cover the release writer. By: Opus (TEST/review, slice6b-records-v2)
- → Dropped as low: `body_json` fallback to `body_base64` (proxy exchanges only). By: Opus (TEST/review, slice6b-records-v2)
- → Dropped as low: the `:json` exponent float limit (writer and reader share `digest/3`; marked `ponytail:`). By: Opus (TEST/review, slice6b-records-v2)

**Repair**
- → **Chose:** RV6A-1 high and BLOCK. **Over:** a medium note. **Because:** `repaired_all` true for Q is a false pass; no repair line runs. **Commits us to:** a repair or a recorded acceptance before the slice review. By: Opus (TEST/review, slice6b-records-v2)
- → **Chose:** RV6A-2 medium. **Over:** high. **Because:** all files pass today; the gap is future coverage only. **Commits us to:** nothing until the docs or a later step. By: Opus (TEST/review, slice6b-records-v2)

**Migrate**
- → RV6A-1 repair, option A (a status 200 Q derivative) or option B (record that Q has no repair evidence). The main agent or the OWNER chooses. By: Opus (TEST/review, slice6b-records-v2)

## Re-check after RV6A-1 (52550d4f)

Fresh-context check of the RV6A-1 fix (`run.py` `repair_releases`, `repaired_replay`). No source or test change. By: Opus (re-check RV6A-1, slice6b-records-v2)

### Runs (Python 3, from the repository root)

| Command | Result | Result dir |
|---|---|---|
| `python3 -B experiments/0004-generated-replay/run.py` | 14 of 14 steps pass, status `pass` (12.5 min) | `results/20261107T161752613981Z` (DRIFT: `results/20261107T161820272952Z`) |
| `unittest discover -p drift_test.py` | 5 of 5 OK (98.6 s) | DRIFT: `results/20261107T163033117603Z` |
| `unittest discover -p slice6_<name>_test.py`, the ten 6a files | 146 of 146 OK | none |
| `unittest discover -p slice6_host_struct_test.py` | 19 failures | none |

- **[Observed]** `slice6_host_struct_test.py` is the step 11 RED of commit `bd8cb895` ("19 cases fail"). It is not a 6a file. The failures are the expected RED. By: Opus (re-check RV6A-1, slice6b-records-v2)

### DRIFT evidence of the full run (`results/20261107T161820272952Z`)

| Row | Edited files | Rebuilds (exit) | Record | Request | Replay result | Host | 0003 copy |
|---|---|---|---|---|---|---|---|
| R | `probe_support.ex`, 0003 `replay_run_test.py` | `repair-release-orders` 0, `repair-release-payments` 0 | version 2, status 200 | `order_id` | `ok` | `ok` | no |
| N | same | same | version 2, status 200 | `order_id` | `ok` | `ok` | no |
| Q | same | same | version 2, status 200 | `order_id`, `channel` | `ok` | `ok` | no |

- **[Observed]** Each row: `repaired.exit_code` 0, report `eval_exit_code` 0, every command of the row log exit 0. `repaired_all` true.
- **[Inference]** The Q status changed from 400 (RED run `20261107T161111078093Z`, Orders rebuild only) to 200 with the Payments rebuild. The rebuild is the cause, and the repaired `valid_order!/1` clause now runs. By: Opus (re-check RV6A-1, slice6b-records-v2)

### False-pass hunt

- **Empty release set.** **[Observed]** All three `arms/gen/repair/*.json` edit `experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex`; `repair_releases` gives `['orders', 'payments']`. A test-only edit gives `[]` (correct). **[Observed]** An edit of the umbrella `config/*.exs` or `mix.exs` also gives `[]`, so the release stays stale. No repair spec edits these files today. The tightened D6B-96 check (status 200, `ok`, host `ok`) fails when a stale release changes the result. Dropped as low. By: Opus (re-check RV6A-1, slice6b-records-v2)
- **Unchecked rebuild exit.** **[Observed]** `repaired_replay` returns `{"exit_code": code}` at the first rebuild with a non-zero exit; `drift_test.py` then fails on `repaired.exit_code`. Inside the DRIFT the exit is checked. See RC1 for the full suite. By: Opus (re-check RV6A-1, slice6b-records-v2)

### Objections

**RC1 · medium · The full suite does not read `repaired_all`** (sharpens RV6A-2)
- **[Observed]** `drift()` sets `status` from the freeze only (`run.py` line 609). `run.py drift` exits 0 when `repaired_all` is false. The full-suite `drift` step judges only that exit code.
- **[Inference]** A failed repair rebuild gives `repaired_all` false and a full-suite `pass`. Only `drift_test.py` catches it, and `run.py` does not run that file (RV6A-2).
- **[Observed]** It hides no failure today: `repaired_all` true, `drift_test.py` 5 of 5.
- **Smallest test:** in the docs/TEST phase, make `drift()` status `fail` when `repaired_all` is false, or add `drift_test.py` to `SLICE_TESTS`. By: Opus (re-check RV6A-1, slice6b-records-v2)

### Verdict

- **RV6A-1: closed.** R, N and Q give status 200, `ok` and host `ok` from a rebuild of both releases; no 0003 copy runs. By: Opus (re-check RV6A-1, slice6b-records-v2)
- **RV6A-2: stays open (medium)** for the docs/TEST phase, with RC1 added. No block. By: Opus (re-check RV6A-1, slice6b-records-v2)

### Decisions

**Undo**
- → Ran `slice6_host_struct_test.py` too, and labelled it the step 11 RED, not a 6a regression. By: Opus (re-check RV6A-1, slice6b-records-v2)
- → Dropped the umbrella `config`/`mix.exs` gap as low. By: Opus (re-check RV6A-1, slice6b-records-v2)

**Repair**
- → **Chose:** RC1 medium. **Over:** high. **Because:** `drift_test.py` catches a failed rebuild and passes today. **Commits us to:** a fix of RV6A-2 and RC1 in the docs/TEST phase. By: Opus (re-check RV6A-1, slice6b-records-v2)
