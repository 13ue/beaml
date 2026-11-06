"""EXPERIMENT 0004 slice 3 replay and live cases (README revision 7.2): D1, D4, D8, D9, D10, D11, D11b, D11c, D14,
D17, D18. Revision 7.2 (DL-054): a REPLAY RUN types the stored body by its own TYPE VERSION before any step.

Old RESPONSE RECORDS replay through the generated decode of a build with `add` and `drop` in the MIGRATE
CHAIN. The trees reuse the arms harness (tests/arms_test.py) and the slice 2 helpers (mode `replay_plain`,
cross-build rule). Each build runs with fixture names (slice3/ sources) and with random names and
constants from the template in slice3_types_test.py.
Expected values come from the table EXPECTED below (README, Cases (slice 3)); never from the compiler.
`unknown_keys` of a REPLAY RUN is the span attribute `unknown_keys`; no attribute means `[]`.
Run serially, loopback only: python3 -B experiments/0004-generated-replay/tests/slice3_replay_test.py [-k NAME]
"""
import atexit
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arm_tree  # noqa: E402
import arms_test as arms  # noqa: E402
import slice2_replay_test as s2  # noqa: E402
import slice3_types_test as s3  # noqa: E402
import stored_types_test as st  # noqa: E402

EXPERIMENT = arm_tree.EXPERIMENT
RANDOM_NAMES = s3.random_names()
# Build: source kind and RECORD SNAPSHOT label of slice3_types_test.
BUILDS = {"radd": ("R-add", "v1"), "ddrop": ("D-drop", "v1"), "m": ("M", "M-all"), "z": ("Z", "Z-all"),
          "rr": ("RR", "RR-v1"), "sar": ("SAR", "SAR-all"), "rd": ("RD", "RD-all")}


def variant(build, names, fixture):
    kind, label = BUILDS[build]
    holder = tempfile.TemporaryDirectory(prefix="beaml-0004-s3-%s-" % build)
    atexit.register(holder.cleanup)
    root = Path(holder.name)
    if fixture:
        source = EXPERIMENT / s3.FIXTURE_SOURCES[kind]
    else:
        source = root / "orders.beaml"
        source.write_text(s3.template_source(names, kind))
    snapshot = root / "stored.jsonl"
    snapshot.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n"
                                for r in s3.snapshot_records(names, label)))
    return ("gen", source, snapshot)


for _build in BUILDS:
    arms.VARIANTS["s3-" + _build] = variant(_build, s3.FIXTURE_NAMES, True)
    arms.VARIANTS["s3-%s-random" % _build] = variant(_build, RANDOM_NAMES, False)

# README, Cases (slice 3). Role keys: k o x c t (fields), cx cw cm cz (constants), or a literal value.
# Each row: build, stored TYPE VERSION (number, field roles), body {role: value}, expected decoded value or
# "decode" (typed reject), expected unknown_keys (roles).
V = lambda *roles: list(roles)  # noqa: E731
EXPECTED = {
    "D1": ("radd", (1, V("k", "o")), {"k": "order-1", "o": "authorized"},
           {"k": "order-1", "o": "authorized", "x": "=cx"}, []),
    "D8": ("radd", (1, V("k", "o")), {"k": "order-1", "o": "authorized", "x": "r-9"},
           {"k": "order-1", "o": "authorized", "x": "=cx"}, ["x"]),
    "D4": ("ddrop", (1, V("k", "o")), {"k": "order-1", "o": "authorized"}, {"k": "order-1"}, []),
    "D9-missing": ("ddrop", (1, V("k", "o")), {"k": "order-1"}, "decode", None),
    "D9-not-string": ("ddrop", (1, V("k", "o")), {"k": "order-1", "o": 7}, "decode", None),
    "D11-v1": ("m", (1, V("k", "o")), {"k": "order-1", "o": "authorized"},
               {"k": "order-1", "t": "authorized", "o": "=cm"}, []),
    "D11-v2": ("m", (2, V("k", "t", "c")), {"k": "order-1", "t": "settled", "c": "app"},
               {"k": "order-1", "t": "settled", "o": "=cm"}, []),
    "D11-v3": ("m", (3, V("k", "t", "o")), {"k": "order-1", "t": "settled", "o": "done"},
               {"k": "order-1", "t": "settled", "o": "done"}, []),
    # DL-054: t is not a field of version 1, so it is a stray key (unknown_keys); t comes from o by the rename.
    "D11b": ("m", (1, V("k", "o")), {"k": "order-1", "t": "settled", "o": "authorized"},
             {"k": "order-1", "t": "authorized", "o": "=cm"}, ["t"]),
    "D14": ("z", (1, V("k", "o")), {"k": "order-1", "o": "authorized"}, {"k": "order-1", "o": "=cz"}, []),
    # Version 3 has the fingerprint of version 1: only the version number may pick the MIGRATE STEPS.
    "D14-v3": ("z", (3, V("k", "o")), {"k": "order-1", "o": "done"}, {"k": "order-1", "o": "done"}, []),
    # Chain {rename o -> t}, {rename x -> o}. DL-054: version 1 is {k, o, x}; t is a stray key (unknown_keys).
    # Step 1 -> 2: o is read as t. Step 2 -> 3: x is read as o. A rename that keeps o gives o = "o-old".
    "D11c": ("rr", (1, V("k", "o", "x")), {"k": "order-1", "o": "o-old", "t": "t-kept", "x": "x-new"},
             {"k": "order-1", "t": "o-old", "o": "x-new"}, ["t"]),
    # D17 (DL-054), chain {drop c}, {add c = cx}, {rename c -> x}. A stray x in an old body never wins:
    # the constant (versions 1 and 2) or the typed c (version 3) reaches x through the rename.
    "D17-v1": ("sar", (1, V("k", "c")), {"k": "order-1", "c": "c-one"}, {"k": "order-1", "x": "=cx"}, []),
    "D17-v1-stray": ("sar", (1, V("k", "c")), {"k": "order-1", "c": "c-one", "x": "STRAY"},
                     {"k": "order-1", "x": "=cx"}, ["x"]),
    "D17-v2-stray": ("sar", (2, V("k")), {"k": "order-1", "x": "STRAY"}, {"k": "order-1", "x": "=cx"}, ["x"]),
    "D17-v3-stray": ("sar", (3, V("k", "c")), {"k": "order-1", "c": "c-three", "x": "STRAY"},
                     {"k": "order-1", "x": "c-three"}, ["x"]),
    # D18 (DL-054), chain {rename o -> t}, {drop t}. The version 1 field o is type-checked; a stray t is unknown.
    "D18-v1": ("rd", (1, V("k", "o")), {"k": "order-1", "o": "o-one"}, {"k": "order-1"}, []),
    "D18-v1-stray-int": ("rd", (1, V("k", "o")), {"k": "order-1", "o": "o-one", "t": 7}, {"k": "order-1"}, ["t"]),
    "D18-v1-old-int": ("rd", (1, V("k", "o")), {"k": "order-1", "o": 7, "t": "t-stray"}, "decode", None),
    "D18-v2-stray": ("rd", (2, V("k", "t")), {"k": "order-1", "t": "t-two", "o": "o-stray"}, {"k": "order-1"}, ["o"]),
    "D18-v2-int": ("rd", (2, V("k", "t")), {"k": "order-1", "t": 7}, "decode", None),
}
# Live calls: the unchanged stub body {k: "order-1", o: "authorized"}. Expected value or "decode", unknown_keys,
# and the TYPE VERSION (number, field roles) of the new record.
LIVE = {
    "D4-live": ("ddrop", {"k": "order-1"}, ["o"], (2, V("k"))),
    "D10-live": ("radd", "decode", None, (2, V("k", "o", "x"))),
    "D14-live": ("z", {"k": "order-1", "o": "authorized"}, [], (3, V("k", "o"))),
}


def resolve(names, mapping):
    """Role keys to names; a value "=<role>" is the constant of that role."""
    value = lambda v: getattr(names, v[1:]) if isinstance(v, str) and v.startswith("=") else v  # noqa: E731
    return {getattr(names, role): value(v) for role, v in mapping.items()}


def unknown(report):
    """`unknown_keys` of each replay EFFECT span; a span without the attribute has none."""
    return [s["attributes"].get("unknown_keys") or [] for s in report.get("spans", [])
            if s["name"] == "orders.payments.authorize"]


class Slice3Replay:
    names, suffix = None, ""

    def tree(self, build):
        return "s3-%s%s" % (build, self.suffix)

    def msg(self):
        return str(self.names)

    def replay(self, case):
        build, (version, roles), body, expected, keys = EXPECTED[case]
        N = self.names
        record = dict(st.v1_record(), type=s3.type_version(N.T, version, [getattr(N, r) for r in roles]))
        record = arms.with_body(record, json.dumps(resolve(N, body), separators=(",", ":"), ensure_ascii=False).encode())
        seen = s2.counts(self.tree(build), case, record, observe=keys is not None)
        if keys is None:
            return s2.decode_rejected(), seen
        return s2.accepted(resolve(N, expected), hint=[sorted(getattr(N, r) for r in keys)]), seen

    def assert_replays(self, *cases):
        expected, actual = {}, {}
        for case in cases:
            expected[case], actual[case] = self.replay(case)
            if "replay_hint" in actual[case]:
                actual[case]["replay_hint"] = [hint or [] for hint in actual[case]["replay_hint"]]
        self.assertEqual(expected, actual, self.msg())

    def live(self, case):
        build, value, keys, (version, roles) = LIVE[case]
        N = self.names
        stub_body = json.dumps(resolve(N, {"k": "order-1", "o": "authorized"}), separators=(",", ":")).encode()
        stub, sent = arms.payments_stub(200, stub_body)
        try:
            report = arms.harness(self.tree(build), case, {"mode": "place", "observe": True},
                                  payments_port=stub.server_address[1])
        finally:
            stub.shutdown()
            stub.server_close()
        written = arms.rows(arms.RESULTS / self.tree(build) / "eval" / case / "responses.jsonl")
        one = written[0] if len(written) == 1 else {}
        actual = {"result": report["result"], "sent": len(sent), "records": len(written), "type": one.get("type"),
                  "finish": report["calls"].get("OrdersBeamlSpike.finish/1")}
        expected = {"sent": 1, "records": 1, "type": s3.type_version(N.T, version, [getattr(N, r) for r in roles])}
        if value == "decode":
            expected.update(result={"error": arms.DECODE_ERROR}, finish=0)
        else:
            expected.update(result={"ok": resolve(N, value)}, finish=1)
            actual["unknown_keys"] = one.get("unknown_keys")
            expected["unknown_keys"] = sorted(getattr(N, r) for r in keys)
        self.assertEqual(expected, actual, self.msg())

    def test_build_radd_compiles_with_warnings_as_errors(self):
        self.assertTrue(arms.build(self.tree("radd"))["strict"], "mix compile --warnings-as-errors failed" + self.msg())

    def test_D1_v1_record_gets_the_add_constant(self):
        self.assert_replays("D1")

    def test_D8_body_key_of_added_field_is_unknown_and_the_constant_wins(self):
        self.assert_replays("D8")

    def test_D10_live_body_gets_no_constant(self):
        self.live("D10-live")

    def test_D4_v1_record_drops_the_field_and_consumes_its_key(self):
        self.assert_replays("D4")

    def test_D4_live_body_keeps_dropped_key_as_unknown(self):
        self.live("D4-live")

    def test_D9_dropped_field_missing_or_not_string_is_typed_decode_error(self):
        self.assert_replays("D9-missing", "D9-not-string")

    def test_D11_each_stored_version_replays_by_its_version(self):
        self.assert_replays("D11-v1", "D11-v2", "D11-v3")

    def test_D11b_v1_record_with_both_names_reads_the_old_field_by_its_version(self):
        self.assert_replays("D11b")

    def test_D14_v1_record_gets_the_constant_not_the_stored_value(self):
        self.assert_replays("D14")

    def test_D14_v3_record_with_the_v1_fingerprint_replays_by_its_version(self):
        self.assert_replays("D14-v3")

    def test_D11c_v1_record_with_a_stray_new_name_reads_by_its_version(self):
        self.assert_replays("D11c")

    def test_D17_stray_key_never_beats_the_constant_or_the_typed_field(self):
        self.assert_replays("D17-v1", "D17-v1-stray", "D17-v2-stray", "D17-v3-stray")

    def test_D18_old_field_is_type_checked_and_stray_key_is_unknown(self):
        self.assert_replays("D18-v1", "D18-v1-stray-int", "D18-v1-old-int", "D18-v2-stray", "D18-v2-int")

    def test_D14_live_body_keeps_its_value(self):
        self.live("D14-live")


class FixtureNames(Slice3Replay, arms.Case):
    names, suffix = s3.FIXTURE_NAMES, ""


class RandomNames(Slice3Replay, arms.Case):
    names, suffix = RANDOM_NAMES, "-random"


class ZzControlUnchanged(arms.Case):
    def test_control_originals_unchanged_by_slice_3_runs(self):
        self.assertEqual(arms.CONTROL_BEFORE, arm_tree.control_hashes())


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    arms.RESULTS.mkdir(parents=True, exist_ok=True)
    print(arms.RESULTS, flush=True)
    unittest.main(verbosity=2)
