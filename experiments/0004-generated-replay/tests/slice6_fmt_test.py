"""EXPERIMENT 0004 slice 6b step 10: `beaml-spike fmt SOURCE.beaml` (DL-013, DL-081, DL-083, DL-104, DL-148).

Plan step 10, D6B-41 to D6B-46; fmt layout (DL-148, ledger workflow/2026-11-08/fmt-layout/). Fixtures: slice6/fmt/<name>.beaml and the expected <name>.formatted.beaml, written
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
# header holds the only signature line directly above clauses (DL-114, replaced by DL-148: the line is a table row).
# layout holds the DL-148 cases: TYPE and ENUM bodies, one table per block of clause and EFFECT lines.
NAMES = ("clauses", "marks", "header", "layout")
# The number of source lines that the fmt diff removes or replaces (D6B-46 event count; fmt-layout notes.md F2).
CHANGED = {"clauses": 11, "marks": 5}


def after_line(n):
    """The clauses.formatted.beaml line of clauses.beaml line `n` (DL-148 adds 5 enum and 3 TYPE lines)."""
    assert n not in (6, 34), "lines 6 and 34 become several lines"
    return n if n < 6 else n + 5 if n < 34 else n + 8


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
            b'fn PaymentState "ok",       _      -> PaymentState = Authorized',
            b'fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined',
            b"fn PaymentState other,      _      -> PaymentState = Unknown(other)",
        ], [line(after, n) for n in range(15, 18)], "group A; a comment line separates it from its signature line")

    def test_signature_line_is_a_table_row(self):
        # DL-148 replaces DL-114 (Q6B-9 A): the signature line is a row; the reading lives in header.formatted.beaml.
        self.assertEqual(expected("header"), self.formatted("header"))

    def test_one_line_fns_of_different_names_align(self):
        # DL-148 (replaces R1 of DL-083): a block of single-line clauses is one table across fn names.
        after = self.formatted("clauses")
        self.assertEqual([b"fn one        a: String  -> String = a", b"fn other_name bb: String -> String = bb"],
                         [line(after, 53), line(after, 54)])

    def test_equals_column_aligns_when_only_the_return_text_differs(self):
        # The `=` column has test power: arguments and `->` already align; one space before `=` is not enough.
        after = self.formatted("clauses")
        self.assertEqual([b'fn check "abc" -> String ! PaymentError  = "x"',
                          b"fn check other -> String !  PaymentError = other"],
                         [line(after, 58), line(after, 59)])

    def test_extra_spaces_before_equals_become_one_column(self):
        after = self.formatted("clauses")
        self.assertEqual([b'fn tag "a = b",       x -> String = x', b'fn tag "long -> key", x -> String = "k"'],
                         [line(after, 21), line(after, 22)], "`->` and `=` inside strings are not columns")

    def test_blank_line_breaks_a_group(self):
        after = self.formatted("clauses")
        self.assertEqual(b'fn tag "m", x -> String = x', line(after, 24),
                         "the clause after the blank line does not align with lines 16 and 17")

    def test_comment_line_breaks_a_group(self):
        after = self.formatted("clauses")
        self.assertEqual([b'fn tag "m", x -> String = x', line(source("clauses"), 20),
                          b"fn tag other, y -> String = other"],
                         [line(after, n) for n in (24, 25, 26)])

    def test_multi_line_clause_breaks_a_group(self):
        after = self.formatted("clauses")
        self.assertEqual([line(source("clauses"), n) for n in (24, 25, 26)]
                         + [b"fn label Unknown(text) -> String = text",
                            b'fn label Declined(r)   -> String = "declined"'],
                         [line(after, n) for n in range(29, 34)])

    def test_lone_clause_is_a_group_of_one(self):
        after = self.formatted("clauses")
        self.assertEqual(b"fn lone x: String -> String = x", line(after, 36))

    def test_effect_line_aligns_arrow_and_equals(self):
        # DL-013 for one EFFECT line (slice 1 supports one EFFECT; notes.md F3).
        after = self.formatted("clauses")
        self.assertEqual(b'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")',
                         line(after, 46))

    def test_comments_stay_byte_for_byte(self):
        before = source("clauses")
        after = self.formatted("clauses")
        comments = [(n, row) for n, row in enumerate(before.split(b"\n"), 1) if b"//" in row]
        self.assertTrue(len(comments) >= 7 and any(row.endswith(b"   ") for _, row in comments), "fixture check")
        for n, row in comments:
            tail = row[row.index(b"//"):]
            self.assertTrue(line(after, after_line(n)).endswith(tail), "line %d keeps its comment bytes" % n)
        self.assertEqual([line(before, 26), line(before, 40), line(before, 41), line(before, 42)],
                         [line(after, after_line(n)) for n in (26, 40, 41, 42)],
                         "a string with `//` and the multi-line clause bodies stay")

    # VERSION MARK form (b) by DL-104 (D6B-43).

    def test_mark_removed_when_a_chain_from_v1_implies_it(self):
        after = self.formatted("marks")
        self.assertIn(b"\ntype Chained {\n  id: String\n  state: String\n  channel: String\n}\n", after)

    def test_squash_mark_without_chain_is_kept(self):
        after = self.formatted("marks")
        self.assertIn(b"\ntype Squashed v3 { id: String }\n", after)

    def test_v1_mark_without_chain_is_kept(self):
        # O3: `type Payment v1` selects the versioned decode of the EFFECT output.
        after = self.formatted("marks")
        self.assertIn(b"\ntype Payment v1 {\n  order_id: String\n  state: String\n}\n", after)

    def test_mark_written_when_the_chain_starts_above_v1(self):
        after = self.formatted("marks")
        self.assertIn(b"\ntype Shortened v5 {\n  id: String\n  note: String\n}\n", after)

    def test_mark_kept_beside_a_chain_above_v1_and_chain_from_v1_unchanged(self):
        after = self.formatted("marks")
        self.assertIn(b"\ntype Kept v5 {\n  id: String\n  note: String\n}\n", after)
        self.assertIn(b"\ntype Plain {\n  id: String\n  state: String\n}\n", after)

    # Layout (DL-148): TYPE and ENUM bodies, one clause table per block.

    def test_type_body_one_line_up_to_one_field_else_one_field_per_line(self):
        after = self.formatted("layout")
        self.assertEqual([b"type Empty {}", b"type Note { text: String }", b"type Amount {", b"  value: String",
                          b"  currency: String", b"}", b"type Order {", b"  order_id: String", b"  amount: Amount",
                          b"}", b"type One { id: String }", b"type Pair {", b"  a: String,", b"  b: String", b"}"],
                         [line(after, n) for n in range(2, 17)], "a one-line body expands, a lone field collapses")

    def test_type_body_with_a_comment_stays_as_written(self):
        after = self.formatted("layout")
        self.assertEqual([line(source("layout"), n) for n in range(13, 17)], [line(after, n) for n in range(17, 21)])

    def test_enum_body_one_line_up_to_one_variant_else_one_variant_per_line(self):
        after = self.formatted("layout")
        self.assertEqual([b"enum Channel {", b'  Web = "web"', b'  App = "app"', b"  Unknown(String)", b"}",
                          b"enum Single { Only }"], [line(after, n) for n in range(21, 27)],
                         "literal and payload variants keep their form")

    def test_one_table_across_signature_constructor_fn_and_effect_lines(self):
        after = self.formatted("layout")
        self.assertEqual([
            b"fn Amount             value: String, currency: String -> Amount ! BadAmount",
            b'fn Amount             _,             ""               -> Amount ! BadAmount  = BadAmount {}',
            b"fn Amount             value,         currency         -> Amount ! BadAmount  = Amount { value: value, "
            b"currency: currency }",
            b'effect orders.save    Order                           -> Order  ! StoreError = db.put("records")',
            b'effect payments.check Note                            -> Note   ! StoreError = http.post("payments/check")',
            b'effect ui.save        Order                           -> Order  ! StoreError = ui.event("save") |> save',
            b"fn check_note         n: Note                         -> Note   ! StoreError = n |> payments.check",
            b'fn label              c: Channel                      -> String              = "a -> b = c"',
        ], [line(after, n) for n in range(31, 39)])

    def test_comment_line_and_multi_line_clause_end_a_table(self):
        after = self.formatted("layout")
        self.assertEqual([line(source("layout"), 31),
                          b"fn save o: Order -> Order ! StoreError = o |> orders.save",
                          b"fn keep n: Note  -> Note               = n",
                          b"fn tidy Only -> String =", b'  "a"', b"fn tidy_one x: String -> String = x"],
                         [line(after, n) for n in range(39, 45)])

    # Invariants (D6B-45).

    def test_fmt_is_idempotent(self):
        for name in NAMES:
            with self.subTest(name):
                path = self.place(name, source(name))
                first = self.fmt(path)
                self.assertEqual((0, expected(name)), (first["code"], first["after"]),
                                 "R2: a no-op fmt must not pass; stderr: " + first["stderr"])
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
                self.assertEqual((0, expected(name)), (run["code"], run["after"]), "R2: " + run["stderr"])
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
