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
        before = lib_hashes()
        done = subprocess.run([sys.executable, "-B", str(EXPERIMENT / "run.py"), "drift"], cwd=str(REPO),
                              capture_output=True, text=True, timeout=7200)
        self.assertEqual(0, done.returncode, done.stdout.strip()[-400:])
        drift = json.loads(done.stdout.strip().splitlines()[-1])["drift"]
        problems = []
        for derivative in DERIVATIVES:
            for arm in ARMS_NAMES:
                row = drift.get(derivative, {}).get(arm, {})
                for observation in OBSERVATIONS:
                    if row.get(observation) not in CLASSES:
                        problems.append("%s %s %s: %r" % (derivative, arm, observation, row.get(observation)))
                if not isinstance(row.get("manual_change_sites"), int):
                    problems.append("%s %s: no manual change site count" % (derivative, arm))
        self.assertEqual([], problems)
        self.assertEqual(before, lib_hashes(), "a DRIFT run changed the frozen LIB")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
