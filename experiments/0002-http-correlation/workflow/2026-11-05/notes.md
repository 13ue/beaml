# Solver decision

**[Proposal]** Choose ULTRA: fixed contracts, direct routers, one capture owner and standard-library Python.
LITE supplies one concrete correction: verify fixture, generated-source and BEAM hashes separately.
No generalized source maps, client wrappers, Collector or replay are needed.
Scope reaches both service releases, compiled fixtures, capture callbacks, runner, query and focused tests.
Root maintains wiki evidence. Compiler 0001 remains unchanged.

## Test-first evidence

The first checker test uses a synthetic valid graph and a missing-log mutation.
Synthetic records are checker inputs, never real HTTP execution evidence.

## Repair authorization

On 2026-11-05, the owner reviewed the seven repair failures and instructed the
team to continue HTTP. The coordinator confirmed that the instruction covers
GREEN for the [seven reviewed cases](repair-red.md).

## Repair GREEN

**[Verified]** The [repair log](repair-green.log) records six query tests and
five repair tests. All passed. The seven RED assertions stayed in place.

- Orders opens one loopback TCP connection and sends one POST. It accepts the
  fixture's bounded HTTP 200 response with a single Content-Length header.
  A redirect, retry response or invalid reply returns the fixed HTTP 502.
  The OTP 27 client retries a short Retry-After without a request option to
  disable it. The repair uses the OTP packet parser and adds no dependency.
  [OTP 27 response handler](https://github.com/erlang/otp/blob/OTP-27.3.4/lib/inets/src/http_client/httpc_response.erl#L344)
- The checker requires both artifact entries and the SDK remote marker to
  verify the cross-service edge. H03 checks separate service traces with the
  four local edges and two logs. It permits only the missing Payments ingress edge.
- The runner stops before build or execution when Python optimization is on.
  Mix commands use the selected PATH with a scoped production build setting.
  The release processes keep their separate runtime settings.

**[Verified]** The [release run](../../results/20261105T220545655633Z/result.json)
passes H01–H05 and records six clean process exits. It rebuilt both releases
with Elixir 1.18.1 and OTP 27.3.4 from the selected executable directories.
The [boundary results](../../results/20261105T220545655633Z/boundary-controls/checks.json)
also record a fixed 502 on transport failure, loss reporting and HTTP 400 controls.
The [forced failure run](../../results/20261105T220612131147Z/result.json)
exited with status 1 after both releases started. Both release processes exited cleanly.
The first [sandbox run](../../results/20261105T220429812820Z/dependencies.stderr)
failed when Mix tried to open its local lock socket. The passing run used local
TCP permission, offline Hex and a temporary copy of the public registry cache.

The wire check covers the two-release loopback fixture and its fixed response.
Other HTTP response framing, external hosts and replay remain outside this run.
