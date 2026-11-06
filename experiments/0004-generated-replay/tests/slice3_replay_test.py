"""EXPERIMENT 0004 slice 3 replay and live cases (README revision 7.1): D1, D4, D8, D9, D10, D11, D11b, D14.

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
BUILDS = {"radd": ("R-add", "v1"), "ddrop": ("D-drop", "v1"), "m": ("M", "M-all"), "z": ("Z", "v1")}


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
    "D11b": ("m", (1, V("k", "o")), {"k": "order-1", "t": "settled", "o": "authorized"},
             {"k": "order-1", "t": "settled", "o": "=cm"}, ["o"]),
    "D14": ("z", (1, V("k", "o")), {"k": "order-1", "o": "authorized"}, {"k": "order-1", "o": "=cz"}, []),
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

    def test_D11b_old_value_of_a_renamed_key_does_not_beat_the_constant(self):
        self.assert_replays("D11b")

    def test_D14_v1_record_gets_the_constant_not_the_stored_value(self):
        self.assert_replays("D14")

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
