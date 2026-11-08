"""EXPERIMENT 0004 slice 5 (README revision 9.1): `type`, `v` on every version number, and the VERSION MARK.

Build cases F1, F2, F3, F3b, F3c, F4, F5, F6, F7, F8, F8b, F8c, F9 (build), F10, F11 (build), F11b, F12, F12b,
F12c, F13, F14, F15. O7 is answered (DL-080, option (a)): F6, F13 and F14 compile, F8c stays a gap error. Rewrite checks: P1 (the `payments.beaml` snapshot), A2 (R-EQ against the base compiler,
closed normaliser S), A3 (stored fixtures unchanged). A1 is in slice5_rewrite_test.py, F20-F28 in
slice5_squash_test.py, the replay and live cases in slice5_replay_test.py.
Each name-dependent case runs twice:
  Fixture   the sources in slice5/ (byte-equal to the template with the fixture names, see the guard);
  Template  the same sources from the template with random TYPE, field and operation names, field names of the form
            `v<digits>` in some draws, random constants with a quote, a backslash and a non-ASCII letter, and a
            random base b in 1 to 10^9 for every source with a VERSION MARK (M3 is `v(b+2)`, Q4s and Q4z `v(b+3)`).
Expected tokens and files come from the README tables and the segments here; never from the compiler.
Run: python3 -B experiments/0004-generated-replay/tests/slice5_syntax_test.py [-k NAME]
"""
import base64
import bisect
import difflib
import json
import os
from pathlib import Path
import random
import re
import shutil
import string
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import COMPILER_PATH, EXPERIMENT, REPO  # noqa: E402
import stored_types_test as st  # noqa: E402

BASE = "f29e3f12"
# Slice 6b step 6a changes the record writer of every EFFECT by contract (repin.md in slice6b-records-v2).
# R-EQ now compares BASE with PRE_6A, the last compiler before step 6a.
# PIN, the step 6b compiler (D6B-172: dotted unknown_keys in every EFFECT source, 237a4578..461d024e), pins the
# bytes; before: 237a4578 (step 12, DL-119), 0747c315 (step 6a).
PRE_6A = "4a7cffba"
PIN = "ca09d361"
U32_MAX = 4294967295
NO_PATH = "no path from the stored TYPE VERSION"
FALLBACK = "expected type, enum, effect, migrate, retire or fn"
EXPERIMENT_REL = "experiments/0004-generated-replay"


class Names:
    """TYPE T, its error TYPE E = T + "Error" (a name with T as prefix, T23), fields k (order_id), o (status),
    t (state), c (channel), x (reference); constants cw (`add c`), cx (`add x`); live operation op; a second
    record TYPE note with field nf and constant nc (F26); three field names vf of the form v<digits> (F5);
    b the base of the marked sources; r the version of the F12c record."""

    def __init__(self, T, k, o, t, c, x, cw, cx, op, note, nf, nc, vf, b, r):
        self.T, self.k, self.o, self.t, self.c, self.x = T, k, o, t, c, x
        self.cw, self.cx, self.op, self.note, self.nf, self.nc = cw, cx, op, note, nf, nc
        self.vf, self.b, self.r = vf, b, r

    @property
    def E(self):
        return self.T + "Error"

    @property
    def M(self):
        """The VERSION MARK of M3."""
        return self.b + 2

    @property
    def V(self):
        """The VERSION MARK of Q4s and Q4z."""
        return self.b + 3

    def __str__(self):
        return " [names: " + " ".join("%s=%r" % kv for kv in vars(self).items()) + "]"


FIXTURE_NAMES = Names("Payment", "order_id", "status", "state", "channel", "reference", "web", "pre-v4",
                      "payments.authorize", "Note", "text", "x", ("v1", "v2", "v3"), 1, 2)


def random_names():
    rng = random.Random()
    word = lambda prefix: prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(6))  # noqa: E731
    const = lambda prefix: word(prefix) + '"\\é' + word("")  # noqa: E731
    while True:
        # Some draws give field names of the form v<digits> (README, Cases (slice 5)).
        field = lambda prefix: "v%d" % rng.randrange(1, 10 ** 12) if rng.random() < .25 else word(prefix)  # noqa
        fields = [field("k_"), field("o_"), field("t_"), field("c_"), field("x_"), field("n_")]
        vf = tuple("v%d" % rng.randrange(1, 10 ** 12) for _ in range(3))
        if len(set(fields) | set(vf)) == 9:
            break
    k, o, t, c, x, nf = fields
    return Names("Tq" + word(""), k, o, t, c, x, const("cw"), const("cx"),
                 # The live operation keeps the namespace `payments` (DL-068).
                 "payments." + word("oq"), "Nq" + word(""), nf, const("nc"), vf,
                 rng.randrange(1, 10 ** 9 + 1), rng.randrange(2, 10 ** 9 + 1))


def literal(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


# Sources (README, Cases (slice 5)). A source is a list of segments (text, tag). Tags: "type" (the declaration of T),
# "type-note" (the declaration of the note TYPE), "s12", "s23", "s34" (the MIGRATE STEPS of T, in chain order),
# "n12" (the step of the note TYPE). The text is the join of the segments; a removal drops tags and inserts marks.
FIXTURE_KINDS = ("B5", "M3", "Q4", "Q4s", "Q4z", "Q4-crlf", "C2")
T23_LAYOUTS = ("T23-block", "T23-comment", "T23-nospace", "T23-tab", "T23-last", "T23-below", "T23-oneline",
               "Q4-crlf", "T23-prefix", "T23-commented")


def tail(N, fields, final_newline=True):
    """Effect, prepare, finish and the flow of T with `fields` (field names in declaration order)."""
    T, E = N.T, N.E
    finish = "fn finish %s { %s } -> %s = %s { %s }\n" % (
        T, ", ".join(fields), T, T, ", ".join("%s: %s%s" % (f, f, ' + ""' if i == 0 else "")
                                              for i, f in enumerate(fields)))
    return [("effect %s Order -> %s ! %s = http.post(\"payments/authorize\")\n" % (N.op, T, E), None), ("\n", None),
            ("fn prepare Order { order_id } -> Order = Order { order_id: order_id + \"\" }\n", None),
            (finish, None), ("\n", None),
            ("fn place order: Order -> %s ! %s =\n  order\n  |> prepare\n  |> %s\n  |> finish%s"
             % (T, E, N.op, "\n" if final_newline else ""), None)]


def declaration(N, fields, mark=None, name=None):
    name = name or N.T
    return "type %s%s { %s }\n" % (name, " v%d" % mark if mark is not None else "",
                                   " ".join("%s: String" % f for f in fields))


def b5_segments(N, keyword="type"):
    """The slice 1 source (arms/gen/orders.beaml) with `type` (README, B5)."""
    T, E, k, o = N.T, N.E, N.k, N.o
    segs = [("%s Order { order_id: String }\n" % keyword, None),
            ("%s %s { %s: String %s: String }\n" % (keyword, T, k, o), "type"),
            ("%s %s { reason: String }\n" % (keyword, E), None), ("\n", None),
            ("// Leaves the module. Recorded live, substituted in a REPLAY RUN.\n", None)] + tail(N, (k, o))
    segs.insert(len(segs) - 1, ("// The flow lives in BEAML. A failed step stops the pipe and passes %s on.\n" % E,
                                None))
    return segs


def b5c_segments(N, numbers=("v1", "v2")):
    """B5 with the field t and one MIGRATE STEP `rename o -> t` (F3, F3b, F3c, F4)."""
    T, k, o, t = N.T, N.k, N.o, N.t
    return [("type Order { order_id: String }\n", None), (declaration(N, (k, t)), "type"),
            ("migrate %s %s -> %s { rename %s -> %s }\n" % (T, numbers[0], numbers[1], o, t), "s12"),
            ("type %s { reason: String }\n" % N.E, None), ("\n", None)] + tail(N, (k, t))


def m3_segments(N, mark=None):
    T, k, t = N.T, N.k, N.t
    mark = N.M if mark is None else mark
    return [("// EXPERIMENT 0004 slice 5: a VERSION MARK without a MIGRATE CHAIN (source M3).\n", None),
            ("type Order { order_id: String }\n", None), (declaration(N, (k, t), mark), "type"),
            ("type %s { reason: String }\n" % N.E, None), ("\n", None)] + tail(N, (k, t))


def q_segments(N, top=4, mark=None):
    """Q4 (slice 4 Q4 after W1 and W2, revision 9.1 comment): steps v(top-3) -> ... -> v(top), the slice 4
    layout (comments above and below the dead steps, a blank line, a multi-line block, no final newline)."""
    T, k, o, t, c, x = N.T, N.k, N.o, N.t, N.c, N.x
    a = top - 3
    return [("// EXPERIMENT 0004 slice 5: a MIGRATE CHAIN of four TYPE VERSIONS (sources Q4, Q4s, Q4z).\n", None),
            ("type Order { order_id: String }\n", None), (declaration(N, (k, t, x), mark), "type"),
            ("// The first two MIGRATE STEPS are DEAD LINES when no record has v%d or older.\n" % (a + 1), None),
            ("migrate %s v%d -> v%d { rename %s -> %s }\n" % (T, a, a + 1, o, t), "s12"), ("\n", None),
            ("migrate %s v%d -> v%d {\n  add %s: String = %s\n}\n" % (T, a + 1, a + 2, c, literal(N.cw)), "s23"),
            ("// The last MIGRATE STEP is a DEAD LINE when only its target version is stored.\n", None),
            ("migrate %s v%d -> v%d { drop %s: String, add %s: String = %s }\n"
             % (T, a + 2, a + 3, c, x, literal(N.cx)), "s34"),
            ("type %s { reason: String }\n" % N.E, None), ("\n", None)] + tail(N, (k, t, x), final_newline=False)


def c2_segments(N):
    T, k, o, t = N.T, N.k, N.o, N.t
    return [("// EXPERIMENT 0004 slice 5: one MIGRATE STEP (source C2, the slice 4 C2 after W1 and W2).\n", None),
            ("type Order { order_id: String }\n", None), (declaration(N, (k, t)), "type"),
            ("migrate %s v1 -> v2 { rename %s -> %s }\n" % (T, o, t), "s12"),
            ("type %s { reason: String }\n" % N.E, None), ("\n", None)] + tail(N, (k, t))


def note_segments(N):
    """Q4 plus an unused record TYPE with its own chain (F26), declared after the error TYPE."""
    segs = q_segments(N)
    at = next(i for i, (text, _) in enumerate(segs) if text.startswith("type %s " % N.E)) + 1
    segs[at:at] = [("type %s { %s: String %s: String }\n" % (N.note, N.nf, N.c), "type-note"),
                   ("migrate %s v1 -> v2 { add %s: String = %s }\n" % (N.note, N.c, literal(N.nc)), "n12")]
    return segs


def t23_segments(N, layout):
    """Type line layouts (README, T23). Every layout is Q4 (v1 to v4) with another form of the declaration of T."""
    T, k, t, x = N.T, N.k, N.t, N.x
    segs = q_segments(N)
    at = next(i for i, (_, tag) in enumerate(segs) if tag == "type")
    body = "{ %s: String %s: String %s: String }" % (k, t, x)
    if layout == "T23-block":
        segs[at] = ("type %s {\n  %s: String\n  %s: String\n  %s: String\n}\n" % (T, k, t, x), "type")
    elif layout == "T23-comment":
        segs[at] = ("type %s // the newest TYPE VERSION follows from the MIGRATE CHAIN\n%s\n" % (T, body), "type")
    elif layout == "T23-nospace":
        segs[at] = ("type %s%s\n" % (T, body), "type")
    elif layout == "T23-tab":
        segs[at] = ("type %s\t%s\n" % (T, body), "type")
    elif layout == "T23-last":
        moved = segs.pop(at)
        segs[-1] = (segs[-1][0] + "\n", None)
        segs.append((moved[0].rstrip("\n"), "type"))
    elif layout == "T23-below":
        moved = segs.pop(at)
        below = next(i for i, (_, tag) in enumerate(segs) if tag == "s34") + 1
        segs.insert(below, moved)
    elif layout == "T23-oneline":
        segs[at - 1:at + 1] = [("type Order { order_id: String } type %s %s\n" % (T, body), "type")]
    elif layout == "T23-prefix":
        error = next(i for i, (text, _) in enumerate(segs) if text.startswith("type %s " % N.E))
        segs.insert(at, segs.pop(error))
    elif layout == "T23-commented":
        segs.insert(at, ("// type %s { %s: String %s: String } was the first TYPE VERSION\n" % (T, k, N.o), None))
    else:
        raise KeyError(layout)
    return segs


def crlf(segs):
    return [(text.replace("\n", "\r\n"), tag) for text, tag in segs]


def segments(N, kind):
    """Segments of `kind`. A suffix `+crlf` changes the line ends of any kind to CRLF."""
    if kind.endswith("+crlf"):
        return crlf(segments(N, kind[:-len("+crlf")]))
    if kind == "Q4-crlf":
        return crlf(q_segments(N))
    if kind.startswith("T23-"):
        return t23_segments(N, kind)
    return {"B5": lambda: b5_segments(N), "B5c": lambda: b5c_segments(N), "M3": lambda: m3_segments(N),
            "Q4": lambda: q_segments(N),
            "Q4s": lambda: [s for s in q_segments(N, N.V, N.V) if s[1] not in ("s12", "s23")],
            "Q4z": lambda: [s for s in q_segments(N, N.V, N.V) if s[1] not in ("s12", "s23", "s34")],
            "C2": lambda: c2_segments(N), "Q4+note": lambda: note_segments(N)}[kind]()


def insert_mark(text, name, version):
    """README step 3: ` v<n>` directly after the last byte of the TYPE name of the `type` declaration."""
    new, count = re.subn(r"(\btype[ \t]+%s)(?![A-Za-z0-9_])" % re.escape(name), r"\g<1> v%d" % version, text, count=1)
    assert count == 1, (text, name)
    return new


def source_text(N, kind, without=(), marks=None):
    """The source text without the segments tagged `without`; `marks` maps a tag to (TYPE name, version)."""
    marks = marks or {}
    return "".join(insert_mark(text, *marks[tag]) if tag in marks else text
                   for text, tag in segments(N, kind) if tag not in without)


def base_form(text):
    """The same source in the base syntax (`interface`, plain numbers, no mark). For R-EQ and the self-check."""
    text = re.sub(r"\btype(?=[ \t]+[A-Z])", "interface", text)
    text = re.sub(r"(\binterface[ \t]+\w+) v\d+", r"\1", text)
    return re.sub(r"(\bmigrate[ \t]+\w+[ \t]+)v(\d+)([ \t]*->[ \t]*)v(\d+)", r"\1\2\3\4", text)


def fixture_path(kind):
    return EXPERIMENT / "slice5" / kind / "orders.beaml"


# RESPONSE RECORDS (README, Cases (slice 5)): field roles per TYPE VERSION form, bodies per role set.
BODIES = {"ko": [{"k": "order-1", "o": "authorized"}], "kt": [{"k": "order-1", "t": "settled"}],
          "ktc": [{"k": "order-1", "t": "settled", "c": "app"}, {"k": "order-1", "t": "pending", "c": "web"}],
          "ktx": [{"k": "order-1", "t": "settled", "x": "r-4"}, {"k": "order-1", "t": "pending", "x": "r-5"}]}


def make_record(N, version, roles, index=0, name=None):
    """A RESPONSE RECORD of stored/v1.jsonl with operation op, TYPE VERSION (name or T, version, roles)."""
    record = dict(st.v1_record(), operation=N.op, trace_id="%032x" % (0x5e1ce5 + index))
    record["type"] = st.type_version(name or N.T, version, [getattr(N, r) for r in roles])
    forms = BODIES[roles]
    return st.with_value(record, {getattr(N, role): value for role, value in forms[index % len(forms)].items()})


def snapshot_bytes(N, spec):
    """`spec` is a list of (version, roles). The records get indexes in list order."""
    return "".join(json.dumps(make_record(N, v, roles, i), separators=(",", ":"), ensure_ascii=False) + "\n"
                   for i, (v, roles) in enumerate(spec)).encode()


PATH = object()  # Token marker: the --stored path of the case.


class Slice5:
    """Shared plumbing for the build and removal cases. A subclass sets `names` and `fixture_based`."""
    maxDiff = None
    fixture_based = False

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s5-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def ctx(self, *parts):
        return " ".join(str(p) for p in parts) + str(self.names)

    def source_bytes(self, kind):
        if self.fixture_based and kind in FIXTURE_KINDS:
            return fixture_path(kind).read_bytes()
        return source_text(self.names, kind).encode()

    def write_source(self, text, label):
        path = self.work / ("%s-%s" % (re.sub(r"[^A-Za-z0-9]", "_", label), random.randrange(10 ** 8))) / "orders.beaml"
        path.parent.mkdir()
        path.write_bytes(text.encode() if isinstance(text, str) else text)
        return path

    def source(self, kind):
        if self.fixture_based and kind in FIXTURE_KINDS:
            return fixture_path(kind)
        return self.write_source(source_text(self.names, kind), kind)

    def snapshot(self, spec):
        if not spec and self.fixture_based:
            return EXPERIMENT / "stored" / "empty.jsonl"
        path = self.work / ("snapshot-%s.jsonl" % random.randrange(10 ** 8))
        path.write_bytes(snapshot_bytes(self.names, spec))
        return path

    def run_compiler(self, argv, cwd=None):
        result = subprocess.run([st.compiler()] + [str(a) for a in argv], cwd=cwd or self.work / "cwd",
                                capture_output=True)
        return result.returncode, result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")

    def compile(self, source, spec=()):
        """Build `source` (a kind or a Path) with `--stored` of `spec`. Return (code, stdout, stderr, source, stored)."""
        path = source if isinstance(source, Path) else self.source(source)
        stored = self.snapshot(list(spec))
        code, stdout, stderr = self.run_compiler([path, "--stored", stored])
        return code, stdout, stderr, str(path), str(stored)

    def assert_rejected(self, source, spec, tokens, absent=(), label=""):
        code, stdout, stderr, path, stored = self.compile(source, spec)
        tokens = [stored if t is PATH else t for t in tokens]
        self.assertEqual(
            (1, "", [], []),
            (code, stdout, [t for t in tokens if t not in stderr], [a for a in absent if a in stderr]),
            self.ctx(label or source, "expected exit 1 (not a crash), no stdout, tokens (missing, unexpected);",
                     "stderr:", stderr))
        return stderr

    def assert_built(self, source, spec, warnings_allowed=False, label=""):
        code, stdout, stderr, path, stored = self.compile(source, spec)
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout),
                         self.ctx(label or source, "expected exit 0 and Elixir on stdout; stderr:", stderr))
        if not warnings_allowed:
            self.assertNotIn("warning:", stderr, self.ctx(label or source, "expected no warning"))
        return stdout, stderr


def record_versions(stdout):
    """The `version` values of the generated RESPONSE RECORD `type` maps (`%{name: ..., version: N, ...}`)."""
    return [int(v) for v in re.findall(r"version: (\d+), fields:", stdout)]


class Slice5Syntax(Slice5):
    # F1: B5 builds and its output equals the base output of the same source in the base syntax (R-EQ).
    def test_F01_B5_builds_and_equals_the_base_output(self):
        N = self.names
        source = self.source("B5")
        new_text = source.read_bytes()
        old_text = base_form(new_text.decode()).encode()
        old = self.write_source(old_text, "B5-base")
        stored = EXPERIMENT / "stored" / "empty.jsonl"
        base = run_base([old.name, "--stored", stored], old.parent)
        pre = run_at(PRE_6A, [source.name, "--stored", stored], source.parent)
        new = run_new([source.name, "--stored", stored], source.parent)
        self.assertEqual((0, 0, 0), (base[0], pre[0], new[0]), self.ctx("F1 exit codes (base, pre 6a, new):", new[2]))
        self.assertEqual((shift_offsets(base[1], old_text, new_text), base[2]), (pre[1], pre[2]),
                         self.ctx("F1: pre 6a stdout equal after the offset shift, stderr equal"))
        self.assertEqual(run_at(PIN, [source.name, "--stored", stored], source.parent), new,
                         self.ctx("F1: the output equals the PIN compiler output"))
        self.assertIn("type %s {" % N.T, new_text.decode(), "B5 uses type")

    # F2: `interface` is a hard error with a help line, at each declaration position.
    def test_F02_interface_is_an_error_with_a_help_line_at_each_position(self):
        N = self.names
        text = source_text(N, "B5")
        for name in ("Order", N.T, N.E):
            with self.subTest(position=name):
                head = "type %s {" % name
                at = text.index(head)
                bad = text[:at] + "interface" + text[at + len("type"):]
                byte = len(bad[:at].encode())
                stderr = self.assert_rejected(self.write_source(bad, "F2"), [], [
                    "interface", "type %s {" % name, "help:", "behaviour contracts", "at byte %d" % byte],
                    label="F2 " + name)
                # Revision 9.2: the exact help line of the README block, not only its tokens.
                self.assertIn("help: declare: type %s { ... }" % name, [line.strip() for line in stderr.splitlines()],
                              self.ctx("F2 %s: the exact line `help: declare: type %s { ... }`;" % (name, name), stderr))

    def test_F02_fallback_error_names_every_declaration_word(self):
        # Revision 9.1: the text that cli.rs line 208 checks for absence is the real fallback error.
        text = source_text(self.names, "B5").replace("type Order {", "record Order {", 1)
        self.assert_rejected(self.write_source(text, "F2-fallback"), [], [FALLBACK], label="F2 fallback")

    # F3, F3b, F3c: plain numbers.
    def test_F03_plain_numbers_in_migrate_are_an_error(self):
        T = self.names.T
        text = source_text(self.names, "B5c").replace("migrate %s v1 -> v2" % T, "migrate %s 1 -> 2" % T, 1)
        self.assert_rejected(self.write_source(text, "F3"), [], [
            "migrate %s 1" % T, "needs v", "help: write: migrate %s v1 -> v2" % T], label="F3")

    def test_F03b_mixed_numbers_name_v2(self):
        T = self.names.T
        text = source_text(self.names, "B5c").replace("migrate %s v1 -> v2" % T, "migrate %s v1 -> 2" % T, 1)
        self.assert_rejected(self.write_source(text, "F3b"), [], [
            "needs v", "help: write: migrate %s v1 -> v2" % T], label="F3b migrate")

    def test_F03b_plain_number_on_the_type_line_is_an_error(self):
        T = self.names.T
        text = source_text(self.names, "B5").replace("type %s {" % T, "type %s 3 {" % T, 1)
        self.assert_rejected(self.write_source(text, "F3b-type"), [], [
            "expected '{' or a VERSION MARK v<number>", "help: write: type %s v3" % T], label="F3b type line")

    def test_F03c_control_v_numbers_build(self):
        self.assert_built(self.write_source(source_text(self.names, "B5c"), "F3c"), [], warnings_allowed=True,
                          label="F3c")

    # F4: VERSION faults in both positions.
    def test_F04_version_faults_on_the_type_line_and_in_migrate(self):
        N = self.names
        faults = {"v0": "versions start at v1", "v03": "write v3", "V3": "v<number>", "v": "v<number>",
                  "v3x": "v<number>", "v4294967296": "version number too large", "v-1": "unsupported token"}
        b5, b5c = source_text(N, "B5"), source_text(N, "B5c")
        for fault, token in faults.items():
            texts = {"type line": b5.replace("type %s {" % N.T, "type %s %s {" % (N.T, fault), 1),
                     "migrate from": b5c.replace("migrate %s v1 ->" % N.T, "migrate %s %s ->" % (N.T, fault), 1),
                     "migrate to": b5c.replace("-> v2 {", "-> %s {" % fault, 1)}
            for position, text in texts.items():
                with self.subTest(fault=fault, position=position):
                    self.assert_rejected(self.write_source(text, "F4"), [], [token],
                                         label="F4 %s %s" % (fault, position))

    # F5: a field that looks like a version stays a field.
    def test_F05_fields_named_like_versions_stay_fields(self):
        N = self.names
        v1, v2, v3 = N.vf
        text = "".join([
            "type Order { order_id: String }\n", "type %s { %s: String %s: String %s: String }\n" % (N.T, N.k, v1, v2),
            "migrate %s v1 -> v2 { rename %s -> %s }\n" % (N.T, v3, v1), "type %s { reason: String }\n" % N.E, "\n"]
            + [seg for seg, _ in tail(N, (N.k, v1, v2))])
        self.assert_built(self.write_source(text, "F5"), [], warnings_allowed=True, label="F5")

    # F7: a squashed source builds with records of the step start.
    def test_F07_Q4s_with_records_of_its_chain_start_builds_without_warning(self):
        V = self.names.V
        stdout, _ = self.assert_built("Q4s", [(V - 1, "ktc"), (V - 1, "ktc")], label="F7")
        self.assertEqual([V], sorted(set(record_versions(stdout))),
                         self.ctx("F7: the generated record writes the newest version as an integer"))

    # F8, F8b: mark and chain disagree (M1).
    def mark_edited(self, kind, mark):
        N = self.names
        text = source_text(N, kind)
        return re.sub(r"(\btype %s) v\d+" % re.escape(N.T), r"\g<1> v%d" % mark, text, count=1)

    def test_F08_mark_below_the_chain_end_is_M1(self):
        N = self.names
        V = N.V
        self.assert_rejected(self.write_source(self.mark_edited("Q4s", V - 1), "F8"), [], [
            "type %s v%d" % (N.T, V - 1), "migrate %s v%d -> v%d" % (N.T, V - 1, V), "must agree",
            "write: type %s v%d" % (N.T, V)], label="F8")

    def test_F08b_mark_above_the_chain_end_is_M1(self):
        N = self.names
        V = N.V
        self.assert_rejected(self.write_source(self.mark_edited("Q4s", V + 1), "F8b"), [], [
            "type %s v%d" % (N.T, V + 1), "migrate %s v%d -> v%d" % (N.T, V - 1, V), "must agree",
            "add migrate %s v%d -> v%d" % (N.T, V, V + 1), "type %s v%d" % (N.T, V)], label="F8b")

    def test_F08c_chain_with_a_gap_is_an_error(self):
        # O7 option (a) (DL-080): a gap stays an error; only option (c) would have changed it.
        T = self.names.T
        text = source_text(self.names, "Q4", without=("s23",))
        self.assert_rejected(self.write_source(text, "F8c"), [], [
            "must count without gaps", "migrate %s v3 -> v4" % T, "expected v2 -> v3"], label="F8c")

    # F9, F10, F11, F11b: M3 (a mark without a chain).
    def test_F09_M3_builds_and_writes_its_mark_as_the_version(self):
        stdout, _ = self.assert_built("M3", [], label="F9")
        self.assertEqual([self.names.M], sorted(set(record_versions(stdout))),
                         self.ctx("F9: the generated record writes the VERSION MARK as an integer"))

    def test_F10_M3_with_older_records_names_the_missing_steps(self):
        N = self.names
        M, s = N.M, N.M - 2
        self.assert_rejected("M3", [(s, "ko")], [
            N.T, "starts at v%d" % M, "TYPE VERSION v%d" % s, "version control",
            "migrate %s v%d -> v%d" % (N.T, s, s + 1), "migrate %s v%d -> v%d" % (N.T, s + 1, M), PATH], label="F10")

    def test_F11_M3_with_records_of_its_mark_builds_without_warning(self):
        self.assert_built("M3", [(self.names.M, "kt"), (self.names.M, "kt")], label="F11")

    def test_F11b_other_fingerprint_gets_a_help_line_with_the_step_and_the_mark(self):
        N = self.names
        M = N.M
        step = "migrate %s v%d -> v%d { rename %s -> %s }" % (N.T, M, M + 1, N.o, N.t)
        mark = "write: type %s v%d" % (N.T, M + 1)
        stderr = self.assert_rejected("M3", [(M, "ko")], [NO_PATH, step, mark, PATH], label="F11b")
        self.assertTrue([line for line in stderr.splitlines() if "help:" in line and step in line and mark in line],
                        self.ctx("F11b: the step and the mark are in one help line;", stderr))

    # F12, F12b, F12c: a stored version newer than the newest version (N1).
    def n1_tokens(self, stored, newest):
        return ["TYPE VERSION v%d" % stored, "newer than", "TYPE VERSION v%d" % newest, "only grow", PATH]

    def assert_whole_versions(self, stderr, *versions):
        # Revision 9.2: `TYPE VERSION v1` must stand as a whole token, not inside `TYPE VERSION v1NNN`.
        missing = [v for v in versions if not re.search(r"TYPE VERSION v%d(?![0-9])" % v, stderr)]
        self.assertEqual([], missing, self.ctx("N1: TYPE VERSION v<n> as a whole token;", stderr))

    def test_F12_record_newer_than_the_mark_is_N1(self):
        N = self.names
        stderr = self.assert_rejected("M3", [(N.M + 2, "kt")], self.n1_tokens(N.M + 2, N.M), label="F12")
        self.assert_whole_versions(stderr, N.M + 2, N.M)

    def test_F12_control_the_same_record_against_a_higher_mark_builds(self):
        N = self.names
        source = self.write_source("".join(t for t, _ in m3_segments(N, N.M + 2)), "F12-control")
        self.assert_built(source, [(N.M + 2, "kt")], label="F12 control")

    def test_F12b_lowered_mark_without_chain_is_N1(self):
        # Revision 9.1: Q4z with the mark lowered by one (a reset), records of the old mark. No O7 dependence.
        N = self.names
        V = N.V
        stderr = self.assert_rejected(self.write_source(self.mark_edited("Q4z", V - 1), "F12b"), [(V, "ktx")],
                                      self.n1_tokens(V, V - 1), label="F12b")
        self.assert_whole_versions(stderr, V, V - 1)

    def test_F12c_record_newer_than_a_source_without_mark_and_chain_is_N1(self):
        N = self.names
        stderr = self.assert_rejected("B5", [(N.r, "ko")], self.n1_tokens(N.r, 1), absent=[
            "migrate %s v%d -> v2" % (N.T, N.r), "migrate %s %d -> 2" % (N.T, N.r)], label="F12c")
        self.assertNotIn("declare: migrate", stderr, self.ctx("F12c: no help line that counts backwards"))
        self.assert_whole_versions(stderr, N.r, 1)

    def test_F12d_record_of_another_name_newer_than_the_mark_is_N1(self):
        # Slice 5 final review, medium 1: N1 fired only when the stored TYPE name equals the source name. A record of
        # another name (a prefix of T) at v(V+2) against `type T vV` got a help line that counts backwards.
        N = self.names
        V, other = N.V, N.T[:3]
        stored = self.work / ("snapshot-%s.jsonl" % random.randrange(10 ** 8))
        stored.write_bytes((json.dumps(make_record(N, V + 2, "kt", name=other), separators=(",", ":"),
                                       ensure_ascii=False) + "\n").encode())
        for kind in ("Q4z", "Q4s"):
            with self.subTest(kind=kind):
                code, stdout, stderr = self.run_compiler([self.source(kind), "--stored", stored])
                backwards = [m.group(0) for m in re.finditer(r"migrate \S+ v(\d+) -> v(\d+)", stderr)
                             if int(m.group(2)) < int(m.group(1))]
                lower = [m.group(0) for m in re.finditer(r"type \S+ v(\d+)", stderr) if int(m.group(1)) < V + 2
                         and "write:" in stderr[max(0, m.start() - 8):m.start()]]
                tokens = [str(stored) if t is PATH else t for t in self.n1_tokens(V + 2, V)]
                self.assertEqual((1, "", [], [], []),
                                 (code, stdout, [t for t in tokens if t not in stderr], backwards, lower),
                                 self.ctx("F12d %s: exit 1, no stdout, N1 tokens (missing), backwards steps, "
                                          "lower `write: type` marks;" % kind, "stderr:", stderr))
                self.assert_whole_versions(stderr, V + 2, V)
                self.assertIn("the stored TYPE name %s is not %s" % (other, N.T), stderr,
                              self.ctx("F12d %s: the name mismatch stays visible;" % kind, stderr))

    # F15: the largest version number.
    def test_F15_largest_version_has_no_newer_version_and_no_panic(self):
        N = self.names
        source = self.write_source("".join(t for t, _ in m3_segments(N, U32_MAX)), "F15")
        self.assert_rejected(source, [(U32_MAX, "ko")], ["no newer version", "v%d" % U32_MAX], absent=["panicked"],
                             label="F15")

    # O7 option (a) (DL-080): every VERSION MARK that agrees with the MIGRATE CHAIN is legal, and a chain without a
    # mark is legal. None of these gives the option (b) or (c) help line.
    O7_REFUSALS = ["remove the VERSION MARK", "must agree", "write: type"]

    def assert_o7_built(self, source, spec, version, label):
        stdout, stderr = self.assert_built(source, spec, label=label)
        self.assertEqual([version], sorted(set(record_versions(stdout))),
                         self.ctx(label, "the generated record writes the newest version as an integer"))
        self.assertEqual([], [t for t in self.O7_REFUSALS if t in stderr], self.ctx(label, "no O7 refusal;", stderr))

    def test_F06_mark_beside_a_chain_from_v1_builds(self):
        N = self.names
        # v1 records keep every MIGRATE STEP live, so the build has no DEAD LINE warning.
        source = self.write_source(source_text(N, "Q4", marks={"type": (N.T, 4)}), "F6")
        self.assert_o7_built(source, [(1, "ko")], 4, "F6")

    def test_F06_control_the_same_chain_with_another_mark_is_M1(self):
        # Option (a) still checks agreement: the F6 source with `v3` gives M1.
        N = self.names
        source = self.write_source(source_text(N, "Q4", marks={"type": (N.T, 3)}), "F6-control")
        self.assert_rejected(source, [], ["type %s v3" % N.T, "migrate %s v3 -> v4" % N.T, "must agree",
                                          "write: type %s v4" % N.T], label="F6 control")

    def test_F13_mark_v1_without_chain_builds(self):
        source = self.write_source("".join(t for t, _ in m3_segments(self.names, 1)), "F13")
        self.assert_o7_built(source, [], 1, "F13")

    def test_F13_control_a_v2_record_against_mark_v1_is_N1(self):
        source = self.write_source("".join(t for t, _ in m3_segments(self.names, 1)), "F13-control")
        stderr = self.assert_rejected(source, [(2, "kt")], self.n1_tokens(2, 1), label="F13 control")
        self.assert_whole_versions(stderr, 2, 1)

    def test_F14_chain_above_v1_without_mark_builds(self):
        source = self.write_source(source_text(self.names, "Q4", without=("s12", "s23")), "F14")
        self.assert_o7_built(source, [(3, "ktc")], 4, "F14")

class Fixture(Slice5Syntax, unittest.TestCase):
    names, fixture_based = FIXTURE_NAMES, True

    def test_fixtures_equal_the_template_byte_for_byte(self):
        # Guard, not RED: every slice5 fixture is the template with the fixture names.
        N = FIXTURE_NAMES
        for kind in FIXTURE_KINDS:
            with self.subTest(kind=kind):
                self.assertEqual(source_text(N, kind).encode(), fixture_path(kind).read_bytes())
        self.assertEqual((EXPERIMENT / "arms/gen/orders.beaml").read_text(), source_text(N, "B5"),
                         "B5 is the slice 1 source with type")
        self.assertEqual(source_text(N, "Q4", without=("s12", "s23"), marks={"type": (N.T, 4)}),
                         source_text(N, "Q4s"), "Q4s is Q4 after F20")
        self.assertEqual(source_text(N, "Q4", without=("s12", "s23", "s34"), marks={"type": (N.T, 4)}),
                         source_text(N, "Q4z"), "Q4z is Q4 after F21")
        data = fixture_path("Q4-crlf").read_bytes()
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"), "Q4-crlf holds CRLF only")


class Template(Slice5Syntax, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.names = random_names()


# Base compiler and R-EQ helpers (README, "Rewrite equivalence R-EQ (A2, revision 9.1)").
_BINARIES = {}


def compiler_at(commit):
    """The compiler of `commit`, built from `git archive` in a scratch directory (no checkout)."""
    if commit not in _BINARIES:
        holder = tempfile.mkdtemp(prefix="beaml-0004-s5-%s-" % commit)
        archive = subprocess.run(["git", "-C", str(REPO), "archive", commit, COMPILER_PATH], capture_output=True,
                                 check=True).stdout
        subprocess.run(["tar", "-x", "-C", holder], input=archive, check=True)
        manifest = Path(holder) / COMPILER_PATH / "Cargo.toml"
        subprocess.run(["cargo", "build", "--offline", "--quiet", "--manifest-path", str(manifest),
                        "--target-dir", str(Path(holder) / "target")], check=True)
        _BINARIES[commit] = str(Path(holder) / "target/debug/beaml-spike")
        print("compiler %s:" % commit, _BINARIES[commit], file=sys.stderr)
    return _BINARIES[commit]


def base_compiler():
    return compiler_at(BASE)


def run_binary(binary, argv, cwd):
    result = subprocess.run([binary] + [str(a) for a in argv], cwd=cwd, capture_output=True)
    return result.returncode, result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")


def run_base(argv, cwd):
    return run_binary(base_compiler(), argv, cwd)


def run_at(commit, argv, cwd):
    return run_binary(compiler_at(commit), argv, cwd)


def run_new(argv, cwd):
    return run_binary(st.compiler(), argv, cwd)


def shift_offsets(stdout, old, new):
    """Move each `beaml-declaration-v1` offset of `stdout` (bytes of `old`) by the byte difference of the changed
    lines of `new` before it. An offset inside a changed line is an error (the rewrite moved a declaration).
    Offsets are byte offsets: text is measured as UTF-8."""
    old, new = [t.encode() if isinstance(t, str) else t for t in (old, new)]
    old_lines, new_lines = old.splitlines(keepends=True), new.splitlines(keepends=True)
    if len(old_lines) != len(new_lines):
        return "<line count changed: %d -> %d>" % (len(old_lines), len(new_lines))
    starts, at = [], 0
    for line in old_lines:
        starts.append(at)
        at += len(line)
    new_starts, at = [], 0
    for line in new_lines:
        new_starts.append(at)
        at += len(line)

    def move(offset):
        offset = int(offset)
        i = max(0, bisect.bisect_right(starts, offset) - 1)
        if i >= len(old_lines):
            return str(offset - len(old) + len(new))
        col = offset - starts[i]
        if col and old_lines[i] != new_lines[i]:
            return "<offset %d inside a rewritten line>" % offset
        return str(new_starts[i] + col)

    return re.sub(r"(# beaml-declaration-v1 \S+) (\d+) (\d+)",
                  lambda m: "%s %s %s" % (m.group(1), move(m.group(2)), move(m.group(3))), stdout)


# Closed normaliser S (README revision 9.1): exact base strings and their new strings.
NORMALISER_S = [("migrate Payment 1 -> 2", "migrate Payment v1 -> v2"),
                ("migrate Payment 2 -> 3", "migrate Payment v2 -> v3"),
                ("has version 1 or older", "has v1 or older"), ("has version 2 or older", "has v2 or older"),
                ("is not in Payment 2", "is not in Payment v2")]


def normalise(stderr):
    for old, new in NORMALISER_S:
        stderr = stderr.replace(old, new)
    return stderr


def without_last_step_warnings(stderr, text):
    """Drop the DEAD LINE warning block of the last MIGRATE STEP of each chain (DL-070, empty snapshot)."""
    last = {}
    for m in re.finditer(r"\bmigrate[ \t]+(\w+)[ \t]+v(\d+)[ \t]*->[ \t]*v(\d+)", text):
        last[m.group(1)] = "warning: DEAD LINE: migrate %s v%s -> v%s" % m.groups()
    heads = set(last.values())
    kept, skipping = [], False
    for line in stderr.splitlines(keepends=True):
        if not line.startswith(" "):
            skipping = line.rstrip("\r\n") in heads
        if not skipping:
            kept.append(line)
    return "".join(kept)


OLD_FORM = re.compile(r"(?m)^(?![ \t]*//).*?(\binterface[ \t]+[A-Z]|\bmigrate[ \t]+\w+[ \t]+\d)")
REWRITE_SKIP = {EXPERIMENT_REL + "/syntax-options.beaml", EXPERIMENT_REL + "/examples/order-flow.beaml"}


def git(*args):
    return subprocess.run(["git", "-C", str(REPO)] + list(args), capture_output=True, check=True).stdout


def rewrite_sources():
    """Every `.beaml` file of the rewrite scope under experiments/ at the base commit."""
    names = git("ls-tree", "-r", "--name-only", BASE, "--", "experiments").decode().splitlines()
    return [n for n in names if n.endswith(".beaml") and "/results/" not in n and n not in REWRITE_SKIP]


class Rewrite(unittest.TestCase):
    """P1, A2, A3: checks of the one-time rewrite against the base commit."""
    maxDiff = None
    SNAPSHOT = EXPERIMENT_REL + "/tests/payments.generated.snapshot"
    PAYMENTS = "experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml"

    def test_P1_payments_snapshot_differs_in_one_offset_line_and_matches_the_build(self):
        old = git("show", "%s:%s" % (BASE, self.SNAPSHOT)).decode().splitlines(keepends=True)
        new = (REPO / self.SNAPSHOT).read_text().splitlines(keepends=True)
        changed = [line for line in difflib.unified_diff(old, new, n=0)
                   if line[:1] in "+-" and not line.startswith(("+++", "---"))]
        self.assertEqual(["-  # beaml-declaration-v1 authorize 91 193\n", "+  # beaml-declaration-v1 authorize 81 183\n"],
                         changed, "P1: the new snapshot differs from the base snapshot in exactly one line")
        old_source = git("show", "%s:%s" % (BASE, self.PAYMENTS))
        new_source = (REPO / self.PAYMENTS).read_bytes()
        at_old, at_new = old_source.index(b"\nfn authorize "), new_source.index(b"\nfn authorize ")
        self.assertEqual((2 * (9 - 4), old_source[at_old:], base_form(new_source.decode()).encode()),
                         (at_old - at_new, new_source[at_new:], old_source),
                         "P1: payments.beaml changes only by W1, 10 bytes before fn authorize")
        code, stdout, stderr = run_new([REPO / self.PAYMENTS], REPO)
        self.assertEqual((0, "".join(new), ""), (code, stdout, stderr), "P1: the build equals the new snapshot")

    def test_A2_rewritten_sources_build_like_the_base(self):
        holder = Path(tempfile.mkdtemp(prefix="beaml-0004-s5-a2-"))
        self.addCleanup(shutil.rmtree, holder)
        empty = EXPERIMENT / "stored" / "empty.jsonl"
        for relative in rewrite_sources():
            with self.subTest(source=relative):
                old = git("show", "%s:%s" % (BASE, relative))
                path = REPO / relative
                self.assertTrue(path.is_file(), "A2: %s was deleted" % relative)
                new = path.read_bytes()
                self.assertIsNone(OLD_FORM.search(new.decode()), "A2: %s is not rewritten (W1, W2)" % relative)
                for side, data in (("old", old), ("new", new)):
                    target = holder / side / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                stored = ["--stored", empty] if re.search(rb"(?m)^[ \t]*(effect|retire)[ \t]", old) else []
                base = run_base([relative] + stored, holder / "old")
                pre = run_at(PRE_6A, [relative] + stored, holder / "new")
                now = run_new([relative] + stored, holder / "new")
                if base[0] == 0:
                    self.assertEqual(
                        (0, shift_offsets(base[1], old.decode(), new.decode()), normalise(base[2])),
                        (pre[0], pre[1], without_last_step_warnings(pre[2], new.decode())),
                        "A2 %s: pre 6a exit, stdout after the offset shift, stderr after S and DL-070" % relative)
                else:
                    first = lambda text: (text.splitlines() or [""])[0]  # noqa: E731
                    self.assertEqual((base[0], normalise(first(base[2]))), (pre[0], first(pre[2])),
                                     "A2 %s: pre 6a, the same error class (exit, first line after S)" % relative)
                # 0005 P4 GREEN: a db EFFECT source changes its text on purpose (S13: bad/unsupported_effect_kind.beaml).
                if not re.search(rb"= *db\.\w+\(", new):
                    self.assertEqual(run_at(PIN, [relative] + stored, holder / "new"), now,
                                     "A2 %s: exit, stdout and stderr equal the PIN compiler" % relative)

    def test_A3_stored_fixtures_are_unchanged(self):
        # Guard, not RED: every stored fixture keeps its records. Slice 6b step 6a (D6B-69) converts each record to
        # version 2 in place: the BASE record with its body as `value` (st.with_value) equals the record now.
        # RECORD FORMAT v3 (DL-143) converts that version 2 record once more with convert_v3.py (QV3-5 A).
        sys.path.insert(0, str(EXPERIMENT / "workflow" / "2026-11-07" / "record-format-v3"))
        import convert_v3
        prefix = EXPERIMENT_REL + "/stored/"
        names = [n for n in git("ls-tree", "-r", "--name-only", BASE, "--", prefix).decode().splitlines()
                 if n.endswith(".jsonl")]
        now = sorted(prefix + p.name for p in (EXPERIMENT / "stored").glob("*.jsonl"))
        self.assertEqual(sorted(names), now, "A3: the same stored files")
        for name in names:
            with self.subTest(file=name):
                old = [json.loads(line) for line in git("show", "%s:%s" % (BASE, name)).decode().splitlines()]
                converted = [convert_v3.convert(dict(st.with_value(r, json.loads(base64.b64decode(r["body_base64"])),
                                                                   r["unknown_keys"]), version=2), False)
                             for r in old]
                self.assertEqual(converted, [json.loads(line) for line in (REPO / name).read_text().splitlines()])


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
