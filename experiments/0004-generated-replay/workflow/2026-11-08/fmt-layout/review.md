# fmt layout (DL-148): TEST and REVIEW

Fresh-context REVIEW, 2026-11-08, HEAD `ffb7605e`. Not a Devil's Advocate. By: Opus (fmt-layout, review).
Target: [DL-148](../../../../../wiki/planning/decision-log.md), [notes.md](notes.md) F1 to F11 and P1 to P6,
[green-output.md](green-output.md), `experiments/0001-syntax-to-beam/src/main.rs` (`fn formatted`, `fn bodies`,
`fn aligned`, `fmt_file`), `tests/slice6_fmt_test.py`, `slice6/fmt/`.

**Verdict: PASS, no code change.** No bug found in `main.rs`; no repair made. Three medium objections, dispositions
pending (OWNER).

Compiler: `cargo build --release` of 0001 at HEAD (no rebuild needed). All probes ran on copies in the scratch directory;
no tracked file was formatted.

## Test results (observed)

| Check | Result |
|---|---|
| `python3 tests/slice6_fmt_test.py` | 30 tests OK |
| `cargo test` (0001) | 22 + 14 passed |

## Idempotence (observed)

All 185 tracked `.beaml` files outside `results/`, each copied to its own directory, `fmt` run twice.

| Count | Meaning |
|---|---|
| 185 | files |
| 83 | first run changes the file: the 82 listed in green-output.md plus the new fmt input `slice6/fmt/layout.beaml` |
| 58 | fmt exits 1: invalid sources (`bad/`, RED cases); fmt checks the source first (D6B-41), writes nothing |
| 44 | already fixed points (first run prints nothing) |
| **0** | second run prints a diff (**83 of 83 idempotent**) |

## Generated Elixir before and after fmt (observed)

All 83 changed files (more than the 10 asked), same file name (the module name comes from the stem), two modes each:
plain `beaml-spike F` and `beaml-spike F --stored stored/empty.jsonl`; stdout, stderr and exit code compared.

| Count | Result |
|---|---|
| 166 | build pairs |
| 68 | byte-equal |
| 98 | equal after a mask of `# beaml-declaration-v1` offsets, `at byte N` and `<file>.beaml:LINE` |
| **0** | differ after the mask |

The `.beaml:LINE` part is in stderr only (DEAD LINE and drift warnings name the source line, which moves when a body
opens). 80 of 83 build with exit 0 under `--stored`; the plain mode exits 1 for 63 (the "needs --stored" error), the
same before and after.

## Comments and strings (observed)

Over the 83 before/after pairs, the sequence of `//` comments (216) and string literals (316) is equal in every file.
Text without whitespace is equal in 80 files; the other 3 (`slice4/Q4s`, `slice4/Q4s-crlf`, `slice6/fmt/marks`) differ
only by the DL-104 VERSION MARK edit (`type Payment v4 {`), which predates DL-148.

## Edge cases (observed)

Input (scratch file, LF and a CRLF copy):

```beaml
type Pair { a: String b: String } // trailing comment after the body
type Open { // comment after the open brace
  a: String b: String }
type Solo {
    id: String
}
enum Mood {
  Glad
}
type StoreError { reason: String }
fn greet s: String -> String
fn greet "ä" -> String = "umlaut"
fn greet "äöü" -> String = "three"
fn greet _ -> String = "other"

fn pick a: String, b: String, c: String -> String = a
fn more x: String -> String = x
fn tail_note x: String -> String = x // trailing comment on a clause
```

Output:

```beaml
type Pair {
  a: String
  b: String
} // trailing comment after the body
type Open { // comment after the open brace
  a: String b: String }
type Solo { id: String }
enum Mood { Glad }
type StoreError { reason: String }
fn greet s: String -> String
fn greet "ä"      -> String = "umlaut"
fn greet "äöü"  -> String = "three"
fn greet _         -> String = "other"

fn pick      a: String, b: String, c: String -> String = a
fn more      x: String                       -> String = x
fn tail_note x: String                       -> String = x // trailing comment on a clause
```

| Case | Result |
|---|---|
| comment after `}` | stays on the `}` line, byte for byte |
| comment inside the body | the body stays as written, also with two members on one line (F4) |
| one member over several lines | collapses to one line (`type Solo`, `enum Mood`), as DL-148 (1) and (2) say |
| rows with 3 and 1 arguments | `->` stands after the longest argument run (F6) |
| trailing comment on a clause | stays; only gaps before `=` change |
| CRLF copy | exit 0, second run empty, output = LF output with `\r\n`, no bare `\n` |
| non-ASCII string argument | columns count bytes: `"ä"` row arrow 1 column left, `"äöü"` row 3 columns left (D038) |

The only tracked source with non-ASCII bytes, `experiments/0001-syntax-to-beam/example.beaml`, holds them after `=`
(`"...: Grüße\n"`), so no tracked table moves today.

## Objections (max three)

**O1 · medium · a comment inside a body silently skips DL-148 (1) and (2).** `type Open { // c` with two members on one
line keeps its form, exit 0, no diff, no note. The file looks formatted but is not. F4 is a worker decision (Opus, RED),
not an OWNER one. Resolving test: decide F4 with the OWNER; if kept, a fixture with two members on the comment line, and
optionally a `note:` line on stderr. Disposition: pending.

**O2 · medium · columns count bytes (D038).** A non-ASCII argument shifts its row left by (bytes − characters) on
screen; probe above. No tracked table is affected today. Resolving test: a fixture row with `"ä"` that expects aligned
characters, once D038 decides the width unit (characters or grapheme clusters). Disposition: pending, noted under D038.

**O3 · medium · one block-wide table widens lines.** The longest name cell of a block sets the first argument column of
every row (`fn Amount` gets 13 spaces from `effect payments.check` in `layout.formatted.beaml`). Over the 83 changed
files, 19 have a line over 120 characters after fmt, 17 before; the largest growth is +26 (`slice6/fmt/layout.beaml`) and
+17 (`slice6/stored-elixir/order.beaml`). This is the DL-114 reason against option B ("gets wide with long TYPE
names"), now per block. It is the OWNER rule, not a bug. Resolving test: the D038 maximum line length, with a fixture of
one long EFFECT name above short clauses. Disposition: pending.

## Inferences

→ **[Inference]** The 82 tracked sources that stay unformatted (P1) change on their first `fmt`; their compiled output
stays equal after the mask above, so that later change moves only offset and line pins.
→ **[Inference]** A file with both CRLF and LF lines gets CRLF in every new body line (`source.contains("\r\n")`); no
tracked file mixes line ends.

## Limits

→ The mask hides offsets and line numbers; a wrong offset value is not checked here (the 0004 and 0005 runs cover the
declaration offsets end to end, green-output.md).
→ The edge probe is one scratch file, not a fixture; no new test was added because no bug was found.
