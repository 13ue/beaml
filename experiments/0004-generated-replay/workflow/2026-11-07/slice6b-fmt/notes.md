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
