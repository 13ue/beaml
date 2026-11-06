"""Exercise exact-source lookup with actual 0002 releases and the public query."""
import datetime
import json
from pathlib import Path
import re
import shutil
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

TEST = "test_two_live_receipts_resolve_original_payments_declaration"
SERVICES = ("payments", "orders")
PAYMENT = {"order_id": "order-1", "status": "authorized"}


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def test_two_live_receipts_resolve_original_payments_declaration(run, result):
    commands = []

    def command(name, args, cwd=REPO, allowed=(0,)):
        args = [str(arg) for arg in args]
        record = {"name": name, "argv": args, "cwd": str(cwd)}
        commands.append(record)
        save(run / "commands.json", commands)
        with (run / (name + ".stdout")).open("wb") as out, (run / (name + ".stderr")).open("wb") as err:
            code = subprocess.run(args, cwd=cwd, stdout=out, stderr=err, timeout=180).returncode
        record["exit_code"] = code
        save(run / "commands.json", commands)
        assert code in allowed, (name, code)
        return code, (run / (name + ".stdout")).read_text()

    def step(action, detail):
        result.setdefault("steps", []).append({"ts": utc().isoformat(), "action": action, "result": detail})
        event(action, TEST, detail)

    def generate(source, destination, service, name):
        _, generated = command(name, ["cargo", "run", "--offline", "--quiet", "--manifest-path",
                                      COMPILER / "Cargo.toml", "--", source])
        assert generated.count("defmodule BeamlSpike do") == 1
        destination.write_text(generated.replace("defmodule BeamlSpike do", f"defmodule {service.title()}BeamlSpike do"))
        return generated

    def reference(source, generated, beam):
        [(start, end)] = re.findall(r"^  # beaml-declaration-v1 authorize (\d+) (\d+)$", generated, re.M)
        start, end = int(start), int(end)
        raw = source.read_bytes()
        declaration = raw[start:end].decode()
        assert declaration.startswith("fn authorize ") and end == len(raw.rstrip())
        return {
            "artifact_id": digest(beam),
            "source_id": {"qualified_name": "payments.authorize", "source_sha256": digest(source)},
            "byte_range": [start, end],
        }, declaration

    step("start", "running")
    versions = {}
    for tool in ("elixir", "mix", "rustc", "cargo", "python3"):
        _, versions[tool] = command(tool + "-version", [tool, "--version"])
    save(run / "toolchain.json", versions)

    # Copy known build inputs only. Keep the shared 0002 build and observations intact.
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
    with tempfile.TemporaryDirectory(prefix="beaml-trace-lookup-") as temporary, ExitStack() as cleanup:
        stage = Path(temporary)
        for path in inputs:
            target = stage / path.relative_to(HTTP)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        mix = ["env", "MIX_ENV=prod", "mix"]
        command("dependencies", [*mix, "deps.get", "--offline"], stage)
        generated = {}
        for service in SERVICES:
            fixture = f"apps/{service}_api/priv/{service}.beaml"
            archived = evidence / f"{service}.beaml"
            shutil.copyfile(stage / fixture, archived)
            staged_code = stage / f"apps/{service}_api/lib/generated.ex"
            generated[service] = generate(archived, staged_code, service, "generate-" + service)
            code = evidence / f"{service}.generated.ex"
            shutil.copyfile(staged_code, code)
            manifest["fixtures"][service] = {"source": fixture, "source_hash": digest(archived)}
            manifest["artifacts"][service] = {"generated_hash": digest(code)}
        for service in SERVICES:
            command("release-" + service, [*mix, "release", service, "--overwrite"], stage)
            release = stage / "_build/prod/rel" / service
            beam_name = f"Elixir.{service.title()}BeamlSpike.beam"
            beam = evidence / (beam_name + ".bin")
            shutil.copyfile(release / f"lib/{service}_api-0.1.0/ebin/{beam_name}", beam)
            manifest["artifacts"][service]["beam_hash"] = digest(beam)
            if service == "payments":
                selected, declaration = reference(evidence / "payments.beaml", generated[service], beam)

        ports, processes = {}, {}
        for service in SERVICES:
            out = run / service
            out.mkdir()
            for kind in ("spans", "logs"):
                (out / (kind + ".jsonl")).touch()
            env = dict(PATH="/usr/bin:/bin:/usr/sbin:/sbin", PROBE_SERVICE=service, PROBE_OUTPUT=str(out),
                       PROBE_PAYMENTS_PORT=str(ports.get("payments", 0)), PROBE_DROP_CONTEXT="false",
                       RELEASE_DISTRIBUTION="none", RELEASE_COOKIE="beaml_synthetic_loopback_test")
            binary = stage / "_build/prod/rel" / service / "bin" / service
            launch = [str(binary), "start"]
            commands.append({"name": "start-" + service, "argv": launch, "cwd": str(REPO)})
            save(run / "commands.json", commands)
            log = cleanup.enter_context((out / "process.log").open("wb"))
            process = subprocess.Popen(launch, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            cleanup.callback(stop, process)
            processes[service] = process
            ready = out / "ready.json"
            deadline = time.monotonic() + 20
            while not ready.exists():
                assert process.poll() is None and time.monotonic() < deadline, ("service_not_ready", service)
                time.sleep(.05)
            ports[service] = json.loads(ready.read_text())["port"]
            status, control = request(ports[service])
            save(out / "startup-control.json", control)
            assert status == 200 and control["count"] == 0
            assert control["listener"] == "127.0.0.1" and control["node"] == "nonode@nohost"
            assert control["own_loaded"] and not control["sibling_loaded"] and not control["sibling_available"]
            assert control["beam_hash"] == manifest["artifacts"][service]["beam_hash"]
            assert all((out / (kind + ".jsonl")).stat().st_size == 0 for kind in ("spans", "logs"))
            manifest["processes"][service] = control
        assert manifest["processes"]["orders"]["pid"] != manifest["processes"]["payments"]["pid"]
        step("step", "fresh_releases_match_archived_beams")

        def query(name, context, allowed=(0,)):
            code, output = command(name, [sys.executable, HTTP / "query.py", "--run", context,
                                         "--order-id", "order-1"], allowed=allowed)
            return code, json.loads(output)

        receipts, seen = [], set()
        window_start = utc().isoformat()
        for call in (1, 2):
            status, body = request(ports["orders"], "/orders", {"order_id": "order-1"})
            assert (status, body) == (200, PAYMENT)
            for service in SERVICES:
                control_status, control = request(ports[service])
                assert control_status == 200 and not control["capture"]["loss"]
                manifest["capture"][service] = control["capture"]
                if service == "payments":
                    assert control["count"] == call
                    save(run / f"payments-control-{call}.json", control)
                for kind in ("spans", "logs"):
                    shutil.copyfile(run / service / (kind + ".jsonl"), evidence / f"{service}.{kind}.jsonl")
            save(evidence / "manifest.json", manifest)
            _, checked = query(f"baseline-call-{call}", evidence)
            traces = set(checked["traces"])
            assert checked["complete"] and seen <= traces and len(traces - seen) == 1
            assert len(checked["edges"]) == 5 * call and len(checked["logs"]) == 2 * call
            trace = (traces - seen).pop()
            receipts.append({"call": call, "status": status, "body": body, "trace_id": trace})
            seen = traces
            step("step", "first_receipt_verified" if call == 1 else "second_receipt_verified")
        manifest["window"] = {"start_utc": window_start, "end_utc": utc().isoformat()}
        manifest["receipts"] = receipts
        manifest["function_lookup"] = selected
        save(evidence / "manifest.json", manifest)
        result["baseline"] = {"receipts": receipts, "edges": 10, "logs": 4, "payments_count_delta": 2}
        for process in processes.values():
            stop(process)
        result["release_exits"] = {service: process.returncode for service, process in processes.items()}
        assert all(code == 0 for code in result["release_exits"].values())

    revised = run / "current-revision"
    revised.mkdir()
    changed = revised / "payments.beaml"
    original = evidence / "payments.beaml"
    assert original.read_bytes().count(b'"authorized"') == 1
    changed.write_bytes(original.read_bytes().replace(b'"authorized"', b'"revised"'))
    revised_code = revised / "payments.generated.ex"
    generated = generate(changed, revised_code, "payments", "generate-revision")
    command("compile-revision", ["elixirc", "-o", revised, revised_code])
    revised_beam = revised / "Elixir.PaymentsBeamlSpike.beam"
    alternate, alternate_declaration = reference(changed, generated, revised_beam)
    assert alternate["source_id"]["qualified_name"] == selected["source_id"]["qualified_name"]
    assert alternate["source_id"] != selected["source_id"] and alternate["artifact_id"] != selected["artifact_id"]
    assert alternate_declaration != declaration
    command("execute-revision", ["elixir", "-pa", revised, "-e",
                                 'true = PaymentsBeamlSpike.authorize(%{"order_id" => "order-1"}) == '
                                 '%{"order_id" => "order-1", "status" => "revised"}'])
    revised_beam.rename(revised / (revised_beam.name + ".bin"))
    save(revised / "manifest.json", alternate)
    manifest["current_revision"] = "../current-revision"
    save(evidence / "manifest.json", manifest)
    missing = run / "missing-original"
    shutil.copytree(evidence, missing)
    (missing / "payments.beaml").unlink()
    step("step", "same_name_distinct_compiled_revision_and_missing_source_control_ready")

    original_hashes = {p.name: digest(p) for p in evidence.iterdir()}
    lookup_exit, observed = query("query-with-current-revision", evidence, allowed=(0, 1))
    missing_exit, absent = query("query-missing-original", missing, allowed=(0, 1))
    assert original_hashes == {p.name: digest(p) for p in evidence.iterdir()}
    summary = observed.get("function_summary")
    expected = {
        "artifact_id": selected["artifact_id"], "source_id": selected["source_id"],
        "matched_calls": 2, "completed_calls": 2, "successful_outcomes": 2,
        "first_trace_id": receipts[0]["trace_id"], "declaration": declaration,
    }
    result["lookup"] = {"expected": expected, "actual": summary,
                        "exit_code": lookup_exit, "query_gaps": observed["gaps"]}
    result["missing_original"] = {"expected_gap": "missing_source", "exit_code": missing_exit,
                                  "actual_gaps": absent["gaps"], "summary": absent.get("function_summary")}
    failures = []
    if lookup_exit != 0 or not isinstance(summary, dict) or any(
        summary.get(key) != value for key, value in expected.items()
    ):
        failures.append("expected artifact + SOURCE ID summary with 2/2 receipts and original declaration; "
                        f"actual function_summary={summary!r}")
    if missing_exit != 1 or absent.get("function_summary") or not any(
        gap["code"] == "missing_source" for gap in absent["gaps"]
    ):
        failures.append(f"expected missing_source with alternate build present; actual gaps={absent['gaps']!r}")
    rows = [json.loads(line) for line in (evidence / "payments.spans.jsonl").read_text().splitlines()]
    calls = [row for row in rows if row["name"] == "payments.authorize"]
    assert len(calls) == 2 and {row["trace_id"] for row in calls} == seen
    assert all(row["ended"] and row["attributes"]["outcome"] == "ok" for row in calls)
    artifact_ids = [row["attributes"].get("artifact_id") for row in calls]
    source_hashes = [row["attributes"].get("source_hash") for row in calls]
    result["span_bindings"] = {"artifact_ids": artifact_ids, "source_hashes": source_hashes}
    if artifact_ids != [selected["artifact_id"]] * 2 or source_hashes != [
        selected["source_id"]["source_sha256"]
    ] * 2:
        failures.append(f"expected both live spans bound to the selected artifact and source; "
                        f"actual artifact_ids={artifact_ids!r}, source_hashes={source_hashes!r}")
    if failures:
        result["assertion_failures"] = failures
        step("fail", "exact_source_lookup_assertions_failed")
        raise AssertionError("\n".join(failures))
    step("pass", "exact_source_lookup_verified")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    run = EXPERIMENT / "results" / utc().strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True)
    result = {"test": TEST, "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "status": "fail"}
    print(run, flush=True)
    try:
        test_two_live_receipts_resolve_original_payments_declaration(run, result)
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
