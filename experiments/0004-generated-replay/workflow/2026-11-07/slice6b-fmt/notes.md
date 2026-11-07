# Slice 6b step 10: notes

## Solve

What this phase takes from the plan (step 10, D6B-41 to D6B-46), the plan review (O3, section (3)) and DL-013, DL-080, DL-081, DL-083, DL-104:

- Baseline: commit `cd379ff0`. The compiler was built from a `git archive` of that commit in a scratch directory, because another worker runs the full suite on the live tree. The test runs with `BEAML_SPIKE` set to that binary.
- **[Observed]** Today `beaml-spike fmt SOURCE.beaml` gives the usage text and exit 1: two arguments match no `main()` pattern. The plan text "`fmt` is read as a source path (`cannot read source`)" is wrong (U10).
- **[Observed]** `write_atomic`, `unified_diff` and `action` exist for `--remove-dead`. `remove_dead_marked` writes a mark at `types.name_ends[name]` with the value `types.newest[name]`.
- **[Observed]** The lexer drops comments (`//` to the line end) and keeps byte ranges per token. A string can hold `//`, `->` and `=`.
- **[Observed]** `newest_version` is the mark, else the chain end, else 1. `versioned` is true for a chain or a mark. So removing `v1` without a chain changes the decode (O3).
- **[Observed]** The compiler rejects a second EFFECT (`slice 1 supports one effect`). A source with an EFFECT needs `--stored` to compile.
- **[Observed]** A file stem must be a lowercase identifier when the source has an EFFECT or a pipe. So the test copies `<name>.formatted.beaml` to `<dir>/<name>.beaml` before a compile or a `fmt`.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| F1 | Undo | All RED cases go in `slice6_fmt_test.py`. Rust unit tests wait for GREEN. | Unit tests in `main.rs` now | RED does not change the production file (task). |
| F2 | Undo | Two fixtures with hand-written expected files: `slice6/fmt/clauses` (alignment, groups, comments, EFFECT line) and `slice6/fmt/marks` (DL-104 rules). The CRLF case is a CRLF copy that the test makes from these files. | A stored CRLF fixture like slice 5 `Q4-crlf` | One source of truth per case; the copy is exact. |
| F3 | Repair | **Chose:** the EFFECT case is one EFFECT line with extra spaces; `->` and `=` get one space before them. **Over:** the plan case (b), two aligned EFFECT lines. **Because:** the compiler rejects a second EFFECT, and `fmt` writes nothing for an invalid source, so two EFFECT lines cannot be formatted in 6b. **Commits us to:** two-line EFFECT alignment stays untested until a source with two EFFECTS builds (U6). | Two EFFECT lines | Observed limit. |
| F4 | Repair | **Chose:** a signature line (`fn` line without `=`) is not a clause. It stays byte-equal and ends a group. **Over:** align it as the header row of its clauses. **Because:** DL-083 names clauses; a typed signature widens every column. **Commits us to:** the OWNER may read DL-083 otherwise (U11). | Header row | DL-083 text. |
| F5 | Repair | **Chose:** a lone single-line clause or EFFECT line is a group of one; its gaps before the columns become one space. **Over:** leave lone lines as they are. **Because:** the column rule F6 gives one space; one rule for every group. **Commits us to:** `fmt` changes extra spaces in every single-line clause. | Lone lines untouched | Same rule. |
| F6 | Repair | **Chose:** a cell is a top-level argument text with its comma (patterns may hold `(...)` and `{ ..., ... }`). Column k starts one space after the longest cell k-1 of the group. `->` follows the last argument column; `=` follows the return TYPE and its `!` list. No width limit. **Over:** align each token. **Because:** DL-083 asks for a table of argument columns, `->` and `=`. | Per-token columns | DL-083. |
| F7 | Repair | **Chose:** the source check of `fmt` runs without `--stored` (parse, TYPE VERSIONS, M1, type checks); a source with an EFFECT formats. **Over:** `fmt SOURCE --stored SNAPSHOT`. **Because:** the D6B-41 command has no `--stored`, and DL-104 keeps the newest version, which needs no stored record. **Commits us to:** GREEN separates the source check from the stored-record checks. | Require `--stored` | D6B-41 command form. |
| F8 | Undo | Invalid source: exit 1, empty stdout, same bytes and inode, no new file in the directory; stderr holds the first line of the compile error of the same source. Cases: a syntax error and an M1 mark. | Exact stderr text | The error text belongs to the compile path. |
| F9 | Repair | CRLF line ends stay CRLF; an edit never touches a line end. A blank line is an empty line or a line with only `\r`. | Write LF | D6B-42: every other byte stays. |
| F10 | Undo | An unchanged file is not rewritten (same inode), stdout is empty, exit 0. | Always rewrite | No write without a change; idempotence check. |
| F11 | Undo | Event `{"source":"cli","action":"fmt","result":"ok","changed":N}`; an error gives `"result":"error","changed":0`. N is the count of old lines whose bytes change (`fmt` adds and removes no line). | Count diff hunks | D6B-46 "count of changed lines". |
| F12 | Undo | The diff label is SOURCE as given, as for `--remove-dead`. The test compares stdout with `difflib.unified_diff(..., n=0)` (slice 5 squash test form). | Absolute path | Same as `--remove-dead`. |
| F13 | Undo | Every line-level test requires exit 0 first, so a no-op cannot pass a "kept" or "not aligned" case. | Compare lines only | A no-op `fmt` passed 6 cases in a first run. |
| F14 | Undo | Guard `test_guard_expected_fixtures_compile_like_their_sources`: each expected file compiles like its source, offsets replaced. It passes on the baseline. | No guard | A wrong hand-written expected file would give a false RED. |
| F15 | Undo | The compile-equivalence test compiles with `--stored stored/empty.jsonl` and the same file name, and replaces `# beaml-declaration-v1 NAME A B` offsets by `N N`. | Raw compare | D6B-45. |
| F16 | Undo | Baseline self-check: removing `v1` from `type Payment v1` changes 70 output lines; removing `v3` from `type Squashed v3` changes 8. So the compile-equivalence test catches a wrong mark removal (O3). | No check | Evidence that D6B-45 (f) has power on this fixture. |

### Points the plan does not settle

- **U1 [Unknown] Tab characters.** A gap before a column is replaced as a whole, so a tab there becomes spaces; a tab elsewhere stays. Column width counts bytes. Not tested. Class Undo.
- **U2 [Unknown] Trailing spaces.** Trailing spaces on a clause line are not a column and stay. Tested on a comment line only. Class Undo.
- **U3 [Open] A clause longer than the others.** One long pattern widens the whole group (no width limit, F6). DL-083 sets no limit. Class Repair; an OWNER limit is a change of DL-083.
- **U4 [Open] `!` and `|` failure lists.** Not columns; only the `=` after them aligns. DL-013 and DL-083 name arrows and `=` only. Class Repair.
- **U5 [Unknown] Clauses with different argument counts in one group.** Possible only with two signatures of one name and no signature line between; F4 makes the signature line end a group. Not tested. Class Undo.
- **U6 [Open] Two EFFECT lines (F3).** Testable when a source with two EFFECTS builds. Class Repair.
- **U7 [Unknown] A file named `fmt`.** `beaml-spike fmt` with one argument stays a compile of the file `fmt`. Not tested. Class Undo.
- **U8 [Inference] DL-081 against DL-104.** DL-104 supersedes the no-chain text. No open question.
- **U9 [Unknown] A comment after a clause in a group.** It moves right with its clause; its bytes stay (fixture line 24 is a group of one). Not tested in a group of two or more. Class Undo.
- **U10 [Observed] Plan text.** "Today: `cannot read source`" is wrong; the actual text is the usage line. Class Undo (docs).
- **U11 [Open, OWNER] Readings of DL-083.** F4, F5 and U3 read an OWNER Migrate text. They change only `fmt` output and a new `fmt` run reverses them. Class Repair; report them to the OWNER in the step report.

## RED

Command (repository root): `BEAML_SPIKE=<scratch>/basecd37/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py -v`. Full output: [red-output.log](red-output.log).
Baseline compiler: commit `cd379ff0`, `cargo build --offline` of a `git archive` copy. Toolchain: cargo 1.94.0, rustc 1.94.0, Python 3.13.12.
Inputs (sha256):
- `slice6/fmt/clauses.beaml` `d0512822023d4690b4fefd6fb295c6a315933e5d3ee052f37a491d5f27784762`
- `slice6/fmt/clauses.formatted.beaml` `7086d08cad4737b333a5038136dea4f19a07c9978792ae25b0a882f13fb81155`
- `slice6/fmt/marks.beaml` `dce5e4983071bf73c7bd55f7ef98e79dcf4d624ee71bb4c8fc1d2e40cc96132a`
- `slice6/fmt/marks.formatted.beaml` `2d94e41854ae0bb22ae0565ba0a33695e4dffefd0570f5654a31ea38f431d906`
- `tests/slice6_fmt_test.py` `d5e611408c8e8ba992fc969bfda5ae1a4bbc9a8a9c4333c7612b86ea9f3a322f`

Result: 22 tests, 21 FAIL (26 failures with subtests), 1 pass (guard F14). Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_fmt_rewrites_the_file_and_prints_the_diff` [clauses, marks] | exit 0, expected file, new inode, diff | exit 1, usage text, file unchanged | No `fmt` command. |
| `test_fmt_needs_no_stored_snapshot` | exit 0, expected file | exit 1, usage | Same. |
| `test_clause_group_aligns_argument_columns_arrow_and_equals` | aligned group A | exit 1, usage | Same. |
| `test_extra_spaces_before_equals_become_one_column` | lines 16, 17 aligned | exit 1, usage | Same. |
| `test_blank_line_breaks_a_group` | line 19 not padded, exit 0 | exit 1, usage | Same. |
| `test_comment_line_breaks_a_group` | lines 19 to 21 not padded, exit 0 | exit 1, usage | Same. |
| `test_multi_line_clause_breaks_a_group` | line 28 padded, 24 not | exit 1, usage | Same. |
| `test_lone_clause_is_a_group_of_one` | one space gaps | exit 1, usage | Same. |
| `test_effect_line_aligns_arrow_and_equals` | one space gaps | exit 1, usage | Same. |
| `test_comments_stay_byte_for_byte` | comment bytes stay, exit 0 | exit 1, usage | Same. |
| `test_mark_removed_when_a_chain_from_v1_implies_it` | `type Chained {` | exit 1, usage | Same. |
| `test_squash_mark_without_chain_is_kept` | `type Squashed v3 {`, exit 0 | exit 1, usage | Same. |
| `test_v1_mark_without_chain_is_kept` | `type Payment v1 {`, exit 0 | exit 1, usage | Same. |
| `test_mark_written_when_the_chain_starts_above_v1` | `type Shortened v5 {` | exit 1, usage | Same. |
| `test_mark_kept_beside_a_chain_above_v1_and_chain_from_v1_unchanged` | lines 15, 19 stay, exit 0 | exit 1, usage | Same. |
| `test_fmt_is_idempotent` [clauses, marks] | exit 0 twice, second run empty | exit 1 | Same. |
| `test_compiled_output_equal_except_declaration_offsets` [clauses, marks] | fmt exit 0, equal build | fmt exit 1 | Same. |
| `test_invalid_source_writes_nothing` [syntax, m1] | stderr holds the source error | stderr is the usage text | Exit 1 for the wrong reason. |
| `test_crlf_line_ends_stay` [clauses, marks] | CRLF expected file | exit 1, usage | Same. |
| `test_action_event_counts_changed_lines` | `fmt` events 7, 0, error 0 | no `fmt` event | Same. |
| `test_action_event_counts_changed_lines_of_marks` | `fmt` event 2 | no `fmt` event | Same. |
| `test_guard_expected_fixtures_compile_like_their_sources` | pass | pass | Guard F14. |

- **[Observed]** Every failure has the usage text as its cause; no setup failure. The CRLF copies build on the baseline (fixture check inside the test passed before the `fmt` call).
- **[Inference]** The RED is genuine: each case needs the `fmt` command, and F13 stops a no-op from passing.

## RED repair

Trigger: [red-review.md](red-review.md) R1 (high), R2 and R3 (medium), the `=` column note. The production file was not changed. Same scratch baseline `cd379ff0` as in RED.

### Changes

- **R1.** `clauses.beaml` lines 44 to 46: `fn one` and `fn other_name`, adjacent one-line fns of different names. Each is a group of one with one-space gaps, so both lines stay. Test `test_one_line_fns_of_different_names_do_not_align`.
- **`=` column.** `clauses.beaml` lines 48 to 51: `fn check` clauses with equal argument and `->` columns. The return text of line 51 has one more space after `!` (not a column, U4). Only `=` aligns: line 50 gets two spaces before `=`. Test `test_equals_column_aligns_when_only_the_return_text_differs`.
- **R2.** `test_fmt_is_idempotent` and `test_compiled_output_equal_except_declaration_offsets` assert that the first `fmt` result is `expected(name)`.
- **R3 isolation.** In `clauses.beaml`, the signature lines and the comment lines above group A (lines 8, 9) and the `tag` group (lines 14, 15) changed places. A comment line now ends each group under both readings of F4. The new fixture `slice6/fmt/header` holds the only signature line directly above clauses. Test `test_signature_line_ends_a_group` compares it with `header.formatted.beaml`. `header` is in `NAMES`, so the guard, idempotence, compile-equivalence and CRLF cases include it.
- `CHANGED["clauses"]` is 8 (was 7): line 50 is the new changed line.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| F17 | Undo | R1 and the `=` case go at the end of `clauses.beaml`; earlier line numbers stay. | A new fixture per case | Fewest files; no test line number changes. |
| F18 | Repair | **Chose:** the `=` case uses a different gap inside the `!` list. **Over:** two EFFECT lines (F3). **Because:** the baseline rejects clauses whose return text differs by tokens (`inconsistent function signature`), and one EFFECT per source is the limit. A gap inside the return text is the only observed way. **Commits us to:** GREEN measures the `=` cell by its bytes, with inner gaps. | Two EFFECT lines; no `=` case | Observed on the baseline. |
| F19 | Repair | **Chose:** isolate F4 in `slice6/fmt/header`; move a comment line between each signature line and its clauses in `clauses.beaml`. **Over:** keep the signature lines directly above groups in `clauses.beaml`. **Because:** an OWNER answer to Q6B-9 then changes one file, `header.formatted.beaml`. **Commits us to:** `clauses.beaml` does not test F4. | Leave F4 in `clauses` | Task R3. |
| F20 | Undo | R2 asserts `(code, file) == (0, expected)` with stderr in the message. | Assert the file only | The failure cause shows the usage text. |
| F21 | Undo | The two event tests keep the cause "no `fmt` event"; the usage text is not in their output. | Assert the stderr in event tests | Same as in RED; the event has no stderr. |

### Q6B-9 [Open, OWNER] Signature line above clauses (F4, R3)

- Option A (current fixtures): a signature line (no `=`) stays byte-equal and ends the group. Only the clauses align.
- Option B: the signature line is the header row of the group. Its cells widen each column of the clauses below it.
- Effect of an answer B: only `slice6/fmt/header.formatted.beaml` changes (and the test name). Class Repair: a new `fmt` run reverses it.

### Rerun (RED repair)

Command: same as RED. Full output: [red-output.log](red-output.log). Toolchain the same.
Inputs (sha256):
- `slice6/fmt/clauses.beaml` `fbbe51b5900a35c618d722d6f537e89989d26837d7cbecfb3be25eed421ff134`
- `slice6/fmt/clauses.formatted.beaml` `1760f06a087310bbe47909eb87b70d89a81207591ef2bb7455e23cb791c85f52`
- `slice6/fmt/header.beaml` `c2e0afbe5dd9da98f0106cfb48e6327c387d8fb72cee8f799f108edcee7a8de0`
- `slice6/fmt/header.formatted.beaml` `253f289083d37c293092f52cc868621503a35ef1f16b518a1e91720e2d0af15b`
- `slice6/fmt/marks.beaml`, `marks.formatted.beaml`: unchanged.
- `tests/slice6_fmt_test.py` `977d335d96824fdf4db19abb2fcf54aac811f62dfde20f99e271f1a8f9f346ac`

- **[Observed]** 25 tests, 24 FAIL (33 failures with subtests), 1 pass (guard F14, now with `header`). Exit 1.
- **[Observed]** The 3 new tests and the new `header` subtests fail with the usage text. Of 33 failures, 31 show the usage text; the 2 event tests fail with "no `fmt` event".
- **[Observed]** Scratch fake `fmt` (the review fake, wrapper over the baseline) probes:

| Fake `fmt` | Result |
|---|---|
| Writes the expected file | 25 of 25 pass |
| No-op, exit 0 | idempotence and compile-equivalence now fail (R2) |
| Pads `fn one` to `fn other_name` (adjacency-only) | R1 test fails |
| One space before `=` on line 50 | `=` test fails |
| Header row in `header` (option B) | `test_signature_line_ends_a_group` fails |

- **[Inference]** R1, R2, R3 and the `=` note are closed for RED. U5 and U9 stay untested (low).

## GREEN

Changed file: `experiments/0001-syntax-to-beam/src/main.rs` (sha256 `a4dbc788304e8694660d268b0089667e0d3e592430648901cb03ecbd51474ccb`). No test or fixture changed. `run.py` was not run. Not committed.
Full output: [green-output.log](green-output.log). Toolchain: cargo 1.94.0, rustc 1.94.0, Python 3.13.12.

### Change

- `main()`: the argument form `fmt SOURCE` starts `fmt_file`. The action event is `fmt` with `changed: N`; an error gives `changed: 0`.
- `fmt_file`: read SOURCE, call `formatted`, return 0 when the text is the same (no write, no output). Else count the changed lines, print `unified_diff`, write with `write_atomic`.
- `formatted`: `lex`, `Parser::program`, `Checker::new`, `Checker::validate`. This is the source check of `build_with_refusals` before the file-name check and `--stored`. Then the mark edits and the column edits, applied from the end of the text.
- `fmt_mark(mark, chain)`: the DL-104 rule as a pure function. Unit test `fmt_mark_follows_dl104` (7 cases).
- `aligned`: rows are single-line clauses and EFFECT lines that are alone on their line. A group is consecutive lines with the same clause `key` and the same cell count. Only the gaps between cells change.

### Results

- **[Observed]** `slice6_fmt_test.py`: 25 of 25 pass.
- **[Observed]** int 16, failure 22, enum 20, pipe 12, decode 10, struct_order 2: all pass. constructor 24 of 25 and decode_ctor 0 of 7: RED by design until step 8.
- **[Observed]** `stored_types_test` 33, `slice3_types_test` 69, `slice4_retire_test` 87, `slice5_syntax_test` 60, `slice5_squash_test` 24, `slice5_rewrite_test` 5: all pass.
- **[Observed]** `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings`, `cargo test --offline --no-fail-fast` (18 + 14): pass.
- **[Observed]** Scratch probe: `fmt` on a copy of each of the 1737 tracked `.beaml` files. No panic. A second `fmt` of each formatted file gives no change (idempotence). Not retained as evidence; the command is in this section only.
- **[Inference]** The compile invariant (D6B-45) holds by construction: an edit replaces only spaces between tokens or applies `fmt_mark`, which keeps `newest_version` and `versioned`. The test checks it on three fixtures only.

### Decisions

| # | Class | Choice | Alternative | Reason | By |
|---|---|---|---|---|---|
| G1 | Undo | The source check is parse, `Checker::new` and `validate`. The file-name rule for EFFECTS and pipes is not checked. | Run the full `build` check without `--stored` | The file name is not source text; a wrong name still fails the compile. | Opus (GREEN, slice6b-fmt) |
| G2 | Undo | A group key is the clause `key` (the signature, `T#k` for a constructor), not only the `fn` name. | The `fn` name | Two signatures of one name never share a column table (U5). | Opus (GREEN, slice6b-fmt) |
| G3 | Undo | Consecutive EFFECT lines form one group by the same rule (key `effect`). | Lone EFFECT lines only | One rule; untestable today (F3, U6). | Opus (GREEN, slice6b-fmt) |
| G4 | Undo | Lines with a different cell count do not join a group. | Pad missing cells | No case exists today (U5). | Opus (GREEN, slice6b-fmt) |
| G5 | Undo | The gap after `->` is a column gap: the return text starts one space after `->`. | Keep the gap after `->` | Fixture line 31 requires it. | Opus (GREEN, slice6b-fmt) |
| G6 | Undo | The gap between `fn` and the name, and gaps inside a cell (`x: String`, the `!` list), stay. | Normalize them | D6B-42: only the column gaps change (U4). | Opus (GREEN, slice6b-fmt) |
| G7 | Undo | Mark removal removes the mark token and the spaces and tabs before it, not past the TYPE name. | Remove from the name end | A comment between name and mark stays. | Opus (GREEN, slice6b-fmt) |
| G8 | Undo | A row must be alone on its line: no token of another item before or after it on that line. | Align any single-line clause | Two items on one line have no column table. | Opus (GREEN, slice6b-fmt) |
| G9 | Undo | Line numbers come from a byte count from the file start (`ponytail:` comment in the code). | A line index table | Fine below the 256 KiB source limit. | Opus (GREEN, slice6b-fmt) |
