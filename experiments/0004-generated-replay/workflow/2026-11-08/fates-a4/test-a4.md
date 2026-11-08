# TEST + review: fates-a4

**[Verified]** TEST on HEAD `ebcd91e9` (GREEN), 2026-11-08. Working tree clean for compiler and grammar (`git diff ebcd91e9` empty).
By: Opus (TEST fates-a4). Normal fresh review, not Devil's Advocate.
Inputs: [plan.md](plan.md), [red-review.md](red-review.md), [green-output.md](green-output.md), DL-148, DL-104, DL-173.

## 1. Full runs (observed)

| Command | Result dir | Result |
|---|---|---|
| `python3 -B experiments/0004-generated-replay/run.py` | `results/20261108T151410308144Z` | 39 of 40 steps pass; only `slice6-fates` fails |
| `python3 -B experiments/0005-prototype-fullstack/run.py db-up` | `results/20261108T153119762662Z` | pass |
| `python3 -B experiments/0005-prototype-fullstack/run.py run` | `results/20261108T153120241618Z` | status fail; acceptance list = `exp0005-N16` only (step `test-n8`); 24 pass, 1 fail, 1 blocked (N9, D036); N17 pass |

**Known failures, verified by name (DL-173):**

- `slice6-fates`: 39 failures, all in class `__main__.FatesA2a` (a2a RED, `fc4e3acf`). The sorted FAIL list is identical to the GREEN run `results/20261108T145443950765Z`.
- 0005: the only failing use case is `exp0005-N16` (`ExUnit.AssertionError`).

**Pin guards:** `slice5-syntax`, `slice6-entry`, `slice6-multi`, `slice6-db`, `slice6-pipe`, `slice6-host-struct`, `slice6-effect-reach`, `record-v3`: all pass. GREEN changes no pin file and no `.beaml` fixture.

## 2. tree-sitter and preview (observed)

CLI `/private/tmp/beaml-zed-highlighting/tools/tree-sitter` 0.26.5, in `integrations/zed-beaml`.

| Command | Result |
|---|---|
| `tree-sitter test --rebuild` | 31 of 31 parses; 5 highlight files pass (`fates.beaml` 27 assertions) |
| `tree-sitter test --wasm --rebuild` | same, pass |
| `python3 integrations/zed-beaml/preview.py --chat slice6/db/fates/*/orders.beaml probe.beaml` | exit 0 |

Preview classes (observed): `quarantine`, `map`, `redact`, `retire`, `keep`, `days`, `migrate`, `enum` are `k`.
Version marks `v1`/`v2`/`v3` on `type`, `enum` and `migrate` are `c` (`@number`, as before a4).
`map "app" -> Mobile`: `Mobile` is `c`; `map channel "app"`: `channel` is `p`.

**Keyword probe** (scratch file, not retained): `type Route v2 { map: String ... quarantine: String redact: String }`,
`migrate Route v1 -> v2 { rename map -> route, quarantine map, quarantine map "x", map map "a" -> Web, redact map, retire map keep 3 days }`,
`fn map ...`, `fn redact ...`. Parse: no ERROR, no MISSING. Field `map:` is `p`, `fn map` is `f`, `rename map`/`quarantine map` operand is `p`.

## 3. Review of the diff

| Check | Result |
|---|---|
| Mark rule per chain | **[Verified]** `fate` is computed from `checker.migrations(name)` per TYPE/ENUM. Probe: one file with a fate chain `Order v3` and a plain chain `Plain v2` from v1: `Order v3` stays, `Plain` loses its mark. T2c covers the same rule. |
| Idempotence | **[Verified]** fmt twice on copies of all 133 `.beaml` files under `slice6` and `0005/app/beaml`: 90 format, 0 non-idempotent; 43 fail in fmt, all `bad/` fixtures (checker errors, expected). The 5 `db/fates` fixtures stay byte-equal. `fmt/marks.beaml` output equals `marks.formatted.beaml`. |
| MIGRATE body | **[Verified]** probe `{ add note: String = "", add memo: String = "a,b" }` becomes one change per line, comma after its change, the comma inside the string stays; a 3-line one-change body becomes `{ map channel "app" -> Mobile }`; second fmt is a no-op. Commas are required between changes (parser error otherwise), so the top-level comma split cannot join two changes. |
| No new syntax (DL-139) | **[Verified]** grammar adds only forms the compiler already parses (`Change` enum: Quarantine, Map, Redact, Retire; enum mark). |
| `retire_operation` field `duration` | **[Verified]** same field name as `retire_declaration`; DL-163 says `keep N days` and names no field, so no conflict. |
| Byte pins | **[Verified]** unchanged, guards pass (section 1). |

## 4. Objections (max three; block only on critical/high)

None critical or high.

- **Medium (note):** the MIGRATE body rule also applies to slice4/slice5 fixtures with two changes on one line
  (`{ drop channel: String, add reference: String = "pre-v4" }`). No test runs fmt on them, so the expansion is unpinned there.
  Smallest test: fmt on `slice5/Q4/orders.beaml` expects one change per line. Not in a4 scope.

## 5. Verdict

**PASS.** The only failures are the accepted DL-173 ones (`FatesA2a`, N16), verified by name. A PASS does not establish production readiness.

## 6. Decisions (By: Opus, TEST fates-a4)

**Undo**
→ idempotence check on scratch copies, not on the repo files
→ keyword probe as a scratch file, not a new corpus case
→ `bad/` fixtures counted as expected fmt errors

**Repair**
→ medium note only statt a blocking objection, weil the slice4/5 expansion follows DL-148 and no test claims otherwise
