# Plan: fates-a4, `beaml fmt` and tree-sitter for VERSION MARKS, MIGRATE STEPS and fate lines

**[Proposal]** PLAN phase, 2026-11-08, HEAD `7c459b54`. Task records only. No production file, no test, no commit.
Parent plan: [fates/plan.md](../fates/plan.md) step a4 (PF-19, QF-7). Rule sources: DL-104, DL-148, DL-155, DL-158, DL-161,
DL-162, DL-167 (By: 13ue, DL-167 By: Fable). Evidence: [fates/green-output.md](../fates/green-output.md) section 2 (GF-12),
[fmt-layout/notes.md](../fmt-layout/notes.md). Machine form: [plan.json](plan.json). By: Opus (PLAN fates-a4) for every
proposal in this file.

**Test-first rule: applies.** `fmt` output and the tree-sitter parse trees are behavior; each change gets a failing test first.

## Scope

1. `fmt` keeps the TYPE VERSION MARK of a chain that holds a fate line (`type Amount v2`, `type Order v3`). ENUM marks stay (they
   stay already at HEAD).
2. `fmt` lays out a MIGRATE STEP body: zero or one change on one line, two or more one per line (PF-19). Fate lines are changes.
3. Second `fmt` run prints nothing. Compiled output equal except `beaml-declaration-v1` offsets.
4. Tree-sitter: `enum E vN`, `quarantine`, `map`, `redact`, `retire … keep N days` inside `migrate`; highlights; corpus; wasm.
5. DL-158: EXPERIMENT 0005 gets use case N17, `fmt` fixed point over every `app/beaml` source and variant.

Excluded: new fate semantics, checker texts, `--stored`, record format (a2a), 0005 fate variants (a3), D038 line length, Zed itself.

## Facts at HEAD `7c459b54` (observed, scratch copies, release binary of 14:03)

- **[Verified]** `fmt` on copies of the seven `slice6/db/fates/*/orders.beaml`: all exit 0; the second run prints nothing.
  Three files change on the first run: `amount_v2` and `two_ctor` lose `v2` (`type Amount {`), `order_map` loses `v3`.
  Cause: `fmt_mark` (main.rs line 7497), DL-104 A, "a mark that a chain from v1 implies goes". `channel_v1`, `channel_v2`,
  `channel_swap`, `stricter_v1` stay byte-equal (enum marks are in `program.enum_marks`, not `program.marks`).
- **[Verified]** The mark removal does not change the build: `amount_v2`, `two_ctor`, `order_map` compile with
  `--stored slice6/db/stored/responses.jsonl` to the same Elixir before and after `fmt` (offsets and module name masked).
  So for a TYPE the mark is redundant to the compiler; keeping it is a layout and readability choice (QA4-1).
- **[Verified]** `fmt` never touches a `migrate` line. `bodies` (line 7541) edits `type` and `enum` bodies only; `aligned`
  (line 7599) takes clause, signature, EFFECT and ENTRY lines only. Probe: `{map channel "app" -> Mobile,   quarantine channel "fax"}`
  and a multi-line body with mixed indent both stay as written, exit 0.
- **[Verified]** The parser (line 891) needs `,` between MIGRATE CHANGES, no trailing comma (K9, K10). Newlines are free.
- **[Verified]** `fmt` runs `Checker::validate` first; a source with a wrong fate line is not formatted (exit 1, file unchanged).
- **[Verified]** Tree-sitter `parse -q` (CLI 0.26.5 at `/private/tmp/beaml-zed-highlighting/tools/tree-sitter`): `ERROR` in
  `amount_v2` (row 10, `quarantine value`), `channel_v2` and `channel_swap` (row 12, the enum mark), `order_map` (row 30, `map`).
  `grammar.js`: `enum_declaration` has no version; `_migrate_operation` is `rename`, `add`, `drop` only.
- **[Verified]** Tracked sources with two or more changes on one migrate line: slice 3 to 5 fixtures (11 files) and
  `integrations/zed-beaml/test/highlight/forms.beaml`. None is a `fmt` input in any test (parent plan, fmt-layout P1).
  Five slice 4/5 sources hold `migrate Payment v2 -> v3 {` with one change on its own line; PF-19 would join it on their first
  `fmt`. Not run in tests.
- **[Verified]** 0005 at HEAD has no fate line (a3 not landed). `fmt` over copies of `app/beaml/orders.beaml` and the four
  variants: exit 0, empty diff.

## Layout rules a4 builds (and the OWNER questions they raise)

DL-148 covers TYPE bodies, ENUM bodies and clause tables. It does not cover MIGRATE STEP bodies or the mark of a fate chain.
So every rule below is an open OWNER question with a built default (DL-139: syntax and layout are OWNER territory).

**QA4-1 · Migrate · Does `fmt` keep `type Amount v2` when `migrate Amount v1 -> v2 { quarantine value }` implies it?**
→ A (built default): keep the mark when a step of the chain holds a fate line; DL-104 A unchanged for every other chain.
⠀⠀↳ the seven fates fixtures stay byte-equal; `marks.beaml` keeps its expected file
→ B: `fmt` never removes a mark. `marks.formatted.beaml` changes (`type Chained v3`), a byte-guard.json row moves.
→ C: DL-104 A as built. The fates fixtures change on `fmt`; the version is visible only through the `migrate` lines.
→ Evidence: observed: removal does not change the build. Observed: DL-155 effect text "Supersedes the DL-104 reading … in so far as
  the version is now forced by data"; DL-167 "DL-155 forces the mark when stored values are affected". Inferred: a fate line is the
  source sign that stored values were affected, so A is the narrowest reading. Unknown: OWNER intent for chains without fate lines.

**QA4-2 · Migrate · MIGRATE STEP body layout (PF-19; QF-7 A was ruled by Fable, not answered by the OWNER in words).**
→ Built default: the DL-148 TYPE body rule. Zero or one change: `migrate T vA -> vB { change }`. Two or more: one change per line,
  indent of the `migrate` line plus two spaces, the comma stays at the end of its change, `}` alone at the `migrate` indent.
  A body that holds a comment stays as written (fmt-layout F4). Each change keeps its own text (F7). CRLF stays (F8).
→ Commits us to: the slice 3 to 5 sources above change on their first `fmt`.

```beaml
// fmt input
migrate Order v2 -> v3 {map channel "app" -> Mobile,   quarantine channel "fax"}
migrate Kind v1 -> v2 {
    quarantine "c"
}

// fmt output (built default QA4-2)
migrate Order v2 -> v3 {
  map channel "app" -> Mobile,
  quarantine channel "fax"
}
migrate Kind v1 -> v2 { quarantine "c" }
```

**QA4-3 · Migrate · Do fate lines or consecutive `migrate` lines align as a table (columns for `->`, the literal)?**
→ Built default: no. DL-148 (3) names clause, signature and EFFECT lines only; TYPE fields do not align either.
→ Option: a column table inside one body (`map "app"  -> Mobile` / `map "fax"  -> Web`). New rule; needs the OWNER.

## Step design (minimum)

- `main.rs` `formatted`: pass "chain holds a fate line" into the mark decision (`Change::fate` exists from a1). `fmt_mark` and
  its unit test `fmt_mark_follows_dl104` get one case (kept mark on a fate chain); the other seven asserts stay.
- `main.rs` `bodies`: one more branch for `migrate`: find `{` after the `migrate` token, split members on top-level `,`
  (a member keeps its comma), reuse the same `0 / 1 / many` body writer. No other function changes.
- `integrations/zed-beaml/grammar.js`: `optional(field("version", $.version))` on `enum_declaration`; `_migrate_operation` gains
  `quarantine_operation` (`quarantine` then a property, a string, or both), `map_operation` (`map`, optional property, string,
  `->`, constructor), `redact_operation` (`redact` property), `retire_operation` (`retire` property `keep` integer `days`).
  `highlights.scm`: `"quarantine" "redact" "map"` in the keyword list. Regenerate `src/` (`tree-sitter generate --abi 15
  --js-runtime native`) and `grammars/beaml.wasm` (README steps).
- `experiments/0005-prototype-fullstack/run.py`: `n17()` beside `n14()`: copy `app/beaml/orders.beaml` and every
  `app/beaml/variants/*/orders.beaml` into the run directory, run `fmt` twice on each copy; pass when every run exits 0 and
  prints nothing. Writes start and finish to `use-cases.jsonl` (no source text, no path in events). `EXPECTED` gains N17.
  It runs on copies, so `lib/generated/orders.ex` and the sources never change.

## RED tests (each fails at HEAD for the stated reason)

New tests in `experiments/0004-generated-replay/tests/slice6_fmt_test.py` (step `slice6-fmt` exists in 0004 `run.py`). Inline
sources or read-only copies of the `slice6/db/fates/` fixtures. No new tracked `.beaml` under `experiments/0004-generated-replay/`.

| ID | Name | Proves | Fails at HEAD because |
|---|---|---|---|
| T1 | `test_fates_fixtures_are_fmt_fixed_points` (subTest per fixture, 7) | exit 0, empty stdout, bytes unchanged | `amount_v2`, `two_ctor`, `order_map` lose the mark (4 subtests are guards) |
| T2 | `test_mark_kept_when_the_chain_holds_a_fate_line` | inline `type Order v3` + `add` step + `map` step keeps `v3` | `fmt` writes `type Order {` |
| T2b | existing `test_mark_removed_when_a_chain_from_v1_implies_it` | DL-104 A stays for chains without fate lines | guard, passes |
| T3 | `test_migrate_body_two_changes_one_per_line` (subTests: owner TYPE step, enum step, `rename` beside a fate line, CRLF) | QA4-2 multi-line form, commas kept | body unchanged |
| T4 | `test_migrate_body_one_change_one_line` (`{quarantine "c"}`, a multi-line single change) | `{ change }` | body unchanged |
| T5 | `test_migrate_body_with_a_comment_stays` | comment body untouched | guard, passes |
| T6 | `test_fates_layout_idempotent_and_build_equal` | second run prints nothing; Elixir equal except offsets | first run does not give the expected text |
| G1 | corpus `integrations/zed-beaml/test/corpus/fates.txt` (`tree-sitter test --rebuild`) | the five fate forms, `enum E v2`, two declarations of one enum, a multi-line body, control `fn map x: String -> String = x` parse to named nodes | `ERROR` nodes |
| G2 | highlight `integrations/zed-beaml/test/highlight/fates.beaml` | `quarantine`, `map`, `redact` are `keyword`; the enum mark is `number`; the `map` target is `constructor` | no keyword capture |
| G3 | `test_grammar_parses_fate_sources` in `slice6_fmt_test.py` (pattern of `slice6_db_test` N16) | `tree-sitter parse -q`: no `ERROR` in the seven fates fixtures and the five 0005 sources | `ERROR` in four fixtures |
| N17 | 0005 `run.py run`, `n17()` | every app source and variant is a `fmt` fixed point | guard at HEAD (no 0005 source has a fate line yet); real RED only when a3 lands `type Amount v2` first (see order) |

**[Proposal]** RED depth probe: a scratch build that only keeps the mark (no body rule) must still fail T3, T4, T6; a build
with only the body rule must still fail T1, T2. Then neither half can pass the slice alone.

G3 skips when the CLI is missing (`TREE_SITTER` env, as N16). The TEST phase counts a skip as a missing check, not a pass.

## Checks for TEST

```sh
python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py
python3 -B experiments/0004-generated-replay/run.py
cd experiments/0001-syntax-to-beam && cargo fmt --check && cargo clippy -- -D warnings && cargo test
cd integrations/zed-beaml && tree-sitter test --rebuild && tree-sitter test --wasm --rebuild
python3 integrations/zed-beaml/preview.py --chat experiments/0004-generated-replay/slice6/db/fates/amount_v2/orders.beaml experiments/0004-generated-replay/slice6/db/fates/channel_v2/orders.beaml
python3 -B experiments/0005-prototype-fullstack/run.py run
```

The preview check passes when the fragment holds `<i class=k>quarantine</i>`, `<i class=k>map</i>` and the enum mark
`<i class=c>v2</i>`, and no line of the fixture is uncoloured where the corpus has a node. The OWNER sees it in the chat widget.

## Files touched

| File | Change |
|---|---|
| `experiments/0001-syntax-to-beam/src/main.rs` | `formatted`, `fmt_mark`, `bodies`; unit test `fmt_mark_follows_dl104` |
| `experiments/0004-generated-replay/tests/slice6_fmt_test.py` | T1 to T6, G3 |
| `integrations/zed-beaml/grammar.js`, `languages/beaml/highlights.scm` | rules, keywords |
| `integrations/zed-beaml/src/{parser.c,grammar.json,node-types.json}`, `grammars/beaml.wasm` | generated |
| `integrations/zed-beaml/test/corpus/fates.txt`, `test/highlight/fates.beaml` | new |
| `experiments/0005-prototype-fullstack/run.py` | `n17()`, `EXPECTED` |
| this ledger | records |

Not touched: every `.beaml` fixture (read only), `slice6_fates_test.py` (a2a owns it), wiki, READMEs (docs phase).

## Byte-pin impact: none moves (confirmed by reading the guards)

| Site | Kind | Moves? | Reason |
|---|---|---|---|
| `tests/slice5_syntax_test.py` `PIN` | hash | no | compiles sources listed at its BASE; `fmt` does not change compiled output |
| `tests/slice6_entry_test.py` `BASE` | hash | no | `ls-files` globs `slice*/*.beaml`, `bad/`, `drift/`, 0001, 0002; a4 adds no file there |
| `tests/slice6_multi_test.py` `BASE` | hash | no | same globs |
| `tests/slice6_db_test.py` `P4_BASE` | hash | no | same globs plus `arms/` |
| `tests/slice6_pipe_test.py` `EFFECT_OUTPUTS` | digest | no | no codegen change |
| `tests/slice6_host_struct_test.py` `BYTE_GUARD` | digest | no | no codegen change |
| `slice6/effect-reach/byte-guard.json` | digest | no | fixed 71-row table; `slice6/fmt/*` rows stay because no fmt fixture changes under QA4-1 A |

**[Inference]** Two ways a4 could move pins, both avoided by design: (1) a new tracked non-db `.beaml` with fate syntax under
`slice*/` makes the three `ls-files` hash guards compile it with their old compiler (parse error there, exit 0 now): so the
tests stay inline. (2) QA4-1 B rewrites `marks.formatted.beaml`: one byte-guard.json row moves (the fmt-layout P3 case). If the
OWNER picks B, the move follows the two-commit rule with a masked diff proof.

## Overlap with fates-a2a and order

- a2a GREEN (record format draft 4) changes `main.rs` in the writer, the reader, `--stored` and codegen, and moves the six pins
  once (DL-168). a4 changes only the `fmt` region (lines 7495 to 7610) and one unit test. The hunks do not overlap; a4 reads no
  a2a code and a2a reads no `fmt` code.
- Shared file: 0005 `run.py` (`EXPECTED`). a2a RED already added N16 (committed `fc4e3acf`); a4 adds one line after it.
- Rule: one code writer at a time. Order: a2a GREEN (after QA2-1 is signed) first, then a4 RED and GREEN on the new HEAD.
  If QA2-1 waits, a4 may go first; a2a GREEN then starts from the a4 commit. No result of a4 depends on a2a.
- a3 (0005 fate variants) is independent of a4. If a3 lands first, N17 is a real RED at a4 time (the stricter v2 source loses
  its mark under HEAD `fmt`). If a4 lands first, N17 guards a3: its new sources must be `fmt` fixed points.

## Risks

- R1 QA4-1 contradicts DL-104 A literally. The default is the narrow DL-155 reading; the OWNER may pick B or C.
- R2 `map`, `quarantine`, `redact` become tree-sitter keywords. With `word: identifier` a keyword applies only where it is valid;
  G1 has the `fn map` control. A field named `map:` gets the same control in G1.
- R3 `tree-sitter build --wasm` may download the WASI SDK (network). If it cannot, TEST records the check as missing.
- R4 `preview.py` uses `npx tree-sitter-cli@0.26.5`; without the npm cache it needs the network. Same rule as R3.
- R5 The tree-sitter grammar stays lenient on commas (`optional(",")`), as for `rename` today. It accepts some sources the
  compiler rejects. Not new; not changed in a4.
- R6 Zed itself is not checked (README limit). `test --wasm --rebuild` does not test the committed wasm file.

## Acceptance criteria

- T1 to T6, G1, G2, G3 fail at HEAD as stated (genuine RED), pass after GREEN; RED depth probe as above.
- All existing `slice6_fmt_test.py` tests pass, `test_mark_removed_when_a_chain_from_v1_implies_it` included.
- The seven fates fixtures survive `fmt` byte-equal (under QA4-1 A). Second `fmt` prints nothing on every input.
- Full 0004 `run.py` status `pass`; 0001 `cargo fmt --check`, `clippy -D warnings`, `cargo test` pass.
- `tree-sitter test --rebuild` and `--wasm --rebuild` pass; `parse -q` has no `ERROR` on the fates fixtures and 0005 sources.
- `preview.py --chat` colours `quarantine`, `map` and the enum mark.
- 0005 `run.py run` passes with N17 in `EXPECTED`; the run directory keeps the `fmt` outputs.
- No pin moved. No source text, path or stored value in any event (fmt events count lines only, D6B-46).
- A PASS does not establish production readiness.

## Decisions (By: Opus, PLAN fates-a4)

**Migrate (OWNER chooses; built defaults)**
→ QA4-1 mark on a fate chain: A keep · B never remove · C DL-104 as built. Default A.
→ QA4-2 MIGRATE STEP body layout: PF-19 form. Default as written above.
→ QA4-3 table inside a migrate body: default none.

**Repair**
→ G3 in `slice6_fmt_test.py` with a skip on a missing CLI, over a hard failure, because N16 does the same; TEST counts a skip as missing.
⠀⠀↳ commits us to: a TEST run with `TREE_SITTER` set
→ N17 as a `run.py` step on copies, over an ExUnit test, because `fmt` needs no database and must not touch the sources.

**Undo**
→ tests inline in `slice6_fmt_test.py`, no new tracked fixture under `slice*/`
→ grammar node names `quarantine_operation`, `map_operation`, `redact_operation`, `retire_operation`
→ a2a GREEN first, a4 after; either order is safe
→ plan.json beside this file
