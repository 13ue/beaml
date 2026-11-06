# Select the implementation and record compiler RED (0003)

## Implementation decision

**[Proposal]** Use the [Ponytail Ultra proposal](proposal-ultra.md) and keep its four review gates. Reuse the 0002 release, HTTP and trace checks. Stage the build outside the 0002 build tree. Reuse the original Orders modules for the REPLAY RUN. Use one loopback release pair for both live receipts. The second Payments build serves only the source lookup control.

Use the existing compiler CLI. Emit an Elixir comment after successful checking with the format `# beaml-declaration-v1 <name> <start> <end>`. Use zero-based UTF-8 byte offsets. Start at `fn` and stop immediately after the last body token. Leave whitespace and comments after the body outside the range. Emit one reference per checked declaration. The 0003 selector requires exactly one `authorize` reference. The host adds `payments` and the archived source digest for the SOURCE ID. This keeps the compiler independent of release and OBSERVATORY identities.

Use the Lite proposal's explicit check of generated public and private `authorize` and its multibyte prefix and trailing comment controls. Keep the small staged build manifest and one query result. Omit a new compiler command, sidecar and metadata framework. The comment preserves the existing Elixir output contract. Keep capture and transport checks separate from lookup so failures identify the missing evidence.

## Compiler RED

**[Verified]** The existing compiler CLI completed for the actual Payments fixture and the comment control. Both outputs contained public and private `authorize`. An independent baseline loaded the original generated module in Elixir and obtained the expected authorized payment. The existing invalid-source test passed.

**[Verified]** `payments_cli_emits_checked_authorize_reference` expected one `authorize` reference for bytes `[91, 193)` of the original fixture. Cargo exited 101. The assertion compared `[]` with `["91 193"]`. The successful compiler output lacks a declaration reference. The comment control expects `[103, 205)` and reaches its range assertion after the original passes.

Run from the repository root.

```sh
cargo test --manifest-path experiments/0001-syntax-to-beam/Cargo.toml --test cli payments_cli_emits_checked_authorize_reference -- --exact --nocapture
```

See [RED output](red-output.log), the [test](../../../0001-syntax-to-beam/tests/cli.rs) and the [retained EXPERIMENT RUN](../../results/20261105T225505014890Z/result.json). The run retains [commands](../../results/20261105T225505014890Z/commands.json), [toolchain](../../results/20261105T225505014890Z/toolchain.json), [input hashes](../../results/20261105T225505014890Z/input-hashes.json) and [output hashes](../../results/20261105T225505014890Z/output-hashes.json). The use-case action log records start, baseline steps, the checked assertion and `missing_checked_authorize_reference`.

**[Requirement]** The owner reviewed this compiler RED and instructed: “Ja, passt. Dann 0003 auf GREEN, let's go. Und zeig mir danach bitte denselben Test nochmal mit RED und GREEN nebeneinander.” This approval covers `payments_cli_emits_checked_authorize_reference`. The later behavior gates still require their own RED review.

## Compiler GREEN

**[Verified]** The lexer now keeps the byte range of each token. The parser keeps the range from `fn` to the end of the last body token. After checking, the compiler emits one Elixir comment for each clause. [Compiler](../../../0001-syntax-to-beam/src/main.rs)

**[Verified]** The exact RED command ran again. The test file SHA-256 matches the RED run.

| Same test | RED | GREEN |
| --- | --- | --- |
| `payments_cli_emits_checked_authorize_reference` | `FAILED`, exit 101 | `ok`, exit 0 |
| Payments reference | `[]` | `["91 193"]` |
| UTF-8 prefix and trailing comment | Assertion not reached | `["103 205"]` |

**[Verified]** Both outputs retain public and private `authorize`. Removing the new comment yields the exact RED baseline Elixir bytes. Elixir returned the expected authorized payment. The invalid-source control, full Cargo suite and formatting check passed.

See the [GREEN test output](../../results/20261105T225807421990Z/compiler-reference-test.stdout), [compiler output](../../results/20261105T225807421990Z/compiler-payments.stdout), [comment control](../../results/20261105T225807421990Z/compiler-comments.stdout) and [result](../../results/20261105T225807421990Z/result.json). The run retains [commands](../../results/20261105T225807421990Z/commands.json), [toolchain](../../results/20261105T225807421990Z/toolchain.json), [input hashes](../../results/20261105T225807421990Z/input-hashes.json) and [output hashes](../../results/20261105T225807421990Z/output-hashes.json). Use-case events record start, steps and pass.

## Remaining behavior gates

**[Proposal]** Establish a working baseline before each new RED. Keep a separate owner review and GREEN record for each gate.

1. **Compiler reference.** Use the test above. Check the original range and both comment boundaries on GREEN. Preserve the invalid-input and code emission behavior.
2. **Live evidence and lookup.** Check two successful receipts and their correlated traces first. Assert the 2/2 artifact and SOURCE ID summary and the archived declaration. Exercise the revised and missing original source controls.
3. **Capture and observer.** Check the successful Orders decision first. Assert the actual predecode response and one connect attempt per receipt. Exercise the real transport observer in a separate failure control.
4. **Replay.** Check the recorded response and shared Orders decision first. After both releases stop, assert the matching result and zero attempts. Exercise missing response, operation mismatch and attempt mismatch separately. Check that each stops before finish with zero attempts.

**[Unknown]** The later gates have no new run evidence yet. The retained RED and GREEN runs cover the compiler reference gate and its controls.
