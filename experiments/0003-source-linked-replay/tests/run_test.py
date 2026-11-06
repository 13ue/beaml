"""Check the EXPERIMENT 0003 runner with stub step commands. Starts no release."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

EXPERIMENT = Path(__file__).resolve().parents[1]
REPO = EXPERIMENT.parents[1]
RUNNER = EXPERIMENT / "run.py"
STEPS = ["compiler-reference", "trace-lookup", "trace-lookup-repair", "response-capture", "replay-run"]
# `run.py --list-steps` prints {"steps": [{"name", "command"}]} with argv relative to the repo root.
# The runner replaces this token with the result dir of the trace-lookup step of the same run.
LOOKUP_DIR_TOKEN = "{result_dir:trace-lookup}"

# Stub step: record argv, create a result dir like the real tests, print it first, exit with the given code.
STUB = r'''
import json, sys, time
from pathlib import Path
name, code, root, make_dir = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3]), sys.argv[4] == "1"
with (root / "calls.jsonl").open("a") as out:
    out.write(json.dumps({"name": name, "argv": sys.argv[5:]}) + "\n")
if make_dir:
    run = root / "step-results" / (name + "-" + str(time.time_ns()))
    run.mkdir(parents=True)
    (run / "toolchain.json").write_text(json.dumps({"python": "stub"}))
    print(run, flush=True)
print("stub output " + name, flush=True)
raise SystemExit(code)
'''


class RunnerTest(unittest.TestCase):
    def execute(self, failing=()):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        tmp = Path(holder.name)
        (tmp / "stub.py").write_text(STUB)
        steps = {}
        for name in STEPS:
            make_dir = "0" if name == "compiler-reference" else "1"
            steps[name] = [sys.executable, "-B", str(tmp / "stub.py"), name,
                           "1" if name in failing else "0", str(tmp), make_dir]
        config = {"steps": steps, "results": str(tmp / "results"), "actions": str(tmp / "actions.jsonl")}
        (tmp / "config.json").write_text(json.dumps(config))
        env = dict(os.environ, BEAML_0003_RUN_CONFIG=str(tmp / "config.json"))
        cp = subprocess.run([sys.executable, "-B", str(RUNNER)], cwd=REPO, env=env,
                            capture_output=True, text=True, timeout=60)
        calls_file = tmp / "calls.jsonl"
        calls = [json.loads(line) for line in calls_file.read_text().splitlines()] if calls_file.exists() else []
        runs = sorted((tmp / "results").iterdir()) if (tmp / "results").is_dir() else []
        result = json.loads((runs[0] / "result.json").read_text()) if len(runs) == 1 and (runs[0] / "result.json").exists() else None
        actions_file = tmp / "actions.jsonl"
        events = [json.loads(line) for line in actions_file.read_text().splitlines()] if actions_file.exists() else []
        return tmp, cp, calls, runs, result, events

    def check_events(self, tmp, events, expected_steps, status):
        self.assertTrue(events, "no action events")
        for item in events:
            self.assertEqual(set(item), {"ts", "source", "action", "target", "result"})
            self.assertEqual(item["source"], "cli")
            for key in ("action", "target", "result"):
                self.assertNotIn("/", str(item[key]), "path in event")
                self.assertNotIn(str(tmp), str(item[key]))
        self.assertEqual(events[0]["action"], "start")
        self.assertEqual([(e["target"], e["result"]) for e in events if e["action"] == "step"], expected_steps)
        self.assertEqual((events[-1]["action"], events[-1]["result"]), ("finish", status))

    def test_all_steps_pass(self):
        tmp, cp, calls, runs, result, events = self.execute()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertEqual([c["name"] for c in calls], STEPS)
        lookup = next(s for s in result["steps"] if s["name"] == "trace-lookup")
        repair = next(c for c in calls if c["name"] == "trace-lookup-repair")
        self.assertEqual(repair["argv"][-2:], ["--source-run", lookup["result_dir"]])
        self.assertEqual(len(runs), 1)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(str(result["command"][-1]).endswith("run.py"), result["command"])
        self.assertLessEqual(result["started_at"], result["finished_at"])
        self.assertIn("python", result["toolchain"])
        self.assertEqual([s["name"] for s in result["steps"]], STEPS)
        for step in result["steps"]:
            self.assertEqual(step["exit_code"], 0)
            self.assertIsInstance(step["command"], list)
            if step["name"] == "compiler-reference":
                self.assertIsNone(step["result_dir"])
            else:
                self.assertTrue(Path(step["result_dir"]).is_dir(), step)
                self.assertIn(step["name"], Path(step["result_dir"]).name)
        self.check_events(tmp, events, [(name, "pass") for name in STEPS], "pass")

    def test_failed_lookup_skips_repair_and_runs_later_steps(self):
        tmp, cp, calls, runs, result, events = self.execute(failing=("trace-lookup",))
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertEqual([c["name"] for c in calls],
                         ["compiler-reference", "trace-lookup", "response-capture", "replay-run"])
        self.assertEqual(len(runs), 1, "failed run not preserved")
        self.assertEqual(result["status"], "fail")
        by_name = {s["name"]: s for s in result["steps"]}
        self.assertEqual(by_name["trace-lookup"]["exit_code"], 1)
        self.assertIsNone(by_name["trace-lookup-repair"]["exit_code"])
        self.assertEqual(by_name["trace-lookup-repair"]["status"], "skipped")
        self.assertEqual(by_name["replay-run"]["exit_code"], 0)
        self.check_events(tmp, events, [("compiler-reference", "pass"), ("trace-lookup", "fail"),
                                        ("trace-lookup-repair", "skipped"), ("response-capture", "pass"),
                                        ("replay-run", "pass")], "fail")

    def test_default_steps_match_gate_commands(self):
        # O1 (red-review.md): the default step list of run.py, without running any step.
        env = {k: v for k, v in os.environ.items() if k != "BEAML_0003_RUN_CONFIG"}
        cp = subprocess.run([sys.executable, "-B", str(RUNNER), "--list-steps"], cwd=REPO, env=env,
                            capture_output=True, text=True, timeout=60)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        listed = json.loads(cp.stdout)
        tests = "experiments/0003-source-linked-replay/tests/"
        manifest = "experiments/0001-syntax-to-beam/Cargo.toml"
        expected = [
            ("compiler-reference", ["cargo", "test", "--manifest-path", manifest, "--test", "cli",
                                    "payments_cli_emits_checked_authorize_reference", "--", "--exact", "--nocapture"]),
            ("trace-lookup", ["python3", "-B", tests + "trace_lookup_test.py"]),
            ("trace-lookup-repair", ["python3", "-B", tests + "trace_lookup_repair_test.py",
                                     "--source-run", LOOKUP_DIR_TOKEN]),
            ("response-capture", ["python3", "-B", tests + "response_capture_test.py"]),
            ("replay-run", ["python3", "-B", tests + "replay_run_test.py"]),
        ]
        self.assertEqual([(s["name"], s["command"]) for s in listed["steps"]], expected)
        for path in (manifest, tests + "trace_lookup_test.py", tests + "trace_lookup_repair_test.py",
                     tests + "response_capture_test.py", tests + "replay_run_test.py"):
            self.assertTrue((REPO / path).is_file(), path)

    def test_failed_independent_step_fails_run(self):
        tmp, cp, calls, runs, result, events = self.execute(failing=("response-capture",))
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertEqual([c["name"] for c in calls], STEPS)
        self.assertEqual(result["status"], "fail")


if __name__ == "__main__":
    unittest.main()
