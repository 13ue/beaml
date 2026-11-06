"""EXPERIMENT 0004 slice 5 (README revision 9.1): the SQUASH by `--remove-dead` and the VERSION MARK it writes.

Cases F20, F21, F21b, F22, F23 (every T23 layout), F24, F25, F26, F27, F28. U2 is a Rust unit test in
0001/src/main.rs. Each case runs with the fixture names (slice5/ sources) and with random names (template in
slice5_syntax_test.py); in the Template class each F23 layout also runs with CRLF line ends at random.
Expected files, diffs and stderr lines come from the README contract (steps 3, 4, 6, 8) and the segments; never
from the compiler. A removal case copies the source into a temporary directory first.
Run: python3 -B experiments/0004-generated-replay/tests/slice5_squash_test.py [-k NAME]
"""
import difflib
import json
import os
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slice5_syntax_test as s5  # noqa: E402

REMOVE_DEAD = "--remove-dead"
ASSUME = "--assume-complete"
REFUSED = "error: removal refused: "
DEAD = "warning: DEAD LINE: "
STEP_TAGS = {"s12": (0, 1), "s23": (1, 2), "s34": (2, 3)}


class Squash(s5.Slice5):
    """Removal plumbing after slice4_retire_test.py, with the VERSION MARK of README revision 9.1."""

    def copy_source(self, kind, data=None):
        relative = "%s-%s/orders.beaml" % (kind.replace("+", "p"), random.randrange(10 ** 8))
        path = self.work / relative
        path.parent.mkdir()
        path.write_bytes(self.source_bytes(kind) if data is None else data)
        return relative, path

    def remove(self, kind, spec, relative=None, extra=()):
        """Run the removal command on a copy of `kind` (or on `relative`). Return a dict of what it did."""
        if relative is None:
            relative, _ = self.copy_source(kind)
        path = self.work / relative
        stored = self.snapshot(list(spec))
        before, stat, listing = path.read_bytes(), os.stat(path), sorted(os.listdir(path.parent))
        code, stdout, stderr = self.run_compiler([relative, "--stored", stored, REMOVE_DEAD] + list(extra), self.work)
        after = os.stat(path)
        return {"relative": relative, "path": path, "stored": stored, "before": before, "after": path.read_bytes(),
                "code": code, "stdout": stdout, "stderr": stderr, "same_inode": after.st_ino == stat.st_ino,
                "same_mtime": after.st_mtime_ns == stat.st_mtime_ns,
                "listing_same": sorted(os.listdir(path.parent)) == listing}

    def events(self):
        log = self.work / ".beaml" / "actions.jsonl"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.is_file() else []

    def assert_removed(self, kind, spec, tags, marks, relative=None, extra=()):
        """README contract: exactly the DEAD LINES go, ` v<n>` after each TYPE name in `marks` (tag -> (name, n),
        in source order), stdout is the difflib diff, stderr has the count and one `wrote VERSION MARK` line per
        mark, the event has `removed` and `marked`."""
        N = self.names
        run = self.remove(kind, spec, relative=relative, extra=extra)
        old_text = run["before"].decode()
        new_text = s5.source_text(N, kind, without=tags, marks=marks)
        rel = run["relative"]
        diff = "".join(difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                            rel, rel, n=0))
        count = "removed %d DEAD LINE%s from %s" % (len(tags), "" if len(tags) == 1 else "S", rel)
        mark_lines = ["wrote VERSION MARK v%d on type %s in %s" % (version, name, rel)
                      for name, version in marks.values()]
        written = [line for line in run["stderr"].splitlines() if line.startswith("wrote VERSION MARK")]
        self.assertEqual(
            {"code": 0, "stdout": diff, "count": True, "error": False, "file": new_text.encode(),
             "renamed": True, "temp_left": False, "marks": mark_lines},
            {"code": run["code"], "stdout": run["stdout"], "count": count in run["stderr"],
             "error": "error:" in run["stderr"], "file": run["after"], "renamed": not run["same_inode"],
             "temp_left": not run["listing_same"], "marks": written},
            self.ctx(kind, "removal contract; stderr:", run["stderr"]))
        events = [e for e in self.events() if e.get("action") == "remove-dead"]
        last = events[-1] if events else {}
        self.assertEqual((1, len(tags), len(marks)), (len(events), last.get("removed"), last.get("marked")),
                         self.ctx("one remove-dead event with removed: <count> and marked: <count>", events))
        log = (self.work / ".beaml" / "actions.jsonl").read_text()
        self.assertEqual([], [p for p in (rel, "migrate", N.T) if p in log], "the event holds no path or TYPE name")
        return run

    def assert_untouched(self, run, tokens):
        self.assertEqual(
            {"code": 1, "stdout": "", "file": run["before"], "same_inode": True, "same_mtime": True,
             "listing_same": True, "missing": [], "mark_line": False},
            {"code": run["code"], "stdout": run["stdout"], "file": run["after"], "same_inode": run["same_inode"],
             "same_mtime": run["same_mtime"], "listing_same": run["listing_same"],
             "missing": [t for t in tokens if t not in run["stderr"]],
             "mark_line": "wrote VERSION MARK" in run["stderr"]},
            self.ctx("the command must write nothing; stderr:", run["stderr"]))

    def assert_clean_build(self, relative, spec):
        stored = self.snapshot(list(spec))
        code, stdout, stderr = self.run_compiler([relative, "--stored", stored], self.work)
        self.assertEqual((0, False, True), (code, "warning:" in stderr, "defmodule BeamlSpike do" in stdout),
                         self.ctx("the result builds without a warning; stderr:", stderr))

    def q4_marks(self):
        return {"type": (self.names.T, 4)}

    def v3(self):
        return [(3, "ktc"), (3, "ktc")]

    def v4(self):
        return [(4, "ktx"), (4, "ktx")]

    # F20: records of v3 remove the first two steps and write v4 on the type line.
    def test_F20_squash_removes_two_steps_and_writes_the_mark(self):
        run = self.assert_removed("Q4", self.v3(), ("s12", "s23"), self.q4_marks())
        if self.fixture_based:
            self.assertEqual(s5.fixture_path("Q4s").read_bytes(), run["after"], "F20: the file equals Q4s")
            rel = run["relative"]
            self.assertEqual(
                "--- %s\n+++ %s\n@@ -3 +3 @@\n-type Payment { order_id: String state: String reference: String }\n"
                "+type Payment v4 { order_id: String state: String reference: String }\n@@ -5 +4,0 @@\n"
                "-migrate Payment v1 -> v2 { rename status -> state }\n@@ -7,3 +5,0 @@\n-migrate Payment v2 -> v3 {\n"
                "-  add channel: String = \"web\"\n-}\n" % (rel, rel), run["stdout"], "F20: the README example diff")

    # F21, F22: records of v4 only; the last step is dead too (DL-070).
    def test_F21_records_of_the_newest_version_remove_every_step(self):
        run = self.assert_removed("Q4", self.v4(), ("s12", "s23", "s34"), self.q4_marks())
        if self.fixture_based:
            self.assertEqual(s5.fixture_path("Q4z").read_bytes(), run["after"], "F21: the file equals Q4z")
        self.assert_clean_build(run["relative"], self.v4())

    def test_F21b_one_step_chain_with_records_of_v2(self):
        N = self.names
        stored = self.snapshot([(2, "kt")])
        source = self.source("C2")
        code, stdout, stderr = self.run_compiler([source, "--stored", stored])
        heads = [line for line in stderr.splitlines() if line.startswith("warning:")]
        self.assertEqual((0, [DEAD + "migrate %s v1 -> v2" % N.T]), (code, heads),
                         self.ctx("F21b build: one W2 warning; stderr:", stderr))
        run = self.assert_removed("C2", [(2, "kt")], ("s12",), {"type": (N.T, 2)})
        self.assertNotIn("migrate", run["after"].decode(), self.ctx("F21b: no migrate line is left"))

    def test_F22_crlf_source_keeps_crlf(self):
        run = self.assert_removed("Q4-crlf", self.v4(), ("s12", "s23", "s34"), self.q4_marks())
        data = run["after"]
        self.assertEqual((data.count(b"\n"), True), (data.count(b"\r\n"), b"type %s v4 {" % self.names.T.encode() in data),
                         self.ctx("F22: CRLF only, and the marked type line"))
        self.assertIn("\r\n", run["stdout"], self.ctx("F22: the diff lines keep CRLF"))

    # F23: every type line layout.
    def test_F23_every_type_line_layout_gets_the_mark_after_the_name(self):
        for layout in s5.T23_LAYOUTS:
            kind = layout
            if not self.fixture_based and layout != "Q4-crlf" and random.random() < .5:
                kind = layout + "+crlf"
            with self.subTest(layout=kind):
                self.assert_removed(kind, self.v4(), ("s12", "s23", "s34"), self.q4_marks())

    # F24, F25: a marked TYPE keeps its line; a second removal changes nothing.
    def test_F24_marked_type_keeps_its_line(self):
        N = self.names
        run = self.assert_removed("Q4s", [(N.V, "ktx")], ("s34",), {})
        self.assertEqual(s5.source_text(N, "Q4z").encode(), run["after"], self.ctx("F24: the file equals Q4z"))

    def test_F25_second_removal_changes_nothing(self):
        first = self.assert_removed("Q4", self.v4(), ("s12", "s23", "s34"), self.q4_marks())
        run = self.remove("Q4z", self.v4(), relative=first["relative"])
        self.assertEqual(
            {"code": 0, "stdout": "", "no_dead": True, "file": first["after"], "same_inode": True, "same_mtime": True,
             "mark_line": False},
            {"code": run["code"], "stdout": run["stdout"],
             "no_dead": "no DEAD LINE in %s" % first["relative"] in run["stderr"], "file": run["after"],
             "same_inode": run["same_inode"], "same_mtime": run["same_mtime"],
             "mark_line": "wrote VERSION MARK" in run["stderr"]},
            self.ctx("F25 idempotence; stderr:", run["stderr"]))

    # F26: two TYPES lose steps in one run; the unused one needs --assume-complete (step 2a).
    def test_F26_two_types_are_marked_in_source_order(self):
        N = self.names
        marks = {"type": (N.T, 4), "type-note": (N.note, 2)}
        self.assert_removed("Q4+note", self.v4(), ("s12", "s23", "s34", "n12"), marks, extra=(ASSUME,))

    def test_F26_without_the_flag_the_note_step_is_refused_and_nothing_is_written(self):
        N = self.names
        run = self.remove("Q4+note", self.v4())
        self.assert_untouched(run, [REFUSED + "migrate %s v1 -> v2" % N.note, "TYPE %s" % N.note, ASSUME])
        refused = [line for line in run["stderr"].splitlines() if line.startswith(REFUSED)]
        self.assertEqual([REFUSED + "migrate %s v1 -> v2" % N.note], refused,
                         self.ctx("F26: only the note step is refused; stderr:", run["stderr"]))

    # F27: an empty snapshot refuses all three steps and writes no mark.
    def test_F27_empty_snapshot_refuses_every_step_and_writes_no_mark(self):
        N = self.names
        run = self.remove("Q4", [])
        forms = ["migrate %s v%d -> v%d" % (N.T, a, b) for a, b in ((1, 2), (2, 3), (3, 4))]
        self.assert_untouched(run, [REFUSED + f for f in forms] + [ASSUME])
        refused = [line[len(REFUSED):] for line in run["stderr"].splitlines() if line.startswith(REFUSED)]
        self.assertEqual(forms, refused, self.ctx("F27: three refusals in source order"))

    # F28: a removed step that a record needs blocks the build again and is named.
    def test_F28_record_older_than_the_squash_names_every_missing_step(self):
        N = self.names
        V = N.V
        self.assert_rejected("Q4s", [(V - 1, "ktc"), (V - 3, "ko")], [
            N.T, "starts at v%d" % (V - 1), "TYPE VERSION v%d" % (V - 3), "version control",
            "migrate %s v%d -> v%d" % (N.T, V - 3, V - 2), "migrate %s v%d -> v%d" % (N.T, V - 2, V - 1), s5.PATH],
            label="F28 Q4s")

    def test_F28_record_older_than_a_mark_without_chain_names_the_step(self):
        N = self.names
        V = N.V
        self.assert_rejected("Q4z", [(V - 1, "ktc")], [
            N.T, "starts at v%d" % V, "TYPE VERSION v%d" % (V - 1), "version control",
            "migrate %s v%d -> v%d" % (N.T, V - 1, V), s5.PATH], label="F28 Q4z")


class Fixture(Squash, unittest.TestCase):
    names, fixture_based = s5.FIXTURE_NAMES, True


class Template(Squash, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.names = s5.random_names()


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
