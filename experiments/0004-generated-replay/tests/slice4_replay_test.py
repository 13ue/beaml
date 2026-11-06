"""EXPERIMENT 0004 slice 4 replay and live cases (README revision 8.1): E2 and E7 (`retired/0`), E3, E3b, E4,
E7, E10, E15b, E17b, and the harness check that every GEN build passes `--stored`.

The trees reuse the arms harness (tests/arms_test.py), mode `replay_plain` and the eval VM of slices 2 and 3.
Each build runs with fixture names (slice4/ sources) and with random names, a random `keep` number and
random constants from the template in slice4_retire_test.py. The harness passes the record unchanged to
`Replay.run/3`. Expected values come from the tables below (README, Cases (slice 4)); never from the compiler.
A `Retired` reject is read from its `inspect` text: `%OrdersBeamlSpike.Replay.Retired{...}` with the fields
`operation` and `keep_days` in any order.
Run serially, loopback only: python3 -B experiments/0004-generated-replay/tests/slice4_replay_test.py [-k NAME]
"""
import atexit
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arm_tree  # noqa: E402
import arms_test as arms  # noqa: E402
import slice2_replay_test  # noqa: E402,F401  (registers the slice 2 trees for the harness check)
import slice3_replay_test  # noqa: E402,F401  (registers the slice 3 trees for the harness check)
import slice4_retire_test as r4  # noqa: E402

EXPERIMENT = arm_tree.EXPERIMENT
RANDOM_NAMES = r4.random_names()
# Tree: source kind, RECORD SNAPSHOT label (README, Cases (slice 4)).
BUILDS = {"gr": ("G+r", "v1"), "gr0": ("G+r0", "v1"), "pr": ("P+r", "v1"), "q4": ("Q4", "q-v3"),
          "q4s": ("Q4s", "q-v3")}
SNAPSHOT_DIGESTS = {}


def variant(build, names, fixture):
    kind, label = BUILDS[build]
    holder = tempfile.TemporaryDirectory(prefix="beaml-0004-s4-%s-" % build)
    atexit.register(holder.cleanup)
    root = Path(holder.name)
    if fixture:
        source = r4.fixture_path(kind)
    else:
        source = root / "orders.beaml"
        source.write_bytes(r4.source_text(names, kind).encode())
    if fixture and label == "v1":
        snapshot = EXPERIMENT / "stored" / "v1.jsonl"
    else:
        snapshot = root / "stored.jsonl"
        snapshot.write_bytes(r4.snapshot_bytes(names, label))
    return ("gen", source, snapshot)


for _build in BUILDS:
    for _suffix, _names, _fixture in (("", r4.FIXTURE_NAMES, True), ("-random", RANDOM_NAMES, False)):
        _tree = "s4-%s%s" % (_build, _suffix)
        arms.VARIANTS[_tree] = variant(_build, _names, _fixture)
        SNAPSHOT_DIGESTS[_tree] = hashlib.sha256(arms.VARIANTS[_tree][2].read_bytes()).hexdigest()

# The EFFECT function of each operation (`a.b` gives `a_b/1`) is watched in the eval VM.
for _names in (r4.FIXTURE_NAMES, RANDOM_NAMES):
    for _op in (_names.old, _names.new):
        _mfa = "{OrdersBeamlSpike, :%s, 1}" % _op.replace(".", "_")
        if _mfa not in arms.WATCHED["gen"]:
            arms.WATCHED["gen"].append(_mfa)

RETIRED = re.compile(r"^%OrdersBeamlSpike\.Replay\.Retired\{(.*)\}$")
FIELD = re.compile(r'(\w+): ("(?:[^"\\]|\\.)*"|\d+)')
RETIRED_SCRIPT = 'IO.puts("RETIRED " <> IO.iodata_to_binary(:json.encode(OrdersBeamlSpike.Replay.retired())))'


def effect_key(op):
    return "OrdersBeamlSpike.%s/1" % op.replace(".", "_")


def result_of(report):
    """The report result; a `Retired` reject becomes {"retired": {field: value}}."""
    result = report["result"]
    match = RETIRED.match(result.get("error", "")) if isinstance(result.get("error"), str) else None
    if match:
        return {"retired": {name: json.loads(value) for name, value in FIELD.findall(match.group(1))}}
    return result


class Slice4Replay:
    names, suffix = None, ""

    def tree(self, build):
        return "s4-%s%s" % (build, self.suffix)

    def msg(self, *parts):
        return " ".join(str(p) for p in parts) + str(self.names)

    def record(self, op_role, version, roles, index=0, body=None):
        return r4.make_record(self.names, op_role, ("T", version, roles), index, body)

    def replay(self, build, case, records, trace_id, live_op=None, observe=False):
        """One REPLAY RUN. Return the result and the counts; `live_op` is the operation of the tree's EFFECT."""
        replay_input = {"mode": "replay_plain", "trace_id": trace_id, "responses": records}
        if observe:
            replay_input["observe"] = True
        report = arms.harness(self.tree(build), case, replay_input)
        calls = report["calls"]
        seen = {"result": result_of(report), "transport": report["transport"],
                **{k: calls.get(k) for k in ("OrdersApi.Router.call/2", ":gen_tcp.connect/4", ":json.decode/1",
                                              "OrdersBeamlSpike.finish/1")}}
        if live_op:
            seen["effect"] = calls.get(effect_key(live_op))
        if observe:
            seen["unknown_keys"] = [s["attributes"].get("unknown_keys") or [] for s in report.get("spans", [])
                                    if s["name"] == "orders." + self.names.old]
        if records:
            seen["cross_build"] = (report.get("artifact") is not None
                                   and records[0].get("artifact_id") != report.get("artifact"))
        return seen

    def rejected(self, result, live_op, cross_build=True):
        expected = {"result": result, "transport": 0, "OrdersApi.Router.call/2": 0, ":gen_tcp.connect/4": 0,
                    ":json.decode/1": 0, "OrdersBeamlSpike.finish/1": 0}
        if live_op:
            expected["effect"] = 0
        if cross_build is not None:
            expected["cross_build"] = cross_build
        return expected

    def retired(self, build):
        """`Replay.retired/0` of the tree, read in the eval VM of the release."""
        built = arms.build(self.tree(build))
        out = arms.RESULTS / self.tree(build) / "eval" / "retired"
        out.mkdir(parents=True, exist_ok=True)
        name = "%s-eval-retired" % self.tree(build)
        code, text = arms.command(name, [built["bin"], "eval", RETIRED_SCRIPT], arm_tree.REPO,
                                  env=arms.orders_env(out, arms.refused_port()), timeout=120)
        lines = [line[8:] for line in text.splitlines() if line.startswith("RETIRED ")]
        self.assertEqual((0, 1), (code, len(lines)), self.msg("retired/0 eval:", arms.stderr_head(name)))
        return json.loads(lines[0])

    # E2, E7: generated metadata.
    def test_E02_retired_metadata_names_the_operation_and_keep_days(self):
        N = self.names
        self.assertEqual([{"operation": N.old, "keep_days": N.n}], self.retired("gr"), self.msg())

    def test_E07_keep_0_days_metadata(self):
        self.assertEqual([{"operation": self.names.old, "keep_days": 0}], self.retired("gr0"), self.msg())

    # E3, E3b, E4: the G+r build.
    def test_E03_retired_record_gives_the_typed_Retired_reject(self):
        N = self.names
        record = self.record("old", 1, "ko")
        self.assertEqual(self.rejected({"retired": {"operation": N.old, "keep_days": N.n}}, N.new),
                         self.replay("gr", "E3", [record], record["trace_id"], N.new), self.msg())

    def test_E03b_record_of_the_live_operation_replays_beside_a_retire_line(self):
        # Kills "every record is Retired when retired/0 is not empty".
        N = self.names
        record = self.record("new", 1, "ko")
        expected = {"result": {"ok": {N.k: "order-1", N.o: "authorized"}}, "transport": 0,
                    "OrdersApi.Router.call/2": 0, ":gen_tcp.connect/4": 0, ":json.decode/1": 1,
                    "OrdersBeamlSpike.finish/1": 1, "effect": 0, "cross_build": True}
        self.assertEqual(expected, self.replay("gr", "E3b", [record], record["trace_id"], N.new), self.msg())

    def test_E04_live_call_through_place_records_the_new_operation(self):
        N = self.names
        stub_body = json.dumps({N.k: "order-1", N.o: "authorized"}, separators=(",", ":")).encode()
        stub, sent = arms.payments_stub(200, stub_body)
        try:
            report = arms.harness(self.tree("gr"), "E4", {"mode": "place", "observe": True},
                                  payments_port=stub.server_address[1])
        finally:
            stub.shutdown()
            stub.server_close()
        written = arms.rows(arms.RESULTS / self.tree("gr") / "eval" / "E4" / "responses.jsonl")
        one = written[0] if len(written) == 1 else {}
        self.assertEqual(
            {"result": {"ok": {N.k: "order-1", N.o: "authorized"}}, "sent": 1, "records": 1, "operation": N.new,
             "type": r4.s3.type_version(N.T, 1, [N.k, N.o]), "finish": 1},
            {"result": report["result"], "sent": len(sent), "records": len(written), "operation": one.get("operation"),
             "type": one.get("type"), "finish": report["calls"].get("OrdersBeamlSpike.finish/1")}, self.msg())

    # E7: keep 0 days; nothing deleted.
    def test_E07_keep_0_days_reject_and_snapshot_unchanged(self):
        N = self.names
        record = self.record("old", 1, "ko")
        self.assertEqual(self.rejected({"retired": {"operation": N.old, "keep_days": 0}}, N.new),
                         self.replay("gr0", "E7", [record], record["trace_id"], N.new), self.msg())
        snapshot = arms.VARIANTS[self.tree("gr0")][2]
        self.assertEqual(SNAPSHOT_DIGESTS[self.tree("gr0")], hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                         "the RECORD SNAPSHOT must stay byte-identical")

    # E10: a source with a RETIRE LINE and no EFFECT.
    def test_E10_retired_record_without_effect_gives_Retired(self):
        N = self.names
        record = self.record("old", 1, "ko")
        self.assertEqual(self.rejected({"retired": {"operation": N.old, "keep_days": N.n}}, None),
                         self.replay("pr", "E10", [record], record["trace_id"]), self.msg())

    def test_E10_record_of_another_operation_gives_operation_mismatch(self):
        record = self.record("new", 1, "ko")
        self.assertEqual(self.rejected({"error": "operation_mismatch"}, None),
                         self.replay("pr", "E10-other", [record], record["trace_id"]), self.msg())

    def test_E10_no_record_gives_missing_response(self):
        record = self.record("old", 1, "ko")
        self.assertEqual(self.rejected({"error": "missing_response"}, None, cross_build=None),
                         self.replay("pr", "E10-none", [], record["trace_id"]), self.msg())

    # E15b: the removal does not change the replay value of a needed record.
    def test_E15b_version_3_records_give_the_same_value_on_Q4_and_Q4s(self):
        N = self.names
        expected, actual = {}, {}
        for index, t_value in enumerate(("settled", "pending")):
            record = self.record("old", 3, "ktc", index)
            for build in ("q4", "q4s"):
                case = "E15b-%s-%d" % (build, index)
                expected[case] = {"result": {"ok": {N.k: "order-1", N.t: t_value, N.x: N.cx}}, "transport": 0,
                                  "OrdersApi.Router.call/2": 0, ":gen_tcp.connect/4": 0, ":json.decode/1": 1,
                                  "OrdersBeamlSpike.finish/1": 1, "effect": 0, "unknown_keys": [[]],
                                  "cross_build": True}
                actual[case] = self.replay(build, case, [record], record["trace_id"], N.old, observe=True)
        self.assertEqual(expected, actual, self.msg())

    # E17b: a stale v1 record against the shortened chain.
    def test_E17b_version_1_record_on_Q4s_is_a_typed_decode_reject(self):
        N = self.names
        record = self.record("old", 1, "ko")
        expected = self.rejected({"error": arms.DECODE_ERROR}, N.old)
        actual = self.replay("q4s", "E17b", [record], record["trace_id"], N.old)
        actual.pop(":json.decode/1", None)
        expected.pop(":json.decode/1")
        self.assertEqual(expected, actual, self.msg())

    def test_build_gr_compiles_with_warnings_as_errors(self):
        self.assertTrue(arms.build(self.tree("gr"))["strict"], "mix compile --warnings-as-errors failed" + self.msg())


class FixtureNames(Slice4Replay, arms.Case):
    names, suffix = r4.FIXTURE_NAMES, ""


class RandomNames(Slice4Replay, arms.Case):
    names, suffix = RANDOM_NAMES, "-random"


class ZzHarness(arms.Case):
    def test_every_gen_tree_has_a_record_snapshot(self):
        # README revision 8.1: the claim holds only with a RECORD SNAPSHOT. E1b shows the block needs it.
        self.assertEqual([], sorted(name for name, (arm, _, stored) in arms.VARIANTS.items()
                                    if arm == "gen" and stored is None))

    def test_every_gen_build_of_this_run_passed_stored(self):
        log = arms.RESULTS / "commands.jsonl"
        runs = [json.loads(line) for line in log.read_text().splitlines()] if log.is_file() else []
        orders = [r for r in runs if r["name"].endswith("-generate-orders")
                  and arms.VARIANTS.get(r["name"][:-len("-generate-orders")], ("",))[0] == "gen"]
        self.assertEqual(([], True), ([r["name"] for r in orders if "--stored" not in r["argv"]], len(orders) > 0))

    def test_control_originals_unchanged_by_slice_4_runs(self):
        self.assertEqual(arms.CONTROL_BEFORE, arm_tree.control_hashes())


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    arms.RESULTS.mkdir(parents=True, exist_ok=True)
    print(arms.RESULTS, flush=True)
    unittest.main(verbosity=2)
