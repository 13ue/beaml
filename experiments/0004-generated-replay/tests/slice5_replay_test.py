"""EXPERIMENT 0004 slice 5 replay and live cases (README revision 9.1): F9 (live call), F11, F11c, F29.

The trees reuse the arms harness (tests/arms_test.py), mode `replay_plain` and the eval VM of slices 2 to 4.
Each build runs with fixture names (slice5/ sources) and with random names and a random base b from the template
in slice5_syntax_test.py. Expected values come from the tables below (README, Cases (slice 5)); never from the
compiler.
Builds: m3 (M3, empty RECORD SNAPSHOT), m3v (M3, records of its mark), q4 (Q4, v4 records), q4z (Q4z, v4 records).
Run serially, loopback only: python3 -B experiments/0004-generated-replay/tests/slice5_replay_test.py [-k NAME]
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
import slice5_syntax_test as s5  # noqa: E402

EXPERIMENT = arm_tree.EXPERIMENT
RANDOM_NAMES = s5.random_names()
FINISH = "OrdersBeamlSpike.finish/1"
COUNTS = ("OrdersApi.Router.call/2", ":gen_tcp.connect/4", ":json.decode/1", FINISH)


def builds(N):
    """Tree: source kind, RECORD SNAPSHOT spec (version, roles). Q4 and Q4z get the same v4 records (F29)."""
    q4z_version = N.V
    return {"m3": ("M3", []), "m3v": ("M3", [(N.M, "kt")]), "q4": ("Q4", [(4, "ktx"), (4, "ktx")]),
            "q4z": ("Q4z", [(q4z_version, "ktx"), (q4z_version, "ktx")])}


def variant(build, names, fixture):
    kind, spec = builds(names)[build]
    holder = tempfile.TemporaryDirectory(prefix="beaml-0004-s5-%s-" % build)
    atexit.register(holder.cleanup)
    root = Path(holder.name)
    if fixture:
        source = s5.fixture_path(kind)
    else:
        source = root / "orders.beaml"
        source.write_bytes(s5.source_text(names, kind).encode())
    snapshot = root / "stored.jsonl"
    snapshot.write_bytes(s5.snapshot_bytes(names, spec))
    return ("gen", source, snapshot)


for _suffix, _names, _fixture in (("", s5.FIXTURE_NAMES, True), ("-random", RANDOM_NAMES, False)):
    for _build in builds(_names):
        arms.VARIANTS["s5-%s%s" % (_build, _suffix)] = variant(_build, _names, _fixture)
    _mfa = "{OrdersBeamlSpike, :%s, 1}" % _names.op.replace(".", "_")
    if _mfa not in arms.WATCHED["gen"]:
        arms.WATCHED["gen"].append(_mfa)


class Slice5Replay:
    names, suffix = None, ""

    def tree(self, build):
        return "s5-%s%s" % (build, self.suffix)

    def msg(self, *parts):
        return " ".join(str(p) for p in parts) + str(self.names)

    def effect_key(self):
        return "OrdersBeamlSpike.%s/1" % self.names.op.replace(".", "_")

    def decode_error(self):
        return '%%OrdersBeamlSpike.%s{reason: "decode"}' % self.names.E

    def replay(self, build, case, records, observe=False):
        replay_input = {"mode": "replay_plain", "trace_id": records[0]["trace_id"], "responses": records}
        if observe:
            replay_input["observe"] = True
        report = arms.harness(self.tree(build), case, replay_input)
        calls = report["calls"]
        seen = {"result": report["result"], "transport": report["transport"], "effect": calls.get(self.effect_key()),
                **{k: calls.get(k) for k in COUNTS},
                "cross_build": report.get("artifact") is not None and records[0].get("artifact_id") != report.get("artifact")}
        if observe:
            seen["unknown_keys"] = [s["attributes"].get("unknown_keys") or [] for s in report.get("spans", [])
                                    if s["name"] == "orders." + self.names.op]
        return seen

    def accepted(self, value, observe=False):
        expected = {"result": {"ok": value}, "transport": 0, "effect": 0, "OrdersApi.Router.call/2": 0,
                    ":gen_tcp.connect/4": 0, ":json.decode/1": 1, FINISH: 1, "cross_build": True}
        if observe:
            expected["unknown_keys"] = [[]]
        return expected

    def live_record(self, build, case, body):
        """One live call through place/1 against a loopback stub. Return (result, the written records)."""
        stub, sent = arms.payments_stub(200, json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode())
        try:
            report = arms.harness(self.tree(build), case, {"mode": "place", "observe": True},
                                  payments_port=stub.server_address[1])
        finally:
            stub.shutdown()
            stub.server_close()
        written = arms.rows(arms.RESULTS / self.tree(build) / "eval" / case / "responses.jsonl")
        return report["result"], len(sent), written

    # F9: the live record of a marked TYPE carries the mark as an integer version.
    def test_F09_live_record_of_M3_has_the_mark_as_integer_version(self):
        N = self.names
        body = {N.k: "order-1", N.t: "settled"}
        result, sent, written = self.live_record("m3", "F9", body)
        one = written[0] if len(written) == 1 else {}
        version = one.get("type", {}).get("version")
        self.assertEqual(
            {"result": {"ok": body}, "sent": 1, "records": 1, "type": s5.st.type_version(N.T, N.M, [N.k, N.t]),
             "integer": True},
            {"result": result, "sent": sent, "records": len(written), "type": one.get("type"),
             "integer": type(version) is int}, self.msg())

    # F11: a record of the mark replays.
    def test_F11_record_of_the_mark_gives_correct_accept(self):
        N = self.names
        record = s5.make_record(N, N.M, "kt")
        self.assertEqual(self.accepted({N.k: "order-1", N.t: "settled"}), self.replay("m3v", "F11", [record]),
                         self.msg())

    # F11c: a stale record below the mark (hand-built, as C9) is a typed decode reject.
    def test_F11c_record_below_the_mark_is_a_typed_decode_reject(self):
        N = self.names
        record = s5.make_record(N, N.M - 2, "ko")
        expected = {"result": {"error": self.decode_error()}, "transport": 0, "effect": 0,
                    "OrdersApi.Router.call/2": 0, ":gen_tcp.connect/4": 0, FINISH: 0, "cross_build": True}
        actual = self.replay("m3", "F11c", [record])
        actual.pop(":json.decode/1", None)
        self.assertEqual(expected, actual, self.msg())

    # F29: the SQUASH changes no replay value and no `type` key of new records.
    def test_F29_v4_records_replay_the_same_on_Q4_and_Q4z(self):
        N = self.names
        expected, actual = {}, {}
        for index, t_value in enumerate(("settled", "pending")):
            for build, version in (("q4", 4), ("q4z", N.V)):
                record = s5.make_record(N, version, "ktx", index)
                case = "F29-%s-%d" % (build, index)
                expected[case] = self.accepted({N.k: "order-1", N.t: t_value, N.x: "r-%d" % (4 + index)}, True)
                actual[case] = self.replay(build, case, [record], observe=True)
        self.assertEqual(expected, actual, self.msg())

    def test_F29_live_records_of_Q4_and_Q4z_have_the_same_type_key(self):
        N = self.names
        body = {N.k: "order-1", N.t: "settled", N.x: "r-9"}
        seen = {}
        for build in ("q4", "q4z"):
            result, sent, written = self.live_record(build, "F29-live-%s" % build, body)
            seen[build] = {"result": result, "sent": sent, "types": [r.get("type") for r in written]}
        # Q4 has v4 by its chain; Q4z has the mark V (4 with the fixture names, b + 3 with random names).
        self.assertEqual(
            {"q4": {"result": {"ok": body}, "sent": 1, "types": [s5.st.type_version(N.T, 4, [N.k, N.t, N.x])]},
             "q4z": {"result": {"ok": body}, "sent": 1, "types": [s5.st.type_version(N.T, N.V, [N.k, N.t, N.x])]}},
            seen, self.msg())


class FixtureNames(Slice5Replay, arms.Case):
    names, suffix = s5.FIXTURE_NAMES, ""


class RandomNames(Slice5Replay, arms.Case):
    names, suffix = RANDOM_NAMES, "-random"


class ZzHarness(arms.Case):
    def test_every_slice5_build_of_this_run_passed_stored(self):
        log = arms.RESULTS / "commands.jsonl"
        runs = [json.loads(line) for line in log.read_text().splitlines()] if log.is_file() else []
        orders = [r for r in runs if r["name"].startswith("s5-") and r["name"].endswith("-generate-orders")]
        self.assertEqual(([], True), ([r["name"] for r in orders if "--stored" not in r["argv"]], len(orders) > 0))

    def test_control_originals_unchanged_by_slice_5_runs(self):
        self.assertEqual(arms.CONTROL_BEFORE, arm_tree.control_hashes())


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    arms.RESULTS.mkdir(parents=True, exist_ok=True)
    print(arms.RESULTS, flush=True)
    unittest.main(verbosity=2)
