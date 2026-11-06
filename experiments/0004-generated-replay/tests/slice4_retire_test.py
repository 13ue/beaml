"""EXPERIMENT 0004 slice 4 (README revision 8.2): RETIRE LINE, DEAD LINE warnings and the removal command.

Build and command cases E1, E1b, E1c, E1d, E2 (build), E5, E5b, E5c, E5d, E6, E6b, E8 (T2-T7), E9, E9b, E9c,
E10b, E10c, E11, E11b, E11c, E11d, E12, E12b, E12c, E13, E14, E15, E15c, E15d, E16, E17, E18, E19, E19b, E19c,
and the revision 8.2 hardening cases E21, E21b, E21c, E21d, E21e, E22, E22b (DL-069). U1 is a Rust unit test.
The replay and live cases (E2 metadata, E3, E3b, E4, E7, E10, E15b, E17b) are in slice4_replay_test.py.
Each case runs twice:
  Fixture   the case sources in slice4/ (byte-equal to the template with the fixture names, see the guard),
            stored/v1.jsonl and stored/empty.jsonl, other RECORD SNAPSHOTS written per test;
  Template  the same sources from the template with random operation names, a random `keep` number
            (0, 4294967295 or other), random TYPE and field names, and random constants with a quote,
            a backslash and a non-ASCII letter.
Expected tokens, warning lines, diffs and files come from the README tables and the source segments here;
never from the compiler. A removal case copies the source into a temporary directory first.
Run: python3 -B experiments/0004-generated-replay/tests/slice4_retire_test.py [-k NAME]
"""
import re
import base64
import difflib
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import string
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import slice3_types_test as s3  # noqa: E402
import stored_types_test as st  # noqa: E402

HAS_NO_EFFECT = "has no effect in the source"
STILL_DECLARES = "still declares effect"
NO_PATH = "no path from the stored TYPE VERSION"
REMOVE_DEAD = "--remove-dead"
DEAD = "warning: DEAD LINE: "
REFUSED = "error: removal refused: "
ASSUME = "--assume-complete"


class Names:
    """TYPE T; fields k (order_id), o (status), t (state), c (channel), x (reference);
    constants cw (the `add c` constant), cx (the `add x` constant); operations old (retired) and new (live);
    n the `keep` number; ghost a TYPE name in no source."""

    def __init__(self, T, k, o, t, c, x, cw, cx, old, new, n, ghost):
        self.T, self.k, self.o, self.t, self.c, self.x = T, k, o, t, c, x
        self.cw, self.cx, self.old, self.new, self.n, self.ghost = cw, cx, old, new, n, ghost

    def __str__(self):
        return " [names: " + " ".join("%s=%r" % kv for kv in vars(self).items()) + "]"


FIXTURE_NAMES = Names("Payment", "order_id", "status", "state", "channel", "reference", "web", "pre-v4",
                      "payments.authorize", "payments.charge", 30, "Ghost")
U32_MAX = 4294967295


def random_names():
    rng = random.Random()
    word = lambda prefix: prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(6))  # noqa: E731
    const = lambda prefix: word(prefix) + '"\\é' + word("")  # noqa: E731
    return Names("Tq" + word(""), word("k_"), word("o_"), word("t_"), word("c_"), word("x_"), const("cw"),
                 const("cx"), word("ns") + "." + word("op"),
                 # The live operation keeps the namespace `payments`: the harness configures only `payments_port`.
                 "payments." + word("oq"),
                 rng.choice([0, U32_MAX, rng.randrange(1, 100000)]), "Gq" + word(""))


def literal(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def retire_form(op, n):
    return "retire %s keep %s days" % (op, n)


# Sources (README, Cases (slice 4)). A source is a list of segments (text, tag). A tag marks a line that
# can be a DEAD LINE: "retire", "s12" (`migrate T 1 -> 2`), "s23" (`migrate T 2 -> 3`). The text of a source
# is the join of its segments; the expected text after a removal is the join without the removed tags.
G_FAMILY = ("B", "G", "B+r", "G+r", "G+r0", "P", "P+r", "C2")
Q_FAMILY = ("Q4", "Q4s", "Q4-crlf", "Q4s-crlf", "Q4g+r", "Q4-oneline")
T_KINDS = ("T2", "T3a", "T3b", "T4", "T5a", "T5b", "T5c", "T6", "T7a", "T7b")
Q4_FIELDS = {1: "ko", 2: "kt", 3: "ktc", 4: "ktx"}


def retire_lines(N, kind):
    """The RETIRE LINE text of a G+r variant; T kinds hold the faults T2-T7 (README, Check rules)."""
    old, cap = N.old, ".".join(s[:1].upper() + s[1:] for s in N.old.split("."))
    return {"G+r": [retire_form(old, N.n)], "B+r": [retire_form(old, N.n)], "P+r": [retire_form(old, N.n)],
            "G+r0": [retire_form(old, 0)],
            "T2": [retire_form(old, N.n), retire_form(old, 1)],
            "T3a": [retire_form(cap, 1)], "T3b": [retire_form(old.split(".")[1], 1)],
            "T4": ["retire %s 30 days" % old], "T5a": ["retire %s keep days" % old],
            "T5b": ["retire %s keep -1 days" % old], "T5c": ["retire %s keep 1.5 days" % old],
            "T6": ["retire %s keep 4294967296 days" % old],
            "T7a": ["retire %s keep 3 weeks" % old], "T7b": ["retire %s keep 1 day" % old]}.get(kind, [])


def segments(N, kind):
    if kind in Q_FAMILY:
        return q_segments(N, kind)
    T, k, o, t = N.T, N.k, N.o, N.t
    header = "// EXPERIMENT 0004 slice 4: one EFFECT, a retired operation (sources B, G, P, C2 and their +r forms).\n"
    fields = (k, t) if kind == "C2" else (k, o)
    op = N.old if kind in ("B", "B+r", "C2") else N.new
    retire = [(line + "\n", "retire") for line in retire_lines(N, kind)]
    head = [(header, None), ("interface Order { order_id: String }\n", None),
            ("interface %s { %s: String %s: String }\n" % (T, fields[0], fields[1]), None)]
    finish = ("fn finish %s { %s, %s } -> %s = %s { %s: %s + \"\", %s: %s }\n"
              % (T, fields[0], fields[1], T, T, fields[0], fields[0], fields[1], fields[1]), None)
    if kind in ("P", "P+r"):
        return head + retire + [("\n", None), finish]
    chain = [("migrate %s 1 -> 2 { rename %s -> %s }\n" % (T, o, t), None)] if kind == "C2" else []
    return head + chain + [
        ("interface PaymentError { reason: String }\n", None), ("\n", None),
        ("effect %s Order -> %s ! PaymentError = http.post(\"payments/authorize\")\n" % (op, T), None)] + retire + [
        ("\n", None), ("fn prepare Order { order_id } -> Order = Order { order_id: order_id + \"\" }\n", None),
        finish, ("\n", None),
        ("fn place order: Order -> %s ! PaymentError =\n  order\n  |> prepare\n  |> %s\n  |> finish\n" % (T, op), None)]


def q_segments(N, kind):
    """Q4 layout (README revision 8.1): a comment directly above and directly below the dead steps, a blank line
    between them, a multi-line `migrate { }` block, and no final newline. CRLF forms change only the line ends."""
    T, k, o, t, c, x = N.T, N.k, N.o, N.t, N.c, N.x
    op = N.new if kind == "Q4g+r" else N.old
    s34 = "migrate %s 3 -> 4 { drop %s: String, add %s: String = %s }" % (T, c, x, literal(N.cx))
    if kind == "Q4-oneline":
        s23 = [("migrate %s 2 -> 3 { add %s: String = %s } %s\n" % (T, c, literal(N.cw), s34), "s23+s34")]
        last = []
    else:
        s23 = [("migrate %s 2 -> 3 {\n  add %s: String = %s\n}\n" % (T, c, literal(N.cw)), "s23")]
        last = [("// The last MIGRATE STEP carries the newest TYPE VERSION. It is never a DEAD LINE.\n", None),
                (s34 + "\n", None)]
    chain = [("// The first two MIGRATE STEPS are DEAD LINES when no record has version 2 or older.\n", None),
             ("migrate %s 1 -> 2 { rename %s -> %s }\n" % (T, o, t), "s12"), ("\n", None)] + s23 + last
    if kind in ("Q4s", "Q4s-crlf"):
        chain = [seg for seg in chain if seg[1] not in ("s12", "s23")]
    retire = [(retire_form(N.old, N.n) + "\n", "retire")] if kind == "Q4g+r" else []
    segs = [("// EXPERIMENT 0004 slice 4: a MIGRATE CHAIN of four TYPE VERSIONS (sources Q4, Q4s, Q4g+r).\n", None),
            ("interface Order { order_id: String }\n", None),
            ("interface %s { %s: String %s: String %s: String }\n" % (T, k, t, x), None)] + chain + [
        ("interface PaymentError { reason: String }\n", None), ("\n", None),
        ("effect %s Order -> %s ! PaymentError = http.post(\"payments/authorize\")\n" % (op, T), None)] + retire + [
        ("\n", None), ("fn prepare Order { order_id } -> Order = Order { order_id: order_id + \"\" }\n", None),
        ("fn finish %s { %s, %s, %s } -> %s = %s { %s: %s + \"\", %s: %s, %s: %s }\n"
         % (T, k, t, x, T, T, k, k, t, t, x, x), None), ("\n", None),
        ("fn place order: Order -> %s ! PaymentError =\n  order\n  |> prepare\n  |> %s\n  |> finish" % (T, op), None)]
    if kind.endswith("-crlf"):
        segs = [(text.replace("\n", "\r\n"), tag) for text, tag in segs]
    return segs


def source_text(N, kind, without=()):
    return "".join(text for text, tag in segments(N, kind) if tag not in without)


def line_of(N, kind, tag):
    """1-based source line where the segment with `tag` starts."""
    before = ""
    for text, t in segments(N, kind):
        if t == tag:
            return before.count("\n") + 1
        before += text
    raise KeyError(tag)


FIXTURE_KINDS = G_FAMILY + Q_FAMILY


def fixture_path(kind):
    return EXPERIMENT / "slice4" / kind / "orders.beaml"


# RECORD SNAPSHOTS (README, Cases (slice 4)): (operation role, (TYPE role, version, field roles) or None).
def snapshot_spec(label):
    q = lambda v: ("T", v, Q4_FIELDS[v])  # noqa: E731
    v1 = ("old", ("T", 1, "ko"))
    return {
        "empty": [], "v1": [v1], "v1x2": [v1, v1],
        "v1+new1": [v1, ("new", ("T", 1, "ko"))],
        "v1+new1-state": [v1, ("new", ("T", 1, "kt"))],
        "v1+ghost": [v1, ("old", ("ghost", 1, "ko"))],
        "v1+untyped": [v1, ("old", None)],
        "new1": [("new", ("T", 1, "ko"))],
        "q-v1": [("old", q(1))], "q-v2": [("old", q(2))], "q-v3": [("old", q(3)), ("old", q(3))],
        "q-v4": [("old", q(4))], "q-v3v1": [("old", q(3)), ("old", q(1))],
        "q-v3v2": [("old", q(3)), ("old", q(2))],
        "qg-v3+old1": [("new", q(3)), ("old", q(1))], "qg-v3": [("new", q(3))],
        "qg-old1": [("old", q(1))],
        "c2-v2": [("old", ("T", 2, "kt"))],
    }[label]


# Body values per stored TYPE VERSION (field roles -> value). Version 3 and 4 have a second form for a
# second record of one snapshot.
BODIES = {"ko": [{"k": "order-1", "o": "authorized"}], "kt": [{"k": "order-1", "t": "settled"}],
          "ktc": [{"k": "order-1", "t": "settled", "c": "app"}, {"k": "order-1", "t": "pending", "c": "web"}],
          "ktx": [{"k": "order-1", "t": "settled", "x": "r-4"}]}


def with_body(record, body):
    return dict(record, body_base64=base64.b64encode(body).decode(), body_length=len(body),
                body_sha256=hashlib.sha256(body).hexdigest())


def make_record(N, op_role, type_spec, index=0, body=None):
    """A RESPONSE RECORD of stored/v1.jsonl with another operation, TYPE VERSION, trace id and body."""
    record = dict(st.v1_record(), operation=getattr(N, op_role), trace_id="%032x" % (0x5e1ce4 + index))
    if type_spec is None:
        record.pop("type")
        roles = "ko"
    else:
        name_role, version, roles = type_spec
        name = N.T if name_role == "T" else N.ghost
        record["type"] = s3.type_version(name, version, [getattr(N, r) for r in roles])
    if body is None:
        forms = BODIES[roles]
        body = forms[index % len(forms)]
    raw = {getattr(N, role): value for role, value in body.items()}
    return with_body(record, json.dumps(raw, separators=(",", ":"), ensure_ascii=False).encode())


def snapshot_records(N, label):
    return [make_record(N, op, spec, i) for i, (op, spec) in enumerate(snapshot_spec(label))]


def snapshot_bytes(N, label):
    return "".join(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n"
                   for r in snapshot_records(N, label)).encode()


PATH = object()  # Token marker: the --stored path of the case.


class Slice4Retire:
    """Shared cases. A subclass sets `names` and implements `fixture(kind)` and `snapshot(label)`."""
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s4-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    # Inputs.
    def write_snapshot(self, label):
        path = self.work / ("snapshot-%s-%s.jsonl" % (label, random.randrange(10 ** 8)))
        path.write_bytes(snapshot_bytes(self.names, label))
        return path

    def copy_source(self, kind):
        """A writable copy of the source. Return (the path as given on the command line, the file)."""
        relative = "%s-%s/orders.beaml" % (kind.replace("+", "p"), random.randrange(10 ** 8))
        path = self.work / relative
        path.parent.mkdir()
        path.write_bytes(self.source_bytes(kind))
        return relative, path

    def source_bytes(self, kind):
        return source_text(self.names, kind).encode()

    # Runs. Bytes in and out: a text pipe would change CRLF line ends.
    def run_compiler(self, argv, cwd):
        result = subprocess.run([st.compiler()] + [str(a) for a in argv], cwd=cwd, capture_output=True)
        return result.returncode, result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")

    def compile(self, kind, label, stored=None):
        stored = stored or self.snapshot(label)
        source = self.source(kind)
        code, stdout, stderr = self.run_compiler([source, "--stored", stored], self.work / "cwd")
        return code, stdout, stderr, str(source), str(stored)

    def events(self, cwd):
        log = Path(cwd) / ".beaml" / "actions.jsonl"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.is_file() else []

    def ctx(self, *parts):
        return " ".join(str(p) for p in parts) + str(self.names)

    # Assertions.
    def assert_rejected(self, kind, label, tokens, absent=(), stored=None):
        code, stdout, stderr, source, stored = self.compile(kind, label, stored)
        self.assertEqual(1, code, self.ctx(kind, label, "expected exit 1 (not a crash); stderr:", stderr))
        self.assertEqual("", stdout, self.ctx(kind, label, "expected no stdout"))
        tokens = [stored if t is PATH else t for t in tokens]
        self.assertEqual(([], []), ([t for t in tokens if t not in stderr],
                                    [a for a in tuple(absent) + ("warning:",) if a in stderr]),
                         self.ctx(kind, label, "tokens (missing, unexpected); actual:", stderr))
        return stderr

    def assert_warnings(self, kind, label, tags):
        """exit 0, non-empty stdout, exactly the DEAD LINE warnings of `tags`, in source line order."""
        N = self.names
        code, stdout, stderr, source, stored = self.compile(kind, label)
        self.assertEqual(0, code, self.ctx(kind, label, "expected exit 0; stderr:", stderr))
        self.assertIn("defmodule BeamlSpike do", stdout, self.ctx(kind, "stdout holds the Elixir source"))
        lines = stderr.splitlines()
        heads = [i for i, line in enumerate(lines) if line.startswith("warning:")]
        expected, actual = [], []
        for number, tag in enumerate(tags):
            line = line_of(N, kind, tag)
            if tag == "retire":
                form, why = retire_form(N.old, N.n), "no stored RESPONSE RECORD of operation %s" % N.old
            else:
                a = int(tag[1])
                form, why = "migrate %s %d -> %d" % (N.T, a, a + 1), "version %d or older" % a
            tokens = [DEAD + form, "at %s:%d" % (source, line), stored, why, REMOVE_DEAD]
            expected.append(tokens)
            block = ""
            if number < len(heads):
                end = heads[number + 1] if number + 1 < len(heads) else len(lines)
                block = "\n".join(lines[heads[number]:end])
            actual.append([t for t in tokens if t in block])
        self.assertEqual((len(tags), expected), (len(heads), actual),
                         self.ctx(kind, label, "warnings (count, tokens per warning in order); stderr:", stderr))
        if tags:
            self.assertTrue(stderr.startswith("warning:"), self.ctx(kind, "stderr starts with warning:", stderr))
        last = (self.events(self.work / "cwd") or [{}])[-1]
        self.assertEqual(len(tags), last.get("warnings"),
                         self.ctx(kind, "the action event records warnings: <count>", last))
        log = json.dumps(self.events(self.work / "cwd"))
        self.assertEqual([], [p for p in (Path(stored).name, source) if p in log], "events hold no path")
        return stdout

    def assert_clean(self, kind, label):
        return self.assert_warnings(kind, label, [])

    def r1_tokens(self, count):
        N = self.names
        return [N.old, HAS_NO_EFFECT, PATH, "help:", retire_form(N.old, "<n>"),
                "stored RESPONSE RECORDS of operation %s: %d" % (N.old, count)]

    # Removal command.
    def remove(self, kind, label, argv=None, relative=None, extra=()):
        """Run the removal command on a copy of `kind` (or on `relative`). Return a dict of what it did."""
        if relative is None:
            relative, _ = self.copy_source(kind)
        path = self.work / relative
        stored = self.snapshot(label) if label is not None else None
        before, stat, listing = path.read_bytes(), os.stat(path), sorted(os.listdir(path.parent))
        argv = argv or [relative, "--stored", stored, REMOVE_DEAD] + list(extra)
        argv = [stored if a is PATH else a for a in argv]
        code, stdout, stderr = self.run_compiler(argv, self.work)
        after = os.stat(path)
        return {"relative": relative, "path": path, "stored": stored, "before": before, "after": path.read_bytes(),
                "code": code, "stdout": stdout, "stderr": stderr, "same_inode": after.st_ino == stat.st_ino,
                "same_mtime": after.st_mtime_ns == stat.st_mtime_ns,
                "listing_same": sorted(os.listdir(path.parent)) == listing}

    def assert_removed(self, kind, label, tags, relative=None, extra=()):
        N = self.names
        run = self.remove(kind, label, relative=relative, extra=extra)
        old_text = run["before"].decode()
        new_text = source_text(N, kind, without=tags)
        rel = run["relative"]
        diff = "".join(difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                            rel, rel, n=0))
        count = "removed %d DEAD LINE%s from %s" % (len(tags), "" if len(tags) == 1 else "S", rel)
        self.assertEqual(
            {"code": 0, "stdout": diff, "count": True, "error": False, "file": new_text.encode(),
             "renamed": True, "temp_left": False},
            {"code": run["code"], "stdout": run["stdout"], "count": count in run["stderr"],
             "error": "error:" in run["stderr"], "file": run["after"], "renamed": not run["same_inode"],
             "temp_left": not run["listing_same"]},
            self.ctx(kind, label, "removal contract; stderr:", run["stderr"]))
        events = [e for e in self.events(self.work) if e.get("action") == "remove-dead"]
        self.assertEqual((1, len(tags)), (len(events), events[-1].get("removed") if events else None),
                         self.ctx("one remove-dead action event with removed: <count>", events))
        log = (self.work / ".beaml" / "actions.jsonl").read_text()
        self.assertEqual([], [p for p in (rel, "migrate", "retire ") if p in log], "the event holds no path or line text")
        return run

    def assert_untouched(self, run, tokens):
        self.assertEqual(
            {"code": 1, "stdout": "", "file": run["before"], "same_inode": True, "same_mtime": True,
             "listing_same": True, "missing": []},
            {"code": run["code"], "stdout": run["stdout"], "file": run["after"], "same_inode": run["same_inode"],
             "same_mtime": run["same_mtime"], "listing_same": run["listing_same"],
             "missing": [t for t in tokens if t not in run["stderr"]]},
            self.ctx("the command must write nothing; stderr:", run["stderr"]))

    # E1-E1d: a deleted EFFECT with stored records (R1).
    def test_E01_deleted_effect_with_stored_record_is_compile_error(self):
        stderr = self.assert_rejected("G", "v1", self.r1_tokens(1))
        first = "error: stored RESPONSE RECORD of operation %s %s" % (self.names.old, HAS_NO_EFFECT)
        self.assertEqual(first, stderr.splitlines()[0], self.ctx("R1 keeps the DL-040 first line"))

    def test_E01b_source_without_any_effect_gives_the_same_error(self):
        self.assert_rejected("P", "v1", self.r1_tokens(1))

    def test_E01c_same_source_with_empty_snapshot_compiles(self):
        self.assert_clean("G", "empty")

    def test_E01d_two_records_of_the_operation_are_counted_in_one_message(self):
        stderr = self.assert_rejected("G", "v1x2", self.r1_tokens(2))
        self.assertEqual(1, stderr.count(HAS_NO_EFFECT), self.ctx("one message for all records", stderr))

    # E2, E5-E5d: a RETIRE LINE.
    def test_E02_retire_line_makes_the_build_pass(self):
        self.assert_clean("G+r", "v1")

    def test_E05_retired_and_live_records_together_compile(self):
        self.assert_clean("G+r", "v1+new1")

    def test_E05b_live_record_without_path_still_fails_beside_a_retire_line(self):
        N = self.names
        self.assert_rejected("G+r", "v1+new1-state", ["of operation %s" % N.new, NO_PATH, PATH],
                             absent=["of operation %s" % N.old])

    def test_E05c_retired_record_of_a_type_in_no_source_is_not_path_checked(self):
        self.assert_clean("G+r", "v1+ghost")

    def test_E05d_retired_record_without_type_version_is_compile_error(self):
        stderr = self.assert_rejected("G+r", "v1+untyped", [st.NO_TYPE_VERSION, PATH])
        self.assertTrue(re.search(r"(\bline 2\b|:2\b)", stderr), self.ctx("E5d names line 2", stderr))

    # E6, E6b, E8: source faults (T1-T7).
    def test_E06_retire_line_for_a_declared_effect_is_compile_error(self):
        N = self.names
        self.assert_rejected("B+r", "v1", ["retire %s" % N.old, "%s %s" % (STILL_DECLARES, N.old)])

    def test_E06b_the_same_error_with_an_empty_snapshot(self):
        N = self.names
        self.assert_rejected("B+r", "empty", ["retire %s" % N.old, "%s %s" % (STILL_DECLARES, N.old)])

    def test_E08_retire_line_faults_T2_to_T7(self):
        N = self.names
        tokens = {"T2": ["retire %s" % N.old, "two times"],
                  "T3a": ["invalid operation name", "namespace.operation"],
                  "T3b": ["invalid operation name", "namespace.operation"],
                  "T4": ["expected keep"], "T5a": ["expected number of days"],
                  # README revision 8.1: the lexer rejects `-` and `.` before the parser (observed message).
                  "T5b": ["unsupported token"], "T5c": ["unsupported token"],
                  "T6": ["number too large"], "T7a": ["keep supports days only"], "T7b": ["keep supports days only"]}
        for kind in T_KINDS:
            with self.subTest(kind=kind):
                self.assert_rejected(kind, "empty", tokens[kind])

    # E9-E9c: W1.
    def test_E09_retire_line_without_records_is_one_W1_warning(self):
        self.assert_warnings("G+r", "empty", ["retire"])

    def test_E09b_retire_line_with_records_has_no_warning(self):
        self.assert_clean("G+r", "v1")

    def test_E09c_records_of_the_live_operation_only_give_one_W1_warning(self):
        # Kills "W1 only when the RECORD SNAPSHOT is empty".
        self.assert_warnings("G+r", "new1", ["retire"])

    # E10b, E10c: a source without an EFFECT.
    def test_E10b_retire_line_without_stored_input_is_compile_error(self):
        code, stdout, stderr = self.run_compiler([self.source("P+r")], self.work / "cwd")
        self.assertEqual((1, "", True), (code, stdout, st.UNKNOWN_STORE in stderr), self.ctx(stderr))

    def test_E10c_source_without_effect_and_retire_line_needs_no_stored_input(self):
        code, stdout, stderr = self.run_compiler([self.source("P")], self.work / "cwd")
        self.assertEqual((0, "", False, False), (code, stderr, "defmodule Replay" in stdout, "def retired" in stdout),
                         self.ctx(stderr))

    # E11-E14: W2.
    def test_E11_records_of_version_1_need_every_step(self):
        self.assert_clean("Q4", "q-v1")

    def test_E11b_records_of_version_2_give_one_W2_warning(self):
        self.assert_warnings("Q4", "q-v2", ["s12"])

    def test_E11c_oldest_record_last_in_the_snapshot_keeps_every_step(self):
        # [v3, v1]: kills a W2 rule that reads the first record or the newest version only.
        self.assert_clean("Q4", "q-v3v1")

    def test_E11d_versions_3_and_2_give_one_W2_warning(self):
        # [v3, v2]: kills a W2 rule that takes the newest stored version.
        self.assert_warnings("Q4", "q-v3v2", ["s12"])

    def test_E12_records_of_version_3_give_two_W2_warnings_in_source_order(self):
        self.assert_warnings("Q4", "q-v3", ["s12", "s23"])

    def test_E12b_empty_snapshot_gives_two_W2_warnings_not_for_the_last_step(self):
        self.assert_warnings("Q4", "empty", ["s12", "s23"])

    def test_E12c_newest_version_only_gives_two_W2_warnings_not_for_the_last_step(self):
        self.assert_warnings("Q4", "q-v4", ["s12", "s23"])

    def test_E13_last_step_is_never_dead(self):
        self.assert_clean("C2", "c2-v2")

    def test_E14_retired_records_do_not_keep_a_step_alive(self):
        self.assert_warnings("Q4g+r", "qg-v3+old1", ["s12", "s23"])

    # E15-E16: the removal command.
    def test_E15_removal_removes_exactly_the_dead_steps(self):
        self.assert_removed("Q4", "q-v3", ("s12", "s23"))

    def test_E15c_removal_of_W1_and_W2_together(self):
        run = self.assert_removed("Q4g+r", "qg-v3", ("retire", "s12", "s23"))
        code, stdout, stderr = self.run_compiler([run["relative"], "--stored", run["stored"]], self.work)
        self.assertEqual((0, False, True), (code, "warning:" in stderr, "defmodule BeamlSpike do" in stdout),
                         self.ctx("the result builds without a warning", stderr))

    def test_E15d_removal_keeps_CRLF_line_ends(self):
        run = self.assert_removed("Q4-crlf", "q-v3", ("s12", "s23"))
        self.assertEqual(source_text(self.names, "Q4s-crlf").encode(), run["after"])

    def test_E16_second_removal_changes_nothing(self):
        first = self.assert_removed("Q4", "q-v3", ("s12", "s23"))
        run = self.remove("Q4", "q-v3", relative=first["relative"])
        self.assertEqual(
            {"code": 0, "stdout": "", "no_dead": True, "file": first["after"], "same_inode": True, "same_mtime": True},
            {"code": run["code"], "stdout": run["stdout"], "no_dead": "no DEAD LINE in %s" % first["relative"] in run["stderr"],
             "file": run["after"], "same_inode": run["same_inode"], "same_mtime": run["same_mtime"]},
            self.ctx("idempotence; stderr:", run["stderr"]))

    # E17: a removed step that a record needs blocks again.
    def test_E17_removed_step_needed_again_blocks_the_build(self):
        N = self.names
        self.assert_rejected("Q4s", "q-v3v1", [N.T, "starts at version 3", "TYPE VERSION 1", "version control", PATH])

    def test_E17_control_shortened_chain_with_version_3_records_compiles(self):
        self.assert_clean("Q4s", "q-v3")

    # E18-E19c.
    def test_E18_removed_retire_line_blocks_again_with_records(self):
        # Revision 8.2: an empty snapshot needs --assume-complete (E21c is the refusal).
        run = self.assert_removed("G+r", "empty", ("retire",), extra=(ASSUME,))
        self.assertEqual(source_text(self.names, "G").encode(), run["after"])
        stored = self.snapshot("v1")
        code, stdout, stderr = self.run_compiler([run["relative"], "--stored", stored], self.work)
        tokens = [str(stored) if t is PATH else t for t in self.r1_tokens(1)]
        self.assertEqual((1, "", []), (code, stdout, [t for t in tokens if t not in stderr]),
                         self.ctx("E18 rebuild with v1", stderr))

    def test_E19_removal_on_a_build_error_writes_nothing(self):
        run = self.remove("G", "v1")
        self.assert_untouched(run, [t if t is not PATH else str(run["stored"]) for t in self.r1_tokens(1)])

    def test_E19b_dead_step_sharing_a_line_with_other_text_is_not_removed(self):
        run = self.remove("Q4-oneline", "q-v3")
        line = line_of(self.names, "Q4-oneline", "s23+s34")
        self.assert_untouched(run, ["cannot remove", "line %d holds other text" % line])

    def test_E19c_removal_without_stored_or_in_other_order_is_a_usage_error(self):
        relative, _ = self.copy_source("Q4")
        for argv in ([relative, REMOVE_DEAD], [relative, REMOVE_DEAD, "--stored", PATH]):
            with self.subTest(argv=" ".join("SNAPSHOT" if a is PATH else a for a in argv[1:])):
                self.assert_untouched(self.remove("Q4", "q-v3", argv=argv, relative=relative), ["usage", REMOVE_DEAD])

    # E21-E22b: hardening of the removal command (README revision 8.2, DL-069).
    def refused_tokens(self, kind, tags, stored):
        N = self.names
        tokens = []
        for tag in tags:
            if tag == "retire":
                tokens += [REFUSED + retire_form(N.old, N.n), "operation %s" % N.old]
            else:
                a = int(tag[1])
                tokens += [REFUSED + "migrate %s %d -> %d" % (N.T, a, a + 1), "TYPE %s" % N.T]
        return tokens + [str(stored), ASSUME]

    def assert_refused(self, kind, label, tags):
        run = self.remove(kind, label)
        self.assert_untouched(run, self.refused_tokens(kind, tags, run["stored"]))
        heads = [line[len(REFUSED):] for line in run["stderr"].splitlines() if line.startswith(REFUSED)]
        N = self.names
        forms = [retire_form(N.old, N.n) if t == "retire" else "migrate %s %s -> %d" % (N.T, t[1], int(t[1]) + 1)
                 for t in tags]
        self.assertEqual((forms, False, True), (heads, "warning:" in run["stderr"], run["stderr"].startswith("error:")),
                         self.ctx(kind, label, "one refusal per DEAD LINE in source order; stderr:", run["stderr"]))

    def test_E21_empty_snapshot_refuses_dead_migrate_steps(self):
        self.assert_refused("Q4", "empty", ("s12", "s23"))

    def test_E21b_retired_records_only_refuse_dead_migrate_steps(self):
        # The snapshot is not empty, but it holds no record of TYPE T from its effect.
        self.assert_refused("Q4g+r", "qg-old1", ("s12", "s23"))

    def test_E21c_empty_snapshot_refuses_a_dead_retire_line(self):
        self.assert_refused("G+r", "empty", ("retire",))

    def test_E21d_assume_complete_removes_with_an_empty_snapshot(self):
        run = self.assert_removed("Q4", "empty", ("s12", "s23"), extra=(ASSUME,))
        self.assertEqual(source_text(self.names, "Q4s").encode(), run["after"])

    def test_E21e_assume_complete_without_or_before_remove_dead_is_a_usage_error(self):
        relative, _ = self.copy_source("Q4")
        for argv in ([relative, "--stored", PATH, ASSUME], [relative, "--stored", PATH, ASSUME, REMOVE_DEAD]):
            with self.subTest(argv=" ".join("SNAPSHOT" if a is PATH else a for a in argv[1:])):
                self.assert_untouched(self.remove("Q4", "q-v3", argv=argv, relative=relative), ["usage", ASSUME])

    def test_E22_removal_through_a_symlink_edits_the_target_and_keeps_the_link(self):
        tag = random.randrange(10 ** 8)
        real = self.work / ("real-%s" % tag) / "orders.beaml"
        real.parent.mkdir()
        real.write_bytes(self.source_bytes("Q4"))
        link_relative = "link-%s/orders.beaml" % tag
        link = self.work / link_relative
        link.parent.mkdir()
        target = os.path.join("..", "real-%s" % tag, "orders.beaml")
        os.symlink(target, link)
        real_inode, real_listing = os.stat(real).st_ino, sorted(os.listdir(real.parent))
        self.assert_removed("Q4", "q-v3", ("s12", "s23"), relative=link_relative)
        self.assertEqual(
            {"link": True, "target": target, "real": source_text(self.names, "Q4s").encode(), "new_inode": True,
             "real_listing": real_listing},
            {"link": os.path.islink(link), "target": os.readlink(link) if os.path.islink(link) else None,
             "real": real.read_bytes(), "new_inode": os.stat(real).st_ino != real_inode,
             "real_listing": sorted(os.listdir(real.parent))},
            self.ctx("the link stays, the real file is rewritten"))

    def test_E22b_read_only_source_is_refused(self):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("root ignores the mode")
        relative, path = self.copy_source("Q4")
        os.chmod(path, 0o444)
        run = self.remove("Q4", "q-v3", relative=relative)
        self.assert_untouched(run, ["not writable", relative])
        self.assertEqual(0o444, os.stat(path).st_mode & 0o777, self.ctx("the mode stays 0444"))


class Fixture(Slice4Retire, unittest.TestCase):
    names = FIXTURE_NAMES

    def source(self, kind):
        if kind in FIXTURE_KINDS:
            return fixture_path(kind)
        path = self.work / kind / "orders.beaml"
        if not path.is_file():
            path.parent.mkdir()
            path.write_bytes(source_text(self.names, kind).encode())
        return path

    def source_bytes(self, kind):
        return fixture_path(kind).read_bytes() if kind in FIXTURE_KINDS else source_text(self.names, kind).encode()

    def snapshot(self, label):
        if label in ("v1", "empty"):
            return EXPERIMENT / "stored" / ("%s.jsonl" % label)
        return self.write_snapshot(label)

    def test_fixtures_equal_the_template_byte_for_byte(self):
        # Guard, not RED: every slice4 fixture is the template with the fixture names; CRLF forms hold CRLF only.
        for kind in FIXTURE_KINDS:
            with self.subTest(kind=kind):
                self.assertEqual(source_text(FIXTURE_NAMES, kind).encode(), fixture_path(kind).read_bytes())
        for kind in ("Q4-crlf", "Q4s-crlf"):
            data = fixture_path(kind).read_bytes()
            self.assertEqual(data.count(b"\n"), data.count(b"\r\n"), kind)
        for kind in Q_FAMILY:
            self.assertFalse(fixture_path(kind).read_bytes().endswith(b"\n"), kind + ": no final newline")
        record = st.v1_record()
        self.assertEqual((FIXTURE_NAMES.old, s3.type_version("Payment", 1, ["order_id", "status"])),
                         (record["operation"], record["type"]))


class Template(Slice4Retire, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.names = random_names()

    def source(self, kind):
        path = self.work / kind / "orders.beaml"
        if not path.is_file():
            path.parent.mkdir()
            path.write_bytes(source_text(self.names, kind).encode())
        return path

    def snapshot(self, label):
        return self.write_snapshot(label)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
