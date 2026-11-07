"""EXPERIMENT 0004 slice 6b step 10: `beaml-spike fmt SOURCE.beaml` (DL-013, DL-081, DL-083, DL-104).

Plan step 10, D6B-41 to D6B-46. Fixtures: slice6/fmt/<name>.beaml and the expected <name>.formatted.beaml, written
by hand from DL-083 and DL-104 (never from the new compiler). The guard test checks with the compiler under test
that each expected file compiles like its source except the `beaml-declaration-v1` byte offsets.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py [-k NAME]
"""
import difflib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import stored_types_test as st  # noqa: E402

FMT = EXPERIMENT / "slice6" / "fmt"
EMPTY_STORED = EXPERIMENT / "stored" / "empty.jsonl"
OFFSETS = re.compile(r"(# beaml-declaration-v1 \S+) \d+ \d+")
NAMES = ("clauses", "marks")
# The number of lines that fmt changes in each fixture (D6B-46 event count).
CHANGED = {"clauses": 7, "marks": 2}


def source(name):
    return (FMT / (name + ".beaml")).read_bytes()


def expected(name):
    return (FMT / (name + ".formatted.beaml")).read_bytes()


def line(data, number):
    """Line `number` (1-based) of `data` without its line end."""
    return data.split(b"\n")[number - 1].rstrip(b"\r")


def crlf(data):
    return data.replace(b"\n", b"\r\n")


class Slice6Fmt(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6fmt-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def place(self, name, data, directory="src"):
        """Write `data` to <work>/<directory>/<name>.beaml (the stem stays a lowercase identifier)."""
        path = self.work / directory / (name + ".beaml")
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        return path

    def check_log(self):
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        text = log.read_text() if log.is_file() else ""
        for secret in (str(self.work), "fn ", "//", "PaymentState", "type "):
            self.assertNotIn(secret, text, "action events must not record source text or paths")
        return [json.loads(row) for row in text.splitlines()]

    def fmt(self, path):
        before, inode, listing = path.read_bytes(), os.stat(path).st_ino, sorted(os.listdir(path.parent))
        result = subprocess.run([st.compiler(), "fmt", str(path)], cwd=self.work / "cwd", capture_output=True,
                                text=True)
        self.check_log()
        return {"code": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "before": before,
                "after": path.read_bytes(), "same_inode": os.stat(path).st_ino == inode,
                "listing_same": sorted(os.listdir(path.parent)) == listing}

    def compile(self, path):
        result = subprocess.run([st.compiler(), str(path), "--stored", str(EMPTY_STORED)], cwd=self.work / "cwd",
                                capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def fmt_events(self):
        return [e for e in self.check_log() if e.get("action") == "fmt"]

    def formatted(self, name):
        """The file after `fmt` of the fixture `name`; `fmt` must succeed (a no-op that exits 1 is no pass)."""
        run = self.fmt(self.place(name, source(name)))
        self.assertEqual(0, run["code"], "fmt must succeed; stderr: " + run["stderr"])
        return run["after"]

    def assert_formatted(self, name, data=None, want=None):
        """D6B-41: exit 0, the file is the expected text (written atomically), stdout is the difflib diff."""
        data = source(name) if data is None else data
        want = expected(name) if want is None else want
        path = self.place(name, data)
        run = self.fmt(path)
        label = str(path)
        diff = "".join(difflib.unified_diff(data.decode().splitlines(keepends=True),
                                            want.decode().splitlines(keepends=True), label, label, n=0))
        self.assertEqual(
            {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
            {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
             "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
            "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        if data == source(name):
            self.assertEqual(diff, run["stdout"], "stdout is the unified diff (n=0) with the path as label")
        return run

    # Contract (D6B-41).

    def test_fmt_rewrites_the_file_and_prints_the_diff(self):
        for name in NAMES:
            with self.subTest(name):
                self.assert_formatted(name)

    def test_fmt_needs_no_stored_snapshot(self):
        # Repair F7: the source check of fmt is the source check without --stored, so a source with an EFFECT
        # formats. clauses.beaml has an EFFECT and needs --stored to compile.
        run = self.fmt(self.place("clauses", source("clauses")))
        self.assertEqual((0, expected("clauses")), (run["code"], run["after"]), run["stderr"])

    # Clause alignment (DL-083, D6B-44).

    def test_clause_group_aligns_argument_columns_arrow_and_equals(self):
        after = self.formatted("clauses")
        self.assertEqual([
            b"fn PaymentState status: String, decline_reason: String -> PaymentState",
            b'fn PaymentState "ok",       _      -> PaymentState = Authorized',
            b'fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined',
            b"fn PaymentState other,      _      -> PaymentState = Unknown(other)",
        ], [line(after, n) for n in range(9, 13)], "group A; the signature line (no `=`) is not in the group")

    def test_extra_spaces_before_equals_become_one_column(self):
        after = self.formatted("clauses")
        self.assertEqual([b'fn tag "a = b",       x -> String = x', b'fn tag "long -> key", x -> String = "k"'],
                         [line(after, 16), line(after, 17)], "`->` and `=` inside strings are not columns")

    def test_blank_line_breaks_a_group(self):
        after = self.formatted("clauses")
        self.assertEqual(b'fn tag "m", x -> String = x', line(after, 19),
                         "the clause after the blank line does not align with lines 16 and 17")

    def test_comment_line_breaks_a_group(self):
        after = self.formatted("clauses")
        self.assertEqual([b'fn tag "m", x -> String = x', line(source("clauses"), 20),
                          b"fn tag other, y -> String = other"],
                         [line(after, n) for n in (19, 20, 21)])

    def test_multi_line_clause_breaks_a_group(self):
        after = self.formatted("clauses")
        self.assertEqual([line(source("clauses"), n) for n in (24, 25, 26)]
                         + [b"fn label Unknown(text) -> String = text",
                            b'fn label Declined(r)   -> String = "declined"'],
                         [line(after, n) for n in range(24, 29)])

    def test_lone_clause_is_a_group_of_one(self):
        after = self.formatted("clauses")
        self.assertEqual(b"fn lone x: String -> String = x", line(after, 31))

    def test_effect_line_aligns_arrow_and_equals(self):
        # DL-013 for one EFFECT line (slice 1 supports one EFFECT; notes.md F3).
        after = self.formatted("clauses")
        self.assertEqual(b'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")',
                         line(after, 38))

    def test_comments_stay_byte_for_byte(self):
        before = source("clauses")
        after = self.formatted("clauses")
        comments = [(n, row) for n, row in enumerate(before.split(b"\n"), 1) if b"//" in row]
        self.assertTrue(len(comments) >= 7 and any(row.endswith(b"   ") for _, row in comments), "fixture check")
        for n, row in comments:
            tail = row[row.index(b"//"):]
            self.assertTrue(line(after, n).endswith(tail), "line %d keeps its comment bytes" % n)
        self.assertEqual([line(before, 26), line(before, 40), line(before, 41), line(before, 42)],
                         [line(after, 26), line(after, 40), line(after, 41), line(after, 42)],
                         "a string with `//` and the multi-line clause bodies stay")

    # VERSION MARK form (b) by DL-104 (D6B-43).

    def test_mark_removed_when_a_chain_from_v1_implies_it(self):
        after = self.formatted("marks")
        self.assertEqual(b"type Chained { id: String state: String channel: String }", line(after, 3))

    def test_squash_mark_without_chain_is_kept(self):
        after = self.formatted("marks")
        self.assertEqual(b"type Squashed v3 { id: String }", line(after, 8))

    def test_v1_mark_without_chain_is_kept(self):
        # O3: `type Payment v1` selects the versioned decode of the EFFECT output.
        after = self.formatted("marks")
        self.assertEqual(b"type Payment v1 { order_id: String state: String }", line(after, 24))

    def test_mark_written_when_the_chain_starts_above_v1(self):
        after = self.formatted("marks")
        self.assertEqual(b"type Shortened v5 { id: String note: String }", line(after, 11))

    def test_mark_kept_beside_a_chain_above_v1_and_chain_from_v1_unchanged(self):
        after = self.formatted("marks")
        self.assertEqual([b"type Kept v5 { id: String note: String }", b"type Plain { id: String state: String }"],
                         [line(after, 15), line(after, 19)])

    # Invariants (D6B-45).

    def test_fmt_is_idempotent(self):
        for name in NAMES:
            with self.subTest(name):
                path = self.place(name, source(name))
                first = self.fmt(path)
                second = self.fmt(path)
                self.assertEqual((0, 0, "", first["after"], True, True),
                                 (first["code"], second["code"], second["stdout"], second["after"],
                                  second["same_inode"], second["listing_same"]),
                                 "fmt(fmt(s)) == fmt(s); an unchanged file is not rewritten")
                again = self.fmt(self.place(name, expected(name), "expected"))
                self.assertEqual((0, "", expected(name), True), (again["code"], again["stdout"], again["after"],
                                                                 again["same_inode"]))

    def test_compiled_output_equal_except_declaration_offsets(self):
        for name in NAMES:
            with self.subTest(name):
                before = self.place(name, source(name), "before")
                code, want, stderr = self.compile(before)
                self.assertEqual(0, code, stderr)
                path = self.place(name, source(name))
                run = self.fmt(path)
                self.assertEqual(0, run["code"], run["stderr"])
                code, got, stderr = self.compile(path)
                self.assertEqual((0, OFFSETS.sub(r"\1 N N", want)), (code, OFFSETS.sub(r"\1 N N", got)), stderr)

    def test_guard_expected_fixtures_compile_like_their_sources(self):
        # Fixture self-check (passes on the baseline): a hand-written expected file must not change the build.
        for name in NAMES:
            with self.subTest(name):
                a = self.compile(self.place(name, source(name), "before"))
                b = self.compile(self.place(name, expected(name), "expected"))
                self.assertEqual((0, 0), (a[0], b[0]), a[2] + b[2])
                self.assertEqual(OFFSETS.sub(r"\1 N N", a[1]), OFFSETS.sub(r"\1 N N", b[1]))

    # Invalid source (D6B-41).

    def test_invalid_source_writes_nothing(self):
        cases = {
            "syntax": source("clauses").replace(b"fn lone x: String   ->  String  = x", b"fn lone x: String ->"),
            "m1": source("marks").replace(b"type Chained v3 {", b"type Chained v4 {"),
        }
        for case, data in cases.items():
            with self.subTest(case):
                self.assertNotEqual(data, source("clauses"))
                checked = self.place("clauses", data, "checked")
                code, _, error = self.compile(checked)
                self.assertEqual(1, code, "fixture check: the source is invalid")
                path = self.place("clauses", data)
                run = self.fmt(path)
                self.assertEqual(
                    {"code": 1, "stdout": "", "file": data, "same_inode": True, "listing_same": True,
                     "reason": True},
                    {"code": run["code"], "stdout": run["stdout"], "file": run["after"],
                     "same_inode": run["same_inode"], "listing_same": run["listing_same"],
                     "reason": error.strip().splitlines()[0] in run["stderr"]},
                    "fmt gives the source error; stderr: %s" % run["stderr"])

    # Line ends (notes.md F9).

    def test_crlf_line_ends_stay(self):
        for name in NAMES:
            with self.subTest(name):
                code, _, stderr = self.compile(self.place(name, crlf(source(name)), "before"))
                self.assertEqual(0, code, "fixture check: the CRLF source builds; " + stderr)
                self.assert_formatted(name, crlf(source(name)), crlf(expected(name)))

    # Action event (D6B-46).

    def test_action_event_counts_changed_lines(self):
        path = self.place("clauses", source("clauses"))
        self.fmt(path)
        self.fmt(path)
        self.fmt(self.place("clauses", b"fn ->\n", "bad"))
        events = [(e.get("source"), e.get("result"), e.get("changed")) for e in self.fmt_events()]
        self.assertEqual([("cli", "ok", CHANGED["clauses"]), ("cli", "ok", 0), ("cli", "error", 0)], events)

    def test_action_event_counts_changed_lines_of_marks(self):
        self.fmt(self.place("marks", source("marks")))
        self.assertEqual([CHANGED["marks"]], [e.get("changed") for e in self.fmt_events()])


if __name__ == "__main__":
    unittest.main()
