"""EXPERIMENT 0004 slice 2 replay cases (README revision 6): C2, C3, C9, C11, C12, C13, C14.
C12 follows DL-054 (README revision 7.2): the stored body is typed by its TYPE VERSION before the rename.
Final review repair: C19 (name reuse) and C20 (rotation), each with fixture names and random names.

Old RESPONSE RECORDS of TYPE VERSION `Payment 1 { order_id status }` (stored/v1.jsonl) replay through the
generated decode of a build with a MIGRATE CHAIN. The trees reuse the arms harness (tests/arms_test.py)
with other Orders sources and RECORD SNAPSHOTS. Mode `replay_plain` returns the decoded value without the
host check `valid_payment!/2`, which knows only `status`.
Cross-build rule (README, artifact check for old records): the harness skips only the caller artifact check
and asserts that the record `artifact_id` differs from the build artifact.
Run serially, loopback only: python3 -B experiments/0004-generated-replay/tests/slice2_replay_test.py [-k NAME]
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
from stored_types_test import type_version  # noqa: E402
import stored_types_test as st  # noqa: E402

EXPERIMENT = arm_tree.EXPERIMENT
V1 = EXPERIMENT / "stored" / "v1.jsonl"
V1_V2 = EXPERIMENT / "stored" / "v1-v2.jsonl"
arms.VARIANTS.update({
    "s2-chain": ("gen", EXPERIMENT / "slice2/N-chain/orders.beaml", V1),   # C2, C3, C11, C12, C13
    "s2-nochain": ("gen", EXPERIMENT / "drift/N/orders.beaml", arms.EMPTY_SNAPSHOT),  # C9 (the C6 build)
    "s2-chain2": ("gen", EXPERIMENT / "slice2/N2-chain/orders.beaml", V1),  # C14
})


def chain_variant(kind, names, fixture):
    """C19 and C20 tree: the chain source (fixture file or template with random names), snapshot v1..v4."""
    holder = tempfile.TemporaryDirectory(prefix="beaml-0004-s2-%s-" % kind)
    atexit.register(holder.cleanup)
    root = Path(holder.name)
    source = EXPERIMENT / st.FIXTURE_SOURCES[kind]
    if not fixture:
        source = root / "orders.beaml"
        source.write_text(st.template_source(names, kind))
    snapshot = root / "stored.jsonl"
    snapshot.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n"
                                for r in st.chain_records(names, kind, [1, 2, 3, 4])))
    return ("gen", source, snapshot)


RANDOM_NAMES = st.random_names()
arms.VARIANTS.update({
    "s2-reuse": chain_variant("reuse", st.FIXTURE_NAMES, True),
    "s2-reuse-random": chain_variant("reuse", RANDOM_NAMES, False),
    "s2-rotation": chain_variant("rotation", st.FIXTURE_NAMES, True),
    "s2-rotation-random": chain_variant("rotation", RANDOM_NAMES, False),
})
# Independent of the compiler: per TYPE VERSION 1..4, the field that holds value X (newest: first field)
# and the field that holds value Y (newest: second field). Roles as in stored_types_test.chain_spec.
CARRIERS = {"reuse": [("s", "c"), ("t", "c"), ("t", "s"), ("p", "s")],
            "rotation": [("b", "a"), ("b", "r"), ("a", "r"), ("a", "b")]}
KEYS = arms.GenTypeMismatch.REPLAY_KEYS
NEW_BODY = b'{"order_id":"order-1","state":"authorized"}'


def records(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def counts(tree, name, record, observe=False):
    """One REPLAY RUN of one record. Return the counts and the artifact pair of the cross-build rule."""
    replay_input = {"mode": "replay_plain", "trace_id": record["trace_id"], "responses": [record]}
    if observe:
        replay_input["observe"] = True
    report = arms.harness(tree, name, replay_input)
    seen = arms.replay_counts(report, KEYS)
    if observe:
        seen["replay_hint"] = [s["attributes"].get("unknown_keys") for s in report.get("spans", [])
                               if s["name"] == "orders.payments.authorize"]
    pair = {"record_artifact_id": record.get("artifact_id"), "build_artifact_id": report.get("artifact")}
    arms.save(arms.RESULTS / tree / "eval" / name / "artifacts.json", pair)
    seen["cross_build"] = pair["build_artifact_id"] is not None and pair["record_artifact_id"] != pair["build_artifact_id"]
    return seen


def accepted(payment, hint=None):
    expected = {"result": {"ok": payment}, "transport": 0, "OrdersApi.Router.call/2": 0,
                "OrdersBeamlSpike.payments_authorize/1": 0, ":gen_tcp.connect/4": 0, ":json.decode/1": 1,
                "OrdersBeamlSpike.finish/1": 1, "ProbeSupport.valid_payment!/2": 0, "cross_build": True}
    if hint is not None:
        expected["replay_hint"] = hint
    return expected


def decode_rejected():
    return {"result": {"error": arms.DECODE_ERROR}, "transport": 0, "OrdersApi.Router.call/2": 0,
            "OrdersBeamlSpike.payments_authorize/1": 0, ":gen_tcp.connect/4": 0, ":json.decode/1": 1,
            "OrdersBeamlSpike.finish/1": 0, "ProbeSupport.valid_payment!/2": 0, "cross_build": True}


class ChainReplay(arms.Case):
    """Build: DRIFT N with `migrate Payment v1 -> v2 { rename status -> state }`, RECORD SNAPSHOT v1."""

    def test_C2_old_v1_record_replays_with_state_from_status(self):
        old = records(V1)[0]
        self.assertEqual(accepted({"order_id": "order-1", "state": "authorized"}), counts("s2-chain", "C2", old))

    def test_C2_new_call_records_type_version_2(self):
        stub, sent = arms.payments_stub(200, NEW_BODY)
        try:
            report = arms.harness("s2-chain", "C2-new", {"mode": "place", "observe": True},
                                  payments_port=stub.server_address[1])
        finally:
            stub.shutdown()
            stub.server_close()
        written = arms.rows(arms.RESULTS / "s2-chain" / "eval" / "C2-new" / "responses.jsonl")
        self.assertEqual(
            {"result": {"ok": {"order_id": "order-1", "state": "authorized"}}, "sent": 1, "records": 1,
             "type": type_version("Payment", 2, ["order_id", "state"]), "artifact_is_build": True},
            {"result": report["result"], "sent": len(sent), "records": len(written),
             "type": written[0].get("type") if len(written) == 1 else None,
             "artifact_is_build": len(written) == 1 and written[0].get("artifact_id") == report.get("artifact")})

    def test_C3_both_stored_versions_replay(self):
        old, new = records(V1_V2)
        self.assertEqual(
            {"v1": accepted({"order_id": "order-1", "state": "authorized"}),
             "v2": accepted({"order_id": "order-1", "state": "settled"})},
            {"v1": counts("s2-chain", "C3-v1", old), "v2": counts("s2-chain", "C3-v2", new)})

    def test_C11_extra_key_does_not_replace_the_old_name(self):
        body = b'{"order_id":"order-1","status":"captured","fraud_score":"0.9"}'
        record = st.with_value(records(V1)[0], json.loads(body))
        self.assertEqual(accepted({"order_id": "order-1", "state": "captured"}, hint=[["fraud_score"]]),
                         counts("s2-chain", "C11", record, observe=True))

    def test_C12_v1_record_with_both_names_reads_the_old_field_by_its_version(self):
        # DL-054 supersedes "current name wins": version 1 is {order_id, status}; state is a stray key.
        body = b'{"order_id":"order-1","state":"settled","status":"authorized"}'
        record = st.with_value(records(V1)[0], json.loads(body))
        self.assertEqual(accepted({"order_id": "order-1", "state": "authorized"}, hint=[["state"]]),
                         counts("s2-chain", "C12", record, observe=True))

    def test_C13_neither_name_is_typed_decode_error(self):
        body = b'{"order_id":"order-1","fraud_score":"0.9"}'
        record = st.with_value(records(V1)[0], json.loads(body))
        self.assertEqual(decode_rejected(), counts("s2-chain", "C13", record))


class StaleSnapshotReplay(arms.Case):
    """C9: the C6 build (DRIFT N, no chain, empty RECORD SNAPSHOT) meets a v1 record."""

    def test_C9_v1_record_against_build_without_chain_is_typed_decode_error(self):
        self.assertEqual(decode_rejected(), counts("s2-nochain", "C9", records(V1)[0]))


class SecondRenameReplay(arms.Case):
    """C14: `Payment { order_ref status }` with `migrate Payment v1 -> v2 { rename order_id -> order_ref }`."""

    def test_C14_v1_record_replays_with_order_ref_from_order_id(self):
        self.assertEqual(accepted({"order_ref": "order-1", "status": "authorized"}),
                         counts("s2-chain2", "C14", records(V1)[0]))


class ChainByVersion:
    """C19 and C20: the decode reads a record by its TYPE VERSION. A live body is the newest version."""
    tree, kind, names = None, None, None

    def body(self, version, tag):
        x, y = (self.names.chain[role] for role in CARRIERS[self.kind][version - 1])
        return json.dumps({x: "X-" + tag, y: "Y-" + tag}, separators=(",", ":")).encode()

    def current(self, tag):
        first, second = st.chain_spec(self.names, self.kind)[0]
        return {first: "X-" + tag, second: "Y-" + tag}

    def test_build_compiles_with_warnings_as_errors(self):
        self.assertTrue(arms.build(self.tree)["strict"], "mix compile --force --warnings-as-errors failed")

    def test_live_current_body_decodes_to_the_current_fields(self):
        stub, sent = arms.payments_stub(200, self.body(4, "live"))
        try:
            report = arms.harness(self.tree, "live", {"mode": "place", "observe": True},
                                  payments_port=stub.server_address[1])
        finally:
            stub.shutdown()
            stub.server_close()
        written = arms.rows(arms.RESULTS / self.tree / "eval" / "live" / "responses.jsonl")
        newest = st.chain_spec(self.names, self.kind)[2][3]
        self.assertEqual(
            {"result": {"ok": self.current("live")}, "sent": 1, "records": 1,
             "type": type_version(self.names.T, 4, newest), "unknown_keys": []},
            {"result": report["result"], "sent": len(sent), "records": len(written),
             "type": written[0].get("type") if len(written) == 1 else None,
             "unknown_keys": written[0].get("unknown_keys") if len(written) == 1 else None},
            "names: %s" % self.names.chain)

    def test_each_stored_version_replays_to_the_current_fields(self):
        expected, actual = {}, {}
        for version in (1, 2, 3, 4):
            tag = "v%d" % version
            [record] = st.chain_records(self.names, self.kind, [version])
            expected[tag] = accepted(self.current(tag))
            actual[tag] = counts(self.tree, tag, st.with_value(record, json.loads(self.body(version, tag))))
        self.assertEqual(expected, actual, "names: %s" % self.names.chain)


class C19NameReuseFixture(ChainByVersion, arms.Case):
    tree, kind, names = "s2-reuse", "reuse", st.FIXTURE_NAMES


class C19NameReuseRandom(ChainByVersion, arms.Case):
    tree, kind, names = "s2-reuse-random", "reuse", RANDOM_NAMES


class C20RotationFixture(ChainByVersion, arms.Case):
    tree, kind, names = "s2-rotation", "rotation", st.FIXTURE_NAMES


class C20RotationRandom(ChainByVersion, arms.Case):
    tree, kind, names = "s2-rotation-random", "rotation", RANDOM_NAMES


class ZzControlUnchanged(arms.Case):
    def test_control_originals_unchanged_by_slice_2_runs(self):
        self.assertEqual(arms.CONTROL_BEFORE, arm_tree.control_hashes())


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    arms.RESULTS.mkdir(parents=True, exist_ok=True)
    print(arms.RESULTS, flush=True)
    unittest.main(verbosity=2)
