"""Check predecode response CAPTURE and the Orders transport observer with actual 0002 releases."""
import base64
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from contextlib import ExitStack

EXPERIMENT = Path(__file__).resolve().parents[1]
REPO = EXPERIMENT.parents[1]
HTTP = EXPERIMENT.parent / "0002-http-correlation"
COMPILER = EXPERIMENT.parent / "0001-syntax-to-beam"
sys.path.insert(0, str(HTTP))
from run import digest, event, request, save, stop

TEST = "test_live_orders_call_captures_predecode_response_and_one_transport_attempt"
SERVICES = ("payments", "orders")
ORDER = {"order_id": "order-1"}
PAYMENT = {"order_id": "order-1", "status": "authorized"}
# [Proposal] Record contract for this gate. One record per live response, written before JSON decode.
OPERATION, ATTEMPT, VERSION = "payments.authorize", 1, 1


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def test_live_orders_call_captures_predecode_response_and_one_transport_attempt(run, result):
    commands, failures = [], []

    def command(name, args, cwd=REPO):
        args = [str(arg) for arg in args]
        record = {"name": name, "argv": args, "cwd": str(cwd)}
        commands.append(record)
        save(run / "commands.json", commands)
        with (run / (name + ".stdout")).open("wb") as out, (run / (name + ".stderr")).open("wb") as err:
            record["exit_code"] = subprocess.run(args, cwd=cwd, stdout=out, stderr=err, timeout=180).returncode
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
    with tempfile.TemporaryDirectory(prefix="beaml-response-capture-") as temporary, ExitStack() as cleanup:
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
        for service in SERVICES:
            command("release-" + service, [*mix, "release", service, "--overwrite"], stage)
            beam_name = f"Elixir.{service.title()}BeamlSpike.beam"
            beam = evidence / (beam_name + ".bin")
            shutil.copyfile(stage / "_build/prod/rel" / service / f"lib/{service}_api-0.1.0/ebin/{beam_name}", beam)
            manifest["artifacts"][service]["beam_hash"] = digest(beam)
        orders_artifact = manifest["artifacts"]["orders"]["beam_hash"]

        def start(service, out, payments_port):
            out.mkdir()
            for kind in ("spans", "logs"):
                (out / (kind + ".jsonl")).touch()
            env = dict(PATH="/usr/bin:/bin:/usr/sbin:/sbin", PROBE_SERVICE=service, PROBE_OUTPUT=str(out),
                       PROBE_PAYMENTS_PORT=str(payments_port), PROBE_DROP_CONTEXT="false",
                       RELEASE_DISTRIBUTION="none", RELEASE_COOKIE="beaml_synthetic_loopback_test")
            launch = [str(stage / "_build/prod/rel" / service / "bin" / service), "start"]
            commands.append({"name": f"start-{service}-{out.name}", "argv": launch, "cwd": str(REPO)})
            save(run / "commands.json", commands)
            log = cleanup.enter_context((out / "process.log").open("wb"))
            process = subprocess.Popen(launch, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
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

        # Live pair. Baseline first: two successful Orders decisions with correlated traces.
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
        result["baseline"] = {"receipts": receipts, "payments_count_delta": 2}
        for process in processes.values():
            stop(process)
        result["release_exits"] = {service: process.returncode for service, process in processes.items()}
        assert all(code == 0 for code in result["release_exits"].values())
        step("step", "live_releases_stopped")

        # Behavior 1: one transport entry per live receipt, read from the Orders control counter.
        check("orders_transport_attempts_after_each_call", [1, 2], attempts)

        # Behavior 2: predecode response record per live receipt, bound to trace, client span, artifact,
        # operation and attempt. Bytes are byte-exact Base64 with length and SHA-256.
        clients = {row["trace_id"]: row["span_id"] for row in rows(run / "orders/spans.jsonl")
                   if row["name"] == "orders.payments.authorize"}
        records = rows(run / "orders/responses.jsonl")
        if records:
            shutil.copyfile(run / "orders/responses.jsonl", evidence / "orders.responses.jsonl")
        check("response_record_traces", [r["trace_id"] for r in receipts], [r.get("trace_id") for r in records])
        if records:
            first = records[0]
            raw = base64.b64decode(first.get("body_base64") or "")
            check("first_response_record", {
                "version": VERSION, "trace_id": receipts[0]["trace_id"],
                "client_span_id": clients.get(receipts[0]["trace_id"]), "artifact_id": orders_artifact,
                "operation": OPERATION, "attempt": ATTEMPT, "request": ORDER, "status": 200,
                "body_length": len(raw), "body_sha256": hashlib.sha256(raw).hexdigest(),
            }, {key: first.get(key) for key in ("version", "trace_id", "client_span_id", "artifact_id",
                                                "operation", "attempt", "request", "status",
                                                "body_length", "body_sha256")})
            check("first_response_body", {"bounded": True, "json": PAYMENT},
                  {"bounded": 1 <= len(raw) <= 1024, "json": json.loads(raw) if raw else None})

        # Behavior 3: separate failure control. A refused loopback connect must still count one entry.
        # An invalid order must not reach the transport.
        with socket.socket() as closed:
            closed.bind(("127.0.0.1", 0))
            refused_port = closed.getsockname()[1]
        process, port, _ = start("orders", run / "observer-control", refused_port)
        invalid_status, invalid_body = request(port, "/orders", {"order_id": "other"})
        assert (invalid_status, invalid_body) == (400, {"error": "invalid_request"})
        _, after_invalid = request(port)
        refused_status, refused_body = request(port, "/orders", ORDER)
        assert (refused_status, refused_body) == (502, {"error": "downstream_failure"})
        _, after_refused = request(port)
        save(run / "observer-control/control-after.json", after_refused)
        stop(process)
        result["observer_control"] = {"refused_port": refused_port, "exit": process.returncode,
                                      "statuses": [invalid_status, refused_status]}
        assert process.returncode == 0 and not after_refused["capture"]["loss"]
        # The 502 comes from the real Orders transport: one ended client span with an error outcome.
        assert [(r["name"], r["attributes"].get("outcome")) for r in rows(run / "observer-control/spans.jsonl")
                if r["name"] == "orders.payments.authorize"] == [("orders.payments.authorize", "error")]
        step("step", "observer_control_reached_transport_failure")
        check("observer_control_attempts_invalid_then_refused", [0, 1],
              [after_invalid["count"], after_refused["count"]])
        check("observer_control_response_records", 0, len(rows(run / "observer-control/responses.jsonl")))

    save(evidence / "manifest.json", manifest)
    if failures:
        result["assertion_failures"] = failures
        step("fail", "capture_and_transport_assertions_failed")
        raise AssertionError("\n".join(failures))
    step("pass", "capture_and_transport_verified")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    run = EXPERIMENT / "results" / utc().strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True)
    result = {"test": TEST, "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "status": "fail"}
    print(run, flush=True)
    try:
        test_live_orders_call_captures_predecode_response_and_one_transport_attempt(run, result)
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
