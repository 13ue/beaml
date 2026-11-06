"""Check the separate REPLAY RUN runner on the first Orders call and the invalid replay records (gate 4, RED revision 2)."""
import base64
import datetime
import hashlib
import http.server
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from contextlib import ExitStack

EXPERIMENT = Path(__file__).resolve().parents[1]
REPO = EXPERIMENT.parents[1]
HTTP = EXPERIMENT.parent / "0002-http-correlation"
COMPILER = EXPERIMENT.parent / "0001-syntax-to-beam"
sys.path.insert(0, str(HTTP))
from run import digest, event, request, save, stop

TEST = "test_separate_runner_replays_first_call_and_rejects_invalid_records"
SERVICES = ("payments", "orders")
ORDER = {"order_id": "order-1"}
PAYMENT = {"order_id": "order-1", "status": "authorized"}
OPERATION, ATTEMPT = "payments.authorize", 1
# A1: valid PAYMENT with non-canonical JSON. Payments itself sends compact JSON.
STUB_BODY = b'{ "status" : "authorized",\n  "order_id" : "order-1" }'
WATCHED = ("OrdersApi.Router.call/2", "OrdersApi.PaymentHttp.authorize/2", ":gen_tcp.connect/4",
           "OrdersBeamlSpike.prepare/1", ":json.decode/1", "OrdersBeamlSpike.finish/1",
           "ProbeSupport.valid_payment!/2")

# [Requirement] Owner decisions 2026-11-06: no replay branch in the live router, no HTTP status for
# replay errors, a separate runner module in the Orders app (option A), a body digest check.
# [Proposal] Runner contract for GREEN: `OrdersApi.Replay.run(order, trace_id, records)` returns
# `{:ok, payment}` or `{:error, reason}`. Reasons: missing_response, operation_mismatch,
# attempt_mismatch, body_digest_mismatch. The runner shares the live decode and validation function
# (review A2). It never calls the router, `authorize/2` or `:gen_tcp.connect/4`.
# The retained Orders release runs this harness with `bin/orders eval`: no application starts.
# BEAM call counts observe the runner from outside. `:json.decode/1` counts decode entries.
HARNESS = r'''
input = :json.decode(File.read!(System.fetch_env!("REPLAY_INPUT")))
:persistent_term.put(:probe_count, :atomics.new(1, []))
watched = [{OrdersApi.Router, :call, 2}, {OrdersApi.PaymentHttp, :authorize, 2}, {:gen_tcp, :connect, 4},
           {OrdersBeamlSpike, :prepare, 1}, {:json, :decode, 1}, {OrdersBeamlSpike, :finish, 1},
           {ProbeSupport, :valid_payment!, 2}]
for {m, _, _} = mfa <- watched, do: (Code.ensure_loaded!(m); 1 = :erlang.trace_pattern(mfa, true, [:call_count]))
result =
  try do
    case input["mode"] do
      # Observer control: the real transport in this VM is counted (refused port).
      "control" -> OrdersApi.PaymentHttp.authorize(OrdersBeamlSpike.prepare(input["order"]), [])
      "replay" -> OrdersApi.Replay.run(input["order"], input["trace_id"], input["responses"])
    end
  rescue
    error -> {:raised, inspect(error.__struct__)}
  end
report = case result do
  {:ok, payment} -> %{ok: payment}
  {:error, reason} -> %{error: Atom.to_string(reason)}
  {:raised, name} -> %{raised: name}
  other -> %{unexpected: inspect(other)}
end
calls = Map.new(watched, fn {m, f, a} = mfa ->
  {"#{inspect(m)}.#{f}/#{a}", elem(:erlang.trace_info(mfa, :call_count), 1)} end)
IO.puts("REPLAY " <> IO.iodata_to_binary(:json.encode(%{
  result: report, transport: ProbeSupport.count(), calls: calls,
  artifact_id: ProbeSupport.beam_hash(OrdersBeamlSpike),
  started: Enum.map(Application.started_applications(), fn {app, _, _} -> Atom.to_string(app) end)})))
'''


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def test_separate_runner_replays_first_call_and_rejects_invalid_records(run, result):
    commands, failures = [], []

    def command(name, args, cwd=REPO, env=None):
        args = [str(arg) for arg in args]
        record = {"name": name, "argv": args, "cwd": str(cwd)}
        commands.append(record)
        save(run / "commands.json", commands)
        with (run / (name + ".stdout")).open("wb") as out, (run / (name + ".stderr")).open("wb") as err:
            record["exit_code"] = subprocess.run(args, cwd=cwd, env=env, stdout=out, stderr=err,
                                                 timeout=180).returncode
        save(run / "commands.json", commands)
        assert record["exit_code"] == 0, (name, record["exit_code"])
        return (run / (name + ".stdout")).read_text()

    def step(action, detail):
        result.setdefault("steps", []).append({"ts": utc().isoformat(), "action": action, "result": detail})
        event(action, TEST, detail)

    def check(name, expected, actual):
        result.setdefault("assertions", {})[name] = {"expected": expected, "actual": actual}
        if expected != actual:
            failures.append(f"{name}: expected {expected!r}; actual {actual!r}")

    step("start", "running")
    save(run / "toolchain.json", {tool: command(tool + "-version", [tool, "--version"])
                                  for tool in ("elixir", "mix", "rustc", "cargo", "python3")})
    inputs = [HTTP / name for name in ("mix.exs", "mix.lock", ".formatter.exs", "config/config.exs",
                                      "config/runtime.exs", "run.py", "query.py")]
    inputs += list((HTTP / "apps").glob("*/mix.exs"))
    inputs += list((HTTP / "apps").glob("*/priv/*.beaml"))
    inputs += [p for p in (HTTP / "apps").glob("*/lib/**/*.ex") if p.name != "generated.ex"]
    save(run / "input-hashes.json", {
        str(p.relative_to(REPO)): digest(p)
        for p in inputs + [Path(__file__).resolve(), COMPILER / "src/main.rs",
                           COMPILER / "Cargo.toml", COMPILER / "Cargo.lock"]
    })

    evidence = run / "original"
    evidence.mkdir()
    manifest = {"fixtures": {}, "capture": {}, "processes": {}, "artifacts": {}}
    with tempfile.TemporaryDirectory(prefix="beaml-replay-run-") as temporary, ExitStack() as cleanup:
        stage = Path(temporary)
        for path in inputs:
            target = stage / path.relative_to(HTTP)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        mix = ["env", "MIX_ENV=prod", "mix"]
        command("dependencies", [*mix, "deps.get", "--offline"], stage)
        for service in SERVICES:
            fixture = f"apps/{service}_api/priv/{service}.beaml"
            archived = evidence / f"{service}.beaml"
            shutil.copyfile(stage / fixture, archived)
            generated = command("generate-" + service, ["cargo", "run", "--offline", "--quiet", "--manifest-path",
                                                        COMPILER / "Cargo.toml", "--", archived])
            assert generated.count("defmodule BeamlSpike do") == 1
            code = stage / f"apps/{service}_api/lib/generated.ex"
            code.write_text(generated.replace("defmodule BeamlSpike do", f"defmodule {service.title()}BeamlSpike do"))
            shutil.copyfile(code, evidence / f"{service}.generated.ex")
            manifest["fixtures"][service] = {"source": fixture, "source_hash": digest(archived)}
            manifest["artifacts"][service] = {"generated_hash": digest(code)}
        release_beam = {}
        for service in SERVICES:
            command("release-" + service, [*mix, "release", service, "--overwrite"], stage)
            beam_name = f"Elixir.{service.title()}BeamlSpike.beam"
            release_beam[service] = stage / "_build/prod/rel" / service / f"lib/{service}_api-0.1.0/ebin/{beam_name}"
            beam = evidence / (beam_name + ".bin")
            shutil.copyfile(release_beam[service], beam)
            manifest["artifacts"][service]["beam_hash"] = digest(beam)
        orders_artifact = manifest["artifacts"]["orders"]["beam_hash"]
        orders_bin = stage / "_build/prod/rel/orders/bin/orders"

        def env(out, payments_port):
            return dict(PATH="/usr/bin:/bin:/usr/sbin:/sbin", PROBE_SERVICE="orders", PROBE_OUTPUT=str(out),
                        PROBE_PAYMENTS_PORT=str(payments_port), PROBE_DROP_CONTEXT="false",
                        RELEASE_DISTRIBUTION="none", RELEASE_COOKIE="beaml_synthetic_loopback_test")

        def start(service, out, payments_port):
            out.mkdir()
            for kind in ("spans", "logs"):
                (out / (kind + ".jsonl")).touch()
            launch = [str(stage / "_build/prod/rel" / service / "bin" / service), "start"]
            commands.append({"name": f"start-{service}-{out.name}", "argv": launch, "cwd": str(REPO)})
            save(run / "commands.json", commands)
            log = cleanup.enter_context((out / "process.log").open("wb"))
            process = subprocess.Popen(launch, env={**env(out, payments_port), "PROBE_SERVICE": service},
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            cleanup.callback(stop, process)
            deadline = time.monotonic() + 20
            while not (out / "ready.json").exists():
                assert process.poll() is None and time.monotonic() < deadline, ("service_not_ready", service)
                time.sleep(.05)
            port = json.loads((out / "ready.json").read_text())["port"]
            status, control = request(port)
            save(out / "startup-control.json", control)
            assert status == 200 and control["count"] == 0 and control["listener"] == "127.0.0.1"
            assert control["own_loaded"] and not control["sibling_loaded"] and not control["sibling_available"]
            assert control["beam_hash"] == manifest["artifacts"][service]["beam_hash"]
            return process, port, control

        # Baseline 1: two live Orders decisions with correlated traces, one transport entry and one
        # predecode response record per receipt (gate 3 behavior).
        ports, processes = {}, {}
        for service in SERVICES:
            processes[service], ports[service], manifest["processes"][service] = start(
                service, run / service, ports.get("payments", 0))
        step("step", "fresh_releases_match_archived_beams")
        receipts, seen, attempts = [], set(), []
        for call in (1, 2):
            status, body = request(ports["orders"], "/orders", ORDER)
            assert (status, body) == (200, PAYMENT)
            controls = {}
            for service in SERVICES:
                control_status, controls[service] = request(ports[service])
                assert control_status == 200 and not controls[service]["capture"]["loss"]
                manifest["capture"][service] = controls[service]["capture"]
                save(run / f"{service}-control-{call}.json", controls[service])
                for kind in ("spans", "logs"):
                    shutil.copyfile(run / service / (kind + ".jsonl"), evidence / f"{service}.{kind}.jsonl")
            assert controls["payments"]["count"] == call
            save(evidence / "manifest.json", manifest)
            checked = json.loads(command(f"baseline-call-{call}", [sys.executable, HTTP / "query.py", "--run",
                                                                   evidence, "--order-id", "order-1"]))
            traces = set(checked["traces"])
            assert checked["complete"] and seen <= traces and len(traces - seen) == 1
            trace = (traces - seen).pop()
            receipts.append({"call": call, "status": status, "body": body, "trace_id": trace})
            attempts.append(controls["orders"]["count"])
            seen = traces
            step("step", f"receipt_{call}_verified")
        for process in processes.values():
            stop(process)
        result["release_exits"] = {service: process.returncode for service, process in processes.items()}
        assert all(code == 0 for code in result["release_exits"].values())
        assert attempts == [1, 2], attempts
        records = rows(run / "orders/responses.jsonl")
        assert [r["trace_id"] for r in records] == [r["trace_id"] for r in receipts]
        first = records[0]
        assert (first["artifact_id"], first["operation"], first["attempt"], first["request"], first["status"]) == (
            orders_artifact, OPERATION, ATTEMPT, ORDER, 200)
        assert json.loads(base64.b64decode(first["body_base64"])) == PAYMENT
        responses = evidence / "orders.responses.jsonl"
        shutil.copyfile(run / "orders/responses.jsonl", responses)
        responses_hash = digest(responses)
        result["baseline"] = {"receipts": receipts, "live_transport_attempts": attempts,
                              "response_records": len(records), "responses_sha256": responses_hash}
        step("step", "live_baseline_and_records_verified")

        # Baseline 2 (review A1): Orders against a loopback stub Payments with a non-canonical body.
        sent = []

        class Stub(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                sent.append(self.rfile.read(int(self.headers["Content-Length"])))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(STUB_BODY)))
                self.end_headers()
                self.wfile.write(STUB_BODY)

            def log_message(self, *args):
                pass

        stub = http.server.HTTPServer(("127.0.0.1", 0), Stub)
        cleanup.callback(stub.server_close)
        threading.Thread(target=stub.serve_forever, daemon=True).start()
        cleanup.callback(stub.shutdown)
        process, port, _ = start("orders", run / "stub", stub.server_address[1])
        assert request(port, "/orders", ORDER) == (200, PAYMENT)
        _, stub_control = request(port)
        stop(process)
        assert process.returncode == 0 and stub_control["count"] == 1 and len(sent) == 1
        assert not stub_control["capture"]["loss"]
        stub_records = rows(run / "stub/responses.jsonl")
        assert len(stub_records) == 1
        check("a1_record_bytes_equal_sent_bytes", base64.b64encode(STUB_BODY).decode(),
              stub_records[0]["body_base64"])
        step("step", "a1_stub_record_retained")

        # Verify the retained Orders artifact against the run record before replay. No rebuild.
        assert digest(release_beam["orders"]) == orders_artifact == stub_records[0]["artifact_id"]

        with socket.socket() as closed:
            closed.bind(("127.0.0.1", 0))
            refused_port = closed.getsockname()[1]

        def replay(name, replay_input):
            out = run / "replay" / name
            out.mkdir(parents=True)
            save(out / "input.json", {"order": ORDER, **replay_input})
            text = command(f"replay-{name}", [orders_bin, "eval", HARNESS],
                           env={**env(out, refused_port), "REPLAY_INPUT": str(out / "input.json")})
            lines = [line[7:] for line in text.splitlines() if line.startswith("REPLAY ")]
            assert len(lines) == 1, ("replay_report", name)
            report = json.loads(lines[0])
            save(out / "report.json", report)
            # Isolation: only the base applications run; the in-VM artifact equals the run record.
            assert set(report["started"]) <= {"kernel", "stdlib", "compiler", "elixir", "logger"}, report
            assert report["artifact_id"] == orders_artifact
            return {"result": report["result"], "transport": report["transport"],
                    **{name: report["calls"][name] for name in WATCHED}}

        # Control: in the same eval VM, the real transport is reached and counted (A4: Orders count
        # means transport entries). So zero counts in the runner cases are meaningful.
        control = replay("control-transport-observer", {"mode": "control"})
        assert control == {"result": {"raised": "MatchError"}, "transport": 1, "OrdersApi.Router.call/2": 0,
                           "OrdersApi.PaymentHttp.authorize/2": 1, ":gen_tcp.connect/4": 1,
                           "OrdersBeamlSpike.prepare/1": 1, ":json.decode/1": 0,
                           "OrdersBeamlSpike.finish/1": 0, "ProbeSupport.valid_payment!/2": 0}, control
        step("step", "replay_vm_observer_control_counted_transport")

        def isolated(result, decided):
            # Never the router or the live transport. Decode, finish and validation only for a decision.
            return {"result": result, "transport": 0, "OrdersApi.Router.call/2": 0,
                    "OrdersApi.PaymentHttp.authorize/2": 0, ":gen_tcp.connect/4": 0,
                    ":json.decode/1": decided, "OrdersBeamlSpike.finish/1": decided,
                    "ProbeSupport.valid_payment!/2": decided}

        def run_replay(name, trace_id, responses):
            return replay(name, {"mode": "replay", "trace_id": trace_id, "responses": responses})

        first_trace = receipts[0]["trace_id"]
        live = {"ok": receipts[0]["body"]}
        check("replay_first_call", {**isolated(live, 1), "OrdersBeamlSpike.prepare/1": 1},
              run_replay("first-call", first_trace, records))
        check("replay_a1_noncanonical_body", {**isolated(live, 1), "OrdersBeamlSpike.prepare/1": 1},
              run_replay("a1-noncanonical", stub_records[0]["trace_id"], stub_records))
        # Digest case: same length, other bytes, still a valid PAYMENT. Only the digest check rejects it.
        original = base64.b64decode(records[0]["body_base64"])
        tampered = json.dumps(dict(reversed(json.loads(original).items())), separators=(",", ":")).encode()
        assert tampered != original and len(tampered) == len(original) == records[0]["body_length"]
        assert json.loads(tampered) == PAYMENT
        derivatives = {
            "missing_response": [r for r in records if r["trace_id"] != first_trace],
            "operation_mismatch": [{**records[0], "operation": "payments.capture"}, *records[1:]],
            "attempt_mismatch": [{**records[0], "attempt": ATTEMPT + 1}, *records[1:]],
            "body_digest_mismatch": [{**records[0], "body_base64": base64.b64encode(tampered).decode()},
                                     *records[1:]],
        }
        for code, derivative in derivatives.items():
            actual = run_replay(code.replace("_", "-"), first_trace, derivative)
            actual.pop("OrdersBeamlSpike.prepare/1")  # not constrained for an evidence error
            check(f"replay_{code}", isolated({"error": code}, 0), actual)
        step("step", "replay_cases_ran")
        assert digest(responses) == responses_hash

    save(evidence / "manifest.json", manifest)
    if failures:
        result["assertion_failures"] = failures
        step("fail", "replay_assertions_failed")
        raise AssertionError("\n".join(failures))
    step("pass", "replay_verified")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    run = EXPERIMENT / "results" / utc().strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True)
    result = {"test": TEST, "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "status": "fail"}
    print(run, flush=True)
    try:
        test_separate_runner_replays_first_call_and_rejects_invalid_records(run, result)
        result["status"] = "pass"
    except Exception:
        (run / "test.stderr").write_text(traceback.format_exc())
        raise
    finally:
        if result["status"] == "fail" and "assertion_failures" not in result:
            event("fail", TEST, "test_setup_failed")
        save(run / "result.json", result)
        save(run / "output-hashes.json", {
            str(path.relative_to(run)): digest(path) for path in sorted(run.rglob("*")) if path.is_file()
        })
