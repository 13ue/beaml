# RED review: fates-a4

**[Verified]** Fresh-context RED review, 2026-11-08, HEAD `ec1cfec2` (RED commit). Normal review, not Devil's Advocate.
Inputs: [plan.md](plan.md) with Repairs, [plan-review.md](plan-review.md), [red-plan.md](red-plan.md),
[red-output.md](red-output.md), `git show ec1cfec2`. Debug `beaml-spike` of HEAD; tree-sitter CLI 0.26.5 at
`/private/tmp/beaml-zed-highlighting/tools/tree-sitter`. Probes on scratch copies only. By: Opus (RED review fates-a4).

**Verdict: GO for GREEN.** The RED is genuine and fails for the planned reasons. No objection is critical or high.
Three medium objections below; O1 and O2 are cheap and should go into the GREEN brief.

## Re-run at HEAD (observed)

| Check | Result | Matches red-output.md |
|---|---|---|
| `python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py` | `Ran 37`, `FAILED (failures=29)`: T1 3, T2 1, T3 8, T4 2, T6 10, G3 5. T5 and the 30 earlier tests pass | yes |
| `tree-sitter test --rebuild` | 6 failures, `fates.txt` entries 11 to 15 and 17; entry 16 (guard) and 24 earlier entries pass | yes |
| same, fates entries excluded | `fates.beaml` fails at `row: 4, column: 27, expected highlight 'keyword'` (`map`) | yes |
| N17 equivalent (fmt twice on copies of the 5 0005 sources) | all exit 0, empty stdout | yes (guard) |

## Challenges (observed unless labelled)

- **Genuine reasons.** T1 and T2 fail on the removed TYPE mark; T3, T4 fail on the unchanged body; T6 fails on both;
  G1 fails on `ERROR` nodes; G3 fails on `ERROR` in the five fixtures with an enum mark or a fate line. No setup failure:
  every T6 input builds (setup assert passes), `fmt_case` asserts exit 0.
- **RED depth probe (run, cheap).** Scratch build of HEAD with `fmt_mark` patched to keep every existing mark
  (`BEAML_SPIKE` pointed at it). Result: T1 and T2 pass; T3 8, T4 2, T6 10 still fail; G3 5 still fail; and the existing
  guards `test_mark_removed_when_a_chain_from_v1_implies_it`, `test_fmt_is_idempotent`, `test_crlf_line_ends_stay`,
  `test_compiled_output_equal_except_declaration_offsets`, `test_fmt_rewrites_the_file_and_prints_the_diff` fail.
  So a mark-only GREEN cannot pass, and a "never remove a mark" GREEN (QA4-1 B) is caught by the old guards.
  **[Inference]** The body-only half fails T1 and T2: the fixtures already hold `{ change }` one-line bodies, so the body
  rule does not touch them and the mark loss stays.
- **T3 to T5 mask the TYPE mark.** T6 runs every T3 and T4 input and compares the full text with the mark, so a GREEN
  that breaks the mark on those inputs fails T6. T5 (comment body) is masked only; a mark loss there passes T5.
  **[Inference]** Low risk: the mark decision reads the parsed `Change::fate`, not the layout. Dropping `unmarked` in T5
  is a one-word change if GREEN wants it.
- **T6 compares exit and stdout, not stderr.** Accepted: DEAD LINE warnings carry line numbers that move with the layout.
  The Elixir equality (offsets masked) carries the semantic check. Low, dropped.
- **Highlight CLI reports the first failure only.** The test still fails on any failing assertion, so a GREEN pass means
  all 27 hold. Checked here instead: every caret points at the intended token (script over `fates.beaml`), and
  `tree-sitter query --captures` at HEAD shows 14 assertions fail and 13 already pass (`enum` keyword, the enum mark
  `number`, `retire`/`keep`/`days`, `30`, `fn map` function, the three `type T` fields, `rename`, `map` after `rename`,
  `redact` after `drop`). The 13 are guards, not RED.
- **Keyword controls pinned.** Corpus entry 16 (`fn map`, fields `map:`/`quarantine:`/`redact:`, `rename map -> route`,
  `drop redact: String`) passes at HEAD and pins `(property)` and `(identifier)` nodes. Entry 17 pins
  `quarantine map, quarantine redact "x"` as `(quarantine_operation (property))`. G2 asserts `property` at
  `rename map`, `quarantine map`, `drop redact` and the fields. With `optional(",")` (R5), `quarantine map` is the
  state where `map` could lex as a keyword; entry 17 and G2 (29, 53) catch that.

## Objections (max three)

**O1 · medium · The mark rule is tested per file, not per chain.**
No source in T1 to T6 holds a fate chain and a plain implied chain together (observed: the seven fixtures and
`marks.beaml`). A GREEN that keeps every mark when the file has any fate line passes the whole slice, against the
plan rule "DL-104 A unchanged for every other chain". Probe: `order_map` plus the `Chained` chain of `marks.beaml`
(`type Chained v3 {…}`, `v1 -> v2 { rename status -> state }`, `v2 -> v3 { add channel: String = "web" }`) validates
(fmt exit 0) and at HEAD loses both marks. Resolving test (T2c, add in GREEN as its first edit, RED at HEAD):
fmt of that source gives `type Order v3 {` and `type Chained {`; second fmt prints nothing.

**O2 · medium · The enum-mark preview and G2 checks have no test power.**
At HEAD the tree-sitter error recovery keeps `v2` as `(ERROR (version))`, so the highlight is already `number`
and the preview line 18 of `channel_v2` is already `<i class=k>enum</i> <i class=t>Channel</i> <i class=c>v2</i> …`.
The red-output fix ("check the `enum Channel v2` line itself") is also true at HEAD. Only G1 entry 11 (`(version)` as a
direct child of `enum_declaration`) and G3 on `channel_v2`/`channel_swap` pin the enum mark. Stronger TEST check:
(a) the preview line of `channel_v2` source line 23 equals exactly
`<i class=k>migrate</i> <i class=t>Channel</i> <i class=c>v1</i> <i class=o>-&gt;</i> <i class=c>v2</i> <i class=b>{</i> <i class=k>map</i> <i class=s>&quot;app&quot;</i> <i class=o>-&gt;</i> <i class=c>Mobile</i> <i class=b>}</i>`;
(b) the `amount_v2` migrate line holds `<i class=k>quarantine</i> <i class=p>value</i>`;
(c) for the enum mark, cite G1 entry 11 and G3 (`parse -q` no `ERROR`), not the preview colour.

**O3 · medium · 0005 `run.py run` is `fail` until a2a GREEN; N16 breaks the DL-147 intent there.**
N17 is a passing guard, so adding it is fine. N16 (a2a RED, `fc4e3acf`) fails in step `test-n8`, so the 0005 run cannot
tell an expected RED from an a4 regression. **[Inference]** DL-147 names `run.py` test files of 0004; its reason
("the full run must mean everything listed passes") applies to 0005 too, and removing N16 from `EXPECTED` alone would not
help (the ExUnit test still fails the step). Resolution: if a4 GREEN lands before a2a GREEN, the a4 TEST phase accepts the
0005 run only when its failures are exactly `exp0005-N16` in step `test-n8` and `exp0005-N17` passes. Whether DL-147
extends to 0005 ExUnit RED cases (tag/exclude until GREEN) is a rule question for the main agent.

## Decisions (By: Opus, RED review fates-a4)

**Repair**
→ GO statt Stop, weil no objection is critical or high
⠀⠀↳ commits us to: O1 T2c and O2 check in the GREEN/TEST brief
→ O3 as TEST acceptance filter statt a run.py change in a4, weil N16 belongs to a2a

**Undo**
→ depth probe on a scratch build only
→ T5 mask and T6 stderr kept (low)
