"""Repeatable command for EXPERIMENT 0003. Runs the gate tests serially and keeps one result dir per run."""
import datetime
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

EXPERIMENT = Path(__file__).resolve().parent
REPO = EXPERIMENT.parents[1]
TESTS = "experiments/0003-source-linked-replay/tests/"
TARGET = "experiment-0003"
LOOKUP, REPAIR = "trace-lookup", "trace-lookup-repair"
TOKEN = "{result_dir:trace-lookup}"
REFERENCE = "compiler-reference"
ONE_TEST = re.compile(r"^test result: ok\. 1 passed; 0 failed; 0 ignored;", re.M)
DEFAULT_STEPS = [
    ("compiler-reference", ["cargo", "test", "--manifest-path", "experiments/0001-syntax-to-beam/Cargo.toml",
                            "--test", "cli", "payments_cli_emits_checked_authorize_reference",
                            "--", "--exact", "--nocapture"]),
    ("trace-lookup", ["python3", "-B", TESTS + "trace_lookup_test.py"]),
    ("trace-lookup-repair", ["python3", "-B", TESTS + "trace_lookup_repair_test.py",
                             "--source-run", TOKEN]),
    ("response-capture", ["python3", "-B", TESTS + "response_capture_test.py"]),
    ("replay-run", ["python3", "-B", TESTS + "replay_run_test.py"]),
]


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def event(actions, action, target, result):
    try:
        actions.parent.mkdir(parents=True, exist_ok=True)
        with actions.open("a") as out:
            out.write(json.dumps({"ts": utc().isoformat(), "source": "cli", "action": action,
                                  "target": target, "result": result}) + "\n")
    except Exception:
        pass


def load_config():
    steps, results, actions = DEFAULT_STEPS, EXPERIMENT / "results", REPO / ".beaml" / "actions.jsonl"
    name = os.environ.get("BEAML_0003_RUN_CONFIG")
    if name:
        config = json.loads(Path(name).read_text())
        steps = list(config["steps"].items()) if "steps" in config else steps
        results = Path(config.get("results", results))
        actions = Path(config.get("actions", actions))
    return steps, results, actions


def first_dir(stdout_path):
    try:
        lines = stdout_path.read_text(errors="replace").splitlines()
    except OSError:
        return None
    if lines and lines[0].strip():
        candidate = Path(lines[0].strip())
        if not candidate.is_absolute():
            candidate = REPO / candidate
        if candidate.is_dir():
            return str(candidate.resolve())
    return None


def one_test_passed(stdout_path):
    """cargo exits 0 also when the filter matches no test. Require exactly one passed test."""
    try:
        text = stdout_path.read_text(errors="replace")
    except OSError:
        return False
    return len(ONE_TEST.findall(text)) == 1 and not re.search(r"^test result: (?!ok\. 1 passed;)", text, re.M)


def resolve(name, template, steps_by_name):
    """Give the repair step the result dir of the lookup step of this run.

    Replace the token when the argv has it, else append it. Return None when the lookup gave no passing dir.
    """
    if name != REPAIR:
        return [str(arg) for arg in template]
    source = steps_by_name.get(LOOKUP)
    if not source or source["status"] != "pass" or not source["result_dir"]:
        return None
    argv = [str(arg) for arg in template]
    if TOKEN in argv:
        return [source["result_dir"] if arg == TOKEN else arg for arg in argv]
    return argv + ["--source-run", source["result_dir"]]


def execute():
    steps, results, actions = load_config()
    started = utc()
    run = results / started.strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True)
    result = {"command": [sys.executable] + sys.argv, "started_at": started.isoformat(), "finished_at": None,
              "toolchain": {"python": platform.python_version()}, "steps": [], "status": "fail"}
    by_name = {}
    event(actions, "start", TARGET, "running")
    try:
        for name, template in steps:
            argv = resolve(name, template, by_name)
            step = {"name": name, "command": argv if argv is not None else list(template),
                    "exit_code": None, "result_dir": None, "status": "skipped"}
            result["steps"].append(step)
            by_name[name] = step
            if argv is not None:
                stdout_path, stderr_path = run / (name + ".stdout"), run / (name + ".stderr")
                try:
                    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
                        step["exit_code"] = subprocess.run(argv, cwd=REPO, stdout=out, stderr=err).returncode
                except Exception as error:
                    with stderr_path.open("a") as err:
                        err.write("runner: %s: %s\n" % (type(error).__name__, error))
                step["result_dir"] = first_dir(stdout_path)
                step["status"] = "pass" if step["exit_code"] == 0 else "fail"
                if name == REFERENCE and step["status"] == "pass" and not one_test_passed(stdout_path):
                    step["status"], step["reason"] = "fail", "expected exactly 1 passed test"
                toolchain = Path(step["result_dir"] or "") / "toolchain.json"
                if step["result_dir"] and toolchain.is_file():
                    try:
                        result["toolchain"][name] = json.loads(toolchain.read_text())
                    except ValueError:
                        result["toolchain"][name] = "unreadable"
            save(run / "result.json", result)
            event(actions, "step", name, step["status"])
        if all(s["status"] == "pass" for s in result["steps"]):
            result["status"] = "pass"
    except Exception as error:
        result["error"] = type(error).__name__ + ":" + str(error)
    finally:
        result["finished_at"] = utc().isoformat()
        save(run / "result.json", result)
        event(actions, "finish", TARGET, result["status"])
    return run, result


if __name__ == "__main__":
    if "--list-steps" in sys.argv[1:]:
        print(json.dumps({"steps": [{"name": n, "command": c} for n, c in DEFAULT_STEPS]}))
        raise SystemExit(0)
    run, result = execute()
    print(json.dumps({"run": str(run), "status": result["status"]}))
    raise SystemExit(0 if result["status"] == "pass" else 1)
