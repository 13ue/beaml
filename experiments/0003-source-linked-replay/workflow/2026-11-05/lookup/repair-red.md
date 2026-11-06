# Test receipt order and window coverage (lookup repair RED)

**[Requirement]** The main agent authorized tests for the first two [review findings](review.md). Owner review of this RED is pending. The shared malformed-service parser, CAPTURE, transport and REPLAY RUN are separate work.

## Run

Run from the repository root.

```sh
python3 -B experiments/0003-source-linked-replay/tests/trace_lookup_repair_test.py
python3 -B experiments/0003-source-linked-replay/tests/trace_lookup_test.py
```

**[Verified]** The repair test copied the original evidence and current revision from the [independent live run](../../../results/20261105T232448420501Z/result.json). It queried an unchanged copy and three separate temporary derivatives through the public CLI. Only the targeted manifest values changed. All four queries ran before the assertions reported failure. The original evidence and current revision matched all 15 retained hashes.

| Case | Expected | Observed |
| --- | --- | --- |
| Unchanged copy | Exit 0, 2/2 coverage and the original first trace | Passed. Exact source summary matched the live result. |
| Swap the receipt trace IDs | Exit 1, incomplete, `receipt_coverage`, no summary | Exit 0, complete, 2/2, no gaps. The first trace became the second call's trace. |
| Remove the window | Exit 1, incomplete, `missing_window`, no summary | Exit 0, complete, 2/2, no gaps. |
| Set a one-hour window in 2000 | Exit 1, incomplete, `outside_window`, no summary | Exit 0, complete, 2/2, no gaps. |

**[Verified]** The repair test exited 1 at the three behavior assertions. The query sorts the receipt IDs and discards their order. It does not read the UTC window. See the [test](../../../tests/trace_lookup_repair_test.py), [assertion output](repair-red-output.log), [result](../../../results/20261105T232809336690Z/result.json), [query commands](../../../results/20261105T232809336690Z/commands.json), [toolchain](../../../results/20261105T232809336690Z/toolchain.json), [input hashes](../../../results/20261105T232809336690Z/input-hashes.json) and [output hashes](../../../results/20261105T232809336690Z/output-hashes.json).

**[Verified]** The original test reran with automatic approval for local loopback TCP and exited 0. Both synthetic calls returned HTTP 200. The 2/2 lookup and missing-source control passed. Both releases exited 0. The test SHA-256 matched the original RED, GREEN and independent TEST. See the [fresh live run](../../../results/20261105T232707610628Z/result.json) and its [input hashes](../../../results/20261105T232707610628Z/input-hashes.json).

**[Proposal]** The archived root spans use VM-local monotonic times. A fresh live run can supply an independent Orders clock reference for the window check. The repair test accepts `--source-run` so the same assertions can use a fresh archive without editing the original acceptance test or historical evidence.
