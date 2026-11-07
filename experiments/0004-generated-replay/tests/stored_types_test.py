"""EXPERIMENT 0004 slice 2 (README revision 6): compile cases against stored TYPE VERSIONS.

Cases C1, C2 (build), C3 (build), C4, C5, C6, C7, C8, C10 (build with v1), C14 (build), C15.
Repair cases: C1b (bad TYPE VERSION at line 2 after a good one), C17 (fields and fingerprint disagree),
C18 (help line `2 -> 3`: newest version 2, stored version 2 without a path).
Final review repair cases: C19 (name reuse in a chain of 3 steps), C20 (rotation in a chain of 3 steps).
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


BODY_KEYS = ("body_base64", "body_length", "body_sha256")


def value_sha256(value, unknown_keys=(), redacted=()):
    """D6B-58: lower-case hex SHA-256 of the canonical JSON of the RESPONSE RECORD projection (version 2)."""
    projection = {"redacted": sorted(redacted), "unknown_keys": sorted(unknown_keys), "value": value}
    text = json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode()).hexdigest()


def with_value(record, value, unknown_keys=(), redacted=()):
    """D6B-68: a version 2 RESPONSE RECORD derivative with another `value` and a recomputed `value_sha256`."""
    record = {k: v for k, v in record.items() if k not in BODY_KEYS}
    return dict(record, version=2, value=value, redacted=sorted(redacted), unknown_keys=sorted(unknown_keys),
                value_sha256=value_sha256(value, unknown_keys, redacted))


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

    def __init__(self, T, k, o, n, x, w, k2, chain=None):
        self.T, self.k, self.o, self.n, self.x, self.w, self.k2 = T, k, o, n, x, w, k2
        # Field names of the chain kinds C19 (reuse: p, s, t, c) and C20 (rotation: a, b, r).
        self.chain = chain or {}


FIXTURE_NAMES = Names("Payment", "order_id", "status", "state", "reference", "statuz", "order_ref",
                      chain={"p": "phase", "s": "status", "t": "state", "c": "code", "a": "a", "b": "b", "r": "c"})
FIXTURE_SOURCES = {"reuse": "slice2/reuse/orders.beaml", "rotation": "slice2/rotation/orders.beaml",
                   "base": "arms/gen/orders.beaml", "N": "drift/N/orders.beaml", "R": "drift/R/orders.beaml",
                   "N-chain": "slice2/N-chain/orders.beaml", "N-statuz": "slice2/N-statuz/orders.beaml",
                   "N2": "slice2/N2/orders.beaml", "N2-chain": "slice2/N2-chain/orders.beaml"}
# Kinds with no fixture file: the Fixture class writes them from the template with the fixture names.
# N2-over-chain: interface [k2, n] with the chain `1 -> 2 { rename o -> n }` (newest version 2).
GENERATED_KINDS = ("N2-over-chain",)

TEMPLATE = """type Order { order_id: String }
type %(T)s { %(declared)s }
%(chain)stype PaymentError { reason: String }

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
    chain = {role: word(role + "_") for role in ("p", "s", "t", "c", "a", "b", "r")}
    return Names("Tq" + word(""), word("k_"), word("o_"), word("n_"), word("x_"), word("w_"), word("m_"), chain=chain)


CHAIN_KINDS = ("reuse", "rotation")


def chain_spec(names, kind):
    """C19 and C20: (newest fields, rename steps in chain order, fields of TYPE VERSION 1, 2, 3, 4).
    reuse:    `T { p s }`, steps s -> t, c -> s, t -> p. The name s leaves in 1 -> 2 and comes back in 2 -> 3.
    rotation: `T { a b }`, steps a -> r, b -> a, r -> b. Version 1 and version 4 have the same names."""
    C = names.chain
    if kind == "reuse":
        p, s, t, c = C["p"], C["s"], C["t"], C["c"]
        return [p, s], [(s, t), (c, s), (t, p)], [[c, s], [c, t], [t, s], [p, s]]
    a, b, r = C["a"], C["b"], C["r"]
    return [a, b], [(a, r), (b, a), (r, b)], [[a, b], [b, r], [a, r], [a, b]]


def chain_records(names, kind, versions, base=None):
    """RESPONSE RECORDS of the stored TYPE VERSIONS `versions` of a chain kind (body of `base` unchanged)."""
    fields = chain_spec(names, kind)[2]
    return [dict(base or v1_record(), type=type_version(names.T, v, fields[v - 1])) for v in versions]


def template_source(names, kind):
    N = names
    if kind in CHAIN_KINDS:
        fields, steps, _ = chain_spec(names, kind)
        chain = "".join("migrate %s v%d -> v%d { rename %s -> %s }\n" % (N.T, i + 1, i + 2, old, new)
                        for i, (old, new) in enumerate(steps))
        return TEMPLATE % {
            "T": N.T, "declared": " ".join("%s: String" % f for f in fields), "chain": chain,
            "pattern": ", ".join(fields),
            "build": ", ".join(("%s: %s + \"\"" if i == 0 else "%s: %s") % (f, f) for i, f in enumerate(fields))}
    fields, chain = {"base": ([N.k, N.o], None), "N": ([N.k, N.n], None), "R": ([N.k, N.o, N.x], None),
                     "N-chain": ([N.k, N.n], (N.o, N.n)), "N-statuz": ([N.k, N.n], (N.w, N.n)),
                     "N2": ([N.k2, N.o], None), "N2-chain": ([N.k2, N.o], (N.k, N.k2)),
                     "N2-over-chain": ([N.k2, N.n], (N.o, N.n))}[kind]
    return TEMPLATE % {
        "T": N.T, "declared": " ".join("%s: String" % f for f in fields),
        "chain": "migrate %s v1 -> v2 { rename %s -> %s }\n" % ((N.T,) + chain) if chain else "",
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

    def ctx(self):
        """Names of this run, for a re-run of a failed template case."""
        N = self.names
        return " [names: T=%s k=%s o=%s n=%s x=%s w=%s k2=%s]" % (N.T, N.k, N.o, N.n, N.x, N.w, N.k2)

    def write_snapshot(self, label, records):
        path = self.work / ("snapshot-%s-%s.jsonl" % (label, random.randrange(10 ** 8)))
        path.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in records))
        return path

    def record(self, version, fields, fingerprint_fields=None):
        """A record of TYPE VERSION (version, fields). With fingerprint_fields, the fingerprint of those fields."""
        tv = type_version(self.names.T, version, fields)
        if fingerprint_fields is not None:
            tv["fingerprint"] = type_version(self.names.T, version, fingerprint_fields)["fingerprint"]
        return dict(v1_record(), type=tv)

    def compile(self, kind, stored):
        argv = [compiler(), str(self.source(kind))] + (["--stored", str(stored)] if stored is not None else [])
        result = subprocess.run(argv, cwd=self.work / "cwd", capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def assert_compiles(self, kind, stored):
        code, stdout, stderr = self.compile(kind, stored)
        self.assertEqual(0, code, "%s with --stored %s: expected exit 0; stderr: %s%s" % (kind, stored, stderr, self.ctx()))
        return stdout

    def assert_rejected(self, kind, stored, tokens):
        code, stdout, stderr = self.compile(kind, stored)
        self.assertNotEqual(0, code, "%s with --stored %s: expected exit != 0%s" % (kind, stored, self.ctx()))
        self.assertEqual("", stdout, "%s: expected no stdout%s" % (kind, self.ctx()))
        missing = [t for t in tokens if t not in stderr]
        self.assertEqual([], missing, "%s: message must name these tokens; actual: %s%s" % (kind, stderr, self.ctx()))
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if stored is not None and log.is_file():
            self.assertNotIn(Path(stored).name, log.read_text(), "action events must not record the --stored path")
        return stderr

    def assert_decode(self, stdout, present, absent):
        body = decode_body(stdout, self.names.T)
        self.assertIsNotNone(body, "no generated decode __beaml_decode_%s%s" % (self.names.T.lower(), self.ctx()))
        self.assertEqual(([], []), ([p for p in present if not mentions(body, p)], [a for a in absent if mentions(body, a)]),
                         "decode names (missing, unexpected): %s%s" % (body, self.ctx()))

    def help_line(self, old, new, stored=1, newest=1):
        """README: `migrate T <stored> -> <next> { rename <old> -> <new> }`, <next> = newest version + 1."""
        return "migrate %s v%d -> v%d { rename %s -> %s }" % (self.names.T, stored, newest + 1, old, new)

    # C1 and C6: the same source; only the stored records differ.
    def test_C1_rename_without_chain_is_compile_error(self):
        N, stored = self.names, self.snapshot("v1")
        self.assert_rejected("N", stored, [N.T, N.o, N.n, str(stored), self.help_line(N.o, N.n)])

    def test_C1b_bad_type_version_after_a_good_one_is_compile_error(self):
        # Line 1 has a path (it is the newest version); line 2 has none. A check of line 1 only passes wrongly.
        N, stored = self.names, self.snapshot("v1new-v1")
        self.assert_rejected("N", stored, [N.T, N.o, N.n, str(stored), self.help_line(N.o, N.n)])

    def test_C17_fingerprint_not_fields_decides_the_path(self):
        # fields = newest version (a path), fingerprint = the old version (no path). README: the compiler
        # compares fingerprints and reads fields only for its message. So the fingerprint wins: no path.
        N, stored = self.names, self.snapshot("v1-fp-mismatch")
        prefix = type_version(N.T, 1, [N.k, N.o])["fingerprint"][:12]
        self.assert_rejected("N", stored, [N.T, str(stored), "fingerprint", prefix])

    def test_C18_help_line_names_stored_and_next_version(self):
        # Newest version 2 (chain o -> n), stored version 2 with k (not k2): no path. Help: 2 -> 3.
        N, stored = self.names, self.snapshot("v2")
        self.assert_rejected("N2-over-chain", stored,
                             [N.T, N.k, N.k2, str(stored), self.help_line(N.k, N.k2, stored=2, newest=2)])

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
        self.assertTrue("line 2" in stderr or "%s:2" % stored in stderr, "C7: message must name line 2: %s%s" % (stderr, self.ctx()))

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

    # Final review repair: name reuse and rotation are legal chains. The replay cases are in slice2_replay_test.py.
    def test_C19_name_reuse_chain_compiles_with_v1_v4_and_all_versions(self):
        self.assert_compiles("reuse", self.snapshot("reuse-v1-v4"))
        self.assert_compiles("reuse", self.snapshot("reuse-all"))

    def test_C20_rotation_chain_compiles_with_v1_v4_and_all_versions(self):
        self.assert_compiles("rotation", self.snapshot("rotation-v1-v4"))
        self.assert_compiles("rotation", self.snapshot("rotation-all"))


class Fixture(StoredTypes, unittest.TestCase):
    names = FIXTURE_NAMES

    def source(self, kind):
        if kind in GENERATED_KINDS:
            path = self.work / kind / "orders.beaml"
            if not path.is_file():
                path.parent.mkdir()
                path.write_text(template_source(self.names, kind))
            return path
        return EXPERIMENT / FIXTURE_SOURCES[kind]

    def snapshot(self, label):
        if label == "v1-untyped":
            untyped = {k: v for k, v in v1_record().items() if k != "type"}
            return self.write_snapshot(label, [v1_record(), untyped])
        if label in ("v1new-v1", "v1-fp-mismatch", "v2") or label.partition("-")[0] in CHAIN_KINDS:
            return self.write_snapshot(label, repair_records(self, label))
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
        records = repair_records(self, label) if label not in records else records[label]
        return self.write_snapshot(label, records)


def repair_records(case, label):
    """Snapshots of the repair cases C1b, C17, C18, C19, C20, for fixture and random names alike."""
    N = case.names
    kind, _, which = label.partition("-")
    if kind in CHAIN_KINDS:
        return chain_records(N, kind, {"v1-v4": [1, 4], "all": [1, 2, 3, 4]}[which])
    return {"v1new-v1": [case.record(1, [N.k, N.n]), case.record(1, [N.k, N.o])],
            "v1-fp-mismatch": [case.record(1, [N.k, N.n], fingerprint_fields=[N.k, N.o])],
            "v2": [case.record(2, [N.k, N.n])]}[label]


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
