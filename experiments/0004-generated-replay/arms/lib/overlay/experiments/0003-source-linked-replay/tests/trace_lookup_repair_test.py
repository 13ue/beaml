"""Exercise receipt order and window coverage with retained live lookup evidence."""
import argparse
import copy
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from trace_lookup_test import EXPERIMENT, HTTP, REPO, digest, event, save, utc

TEST = "test_lookup_requires_receipt_order_and_recorded_window"
BASELINE = EXPERIMENT / "results/20261105T232448420501Z"
QUERY = HTTP / "query.py"


def hashes(directory):
    return {str(path.relative_to(directory)): digest(path)
            for path in sorted(directory.rglob("*")) if path.is_file()}


def test_lookup_requires_receipt_order_and_recorded_window(source_run, run, result):
    event("start", TEST, "running")
    original = source_run / "original"
    revision = source_run / "current-revision"
    before = {"original": hashes(original), "current-revision": hashes(revision)}
    save(run / "input-hashes.json", {
        "retained": before,
        "code": {str(path.relative_to(REPO)): digest(path) for path in (
            QUERY, EXPERIMENT / "tests/trace_lookup_test.py", EXPERIMENT / "tests/trace_lookup_repair_test.py",
        )},
    })
    manifest = json.loads((original / "manifest.json").read_text())
    reference = json.loads((source_run / "result.json").read_text())
    assert reference["status"] == "pass", "The source run must have passed live lookup"
    assert manifest["receipts"] == reference["baseline"]["receipts"]
    expected_summary = reference["lookup"]["actual"]
    first, second = [receipt["trace_id"] for receipt in manifest["receipts"]]
    assert first != second

    swapped = copy.deepcopy(manifest)
    swapped["receipts"][0]["trace_id"] = second
    swapped["receipts"][1]["trace_id"] = first
    missing = {key: value for key, value in manifest.items() if key != "window"}
    outside = {**manifest, "window": {
        "start_utc": "2000-01-01T00:00:00+00:00", "end_utc": "2000-01-01T01:00:00+00:00",
    }}
    cases = (
        ("unchanged", manifest, None),
        ("swapped-receipts", swapped, "receipt_coverage"),
        ("missing-window", missing, "missing_window"),
        ("outside-window", outside, "outside_window"),
    )
    commands = []
    failures = []
    with tempfile.TemporaryDirectory(prefix="beaml-lookup-repair-") as temporary:
        stage = Path(temporary)
        shutil.copytree(revision, stage / "current-revision")
        for name, candidate, expected_gap in cases:
            context = stage / name
            shutil.copytree(original, context)
            if expected_gap:
                save(context / "manifest.json", candidate)
            shutil.copyfile(context / "manifest.json", run / f"{name}.manifest.json")
            args = [sys.executable, "-B", str(QUERY), "--run", str(context), "--order-id", "order-1"]
            completed = subprocess.run(args, cwd=REPO, capture_output=True, timeout=20)
            commands.append({"name": name, "argv": args, "cwd": str(REPO),
                             "exit_code": completed.returncode})
            save(run / "commands.json", commands)
            (run / f"{name}.stdout").write_bytes(completed.stdout)
            (run / f"{name}.stderr").write_bytes(completed.stderr)
            data = json.loads(completed.stdout)
            summary = data.get("function_summary")
            observed = {
                "exit_code": completed.returncode,
                "complete": data["complete"],
                "gaps": data["gaps"],
                "coverage": [summary["matched_calls"], summary["completed_calls"]] if summary else None,
                "first_trace_id": summary["first_trace_id"] if summary else None,
            }
            if expected_gap:
                passed = (completed.returncode == 1 and data["complete"] is False
                          and "function_summary" not in data
                          and expected_gap in [gap["code"] for gap in data["gaps"]])
                expectation = f"exit 1, incomplete, {expected_gap}, and no function summary"
            else:
                passed = (completed.returncode == 0 and data["complete"] is True
                          and not data["gaps"] and summary == expected_summary)
                expectation = "exit 0 and the unchanged original 2/2 summary with the first receipt trace"
            result["cases"][name] = {"expected": expectation, "observed": observed, "passed": passed}
            line = f"{name}: expected {expectation}; actual {observed}"
            print(line, flush=True)
            if not passed:
                failures.append(line)
            event("step", TEST, name + ("_passed" if passed else "_failed"))
    assert before == {"original": hashes(original), "current-revision": hashes(revision)}
    assert not failures, "\n" + "\n".join(failures)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, default=BASELINE)
    source_run = parser.parse_args().source_run.resolve()
    run = EXPERIMENT / "results" / utc().strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir()
    result = {"test": TEST, "command": [sys.executable, "-B", *sys.argv], "cwd": str(REPO),
              "source_run": str(source_run), "status": "fail", "cases": {}}
    save(run / "toolchain.json", {"python": platform.python_version()})
    print(run, flush=True)
    try:
        test_lookup_requires_receipt_order_and_recorded_window(source_run, run, result)
        result["status"] = "pass"
    finally:
        event(result["status"], TEST, "lookup_order_and_window")
        save(run / "result.json", result)
        save(run / "output-hashes.json", hashes(run))
