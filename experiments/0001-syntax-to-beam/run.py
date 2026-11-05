#!/usr/bin/env python3
"""Run experiment 0001 and retain one separate evidence directory per run."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

EXPERIMENT = Path(__file__).resolve().parent
ROOT = EXPERIMENT.parent.parent
ACTIONS = ROOT / ".beaml" / "actions.jsonl"


def event(action, target, result):
    try:
        ACTIONS.parent.mkdir(exist_ok=True)
        with ACTIONS.open("a") as stream:
            stream.write(json.dumps({"ts": time.time(), "source": "cli", "action": action,
                                     "target": target, "result": result}) + "\n")
    except OSError:
        pass


def main():
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = EXPERIMENT / "results" / run_id
    output.mkdir(parents=True)
    record = {"experiment": "0001", "run": run_id, "status": "running", "steps": [], "hashes": {}}
    event("use-case-start", "experiment-0001", "running")

    def step(name, command):
        event("use-case-step", name, "start")
        try:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as error:
            event("use-case-step", name, type(error).__name__)
            record["steps"].append({"name": name, "status": "error", "reason": type(error).__name__})
            raise RuntimeError(f"{name}: {type(error).__name__}") from error
        (output / f"{name}.stdout").write_bytes(completed.stdout)
        (output / f"{name}.stderr").write_bytes(completed.stderr)
        record["steps"].append({"name": name, "command": command, "exit_code": completed.returncode})
        event("use-case-step", name, "pass" if completed.returncode == 0 else "fail")
        if completed.returncode:
            raise RuntimeError(f"{name}: exit {completed.returncode}. See retained stderr.")
        return completed.stdout

    try:
        record["toolchain"] = {
            "rustc": step("rust-version", ["rustc", "--version"]).decode().strip(),
            "cargo": step("cargo-version", ["cargo", "--version"]).decode().strip(),
            "elixir_otp": step("elixir-version", ["elixir", "--version"]).decode().strip(),
        }
        manifest = "experiments/0001-syntax-to-beam/Cargo.toml"
        step("compiler-format", ["cargo", "fmt", "--manifest-path", manifest, "--", "--check"])
        step("compiler-lint", ["cargo", "clippy", "--offline", "--manifest-path", manifest,
                               "--all-targets", "--", "-D", "warnings"])
        step("compiler-tests", ["cargo", "test", "--offline", "--manifest-path", manifest])
        generated = step("generate", ["cargo", "run", "--offline", "--quiet", "--manifest-path", manifest,
                                      "--", "experiments/0001-syntax-to-beam/example.beaml"])
        (output / "generated.ex").write_bytes(generated)
        step("beam-compile", ["elixirc", "--warnings-as-errors", "-o", str(output), str(output / "generated.ex")])
        step("runtime-tests", ["elixir", "-pa", str(output),
                               "experiments/0001-syntax-to-beam/tests/runtime_test.exs"])
        record["status"] = "pass"
    except RuntimeError as error:
        record["status"] = "fail"
        record["error"] = str(error)
    finally:
        inputs = [EXPERIMENT / name for name in ["Cargo.toml", "Cargo.lock", "src/main.rs", "example.beaml", "run.py", "tests/runtime_test.exs", "tests/cli.rs"]]
        for path in inputs + [output / "generated.ex", output / "Elixir.BeamlSpike.beam"]:
            if path.exists():
                record["hashes"][str(path.relative_to(EXPERIMENT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        (output / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        event("use-case-end", "experiment-0001", record["status"])
    print(f"EXPERIMENT 0001: {record['status']} ({output.relative_to(ROOT)}/result.json)")
    return 0 if record["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
