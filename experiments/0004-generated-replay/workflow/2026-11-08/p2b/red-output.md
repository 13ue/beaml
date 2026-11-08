# RED output: P2b

**[Verified]** RED run, 2026-11-08, HEAD `0b460f9d`. By: Opus (RED P2b). Plan: [red-plan.md](red-plan.md).

## Commands

```
git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>/src
cargo build --offline --quiet            # in <scratch>/src/experiments/0001-syntax-to-beam
export BEAML_SPIKE=<scratch>/src/experiments/0001-syntax-to-beam/target/debug/beaml-spike
python3 -B experiments/0004-generated-replay/tests/slice6_db_stored_test.py
python3 -B experiments/0004-generated-replay/tests/record_v3_test.py
python3 -B experiments/0004-generated-replay/tests/slice6_entry_test.py
python3 -B experiments/0004-generated-replay/tests/stored_types_test.py
```

Toolchain: rustc 1.94.0, Python 3.13.12, Elixir 1.18.1 on Erlang/OTP 27 (the R5 digest emit). Plan check read
OTP 28.3.1 `json.erl`; OTP 27 writes the same upper-case form (observed: `\u000B`, `\u001B`).

## Counts

| File | Ran | Fail | Skip | Fails are |
|---|---|---|---|---|
| `slice6_db_stored_test.py` | 28 | 6 | 3 | R1, R2, R2b, R5, R6, N25 control |
| `record_v3_test.py` | 33 | 7 (subtests) | 1 | R3 [valid, constructor, held], V14, V14c, V22, V23 |
| `slice6_entry_test.py` | 22 | 2 (subtests) | 0 | R4 [valid, value_faults] |
| `stored_types_test.py` | 54 | 0 | 0 | (helper change, all pass) |

Every failure is a planned RED. Every guard passes: G1 (three files), N21, N21b, N29 (two left), V14b, V15, V16,
V17, V18b, V24, V25, N2, N2b, s1, s5, s5b, and all other tests of the four files.

## Reasons at HEAD

→ **R1, R2, R2b, R6** (rows): exit 0, stderr without the rows line `[]`. HEAD folds `!digest_holds` (and
  `!accepted`) into `continue`; the row is counted as not decodable. R2b: the STRICTER constructor never runs.
→ **R5** (Erlang digest): `rows: 1 rows, 0 checked, 1 not decodable` instead of `1 checked, 0 not decodable`. The
  Rust `canonical` writes `\u000b`; the emitter digest is over `\u000B`. Helper guard in the same test passes
  (`st.value_sha256` now gives `8dd130c3…`).
→ **R3** valid: exit 0, Elixir on stdout. Constructor: the DL-102 text `fails the constructor of Amount` instead of
  the digest error. Held: the D6B-72 text `holds a value of the redacted field card_holder`.
→ **R4** valid: exit 0. Value faults: the DL-122 text `TYPE PlaceOrder v1: … no ENUM LITERAL of Channel` instead of
  the digest error.
→ **V14, V14c, V22, V23, N25 control**: HEAD prints the extra line `digest not verified (P2b)`.

Not genuine-RED risks checked: no failure is an import, setup or syntax error (each assertion names the planned
texts); the expected digest error comes from `st.digest_error`, not from a new compiler.

## Decisions

**Undo**
→ Logs kept in the scratch directory, not in the repository; counts and reasons here. By: Opus (RED P2b)
