# TEST and review: DB TRANSPORTS, P4a and P4b (EXPERIMENT 0005 prerequisite P4)

**Verdict: PASS.** No critical or high objection. Three medium notes below.
2026-11-08. By: Opus (TEST db-transport), fresh context, one round. HEAD b332b12c (GREEN 060a075d plus the pin commit). No code changed, no commit.
Inputs: [plan.md](plan.md) with both repairs, [decisions.md](decisions.md), [red-plan.md](red-plan.md), [red-output.md](red-output.md), [red-review.md](red-review.md) (P4a, P4b), [green-output.md](green-output.md), the 0005 [owner review](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md) "P4 GREEN defaults".

## Checks run (observed)

| Check | Result |
|---|---|
| `python3 -B experiments/0004-generated-replay/run.py` | pass, 38 of 38 steps, 1035 s wall time (17 min 15 s); `experiments/0004-generated-replay/results/20261108T000131342068Z/` |
| `python3 -B experiments/0001-syntax-to-beam/run.py` | pass, `experiments/0001-syntax-to-beam/results/20261108T000948165865Z/` |
| `cargo fmt --check` (0001) | exit 0 |
| `cargo clippy --offline --all-targets -- -D warnings` | exit 0 |
| `cargo test --offline` | 22 + 14 passed |
| `python3 scripts/lint_wiki.py` | 85 files, 0 errors |
| tree-sitter `test` (`integrations/zed-beaml/`) | 24 of 24 parses, highlight assertions pass |
| tree-sitter `parse -q` on every fixture under `slice6/db/` and `slice6/multi/` | 33 of 33, no `ERROR` or `MISSING` |
| `tests/overlay_diff_test.py` | FAIL, see below |

**overlay_diff_test: pre-existing, not P4.** **[Observed]** It fails `experiments/0002-http-correlation/query.py: 211 lines, original 213` at HEAD. Neither the copy nor the original changed after ce190054 (`git log`: last copy change 237a4578, slice 6b step 12; original 1fc27225). **[Verified]** The test left the check list at slice 6b step 6a (DL-110, option B; `run.py` comment line 76), so `run.py` does not run it. Class: retired check with a stale copy, unrelated to P4.

## Probes (observed, scratch only)

Scratch compiler from `git archive HEAD`; a ce190054 compiler for the guard probe. Probe file: a subclass of `Slice6DbStored` with the repo fake `BeamlDb` (scratchpad, not kept in the repository). No stored value or MARKER is copied here.

**Runtime (fake `BeamlDb`, `orders.beaml`, `two_rows/`)**
→ put/get/list round trip with JSON binaries: pass (repo N2, N4, N7; my replay-of-list from JSON: equal to live).
→ `:null` vs `nil`: the raw capture holds `reason: :null`; no raw capture and no put binary contains `"nil"` (`:json.encode(nil)` gives `"nil"`, so the check is real).
→ host `raise` and `exit`: record `rejected` / `transport`, `value: :null`.
→ `db.get`: newest row wins, also when the newest row is bad (`decode`); an input with an extra key raises `invalid BEAML input` before `BeamlDb` is called (the strict input check).
→ one bad row fails the list (`decode`); a row with a missing String field fails the list too (`decode`).
→ Note v1 row read as v2 with `tag: ""`; `list_orders` ignores Note rows.

**Compile**
→ `[T]` in a db.put ROW TYPE: the Q5-3 LIST TYPE error. `[T]` in an http.post output: `slice 1 decodes String fields only`. `[[Order]]`: a parse error (`expected identifier`).
→ fifth KIND `db.delete`: the four-KIND text and help. Table `"Records"` and `"orders"`: the DL-127 text.
→ `with` after a db call: a parse error, not the GREEN text `with stands only after http.post` (that branch is unreachable from this form; Undo, untested as recorded).
→ stem `beaml_db`: the reserved-name error. Constructor with a one-field first signature: the PDB-13 error.
→ http.post plus db.put in one source: builds, `Http` and `Replay` modules present. db-only source: no `Http` module, no `Http.` call.

**`--stored` over `rows.jsonl`**
→ stricter constructor, lost literal, two ROW TYPES, `Note` row under `Order`, orphan rows, `row_count` above and below: as the repo tests (all pass in the run).
→ RETIRE LINE `retire notes.save keep 30 days` frees two orphan Note rows: exit 0, `rows: 3 rows, 1 checked, 2 not decodable`.
→ `row_count` as a String and a missing `row_count`: `snapshot-meta.json has no row_count (P5-19)`.
→ count lines: a clean accepted db record prints only the rows line; a rejected one adds the unchanged P2 pair (`1 records, 0 checked, 1 rejected at capture`, `digest not verified (P2b)`) before the rows line.
→ DL-124: no stored String, row id or trace id in any probe stderr.
→ Missing field: a missing constructor field (`amount`) or enum field (`channel`) blocks (`matches no signature`, `has no variant`). A missing or Int-valued String field (`order_id`) with a valid digest **builds** (`1 checked`), for rows and for RESPONSE RECORDS alike; at run time the same row fails the whole `db.list` (`decode`). See O1.

**Pin sites**
→ **[Observed]** `git diff ce190054 HEAD`: `slice5_syntax_test.py` PIN, `slice6_pipe_test.py` EFFECT_OUTPUTS, `slice6_host_struct_test.py` BYTE_GUARD and `slice6/effect-reach/byte-guard.json` unchanged; the PIN compare in A2 skips db sources; S13 moved as planned. Entry and multi N13 `BASE` stay ce190054, filters skip `= db.x(` and `: [`. `P4_BASE = "060a075d"`.
→ **[Observed]** Of 173 tracked sources, the filter skips 24, and all 24 hold a db EFFECT line (23 under `slice6/db/`, plus S13). No non-db source is hidden today.
→ **[Observed]** Probe: `slice6/multi/orders.beaml` with an added comment `// note: [not a list]` gives equal exit, stdout and stderr at ce190054 and HEAD, but the filter matches it, so all three N13 guards would skip it. **[Inference]** The filter is a text match, not a db check: a future non-db source with `: [` in a comment escapes every N13. Low (no such source exists; pins 1 to 4 still hold their own sources). Dropped.
→ **[Inference]** With `P4_BASE` at 060a075d, `slice6_db_test` N13 now compares HEAD with itself until main.rs changes; the cross-version proof for non-db sources is the entry and multi N13 against ce190054. Intended by the RV3-14 rule.

## Objections (medium, no block)

**O1. A row with a missing String field passes `--stored` and breaks the page at run time.**
Evidence: probe above. `order_id` removed (digest recomputed) → exit 0, `rows: 1 rows, 1 checked, 0 not decodable`; the same row seeded in the fake → `Orders.list_orders` fails with `decode` for all rows (QDB-4 A). The same build pass holds for a RESPONSE RECORD, so it is not new with P4, but QDB-4 A makes the row case worse: one row takes the whole list down.
Judgement on the GREEN default "no DL-101 shape check over rows": DL-102 targets a new rule over an unchanged field shape, so a missing field with a matching fingerprint is a hand edit or a foreign writer, not a DL-102 case. But DL-137 and DL-136 say the check reads the rows that `db.list` decodes and the check result equals the read result (DL-121); "1 checked" and green against a failing read breaks that. The remedy (block with a DL-102 text, or count as not decodable like a bad digest) is a stream rule for both RESPONSE RECORDS and rows. **Class raised: Repair → Migrate** (default as built, open; pulls in the OWNER). Severity medium: 0005 rows come only from the generated `put`, and the digest must be recomputed for the row to reach the check.
→ Smallest test: `N32_row_missing_string_field`: `orders.beaml`, one row `{"amount": EUR, "channel": "web"}` with its own digest; expect exit 1 (or `0 checked, 1 not decodable`, per the OWNER answer). Control: the same row for a RESPONSE RECORD.

**O2. The RETIRE LINE frees orphan rows with no test, inside parked M5.**
Evidence: probe above (exit 0, the two Note rows counted). N28b is skipped because "the RETIRE LINE meaning for rows is M5, parked by D036"; the GREEN built the free through the existing DL-040 orphan rule (`self.retire(op)` in `check_rows`) and the help line offers it. The owner review lists it, so it is not hidden. If M5 decides that a retired row must still be removed or quarantined, today's build is a false pass, and no test moves when M5 is answered.
→ Smallest test: un-skip N28b as a pin of the built default (`retire notes.save keep 30 days` → exit 0, `rows: 3 rows, 1 checked, 2 not decodable`), marked "default, open, M5".

**O3. N27 can fail at random: 4-digit row ids against timestamp digits in the action log.**
Evidence: in one probe test with about 20 compiles, `compile()` reported `N27: events hold a stored value` for a row id. The compiler event `ts` is an epoch float with microseconds; `ROW_IDS` counts from 7001, and N27 tests `w in text` on the whole log. **[Inference]** Each event and id pair hits with about 3 in 10000; over the 41 tests of `slice6_db_stored_test.py` this is a few percent per full run. A false fail only, never a false pass, but `run.py` can then report 37 of 38.
→ Smallest fix: row ids outside the digit stream (for example a String id `row-7001`), or match ids as JSON tokens (`"row_id":7001`); test: run `slice6_db_stored_test.py` 20 times with no N27 failure.

## Review of the GREEN Repair and Migrate defaults

| Default | Finding |
|---|---|
| No DL-101 shape check over rows | Partly true: constructor and enum fields are checked by the DL-101 tail; a missing or mistyped String field is not. Raised to Migrate (O1). |
| Constructor field of a ROW TYPE needs a first signature with exactly its String fields | Built and surfaced as big (owner review). **[Observed]** The check compares the field names as a set: a reversed signature `currency: String, value: String` builds. With the existing positional clause `fn Amount value, currency` that source would swap the values on decode; this is the source author's constructor (D6B-48 decode), not P4. Low, dropped. Class Migrate stays. |
| `BeamlDb` reserved | Built and pinned by my probe; surfaced as big. Migrate stays. |
| ROW TYPE fields as the http output rule | Consistent with `slice 1 decodes String fields only`. Repair stays. |
| Orphan help and RETIRE LINE | O2. |
| Row digest in Rust | N21, N29 pass. Repair stays. |
| A2 and N13 filter skips | Only db sources skipped today; see Pin sites. Repair stays. |
| Count line always printed, P2 pair unchanged | Observed; the merged count-line OWNER question stays open. |

**RED and GREEN chain.** **[Observed]** P4a RED review M1 (`N10_constructor_record`) and M2 (owner review lines) are in place; M3 (pin-site wording) is in the docstring. P4b M2 (`N24_row_count_below_lines_blocks`) is in place and passes.

## Limits

→ Fake `BeamlDb` only; Postgres `jsonb` and the real host module stay 0005 (N2c).
→ The probes ran against a `git archive` HEAD build, not the repository target.
→ O3 rate is estimated, not measured over many runs.

## Decisions

**Migrate**
→ O1: "no shape check over rows" raised from Repair to Migrate; options block (DL-102 text) or count as not decodable; default as built; the OWNER chooses. → By: Opus (TEST db-transport) · Migrate

**Repair**
→ PASS statt BLOCK, weil O1 to O3 need a hand-edited row, an open parked item or a random hit. → By: Opus (TEST db-transport) · Repair
→ O2 and O3 as medium notes statt blocks, weil no wrong build reaches 0005 today. → By: Opus (TEST db-transport) · Repair

**Undo**
→ overlay_diff_test failure classified as pre-existing, retired from run.py (DL-110). → By: Opus (TEST db-transport) · Undo
→ N13 text filter accepted; comment case dropped as low. → By: Opus (TEST db-transport) · Undo
→ Reversed constructor signature and `[[T]]` parse text dropped as low. → By: Opus (TEST db-transport) · Undo
→ Probes kept in the scratchpad, not added to the repository. → By: Opus (TEST db-transport) · Undo
→ 0001 `run.py` and `cargo test` run while 0004 `run.py` ran (no shared port, binary up to date). → By: Opus (TEST db-transport) · Undo
