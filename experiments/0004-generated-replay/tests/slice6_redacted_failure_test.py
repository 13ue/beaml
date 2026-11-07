"""EXPERIMENT 0004 slice 6b step 6c: no non-redacted copy of a redacted value (DL-105, DL-112, DL-113, D6B-67).

Plan: workflow/2026-11-07/slice6b-redacted/plan.md, "Failure TYPE rule (6c)" and "6c". Ledger: workflow/2026-11-07/
slice6b-redacted-failure/ (spec.md, notes.md). Fixtures: slice6/redacted-failure/, one case per file.
RED cases (f*, d*): a direct copy of a redacted value into a place that is not redacted is a compile error with the
exact text of D6B-67, D6B-175 to D6B-177. Guards (g*): allowed copies build. Limits (l*): derived values that the
reach rule D6B-174 does not follow; they build, and the test name says that this is a limit, not a wanted outcome.
Compile only: no runtime harness, so no fixture depends on a failure struct as a host value (red-team-01 B4).
Expected values come from the plan, the decision log and notes.md, never from the new compiler.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_redacted_failure_test.py [-k NAME]
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT, REPO  # noqa: E402

COMPILER_PATH = "experiments/0001-syntax-to-beam"
_BINARY = []
FIX = EXPERIMENT / "slice6" / "redacted-failure"
EMPTY = EXPERIMENT / "stored" / "empty.jsonl"
AT_BYTE = re.compile(r"  at byte \d+")  # D6B-153: a later position line is allowed


def compiler():
    """The 0001 compiler binary, built once. BEAML_SPIKE points at a scratch build instead."""
    if not _BINARY:
        if os.environ.get("BEAML_SPIKE"):
            _BINARY.append(os.environ["BEAML_SPIKE"])
        else:
            manifest = REPO / COMPILER_PATH / "Cargo.toml"
            subprocess.run(["cargo", "build", "--offline", "--quiet", "--manifest-path", str(manifest)], check=True)
            _BINARY.append(str(REPO / COMPILER_PATH / "target/debug/beaml-spike"))
        print("compiler:", _BINARY[0], file=sys.stderr)
    return _BINARY[0]


def record_text(fn, field, owner, target, place, mark_field, mark_type):
    """D6B-67 (a) for a failure TYPE (help DL-105), D6B-175 for every other record TYPE (help DL-112)."""
    dl = "DL-105" if place.startswith("failure ") else "DL-112"
    return ["error: fn %s copies the redacted field %s of %s into %s of the %s, which is not redacted"
            % (fn, field, owner, target, place),
            "  help: mark %s as redacted in %s, or do not copy the value (%s)" % (mark_field, mark_type, dl)]


def hold_text(fn, field, owner, kind, type_name, dl):
    """D6B-67 (b), (c) and D6B-175: a variant payload or a whole clause body (D6B-176 help line)."""
    return ["error: fn %s copies the redacted field %s of %s into the %s %s, which cannot hold a redacted value"
            % (fn, field, owner, kind, type_name), "  help: do not copy the value (%s)" % dl]


# Each RED fixture and its exact first two stderr lines.
RED = {
    # F1, the first RED (plan 6c).
    "f1_failure_record": record_text("check", "card_holder", "Order", "reason", "failure TYPE Bad", "reason", "Bad"),
    "f3_failure_enum": hold_text("check", "card_holder", "Order", "failure TYPE", "Why", "DL-105"),
    # D6B-177: a nested target is the dotted path from the failure TYPE; the help names the declaring TYPE.
    "f4_failure_nested": record_text("check", "card_holder", "Order", "inner.text", "failure TYPE Bad", "text",
                                     "Inner"),
    "f7_failure_body": hold_text("check", "card_holder", "Order", "failure TYPE", "String", "DL-105"),
    # DL-112: the same rule for every record literal and variant payload.
    "d1_record_field": record_text("receipt", "card_holder", "Order", "holder", "TYPE Receipt", "holder", "Receipt"),
    # D6B-174: one fn that returns its parameter unchanged keeps the value direct (pipe step and call).
    "d2_pipe_identity": record_text("receipt", "card_holder", "Order", "holder", "TYPE Receipt", "holder", "Receipt"),
    "d3_call_identity": record_text("receipt", "card_holder", "Order", "holder", "TYPE Receipt", "holder", "Receipt"),
    "d4_enum_payload": hold_text("state", "card_holder", "Order", "TYPE", "State", "DL-112"),
    "d5_variant_pipe": hold_text("box", "card_holder", "Order", "TYPE", "State", "DL-112"),
    "d6_renamed_binding": record_text("receipt", "card_holder", "Order", "holder", "TYPE Receipt", "holder", "Receipt"),
    # D6B-177: F of T names the TYPE that declares the redacted field.
    "d7_nested_pattern": record_text("receipt", "holder", "Card", "holder", "TYPE Receipt", "holder", "Receipt"),
}
GUARDS = ["g1_redacted_target", "g2_failure_redacted_target", "g3_same_name_other_value", "g4_whole_record"]
LIMITS = ["l1_concat", "l2_constructor_other_type", "l3_fn_builds_record", "l4_two_levels", "l5_success_body"]


class RedactedFailureTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6rf-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)

    def build(self, name, data=None):
        """Compile slice6/redacted-failure/<name>.beaml (or `data` under that name) in a fresh cwd."""
        path = FIX / (name + ".beaml")
        if data is not None:
            path = self.work / (name + ".beaml")
            path.write_text(data)
        cwd = self.work / ("cwd-" + name)
        cwd.mkdir(exist_ok=True)
        result = subprocess.run([compiler(), str(path), "--stored", str(EMPTY)], cwd=cwd, capture_output=True,
                                text=True)
        return result.returncode, result.stdout, result.stderr

    def assert_reject(self, name, want):
        code, stdout, stderr = self.build(name)
        lines = stderr.splitlines()
        self.assertEqual((1, want), (code, lines[:2]), "%s: exit and first two stderr lines" % name)
        self.assertTrue(all(AT_BYTE.fullmatch(line) for line in lines[2:]), "%s: extra stderr %r" % (name, lines[2:]))
        self.assertEqual("", stdout, name + ": a reject writes no module")

    def assert_builds(self, name, data=None):
        code, stdout, stderr = self.build(name, data)
        self.assertEqual((0, ""), (code, stderr), name + ": must build")
        self.assertIn("defmodule", stdout, name + ": the module is written")

    def test_F1_failure_record_field_copy_is_rejected(self):
        """The first RED (plan 6c F1, D6B-67 a)."""
        self.assert_reject("f1_failure_record", RED["f1_failure_record"])

    def test_failure_type_copies_are_rejected(self):
        """Plan F3, F4 and D6B-67 (c)."""
        for name in ["f3_failure_enum", "f4_failure_nested", "f7_failure_body"]:
            with self.subTest(name):
                self.assert_reject(name, RED[name])

    def test_DL112_copies_everywhere_are_rejected(self):
        """DL-112: every record literal and variant payload; D6B-174 reach of one identity fn."""
        for name in sorted(n for n in RED if n.startswith("d")):
            with self.subTest(name):
                self.assert_reject(name, RED[name])

    def test_allowed_copies_build(self):
        """G1, G2 (plan F2): a redacted target; G3: DL-113 same name, other value; G4 (plan F6): whole record."""
        for name in GUARDS:
            with self.subTest(name):
                self.assert_builds(name)

    def test_limit_derived_values_are_not_checked(self):
        """Records a limit, not a wanted outcome (plan F5, DL-112, D6B-174): derived values build."""
        for name in LIMITS:
            with self.subTest(name):
                self.assert_builds(name)

    def test_setup_red_sources_build_without_redacted(self):
        """Setup control: each RED source builds when no field is redacted, so the RED reason is the rule only."""
        for name in RED:
            with self.subTest(name):
                data = (FIX / (name + ".beaml")).read_text()
                self.assertIn(": redacted ", data)
                self.assert_builds(name, data.replace(": redacted ", ": "))

    def test_fmt_keeps_every_fixture(self):
        """fmt does not check the rule: each fixture is already formatted and stays byte-equal (exit 0)."""
        for path in sorted(FIX.glob("*.beaml")):
            with self.subTest(path.name):
                copy = self.work / path.name
                shutil.copyfile(path, copy)
                result = subprocess.run([compiler(), "fmt", str(copy)], cwd=self.work, capture_output=True,
                                        text=True)
                self.assertEqual((0, path.read_bytes()), (result.returncode, copy.read_bytes()), result.stderr)

    def test_fixture_set_is_complete(self):
        """Every fixture file belongs to exactly one group."""
        self.assertEqual(sorted(list(RED) + GUARDS + LIMITS), sorted(p.stem for p in FIX.glob("*.beaml")))


if __name__ == "__main__":
    unittest.main()
