---
id: experiment-0002-http-correlation-plan
kind: experiment
status: independent-verification-passed
updated: 2026-11-05
---

# EXPERIMENT 0002 — HTTP correlation

**[Proposal]** Can one synthetic order reference find a causal path and its logs across two independent BEAM processes?
The hypothesis is that explicit HTTP propagation and a shared observation adapter can preserve this relationship around compiled BEAML functions.

**[Requirement]** The owner requested a plan before implementation, then authorized the EXPERIMENT and the seven reviewed repairs.
The [planning request](../../raw/requirements/2026-11-05-http-probe-plan.md), [workflow adoption](../../raw/requirements/2026-11-05-implementation-workflow.md) and [repair record](workflow/2026-11-05/notes.md#repair-authorization) retain those decisions.
The [workflow baseline](workflow/2026-11-05/spec.md) preserves the original proposed scope.

## Run the EXPERIMENT

Use a POSIX host with loopback TCP available. The [recorded run](results/20261105T220545655633Z/result.json) used Python 3.9.6, Elixir/Mix 1.18.1, Erlang/OTP 27.3.4 and Rust/Cargo 1.94.0.
Put the selected Elixir, Erlang and Rust tools on PATH. Run Python with optimization disabled.
Install Hex and Rebar for the selected Mix toolchain. Populate the local Hex cache with the packages in [mix.lock](mix.lock).
On a host with an empty cache, run the dependency setup with network access from the repository root.

```sh
(
  cd experiments/0002-http-correlation
  mix local.hex --force
  mix local.rebar --force
  MIX_ENV=prod mix deps.get
)
```

Run from the repository root after dependency setup. The runner fetches from the local cache with Mix offline mode and needs local sockets for Mix and the two HTTP services.

```sh
python3 experiments/0002-http-correlation/run.py
```

The runner prints the run directory and status. It regenerates both Elixir fixtures with the EXPERIMENT 0001 compiler, builds the releases and runs formatting, strict compilation, Python discovery and ExUnit checks.
It runs H01–H05 against the releases and stops the processes on exit.
Each EXPERIMENT RUN records commands, tool versions, build inputs and hashes, observations, case results and cleanup under `results/<UTC-id>/`.
CLI and case actions append to the repository's `.beaml/actions.jsonl` with fixed action names and outcomes.

Query the `normal` evidence directory of an EXPERIMENT RUN. This example uses the retained repaired run.

```sh
python3 experiments/0002-http-correlation/query.py \
  --run experiments/0002-http-correlation/results/20261105T220545655633Z/normal \
  --order-id order-1
```

The query checks trace and span identities, parent references, the SDK remote marker, log identity, fixture hashes, generated source hashes and recorded BEAM hashes.
It returns JSON and exits 1 for incomplete evidence. The parent check uses trace and span identity. The order reference selects records.

Run the focused checks after building both releases with the runner.

```sh
(
  cd experiments/0002-http-correlation
  python3 -m unittest discover -s tests
  python3 tests/http_repair_test.py -v
)
```

## Fixed HTTP subset

**[Verified]** One umbrella builds two releases. Each release runs its own business application in a separate BEAM operating-system process.
The recorded releases use loopback listeners and disable Erlang distribution. Each release reports its sibling application absent.
The shared `probe_support` application owns observation and boundary helpers. See the [release manifest](results/20261105T220545655633Z/normal/manifest.json).

- LANGUAGE/COMPILATION owns the String and exact-interface subset and generated entry checks.
- EXECUTION owns HTTP, JSON, the fixed order and payment values, and observed outcomes.
- OBSERVATORY owns local trace and log projection and correlation checks.

Orders accepts only `{"order_id":"order-1"}` at `POST /orders`.
It calls compiled `prepare`, sends one `POST /payments/authorize` and calls compiled `finish`.
Payments calls compiled `authorize` and returns the synthetic `{"order_id":"order-1","status":"authorized"}`.
The host checks the matching order and expected status. The Payments stub has no business mutation.

Orders accepts a loopback HTTP/1.0 or HTTP/1.1 response with status 200 and one Content-Length of 1–1024 bytes.
The client rejects transfer encoding, redirects and retry responses. It uses one TCP connection per payment request.
Malformed or invalid input returns HTTP 400 with `invalid_request`. Downstream transport or response failure returns HTTP 502 with `downstream_failure`.
See the [Orders HTTP client](apps/orders_api/lib/orders_api/payment_http.ex) and [boundary checks](results/20261105T220545655633Z/boundary-controls/checks.json).

## Trace and log contract

**[Verified]** The releases use real OpenTelemetry spans and W3C TRACE CONTEXT propagation via `traceparent`.
Orders starts a fresh root per accepted request. Payments extracts the remote parent.
The checked request body supplies the synthetic order reference. The propagator carries trace identity.

| Span | Kind | Parent |
|---|---|---|
| `orders.request` | server | Root |
| `orders.prepare` | internal | `orders.request` |
| `orders.payment_http` | client | `orders.request` |
| `payments.request` | server | Remote `orders.payment_http` |
| `payments.authorize` | internal | `payments.request` |
| `orders.finish` | internal | `orders.request` |

The structured `payment_request_prepared` and `payment_stub_returned` logs refer to their actual trace and span identities.
These are OBSERVATION EVENTS. The three internal spans carry configured fixture paths, function names and source hashes.
The SDK exporter and Logger handler write local JSONL files with a 1 MiB cap per file.
The control endpoint reports capture loss separately from the business HTTP response.
The [normal query evidence](results/20261105T220545655633Z/normal/query-H02.json) shows the two connected traces.

**[Verified]** Note, 2026-11-07 (EXPERIMENT 0004 slice 6b step 12, D6B-127): `ProbeSupport.event/2` with no open span records `trace_id` and `span_id` as the literal `"none"`, returns `:ok` and does not raise. Such a row has no span link. The router runs above always have an open span. Evidence: [0004 steps 12 and 12b](../0004-generated-replay/README.md#slice-6b-steps-12-and-12b-spans-on-the-effect-path-and-a-pure-constructor).

## Retained results

**[Verified]** The [repaired EXPERIMENT RUN](results/20261105T220545655633Z/result.json) passed H01–H05. All six release processes exited with status 0.

| Case | Observed result |
|---|---|
| H01 | HTTP 200 with the exact response, six connected spans and two correlated logs |
| H02 | Two traces for the same order, ten parent edges and four correlated logs |
| H03 | Two separate traces, four local edges and two logs. The sole gap is the missing cross-service parent edge. |
| H04 | The query exited 1 for the missing log in a derivative copy. The original observation files stayed unchanged. |
| H05 | HTTP 400 for an extra field. The independent Payments request counter stayed at 2. |

The [boundary checks](results/20261105T220545655633Z/boundary-controls/checks.json) also record HTTP 400 for malformed JSON and invalid shapes, HTTP 502 for transport failure, and explicit capture loss with HTTP 200 preserved.
The [forced failure run](results/20261105T220612131147Z/result.json) records the deliberate post-start failure and clean exit of both release processes.
The [repair log](workflow/2026-11-05/repair-green.log) records six passing query tests, five passing repair tests and rejection of optimized Python.
The [initial independent test](workflow/2026-11-05/test-result.json), [review](workflow/2026-11-05/review.md) and [repair RED record](workflow/2026-11-05/repair-red.md) preserve the earlier findings.
**[Verified]** [Independent final verification](workflow/2026-11-05/result.json) passed all seven repair assertions. The [final EXPERIMENT RUN](results/20261105T221134010042Z/result.json) passed H01–H05.
The owner adopted the review checkpoint after the initial GREEN. Owner review of the initial RED remains unverified. The owner approved the seven repair assertions before implementation.

## Limits

The result covers two local releases, one fixed order reference and bounded file evidence.
The fixture uses manual host instrumentation. Automatic source maps, language instrumentation and comparative author effort remain unmeasured.
Inventory, live payments, persisted DOMAIN EVENTS, production deployment, durability, performance and REPLAY RUNS are outside scope.
