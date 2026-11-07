# BEAML syntax in Zed

Open a `.beaml` file to use BEAML syntax highlighting. The grammar covers the syntax in [EXPERIMENT 0001](../../experiments/0001-syntax-to-beam/README.md). The compiler checks TYPE correctness and record completeness.

The grammar also covers the forms of the decision log (`wiki/planning/decision-log.md`):

- `effect` with a dotted name, the pipe `|>` and `!` failure TYPES (DL-013 to DL-015).
- `with ... do ... else ... end` (DL-014). Only the keywords are decided; the clause shapes parse tolerantly.
- `type Name { ... }` and `type Name v3 { ... }` (DL-061, DL-070 to DL-072). `interface` is no record keyword (DL-074): it parses as an ERROR node.
- `enum` variants with and without a payload, for example `Unknown(String)` (DL-062).
- `redacted` before a field TYPE (DL-059).
- MIGRATE CHAIN steps `migrate T v1 -> v2 { ... }` with `rename`, `add` and `drop` (DL-022, DL-023, DL-072). A plain number gives an ERROR node (DL-074).
- `retire op.name keep 30 days` (DL-055, DL-057).
- ENUM LITERALS `Authorized = "ok"`: a variant has a payload or a String literal, never both (DL-082).
- Constructor clauses and signature lines: `fn PaymentState "ok", _ -> PaymentState = Authorized`. A signature line is a clause without `= body` (DL-084, DL-085, DL-092).
- Failure TYPES `-> T ! E1 | E2` on a `fn` (DL-092, DL-093). The overlap rule of DL-093 is a compiler check: `-> String ! String` parses.
- Pipe steps that are constructors or variants: `reason |> DeclineReason |> Declined` (DL-086).
- Integer literals in patterns and expressions, for example `fn NonZeroInt 0 -> …` (DL-092).
- A redaction release on an `effect`: `= http.post(...) with card_holder`, or a comma list of fields (DL-089). A `fn` cannot have `with`.

An uppercase function name, an uppercase pipe step and a bare uppercase name in an expression get the capture `@constructor`. Lowercase names stay `@function`.

A version is `v` and a number without a leading zero (`v[1-9][0-9]*`): `v0` and `v03` give an ERROR node. The grammar does not check the u32 range: the compiler rejects `v4294967296` (F4). The corpus file [errors.txt](test/corpus/errors.txt) holds the ERROR cases.

Version numbers use the capture `@number`. `preview.py` shows it in the constructor colour (class `c`).

## Install in Zed 1.27 on macOS

1. Open `~/Library/Application Support/Zed/extensions/` in Finder.
2. Create a folder named `beaml` in `staging`.
3. Copy [extension.toml](extension.toml), [grammars](grammars/) and [languages](languages/) into that folder.
4. Move the complete `beaml` folder from `staging` to `installed`. Zed watches the installed folder.
5. Open the [example](../../experiments/0001-syntax-to-beam/example.beaml). Check for **BEAML** in the status bar. Use `dev: open highlights tree view` to inspect captures.

This package uses a prebuilt grammar. Zed's `Install Dev Extension` action expects a Git repository and revision for the grammar.

## Test and build

Use Tree-sitter CLI **0.26.5** and WASI SDK **29**. The CLI can download the SDK during the first WASM build.

```sh
cd integrations/zed-beaml
tree-sitter generate --abi 15 --js-runtime native
tree-sitter test --rebuild
tree-sitter test --wasm --rebuild
tree-sitter parse --wasm -q ../../experiments/0001-syntax-to-beam/example.beaml
tree-sitter build --wasm -o grammars/beaml.wasm
```

Run the tests after grammar or query changes. Build the WASM again before installing a changed grammar.

Always use `--rebuild` with `tree-sitter test`. Without it, the CLI can use a stale parser from its shared cache, and a test can pass on the wrong grammar (slice 6a RED).

**[Unknown]** The committed `grammars/beaml.wasm` is rebuilt from the slice 6a grammar but not checked in Zed. `test --wasm --rebuild` builds its own WASM, so it does not test the committed file. The shared `#match?` over the constructor alternatives is also not checked in Zed. See the [slice 6a review](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6-grammar/review.md).
