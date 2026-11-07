# Slice 6b step 10: `beaml-spike fmt`

Step: [plan.md, Step 10](../slice6b-plan/plan.md), `plan.json` step `fmt`.
Decisions: [D6B-41 to D6B-46](../slice6b-plan/decisions.md); [plan review](../slice6b-plan/plan-review.md) O3 and section (3).
Decision log: DL-013, DL-080, DL-081, DL-083, DL-104 in [decision-log.md](../../../../../wiki/planning/decision-log.md).

## Contract

- `beaml-spike fmt SOURCE.beaml` checks the source without `--stored`, then rewrites SOURCE in place with `write_atomic` and prints the unified diff (n=0, label = SOURCE as given) on stdout. Exit 0 (D6B-41, notes.md F7, F12).
- An unchanged file is not rewritten: exit 0, empty stdout, same inode (notes.md F10).
- An invalid source writes nothing: exit 1, empty stdout, the source error on stderr, no temporary file (D6B-41, F8).
- Edits by token ranges only: the VERSION MARK tokens and the spaces before argument columns, `->` and `=`. Comments, strings and every other byte stay (D6B-42). CRLF line ends stay (F9).
- VERSION MARK form (b) by DL-104 (D6B-43): remove a mark only when a chain from v1 ends at it; keep a mark without a chain (`v3` and `v1` alike); write ` v<end>` after the TYPE name when the chain starts above v1 and has no mark; keep every other mark.
- Alignment groups (D6B-44): consecutive single-line clauses (`fn` lines with `=`) of one `fn` name, with no blank line and no comment line between. A multi-line clause and a signature line (no `=`) end a group (F4; OWNER question Q6B-9, only `slice6/fmt/header.formatted.beaml` encodes it). Each column (argument k, `->`, `=`) starts one space after the longest previous cell of the group (F5, F6). An EFFECT line aligns `->` and `=` the same way (DL-013, F3).
- Invariants (D6B-45): `fmt(fmt(s)) == fmt(s)`; the compiled output of `s` and `fmt(s)` is equal except the `beaml-declaration-v1` byte offsets.
- Event (D6B-46): `{"action":"fmt","result":"ok"|"error","changed":N}` in `.beaml/actions.jsonl`; N is the count of changed lines; an error gives 0. No source text, no path (F11).

## Pass rule

- `python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py` (repository root): 25 of 25 pass, all subtests pass (RED repair: 22 + R1, the `=` column, Q6B-9 header case).
- `cargo test --offline --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` pass.
- The slice 3 to 6 compile-level tests stay green; `--remove-dead` behaviour stays.

## Exclusions

- Whitespace other than the aligned columns and the mark, line breaking, `--check`, editor integration, `beaml check --json` (plan step 10).
- Alignment of two or more EFFECT lines (one EFFECT per source today, F3). Alignment of `!` and `|` failure lists (U4).
- Do not touch `integrations/zed-beaml/`.
