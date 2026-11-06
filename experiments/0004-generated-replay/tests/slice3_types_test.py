"""EXPERIMENT 0004 slice 3 (README revision 7.1): compile cases of `add` and `drop` in the MIGRATE CHAIN.

Cases D2, D2b, D3, D5, D5b, D5c, D6, D7, D7b, D12, D13, D15, D15b, K1-K12 and the builds of D1, D4, D11
and D14. The replay and live cases are in slice3_replay_test.py.
Each case runs twice:
  Fixture   the case sources in slice3/ and drift/, the RECORD SNAPSHOTS in stored/ or written per test;
  Template  the same sources and snapshots built from a template with random TYPE names, field names and
            constants. A random constant holds a quote, a backslash and a non-ASCII letter.
Expected tokens come from the README tables, written here; never from the compiler.
The fingerprint of a TYPE VERSION is the lower-case hex SHA-256 of the compact JSON of the field list
sorted by field name (README, slice 2).
Run: python3 -B experiments/0004-generated-replay/tests/slice3_types_test.py [-k NAME]
"""
import hashlib
import json
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
import stored_types_test as st  # noqa: E402

STRING_ONLY = "String fields only"
DROP_STRING_ONLY = "drop supports String fields only"
NOT_IN = "not in"
STILL_IN = "still in"
TWO_TIMES = "two times"
EMPTY_STEP = "at least one rename, add or drop"
PLACEHOLDER = "<constant>"


def type_version(name, version, fields):
    """`fields`: names (TYPE String) or (name, TYPE) pairs. README fingerprint rule."""
    pairs = sorted([f, "String"] if isinstance(f, str) else [f[0], f[1]] for f in fields)
    text = json.dumps(pairs, separators=(",", ":"))
    return {"name": name, "version": version, "fields": pairs,
            "fingerprint": hashlib.sha256(text.encode()).hexdigest()}


class Names:
    """TYPE T; fields k (order_id), o (status), x (reference), c (channel), t (state).
    Constants: cx (the `add x` constant), cw and cm (the M chain), cz (Z), cd (D15)."""

    def __init__(self, T, k, o, x, c, t, cx, cw, cm, cz, cd):
        self.T, self.k, self.o, self.x, self.c, self.t = T, k, o, x, c, t
        self.cx, self.cw, self.cm, self.cz, self.cd = cx, cw, cm, cz, cd

    def __str__(self):
        return " [names: " + " ".join("%s=%r" % kv for kv in vars(self).items()) + "]"


FIXTURE_NAMES = Names("Payment", "order_id", "status", "reference", "channel", "state",
                      "pre-v2", "web", "migrated", "new", "x")


def random_names():
    rng = random.Random()
    word = lambda prefix: prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(6))  # noqa: E731
    # A quote, a backslash and a non-ASCII letter: a constant written into the compiler or a wrong escape fails.
    const = lambda prefix: word(prefix) + '"\\é' + word("")  # noqa: E731
    return Names("Tq" + word(""), word("k_"), word("o_"), word("x_"), word("c_"), word("t_"),
                 const("cx"), const("cw"), const("cm"), const("cz"), const("cd"))


def literal(text):
    """A BEAML string literal of `text`."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def add(field, const, ty="String"):
    return "add %s: %s = %s" % (field, ty, literal(const))


def kinds(N):
    """Source kind -> (declared fields, MIGRATE STEPS as lists of MIGRATE CHANGE texts). README, Cases (slice 3)."""
    PE = "PaymentError"
    m_step1 = ["rename %s -> %s" % (N.o, N.t), add(N.c, N.cw)]
    return {
        "R-add": ([N.k, N.o, N.x], [[add(N.x, N.cx)]]),
        "R": ([N.k, N.o, N.x], []),
        "R2": ([N.k, N.o, N.x, N.c], []),
        "D-drop": ([N.k], [["drop %s: String" % N.o]]),
        "D": ([N.k], []),
        "N": ([N.k, N.t], []),
        "M": ([N.k, N.t, N.o], [m_step1, ["drop %s: String" % N.c, add(N.o, N.cm)]]),
        "M-nodrop": ([N.k, N.t, N.o], [m_step1, [add(N.o, N.cm)]]),
        "Z": ([N.k, N.o], [["drop %s: String" % N.o], [add(N.o, N.cz)]]),
        "D15": ([N.k, N.o], [[add(N.o, N.cd)]]),
        "D7": ([N.k], [["drop %s: %s" % (N.o, PE)]]),
        # K1-K12 (README, Consistency checks). A step given as one text is written as it is.
        "K1": ([N.k, N.o], [[add(N.c, N.cx)]]),
        "K2": ([N.k, N.o, N.x], [[add(N.x, N.cx, PE)]]),
        "K3": ([N.k, N.o, N.x], [["add %s: String = 5" % N.x]]),
        "K4": ([N.k, N.o, (N.x, PE)], [[add(N.x, N.cx, PE)]]),
        "K5": ([N.k, N.o], [["drop %s: String" % N.o]]),
        "K6": ([N.k], [["drop %s: Int" % N.o]]),
        "K7a": ([N.k, N.o], [["drop %s: String" % N.o, add(N.o, N.cx)]]),
        "K7b": ([N.k, N.t, N.o], [["rename %s -> %s" % (N.o, N.t), add(N.o, N.cx)]]),
        "K8": ([N.k, N.o], ["{ }"]),
        "K9": ([N.k, N.o, N.x], ["{ %s drop %s: String }" % (add(N.x, N.cx), N.c)]),
        "K10": ([N.k], ["{ drop %s: String, }" % N.o]),
        "K11": ([N.k, N.o, N.x], [["add %s: String" % N.x]]),
        "K12": ([N.k, N.o, N.x], [["%s = Money(%s, %s)" % (N.x, N.k, N.o)]]),
    }


FIXTURE_SOURCES = {kind: "slice3/%s/orders.beaml" % kind
                   for kind in ("R-add", "R2", "D-drop", "D", "M", "M-nodrop", "Z", "D15", "D7")}
FIXTURE_SOURCES.update({"R": "drift/R/orders.beaml", "N": "drift/N/orders.beaml"})


def template_source(N, kind):
    fields, steps = kinds(N)[kind]
    typed = [f if isinstance(f, tuple) else (f, "String") for f in fields]
    names = [f for f, _ in typed]
    chain = "".join("migrate %s %d -> %d %s\n" % (N.T, i + 1, i + 2,
                                                   step if isinstance(step, str) else "{ %s }" % ", ".join(step))
                    for i, step in enumerate(steps))
    return st.TEMPLATE % {
        "T": N.T, "declared": " ".join("%s: %s" % ft for ft in typed), "chain": chain,
        "pattern": ", ".join(names),
        "build": ", ".join(("%s: %s + \"\"" if i == 0 else "%s: %s") % (f, f) for i, f in enumerate(names))}


def snapshot_types(N, label):
    """RECORD SNAPSHOT label -> TYPE VERSIONS of its records (README, Cases (slice 3))."""
    return {"empty": [],
            "v1": [(1, [N.k, N.o])],
            "M-all": [(1, [N.k, N.o]), (2, [N.k, N.t, N.c]), (3, [N.k, N.t, N.o])],
            "M-v2-no-c": [(2, [N.k, N.t])],
            "v1-typed": [(1, [N.k, (N.o, "PaymentError")])]}[label]


def snapshot_records(N, label):
    return [dict(st.v1_record(), type=type_version(N.T, v, fields)) for v, fields in snapshot_types(N, label)]


class Slice3Types:
    """Shared cases. A subclass sets `names` and implements `source(kind)` and `snapshot(label)`."""
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s3-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def write_snapshot(self, label):
        path = self.work / ("snapshot-%s-%s.jsonl" % (label, random.randrange(10 ** 8)))
        path.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n"
                                for r in snapshot_records(self.names, label)))
        return path

    def compile(self, kind, stored):
        argv = [st.compiler(), str(self.source(kind)), "--stored", str(stored)]
        result = subprocess.run(argv, cwd=self.work / "cwd", capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def assert_compiles(self, kind, label):
        stored = self.snapshot(label)
        code, stdout, stderr = self.compile(kind, stored)
        self.assertEqual(0, code, "%s with %s: expected exit 0; stderr: %s%s" % (kind, label, stderr, self.names))
        return stdout

    def assert_rejected(self, kind, label, tokens, absent=()):
        stored = self.snapshot(label)
        code, stdout, stderr = self.compile(kind, stored)
        self.assertNotEqual(0, code, "%s with %s: expected exit != 0%s" % (kind, label, self.names))
        self.assertEqual("", stdout, "%s: expected no stdout%s" % (kind, self.names))
        tokens = [str(stored) if t is PATH else t for t in tokens]
        self.assertEqual(([], []), ([t for t in tokens if t not in stderr], [a for a in absent if a in stderr]),
                         "%s with %s: tokens (missing, unexpected); actual: %s%s" % (kind, label, stderr, self.names))
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            self.assertNotIn(stored.name, log.read_text(), "action events must not record the --stored path")
        return stderr

    def assert_decode_mentions(self, stdout, words):
        body = st.decode_body(stdout, self.names.T)
        self.assertIsNotNone(body, "no generated decode __beaml_decode_%s%s" % (self.names.T.lower(), self.names))
        self.assertEqual([], [w for w in words if not st.mentions(body, w)],
                         "decode must name these words: %s%s" % (body, self.names))

    def help_add(self, *fields):
        N = self.names
        return "migrate %s 1 -> 2 { %s }" % (N.T, ", ".join("add %s: String = %s" % (f, PLACEHOLDER)
                                                                for f in sorted(fields)))

    # Path errors and help lines. D3, D6 and D15b are the controls: same source, empty RECORD SNAPSHOT.
    def test_D2_added_field_without_add_is_compile_error(self):
        N = self.names
        self.assert_rejected("R", "v1", [N.T, N.x, PATH, self.help_add(N.x)])

    def test_D2b_two_added_fields_help_line_sorted_by_name(self):
        N = self.names
        self.assert_rejected("R2", "v1", [N.T, N.x, N.c, PATH, self.help_add(N.x, N.c)])

    def test_D3_added_field_with_empty_snapshot_compiles(self):
        self.assert_compiles("R", "empty")

    def test_D5_removed_field_without_drop_is_compile_error(self):
        N = self.names
        self.assert_rejected("D", "v1", [N.T, N.o, "String", PATH,
                                         "migrate %s 1 -> 2 { drop %s: String }" % (N.T, N.o)])

    def test_D5b_one_removed_one_added_field_gives_rename_and_drop_add_help(self):
        N = self.names
        self.assert_rejected("N", "v1", [
            N.T, PATH, "migrate %s 1 -> 2 { rename %s -> %s }" % (N.T, N.o, N.t),
            "migrate %s 1 -> 2 { drop %s: String, add %s: String = %s }" % (N.T, N.o, N.t, PLACEHOLDER)])

    def test_D5c_removed_field_of_other_type_has_no_drop_form(self):
        N = self.names
        self.assert_rejected("D", "v1-typed", [N.T, N.o, "PaymentError", PATH, DROP_STRING_ONLY],
                             absent=["drop %s: PaymentError" % N.o])

    def test_D6_removed_field_with_empty_snapshot_compiles(self):
        self.assert_compiles("D", "empty")

    def test_D7_drop_of_other_type_is_compile_error(self):
        N = self.names
        self.assert_rejected("D7", "v1", ["drop %s" % N.o, "PaymentError", STRING_ONLY])

    def test_D7b_drop_of_other_type_fails_also_with_empty_snapshot(self):
        N = self.names
        self.assert_rejected("D7", "empty", ["drop %s" % N.o, "PaymentError", STRING_ONLY])

    def test_D12_add_of_field_not_in_next_version_is_K1(self):
        N = self.names
        self.assert_rejected("M-nodrop", "empty", ["migrate %s 1 -> 2" % N.T, "add %s" % N.c,
                                                   "%s %s 2" % (NOT_IN, N.T)])

    def test_D13_version_2_record_without_added_field_has_no_path(self):
        N = self.names
        self.assert_rejected("M", "M-v2-no-c", [N.T, N.c, "derived TYPE VERSION 2", PATH])

    def test_D15_add_of_field_that_old_records_hold_has_no_path(self):
        N = self.names
        self.assert_rejected("D15", "v1", [N.T, N.o, "derived TYPE VERSION 1", PATH])

    def test_D15b_same_source_with_empty_snapshot_compiles(self):
        self.assert_compiles("D15", "empty")

    # Builds of the replay cases: exit 0, and the decode holds the constants.
    def test_D1_build_add_chain_with_v1(self):
        self.assert_decode_mentions(self.assert_compiles("R-add", "v1"), [self.names.cx])

    def test_D4_build_drop_chain_with_v1(self):
        self.assert_decode_mentions(self.assert_compiles("D-drop", "v1"), [self.names.o])

    def test_D11_build_mixed_chain_with_versions_1_2_3(self):
        N = self.names
        self.assert_decode_mentions(self.assert_compiles("M", "M-all"), [N.cw, N.cm, N.c])

    def test_D14_build_drop_then_add_chain_with_v1(self):
        self.assert_decode_mentions(self.assert_compiles("Z", "v1"), [self.names.cz])

    # K1-K12: source faults, empty RECORD SNAPSHOT (README, Consistency checks).
    def test_K01_add_of_field_not_in_next_version(self):
        N = self.names
        self.assert_rejected("K1", "empty", ["migrate %s 1 -> 2" % N.T, "add %s" % N.c, "%s %s 2" % (NOT_IN, N.T)])

    def test_K02_add_with_other_type_than_the_field(self):
        self.assert_rejected("K2", "empty", ["add %s" % self.names.x, "PaymentError", "String"])

    def test_K03_add_constant_not_a_string_literal(self):
        self.assert_rejected("K3", "empty", ["add %s" % self.names.x, "5", "String"])

    def test_K04_add_of_field_with_type_other_than_string(self):
        # Reachable only with the K checks before the EFFECT output check (README revision 7.1).
        self.assert_rejected("K4", "empty", ["add %s" % self.names.x, "PaymentError", STRING_ONLY])

    def test_K05_drop_of_field_still_in_next_version(self):
        N = self.names
        self.assert_rejected("K5", "empty", ["drop %s" % N.o, "%s %s 2" % (STILL_IN, N.T)])

    def test_K06_drop_of_type_other_than_string(self):
        self.assert_rejected("K6", "empty", ["drop %s" % self.names.o, "Int", STRING_ONLY])

    def test_K07_field_two_times_in_one_step(self):
        N = self.names
        for kind in ("K7a", "K7b"):
            with self.subTest(kind=kind):
                self.assert_rejected(kind, "empty", ["migrate %s 1 -> 2" % N.T, N.o, TWO_TIMES])

    def test_K08_empty_step(self):
        self.assert_rejected("K8", "empty", ["migrate %s 1 -> 2" % self.names.T, EMPTY_STEP])

    def test_K09_missing_comma(self):
        self.assert_rejected("K9", "empty", ["expected ','"])

    def test_K10_trailing_comma(self):
        self.assert_rejected("K10", "empty", ["expected rename, add or drop"])

    def test_K11_add_without_constant(self):
        self.assert_rejected("K11", "empty", ["expected '='"])

    def test_K12_computed_assignment(self):
        self.assert_rejected("K12", "empty", ["unsupported migrate step", "rename", "add", "drop"])


PATH = object()  # Token marker: the --stored path of the case.


class Fixture(Slice3Types, unittest.TestCase):
    names = FIXTURE_NAMES

    def source(self, kind):
        if kind in FIXTURE_SOURCES:
            return EXPERIMENT / FIXTURE_SOURCES[kind]
        path = self.work / kind / "orders.beaml"
        if not path.is_file():
            path.parent.mkdir()
            path.write_text(template_source(self.names, kind))
        return path

    def snapshot(self, label):
        if label in ("v1", "empty"):
            return EXPERIMENT / "stored" / ("%s.jsonl" % label)
        return self.write_snapshot(label)

    def test_fixtures_match_the_template_rule(self):
        # Guard, not RED: fixture files equal the template with the fixture names; stored/v1 is TYPE VERSION 1.
        code = lambda text: [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("//")]  # noqa: E731
        for kind, path in FIXTURE_SOURCES.items():
            self.assertEqual(code((EXPERIMENT / path).read_text()), code(template_source(FIXTURE_NAMES, kind)), kind)
        self.assertEqual(snapshot_records(FIXTURE_NAMES, "v1"), [st.v1_record()])


class Template(Slice3Types, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.names = random_names()

    def source(self, kind):
        path = self.work / kind / "orders.beaml"
        if not path.is_file():
            path.parent.mkdir()
            path.write_text(template_source(self.names, kind))
        return path

    def snapshot(self, label):
        return self.write_snapshot(label)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
