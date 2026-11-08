# RED plan: fates-a4

**[Proposal]** RED phase, 2026-11-08, HEAD `d6ab59c9`. Tests only; no production file (`main.rs`, `grammar.js`,
`highlights.scm`, `src/`, wasm) changed. Inputs: [plan.md](plan.md) with its Repairs section, [plan-review.md](plan-review.md).
By: Opus (RED fates-a4) for every decision in this file.

## Tests written

| ID | Where | Inputs | Expected (built defaults QA4-1 A, QA4-2, QA4-3) |
|---|---|---|---|
| T1 | `slice6_fmt_test.py` `test_fates_fixtures_are_fmt_fixed_points` | 7 fates fixtures, read-only copies | exit 0, empty stdout, bytes equal |
| T2 | `test_mark_kept_when_the_chain_holds_a_fate_line` | `order_map` with `quarantine channel "fax"` as the last step | `type Order v3 {` stays, file equal |
| T3 | `test_migrate_body_two_changes_one_per_line` | 8 subTests (below) | one change per line, comma after its change, `}` alone |
| T4 | `test_migrate_body_one_change_one_line` | `{quarantine "fax"}`, `{` NL `quarantine value` NL `}` | `{ change }` |
| T5 | `test_migrate_body_with_a_comment_stays` | body with `// zero amounts` on a member line | body unchanged (guard) |
| T6 | `test_fates_layout_idempotent_and_build_equal` | every T3 and T4 input (10) | full text with mark; 2nd fmt prints nothing, same inode; Elixir equal except offsets |
| G1 | `integrations/zed-beaml/test/corpus/fates.txt` | 7 entries | named nodes, no `ERROR` |
| G2 | `integrations/zed-beaml/test/highlight/fates.beaml` | fate lines, enum mark, controls | `keyword`, `number`, `constructor`, `property`, `function` |
| G3 | `test_grammar_parses_fate_sources` | 7 fixtures + 5 0005 sources | `parse -q` exit 0, no `ERROR`; skip without CLI |
| N17 | 0005 `run.py` `n17()`, `EXPECTED` | `app/beaml/orders.beaml` + 4 variants, copies in the run dir | fmt twice, exit 0, empty stdout |

T3 subTests: owner TYPE step (`map f "l" -> C` + `quarantine f "l"`, three spaces after the comma), two quarantine lines
on one TYPE (DL-172), `quarantine value ,` (O2), leading comma (O2), enum step (`quarantine "l"` + `map "l" -> C`),
blank lines in the body, `rename` beside a fate line, CRLF.

G1 entries: enum mark and two declarations of one enum; `quarantine f` / `"l"` / `f "l"` and two in one body; `map "l" -> C`
and `map f "l" -> C`; `redact f` and `retire f keep N days`; multi-line body with comment and leading comma; keyword
controls (guard: `fn map`, `type T { map: String, quarantine: String, redact: String }`, `rename map -> route`,
`drop redact: String`); `quarantine map, quarantine redact "x"`.

## Decisions (By: Opus, RED fates-a4)

**Repair**
→ T3, T4, T5 mask the TYPE mark statt full text, weil the body rule must fail apart from QA4-1
⠀⠀↳ commits us to: T6 and T1/T2 carry the mark check
→ T2 fate line in the last step statt first step, weil the checker allows fate lines only there
→ T6 builds with `slice6/db/stored/responses.jsonl` statt `stored/empty.jsonl`, weil db sources need `rows.jsonl`
→ T6 compares exit code and stdout statt stderr, weil DEAD LINE warnings print line numbers
→ blank lines in a MIGRATE body go statt stay, weil the TYPE body rule drops them at HEAD
⠀⠀↳ commits us to: one more detail on the QA4-2 OWNER card
→ G1 keyword controls split: guard entry plus `quarantine map` entry, weil one entry hid the guard

**Undo**
→ `fmt_mark_follows_dl104` unit case left to GREEN (production file, signature open)
→ inline sources only; no tracked `slice*/**.beaml` added
→ N17 runs after n14; fmt cwd is the copy directory (events stay in the run dir)
→ RED depth probe not run (needs a scratch production build); covered by construction
