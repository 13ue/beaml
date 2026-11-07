"""EXPERIMENT 0004, RED TEAM 01 repair C3 (and C4): the DRIFT status judges the classes; the full run covers slice 6.

Finding: workflow/2026-11-07/red-team-01/rt-correctness.md C3 and C4, probe-c3-crash-run.md section 5. Contract:
workflow/2026-11-07/red-team-01-repairs/spec.md, decisions D6B-189 (`run.drift_status(summary) -> "pass" | "fail"` with
the class pin) and D6B-190 (STEPS runs every slice 6 file and drift_test.py). Input: two retained drift.json files;
no DRIFT run starts here.
Run: python3 -B experiments/0004-generated-replay/tests/redteam_c3_test.py
"""
import copy
import inspect
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT, REPO  # noqa: E402

sys.path.insert(0, str(EXPERIMENT))
import run  # noqa: E402

CRASH = EXPERIMENT / "results" / "20261107T171545190446Z" / "drift.json"  # new_live untyped_crash for R, N, Q
GOOD = EXPERIMENT / "results" / "20261107T180431928222Z" / "drift.json"  # TEST of steps 12 and 13
TESTS = "experiments/0004-generated-replay/tests/"


def load(path):
    return json.loads(path.read_text())


class RedTeamC3Status(unittest.TestCase):
    maxDiff = None

    def status(self, summary):
        rule = getattr(run, "drift_status", None)
        self.assertTrue(callable(rule), "run.py has no drift_status(summary) (D6B-189)")
        return rule(summary)

    def test_c3a_crash_run_fails(self):
        self.assertEqual("pass", load(CRASH)["status"], "guard: the retained status is the false pass")
        self.assertEqual("fail", self.status(load(CRASH)))

    def test_c3b_good_run_passes(self):
        self.assertEqual("pass", self.status(load(GOOD)))

    def test_c3c_each_broken_input_fails(self):
        # Mutations of the good run; each one alone must give fail.
        def repaired_false(s):
            s["repaired_all"] = False

        def freeze_fail(s):
            s["freeze"]["status"] = "fail"

        def wrong_accept(s):
            s["drift"]["Q"]["gen"]["new_live"] = "wrong_accept"

        def compile_error(s):
            s["drift"]["R"]["gen"].update(build="compile_error", new_live="compile_error", pre_change="compile_error")

        def pre_change_crash(s):
            s["drift"]["N"]["gen"]["pre_change"] = "untyped_crash"

        def row_missing(s):
            del s["drift"]["N"]

        for change in (repaired_false, freeze_fail, wrong_accept, compile_error, pre_change_crash, row_missing):
            with self.subTest(change.__name__):
                summary = copy.deepcopy(load(GOOD))
                change(summary)
                self.assertEqual("fail", self.status(summary))

    def test_c3d_drift_step_uses_the_rule(self):
        # A GREEN that adds the function but keeps the freeze-only line in drift() fails here.
        source = inspect.getsource(run.drift)
        self.assertTrue('summary["status"] = drift_status(summary)' in source,
                        "drift() does not set its status with drift_status(summary)")


class RedTeamC4Steps(unittest.TestCase):
    def test_c4_full_run_lists_every_slice6_file_and_drift_test(self):
        done = subprocess.run([sys.executable, "-B", str(EXPERIMENT / "run.py"), "--list-steps"], cwd=str(REPO),
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(0, done.returncode, done.stderr)
        commands = {arg for step in json.loads(done.stdout)["steps"] for arg in step["command"]}
        wanted = sorted(TESTS + p.name for p in (EXPERIMENT / "tests").glob("slice6_*_test.py")) + [TESTS + "drift_test.py"]
        self.assertEqual([], [w for w in wanted if w not in commands], "files that no full-run step runs")


if __name__ == "__main__":
    unittest.main()
