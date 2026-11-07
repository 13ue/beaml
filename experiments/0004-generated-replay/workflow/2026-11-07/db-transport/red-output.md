# RED output: DB TRANSPORTS, part P4a

**[Observed]** 2026-11-07. By: Opus (RED db-transport). Raw log: [red-output.log](red-output.log). Mapping: [red-plan.md](red-plan.md).

## Run

```
git archive ea64059c experiments/0001-syntax-to-beam | tar -x -C <scratch>/head
cargo build --offline --quiet --manifest-path <scratch>/head/experiments/0001-syntax-to-beam/Cargo.toml --target-dir <scratch>/head/target
BEAML_SPIKE=<scratch>/head/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_db_test.py
```

- Compiler: HEAD `ea64059c` (no `0001` change up to `eb6def2c`, checked with `git diff --stat`). Elixir 1.18.1, OTP 27. tree-sitter 0.26.5 (`/private/tmp/beaml-zed-highlighting/tools/tree-sitter`).
- `slice6_db_test.py` sha256 `d2dfb751…0ed4`; `slice6/db/orders.beaml` sha256 `89b8cbaf…f0d7`.
- Result: **16 tests, 40 failing subtests, 1 skipped (N2c), 1 guard passes (N13, 148 sources).**

## Failures and reasons

| Test | Fails | Actual (HEAD) | Reason |
|---|---|---|---|
| N1 | 1 | exit 1, `unsupported token at byte 603` | lexer has no `[` (`[Order]`) |
| N1b | 4 | `unsupported token at byte 214 / 301 / 609 / 562` | lexer `[` |
| N2 to N11 runtime | 1 (setup, 48 cases) | compile exit 1, lexer `[` | the module is not built |
| N5 control, N5 | 2 (setup, 1 + 5 cases) | lexer `[` | same |
| N12 rejects | 15 | `unsupported effect kind: db.<k> in effect <op> (slice 1 supports http.post)` (12 files, `fourth_kind` with `db.query`); `unsupported token at byte N` (3 files: `list_query`, `list_elsewhere`, `list_element`) | no db KIND, no LIST TYPE |
| N12 order_v2 | 1 | `unsupported token at byte 676` | lexer `[` |
| N12 S13 | 1 | `unsupported effect kind: db.get in effect payments.authorize (slice 1 supports http.post)` | db.get is no KIND yet |
| N15 | 5 | fmt exit 1, `unsupported token at byte N`, file unchanged | lexer `[` |
| N15b | 1 | fmt exit 1, lexer `[` | same |
| N16 | 6 | no `list_type` rule, no `list_type.txt`, no `"["` highlight; parse `ERROR` at the `[` | grammar has no LIST TYPE |
| N25b and 2 controls | 3 | exit 1, lexer `[` (`no_app/` byte 562, `orders.beaml` byte 603) | same |

- Every failure is the missing feature: the lexer stops at `[`, or `effects()` refuses a db KIND. No failure is a P3 text (`slice 1 supports one effect`) or a P2 text: the lexer and the KIND check run before both.
- N13 passes before and after (guard).

## Harness check (no typo RED)

- The 54 runtime cases never reach the generated code today. **[Observed]** In scratch, the same `checks.exs` files ran against a hand stub `Orders` module (`save`, `load`, `list_orders` raise): all three scripts exit 0; 48 + 1 + 5 cases print `FAIL` with `RuntimeError stub`; no case fails on an Elixir syntax or helper error.
- **[Observed]** The fake `BeamlDb` alone: `list` gives rows newest first with `id`, `version`, `value` (binary as given); `get` by key finds row 1 and gives `nil` for no match; modes give `{:error, "down"}`, `:what`, `{:ok, :what}`, a `RuntimeError` (raise, forbid) and `exit(:noproc)`; every call is logged.
- **[Inference]** A case can still fail for a wrong expected value that only the GREEN output shows. Expected values come from the plan and the test's own digest and fingerprint code (`stored_types_test.value_sha256`, the 6d `PLACE_TYPE` form).

## Limits

- **[Inference]** The RED reasons are pre-P2 and pre-P3. Re-run after P2 and P3 GREEN: the first failures must still be the lexer and KIND texts (red-plan.md, "Dependencies").
- **[Unknown]** Whether GREEN's `__beaml_db__` wrapper passes N8 `:exit` without killing the script; the tail catches any throw or exit, so one bad case fails alone.
- N16 runs `tree-sitter parse` only; `generate` and `test --rebuild` are GREEN/TEST commands.
