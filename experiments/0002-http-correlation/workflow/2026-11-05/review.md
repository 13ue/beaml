# EXPERIMENT 0002 independent review

**[Verified]** The [independent run](../../results/20261105T213931184317Z/result.json) reports H01–H05 passes and six terminated release processes. Its retained H03 graph shows separate Orders and Payments traces and the expected missing cross-service edge. The successful Payments ingress records have the remote parent marker. The [test record](test-result.json) also covers the focused tests, both release builds, strict compilation, explicit writer loss and forced post-start cleanup.

## Fix before acceptance

1. **The Orders client can send a second POST.** [Orders router](../../apps/orders_api/lib/orders_api/router.ex#L35)
   - **[Verified]** The installed OTP 27.3.4 client retries POST after `503 Retry-After: 0`. A synthetic loopback stub received two POSTs and the client returned the second response, HTTP 200. The reproduction used `autoredirect: false`.
   - **[Verified]** The current call also leaves redirects enabled. The installed OTP response handler follows 307/308 for POST and can change the host. This violates the loopback-only, one-request contract and can mask an unexpected downstream response.
   - **[Proposal]** Use a bounded one-shot client configuration or client that rejects redirects and retries. Keep the existing fixed 502 response. RED should assert 502 and a count of one after a 503 with `Retry-After: 0`. A 307 to a second loopback listener should return 502 with that listener untouched.

2. **H03 can pass with propagation intact.** [Runner H03](../../run.py#L130)
   - **[Verified]** A scratch copy retained a complete Orders-to-Payments parent edge and moved only `orders.finish` to another trace. The current H03 predicate passed on two traces and the missing local finish edge. No retained run was changed.
   - **[Proposal]** Require the exact intended break, Orders and Payments on their own traces, and their remaining expected spans and logs. Reject unrelated gaps. RED should show that the intact cross-service edge and detached finish span cannot pass H03.

3. **The query accepts missing proof of a remote parent and artifact integrity.** [Query checker](../../query.py#L33)
   - **[Verified]** A scratch copy changed both `payments.request` records to `parent_remote=false`. The query still reported `complete=true`. The SDK exporter retains the marker.
   - **[Verified]** The checker only verifies generated-source and BEAM evidence if the manifest includes `artifacts`. The focused synthetic complete fixture omits that section. A removed section can bypass both checks.
   - **[Proposal]** Require the SDK marker for `payments.request` and the generated-source and BEAM manifest entries for complete run evidence. RED should mutate the ingress marker without changing parent IDs and remove artifacts in a separate case. Each should yield a structured gap.

4. **Optimized Python removes acceptance checks and one test request.** [Runner](../../run.py#L114)
   - **[Verified]** Python `-O` removes the H01–H05 runtime assertions. Bytecode inspection confirms it removes the H03 HTTP request too, because it is inside an assertion. The runner can publish case passes without those checks.
   - **[Proposal]** Reject optimized mode at the runner boundary or use explicit runtime checks. RED should require a clear nonzero result for an optimized CLI invocation, or verify that it still executes and checks the case.

## Reproduction and documentation

5. **The build uses machine-specific paths.** [Runner build commands](../../run.py#L66)
   - **[Verified]** Toolchain reporting and dependency setup use the caller's tools. Release builds and strict compilation instead force absolute asdf paths and another fixed build environment. The reported versions therefore need not describe the tools that produced the releases. The advertised command fails where that installation does not exist.
   - **[Proposal]** Use the same selected toolchain for version reporting, dependency setup, strict compilation and releases. Keep build and runtime settings separate. Verify the command with a toolchain resolved from a different directory.

6. **The README and wiki still describe a proposal.** [Experiment README](../../README.md) · [Experiment register](../../../../wiki/planning/research-and-development.md) · [Wiki index](../../../../wiki/index.md)
   - **[Verified]** The README and register say that implementation or an actual run does not exist. The retained independent run exists. Link the run and state the review defects and experiment limits.
   - **[Verified]** The two [wiki lint errors](test-wiki.log) are separate from the HTTP runtime. The test-first-policy source page lacks an index entry and an incoming link. Preserve that issue separately when reporting lint status.

## Test-first record

**[Verified]** The [solver RED log](solver-red.log) records a meaningful checker failure. `test_complete_and_missing_log` expected `complete=True` and observed `False`. The [solver GREEN log](solver-green.log) and [independent test record](test-result.json) retain passing checks. The checked ledger does not record an owner review or explicit waiver between RED and GREEN. Record any existing authorization from the actual exchange. Do not infer it from task authorization.

**[Proposal]** Establish new RED evidence for the behavior repairs and obtain the required owner review before production edits. The scratch mutations and loopback probe identify the defects. They are review evidence.

## Disposition

**[Verified]** The recorded successful exchange supports the bounded HTTP correlation hypothesis. Review remains open on the transport and acceptance findings. Review changed only this record. It did not rerun the full suite or test replay, production durability, or arbitrary workloads.
