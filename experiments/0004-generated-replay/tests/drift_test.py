"""EXPERIMENT 0004 slice 1 case (f): DRIFT runs only against the frozen LIB and records outcome classes.

The outcomes are recorded, not asserted: the pass and reject rule judges them (README).
Run: python3 -B experiments/0004-generated-replay/tests/drift_test.py
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import ARMS, EXPERIMENT, PAYMENTS_BEAML, REPO  # noqa: E402

DERIVATIVES = ("R", "N", "Q")
ARMS_NAMES = ("gen", "lib")
OBSERVATIONS = ("build", "new_live", "pre_change")
# README "(f) DRIFT": outcome classes.
CLASSES = {"compile_error", "typed_reject", "correct_accept", "false_reject", "wrong_accept", "untyped_crash"}
LIB_MODULES = ("ReplayLib", "OrdersApi.ReplayDescriptor")
ACCEPT = {"correct_accept", "wrong_accept"}
REJECT = {"typed_reject", "false_reject"}
RESULTS_ROOT = EXPERIMENT / "results"
# Review round 2, evidence per row of `run.py drift` (last stdout line {"run": <new dir in results/>, "drift": ...}):
#   row["evidence"] = {"build_output": <file>, "build_exit_code": <int>,
#                      "new_live_report": <live observed.json: {"reply": [code, body], ...}>,
#                      "pre_change_replay_report": <eval report.json: {"result": {"ok"|"error"|"raised": ...}}>}
# All files lie inside the run dir. With a failed build, both report paths may be absent.


def lib_hashes():
    found = {}
    root = ARMS / "lib" / "overlay"
    for path in sorted(root.rglob("*.ex")) if root.is_dir() else []:
        for name in LIB_MODULES:
            if ("defmodule %s do" % name) in path.read_text():
                found[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


class DriftFixtures(unittest.TestCase):
    """Guard, not RED: a derivative changes only BEAML declarations; the flow `place` stays."""

    def test_f_drift_fixtures_change_only_beaml_declarations(self):
        bases = {"orders.beaml": ARMS / "gen/orders.beaml", "payments.beaml": REPO / PAYMENTS_BEAML}
        for derivative in DERIVATIVES:
            for name, base in bases.items():
                old = base.read_text().splitlines()
                new = (EXPERIMENT / "drift" / derivative / name).read_text().splitlines()
                self.assertNotEqual(old, new, (derivative, name))
                changed = [line for line in new if line not in old]
                self.assertTrue(all(line.startswith(("interface ", "effect ", "fn ")) for line in changed),
                                (derivative, name, changed))
                self.assertFalse(any(line.startswith("fn place") for line in changed), (derivative, name))
                flow = [line for line in old if line.startswith("  ")]
                self.assertEqual(flow, [line for line in new if line.startswith("  ")], (derivative, name))


class DriftRun(unittest.TestCase):
    maxDiff = None

    def test_f_lib_is_frozen_before_drift(self):
        freeze = ARMS / "lib" / "freeze.json"
        self.assertTrue(freeze.is_file(), "no LIB freeze record")
        self.assertEqual(lib_hashes(), json.loads(freeze.read_text()).get("sha256"))
        self.assertEqual(set(LIB_MODULES), set(lib_hashes()))

    def test_f_drift_outcomes_recorded_per_arm_and_derivative(self):
        # Review round 2: a class string alone is not evidence. Each row names the files of this run
        # (EVIDENCE_CONTRACT), and the test re-derives the class families from them.
        before = lib_hashes()
        results_before = set(RESULTS_ROOT.iterdir()) if RESULTS_ROOT.is_dir() else set()
        done = subprocess.run([sys.executable, "-B", str(EXPERIMENT / "run.py"), "drift"], cwd=str(REPO),
                              capture_output=True, text=True, timeout=7200)
        self.assertEqual(0, done.returncode, done.stdout.strip()[-400:])
        summary = json.loads(done.stdout.strip().splitlines()[-1])
        run_dir = Path(summary.get("run") or "/nonexistent").resolve()
        self.assertTrue(run_dir.is_dir() and run_dir.parent == RESULTS_ROOT.resolve(), "no run dir: %r" % run_dir)
        self.assertNotIn(run_dir, {path.resolve() for path in results_before}, "run dir is not new")
        drift = summary["drift"]
        problems = []
        for derivative in DERIVATIVES:
            for arm in ARMS_NAMES:
                row = drift.get(derivative, {}).get(arm, {})
                where = "%s %s" % (derivative, arm)
                for observation in OBSERVATIONS:
                    if row.get(observation) not in CLASSES:
                        problems.append("%s %s: %r" % (where, observation, row.get(observation)))
                if not isinstance(row.get("manual_change_sites"), int):
                    problems.append("%s: no manual change site count" % where)
                problems.extend(evidence_problems(where, row, run_dir))
        self.assertEqual([], problems)
        self.assertEqual(before, lib_hashes(), "a DRIFT run changed the frozen LIB")


def evidence_file(where, row, key, run_dir, problems):
    """Return the parsed path of row["evidence"][key] if it is a file inside this run dir, else None."""
    value = (row.get("evidence") or {}).get(key)
    if not isinstance(value, str):
        problems.append("%s: no evidence path %s" % (where, key))
        return None
    path = Path(value).resolve()
    if not path.is_file():
        problems.append("%s: evidence %s is not a file: %s" % (where, key, value))
        return None
    if run_dir not in path.parents:
        problems.append("%s: evidence %s is outside this run dir: %s" % (where, key, value))
        return None
    return path


def evidence_problems(where, row, run_dir):
    """Re-derive the class family of each observation from the evidence files of one row."""
    problems = []
    evidence = row.get("evidence") or {}
    evidence_file(where, row, "build_output", run_dir, problems)
    exit_code = evidence.get("build_exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        problems.append("%s: no build exit code" % where)
        return problems
    if (exit_code != 0) != (row.get("build") == "compile_error"):
        problems.append("%s: build exit %d contradicts build class %r" % (where, exit_code, row.get("build")))
    if exit_code != 0:
        # No release, so no live call and no replay: both observations are the compile-time class.
        for observation in ("new_live", "pre_change"):
            if row.get(observation) != "compile_error":
                problems.append("%s: build failed but %s is %r" % (where, observation, row.get(observation)))
        return problems
    live = evidence_file(where, row, "new_live_report", run_dir, problems)
    if live is not None:
        reply = json.loads(live.read_text()).get("reply")
        code = reply[0] if isinstance(reply, list) and reply else None
        family = ACCEPT if code == 200 else REJECT | {"untyped_crash"}
        if row.get("new_live") not in family:
            problems.append("%s: new_live HTTP %r contradicts class %r" % (where, code, row.get("new_live")))
    replay = evidence_file(where, row, "pre_change_replay_report", run_dir, problems)
    if replay is not None:
        result = json.loads(replay.read_text()).get("result") or {}
        family = (ACCEPT if "ok" in result else REJECT if "error" in result
                  else {"untyped_crash"} if "raised" in result else set())
        if row.get("pre_change") not in family:
            problems.append("%s: pre_change result %r contradicts class %r" % (where, result, row.get("pre_change")))
    return problems

if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
