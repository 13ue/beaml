"""EXPERIMENT 0004 slice 2 (README revision 6): compile cases against stored TYPE VERSIONS.

Cases C1, C2 (build), C3 (build), C4, C5, C6, C7, C8, C10 (build with v1), C14 (build), C15.
Each case runs twice:
  Fixture   the case sources in drift/ and slice2/, the RECORD SNAPSHOTS in stored/;
  Template  the same sources and snapshots built from a template with random TYPE and field names,
            so that a compiler with fixture names written into it cannot pass.
The fingerprint of a TYPE VERSION is the lower-case hex SHA-256 of the compact JSON of the field
list sorted by field name (README, revision 6). The compiler reads no body bytes.
Run: python3 -B experiments/0004-generated-replay/tests/stored_types_test.py [-k NAME]
"""
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
from arm_tree import COMPILER_PATH, EXPERIMENT, REPO  # noqa: E402

V1_FIXTURE = EXPERIMENT / "stored" / "v1.jsonl"
UNKNOWN_STORE = "stored TYPE VERSIONS unknown"
NO_TYPE_VERSION = "stored RESPONSE RECORD has no TYPE VERSION"
_BINARY = []


def compiler():
    """The 0001 compiler binary, built once. BEAML_SPIKE replaces it for a scratch self-check only."""
    if not _BINARY:
        if os.environ.get("BEAML_SPIKE"):
            _BINARY.append(os.environ["BEAML_SPIKE"])
        else:
            manifest = REPO / COMPILER_PATH / "Cargo.toml"
            subprocess.run(["cargo", "build", "--offline", "--quiet", "--manifest-path", str(manifest)], check=True)
            _BINARY.append(str(REPO / COMPILER_PATH / "target/debug/beaml-spike"))
        print("compiler:", _BINARY[0], file=sys.stderr)
    return _BINARY[0]


def type_version(name, version, fields):
    fields = sorted([field, "String"] for field in fields)
    text = json.dumps(fields, separators=(",", ":"))
    return {"name": name, "version": version, "fields": fields,
            "fingerprint": hashlib.sha256(text.encode()).hexdigest()}


def v1_record():
    return json.loads(V1_FIXTURE.read_text().splitlines()[0])


def mentions(text, word):
    """The emitter writes BEAML strings as byte lists. Accept the plain text or that form."""
    codes = [str(b) for b in word.encode()]
    return word in text or "<<%s>>" % ",".join(codes) in text or "<<%s>>" % ", ".join(codes) in text


def decode_body(stdout, type_name):
    """Source of the generated decode of the TYPE only (rule of tests/cli.rs, `decode_body`)."""
    heads = ["def __beaml_decode_%s(" % type_name.lower(), "defp __beaml_decode_%s(" % type_name.lower()]
    is_head = lambda text: any(text.startswith(head) for head in heads)  # noqa: E731
    indent = lambda line: len(line) - len(line.lstrip())  # noqa: E731
    lines = stdout.splitlines()
    start = next((i for i, line in enumerate(lines) if is_head(line.lstrip())), None)
    if start is None:
        return None
    level, body = indent(lines[start]), [lines[start]]
    for line in lines[start + 1:]:
        text = line.lstrip()
        if text:
            if indent(line) < level or (indent(line) == level and text != "end" and not is_head(text)):
                break
        body.append(line)
    return "\n".join(body)


class Names:
    """TYPE name T; fields: k (kept), o (old), n (new), x (added in R), w (wrong old name), k2 (new name of k)."""

    def __init__(self, T, k, o, n, x, w, k2):
        self.T, self.k, self.o, self.n, self.x, self.w, self.k2 = T, k, o, n, x, w, k2


FIXTURE_NAMES = Names("Payment", "order_id", "status", "state", "reference", "statuz", "order_ref")
FIXTURE_SOURCES = {"base": "arms/gen/orders.beaml", "N": "drift/N/orders.beaml", "R": "drift/R/orders.beaml",
                   "N-chain": "slice2/N-chain/orders.beaml", "N-statuz": "slice2/N-statuz/orders.beaml",
                   "N2": "slice2/N2/orders.beaml", "N2-chain": "slice2/N2-chain/orders.beaml"}

TEMPLATE = """interface Order { order_id: String }
interface %(T)s { %(declared)s }
%(chain)sinterface PaymentError { reason: String }

effect payments.authorize Order -> %(T)s ! PaymentError = http.post("payments/authorize")

fn prepare Order { order_id } -> Order = Order { order_id: order_id + "" }
fn finish %(T)s { %(pattern)s } -> %(T)s = %(T)s { %(build)s }

fn place order: Order -> %(T)s ! PaymentError =
  order
  |> prepare
  |> payments.authorize
  |> finish
"""


def random_names():
    rng = random.Random()
    word = lambda prefix: prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(6))  # noqa: E731
    return Names("Tq" + word(""), word("k_"), word("o_"), word("n_"), word("x_"), word("w_"), word("m_"))


def template_source(names, kind):
    N = names
    fields, chain = {"base": ([N.k, N.o], None), "N": ([N.k, N.n], None), "R": ([N.k, N.o, N.x], None),
                     "N-chain": ([N.k, N.n], (N.o, N.n)), "N-statuz": ([N.k, N.n], (N.w, N.n)),
                     "N2": ([N.k2, N.o], None), "N2-chain": ([N.k2, N.o], (N.k, N.k2))}[kind]
    return TEMPLATE % {
        "T": N.T, "declared": " ".join("%s: String" % f for f in fields),
        "chain": "migrate %s 1 -> 2 { rename %s -> %s }\n" % ((N.T,) + chain) if chain else "",
        "pattern": ", ".join(fields),
        "build": ", ".join(("%s: %s + \"\"" if i == 0 else "%s: %s") % (f, f) for i, f in enumerate(fields))}


class StoredTypes:
    """Shared cases. A subclass sets `names` and implements `source(kind)` and `snapshot(kind)`."""
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s2-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def write_snapshot(self, label, records):
        path = self.work / ("snapshot-%s-%s.jsonl" % (label, random.randrange(10 ** 8)))
        path.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in records))
        return path

    def record(self, version, fields):
        return dict(v1_record(), type=type_version(self.names.T, version, fields))

    def compile(self, kind, stored):
        argv = [compiler(), str(self.source(kind))] + (["--stored", str(stored)] if stored is not None else [])
        result = subprocess.run(argv, cwd=self.work / "cwd", capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def assert_compiles(self, kind, stored):
        code, stdout, stderr = self.compile(kind, stored)
        self.assertEqual(0, code, "%s with --stored %s: expected exit 0; stderr: %s" % (kind, stored, stderr))
        return stdout

    def assert_rejected(self, kind, stored, tokens):
        code, stdout, stderr = self.compile(kind, stored)
        self.assertNotEqual(0, code, "%s with --stored %s: expected exit != 0" % (kind, stored))
        self.assertEqual("", stdout, "%s: expected no stdout" % kind)
        missing = [t for t in tokens if t not in stderr]
        self.assertEqual([], missing, "%s: message must name these tokens; actual: %s" % (kind, stderr))
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if stored is not None and log.is_file():
            self.assertNotIn(Path(stored).name, log.read_text(), "action events must not record the --stored path")
        return stderr

    def assert_decode(self, stdout, present, absent):
        body = decode_body(stdout, self.names.T)
        self.assertIsNotNone(body, "no generated decode __beaml_decode_%s" % self.names.T.lower())
        self.assertEqual(([], []), ([p for p in present if not mentions(body, p)], [a for a in absent if mentions(body, a)]),
                         "decode names (missing, unexpected): %s" % body)

    def help_line(self, old, new):
        return "migrate %s 1 -> 2 { rename %s -> %s }" % (self.names.T, old, new)

    # C1 and C6: the same source; only the stored records differ.
    def test_C1_rename_without_chain_is_compile_error(self):
        N, stored = self.names, self.snapshot("v1")
        self.assert_rejected("N", stored, [N.T, N.o, N.n, str(stored), self.help_line(N.o, N.n)])

    def test_C6_same_source_with_empty_snapshot_compiles(self):
        stdout = self.assert_compiles("N", self.snapshot("empty"))
        self.assert_decode(stdout, [self.names.k, self.names.n], [self.names.o])

    def test_C2_chain_compiles_and_decode_reads_old_name(self):
        N = self.names
        self.assert_decode(self.assert_compiles("N-chain", self.snapshot("v1")), [N.k, N.n, N.o], [])

    def test_C3_chain_compiles_with_two_stored_versions(self):
        self.assert_compiles("N-chain", self.snapshot("v1-v2"))

    def test_C4_rename_of_unknown_old_field_is_compile_error(self):
        N, stored = self.names, self.snapshot("v1")
        self.assert_rejected("N-statuz", stored, [N.T, N.w, N.o, str(stored)])

    def test_C5_added_field_without_step_is_compile_error(self):
        N, stored = self.names, self.snapshot("v1")
        self.assert_rejected("R", stored, [N.T, N.x, str(stored)])

    def test_C7_record_without_type_version_is_compile_error(self):
        stored = self.snapshot("v1-untyped")
        stderr = self.assert_rejected("base", stored, [NO_TYPE_VERSION, str(stored)])
        self.assertTrue("line 2" in stderr or "%s:2" % stored in stderr, "C7: message must name line 2: %s" % stderr)

    def test_C8_effect_source_without_stored_input_is_compile_error(self):
        self.assert_rejected("base", None, [UNKNOWN_STORE])

    def test_C10_slice_1_source_compiles_with_v1(self):
        N = self.names
        self.assert_decode(self.assert_compiles("base", self.snapshot("v1")), [N.k, N.o], [N.n])

    def test_C14_second_rename_chain_compiles_and_decode_reads_old_name(self):
        N = self.names
        self.assert_decode(self.assert_compiles("N2-chain", self.snapshot("v1")), [N.k2, N.o, N.k], [])

    def test_C15_second_rename_without_chain_is_compile_error(self):
        N, stored = self.names, self.snapshot("v1")
        self.assert_rejected("N2", stored, [N.T, N.k, N.k2, str(stored), self.help_line(N.k, N.k2)])


class Fixture(StoredTypes, unittest.TestCase):
    names = FIXTURE_NAMES

    def source(self, kind):
        return EXPERIMENT / FIXTURE_SOURCES[kind]

    def snapshot(self, label):
        if label == "v1-untyped":
            untyped = {k: v for k, v in v1_record().items() if k != "type"}
            return self.write_snapshot(label, [v1_record(), untyped])
        return EXPERIMENT / "stored" / ("%s.jsonl" % label)

    def test_fixtures_match_the_template_rule(self):
        # Guard, not RED: the fixture snapshots hold the fingerprints of the README rule.
        lines = [json.loads(line) for line in (EXPERIMENT / "stored/v1-v2.jsonl").read_text().splitlines()]
        self.assertEqual([type_version("Payment", 1, ["order_id", "status"]),
                          type_version("Payment", 2, ["order_id", "state"])], [r["type"] for r in lines])
        self.assertEqual(lines[0], v1_record())
        self.assertEqual("", (EXPERIMENT / "stored/empty.jsonl").read_text())
        # The template with the fixture names gives the fixture sources, apart from comments and blank lines.
        code = lambda text: [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("//")]  # noqa: E731
        for kind, path in FIXTURE_SOURCES.items():
            self.assertEqual(code((EXPERIMENT / path).read_text()), code(template_source(FIXTURE_NAMES, kind)), kind)


class Template(StoredTypes, unittest.TestCase):
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
        N = self.names
        records = {"empty": [], "v1": [self.record(1, [N.k, N.o])],
                   "v1-v2": [self.record(1, [N.k, N.o]), self.record(2, [N.k, N.n])],
                   "v1-untyped": [self.record(1, [N.k, N.o]), {k: v for k, v in v1_record().items() if k != "type"}]}
        return self.write_snapshot(label, records[label])


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
