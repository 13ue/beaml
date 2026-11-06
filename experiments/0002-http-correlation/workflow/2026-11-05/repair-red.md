# EXPERIMENT 0002 repair RED

**[Verified]** The new tests reached their behavior assertions against the unchanged implementation. See [commands and assertion output](repair-red.log).

| Test | Expected | Observed | Cause |
|---|---|---|---|
| `test_retry_after_zero_sends_exactly_one_post` | Fixed HTTP 502 and one Payments POST | HTTP 200 and two Payments POSTs | The HTTP client follows `503 Retry-After: 0` with a second POST. |
| `test_redirect_is_rejected_without_calling_sink` | Fixed HTTP 502 and zero sink POSTs | HTTP 200 and one sink POST | The HTTP client follows the 307 response to the second loopback listener. |
| `test_h03_rejects_intact_payment_edge_with_detached_finish` | H03 fails when the Orders-to-Payments edge survives | H03 passes. Its sole missing causal edge points to `orders.finish`. | The predicate accepts any missing edge with two trace IDs. |
| `test_payments_ingress_requires_remote_parent` | `complete=false` and a `remote_parent` gap | `complete=true` and no gaps | The checker validates parent identity without checking the SDK remote marker. |
| `test_missing_artifact_metadata_is_a_gap` | `complete=false` and a `missing_artifacts` gap | `complete=true` and no gaps | The checker skips generated-source and BEAM verification when the section is absent. |
| `test_optimized_runner_keeps_acceptance_or_rejects_before_running` | Reject `-O` before a run, or execute and enforce H03 | H03 reports pass with `no_traces`. | Python removes both the H03 HTTP request and acceptance checks under `-O`. |
| `test_build_uses_the_toolchain_selected_on_path` | Version, setup and build use the alternate tool directory | The two release builds and strict compilation use a different Mix. | Those commands replace the selected PATH with an absolute machine-specific PATH. |

The query tests first pass a complete fixture with both generated-source hashes, matching BEAM metadata and the remote ingress marker. The transport tests start the prebuilt Orders release and count actual loopback POSTs. The H03 tests use the runner CLI and both prebuilt releases. They bypass build commands and inject the wrong edge into a temporary capture. The alternate PATH test records executable resolution without running a build. Use the independent full run to verify compilation and the retained acceptance evidence after repair.

Run from the EXPERIMENT directory.

```sh
python3 -m unittest discover -s tests -p test_query.py -v
python3 tests/http_repair_test.py -v
```

The repair RED phase changed tests and this record. Production changes require owner review and an explicit instruction to continue.
