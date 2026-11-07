"""EXPERIMENT 0004 slice 6b step 6a: RESPONSE RECORD version 2, the projection (DL-105, D6B-53 to D6B-60, D6B-59).

Plan: workflow/2026-11-07/slice6b-redacted/plan.md, "First failing test per sub-step", 6a (P1 to P6). Ledger:
workflow/2026-11-07/slice6b-records-v2/ (spec.md, notes.md). Source: arms/gen/orders.beaml, `--stored stored/empty.jsonl`.

The release-free harness of step 7 (tests/slice6_decode_test.py STUBS): `ProbeSupport.Capture.write/2` keeps the record
in the process dictionary. `stored.(status, bytes)` sends the captured record through `:json.encode` and `:json.decode`
(the encode of the real `ProbeSupport.json/1`), so each case reads the record as a RECORD SNAPSHOT line holds it.
Expected values and digests come from the plan and from Python (`stored_types_test.value_sha256`), never from the new
compiler. P6 asserts the exact message of D6B-59.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_record_test.py [-k NAME]
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import slice6_decode_test as sd  # noqa: E402
import slice6_failure_test as sf  # noqa: E402
import stored_types_test as st  # noqa: E402

ORDERS = EXPERIMENT / "arms" / "gen" / "orders.beaml"
# One version 1 record: stored/v1.jsonl as it was before the 6a conversion (D6B-69), correct `type` key.
V1_RECORD = EXPERIMENT / "slice6" / "record" / "stored-v1.jsonl"

PAYMENT = {"order_id": "order-1", "status": "authorized"}
VALID_BODY = b'{"order_id":"order-1","status":"authorized"}'
REORDERED_BODY = b'{"status":"authorized","order_id":"order-1"}'
UNKNOWN_KEY_BODY = b'{"order_id":"order-1","status":"authorized","fraud_score":"low"}'
MISSING_KEY_BODY = b'{"order_id":"order-1"}'
MISSING_KEY_EXTRA_BODY = b'{"order_id":"order-1","fraud_score":"low"}'
NOT_JSON_BODY = b'not json'
NON_ASCII = {"order_id": "order-1", "status": "autorisé ✓ \U0001f600"}
NON_ASCII_BODY = json.dumps(NON_ASCII, ensure_ascii=False).encode()
BODY_KEYS = ("body_base64", "body_length", "body_sha256")
# D6B-53, sorted. `unknown_fields` only where step 7 writes it; arms/gen/orders.beaml has no enum, so none here.
RECORD_KEYS = ["artifact_id", "attempt", "client_span_id", "operation", "redacted", "request", "status", "trace_id",
               "type", "unknown_keys", "value", "value_sha256", "version"]


def b(data):
    """Bytes as an Elixir binary literal."""
    return "<<%s>>" % ",".join(str(c) for c in data)


def ex(value):
    """A JSON value as the Elixir term that `:json.decode/1` gives."""
    if value is None:
        return ":null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return b(value.encode())
    if isinstance(value, list):
        return "[%s]" % ", ".join(ex(v) for v in value)
    if isinstance(value, dict):
        return "%%{%s}" % ", ".join("%s => %s" % (ex(k), ex(v)) for k, v in value.items())
    return json.dumps(value)


HELPERS = r'''
captured = fn status, bytes ->
  Process.delete(:capture)
  BeamlSpike.Replay.record(%{"order_id" => "order-1"}, status, bytes)
  Process.get(:capture)
end
text = fn status, bytes -> captured.(status, bytes) |> :json.encode() |> IO.iodata_to_binary() end
stored = fn status, bytes -> text.(status, bytes) |> :json.decode() end
replay = fn record -> BeamlSpike.Replay.run(%{"order_id" => "order-1"}, record["trace_id"], [record]) end
digest_mismatch = {:error, :body_digest_mismatch}
'''
V1_LINE = V1_RECORD.read_text().splitlines()[0] if V1_RECORD.is_file() else "{}"
DECODE_ERROR = '{:error, %BeamlSpike.PaymentError{reason: "decode"}}'
U, M, MX, N, R, V = (b(UNKNOWN_KEY_BODY), b(MISSING_KEY_BODY), b(MISSING_KEY_EXTRA_BODY), b(NOT_JSON_BODY),
                     b(REORDERED_BODY), b(VALID_BODY))
CASES = {
    # P1: the writer shape (D6B-53, D6B-54, D6B-55, D6B-56, D6B-58).
    "P1_version_is_2": 'stored.(200, %s)["version"] == 2' % U,
    "P1_value_is_the_declared_keys": 'stored.(200, %s)["value"] == %s' % (U, ex(PAYMENT)),
    "P1_redacted_is_empty": 'stored.(200, %s)["redacted"] == []' % U,
    "P1_unknown_keys_are_names": 'stored.(200, %s)["unknown_keys"] == %s' % (U, ex(["fraud_score"])),
    "P1_value_sha256_is_the_canonical_digest": ('stored.(200, %s)["value_sha256"] == %s'
                                                % (U, ex(st.value_sha256(PAYMENT, ["fraud_score"])))),
    "P1_no_body_keys": 'Enum.all?(%s, fn k -> not Map.has_key?(stored.(200, %s), k) end)' % (ex(list(BODY_KEYS)), U),
    "P1_unknown_value_is_in_no_record_byte": 'not String.contains?(text.(200, %s), "low")' % U,
    # RED repair RR6A-2: the exact key set, so no second key can keep the raw body (DL-105).
    "P1_key_set_is_D6B_53": 'Enum.sort(Map.keys(stored.(200, %s))) == %s' % (U, ex(RECORD_KEYS)),
    "P1_request_unchanged": 'stored.(200, %s)["request"] == %s' % (U, ex({"order_id": "order-1"})),
    # P2: the REPLAY RUN reads `value` and checks the digest (D6B-58, D6B-59 second guard, D6B-60).
    "P2_replay_of_the_record": 'replay.(stored.(200, %s)) == {:ok, %s}' % (U, ex(PAYMENT)),
    "P2_tampered_value_is_digest_mismatch": (
        'replay.(Map.update!(stored.(200, %s), "value", &Map.put(&1, "status", "declined"))) == digest_mismatch' % U),
    "P2_tampered_unknown_keys_is_digest_mismatch": (
        'replay.(Map.put(stored.(200, %s), "unknown_keys", [])) == digest_mismatch' % U),
    "P2_version_1_record_is_digest_mismatch": 'replay.(:json.decode(%s)) == digest_mismatch' % b(V1_LINE.encode()),
    # a1 (DL-110, plan Q6B-10 option A text): the key order of the body does not matter.
    "a1_key_order_does_not_matter": ('stored.(200, %s)["value_sha256"] == %s and replay.(stored.(200, %s)) == {:ok, %s}'
                                     % (R, ex(st.value_sha256(PAYMENT)), R, ex(PAYMENT))),
    # P3: a body that fails the decode keeps its declared keys and the names of the other keys (D6B-56).
    "P3_failed_decode_value": 'stored.(200, %s)["value"] == %s' % (M, ex({"order_id": "order-1"})),
    "P3_failed_decode_unknown_keys": 'stored.(200, %s)["unknown_keys"] == %s' % (MX, ex(["fraud_score"])),
    "P3_failed_decode_digest": ('stored.(200, %s)["value_sha256"] == %s'
                                % (MX, ex(st.value_sha256({"order_id": "order-1"}, ["fraud_score"])))),
    "P3_failed_decode_replays_as_decode": 'replay.(stored.(200, %s)) == %s' % (M, DECODE_ERROR),
    # P4: a body that is not JSON gives `value: null`; a 503 body gets the same projection (D6B-54, D6B-57).
    "P4_not_json_value_is_null": ('Map.fetch(stored.(200, %s), "value") == {:ok, :null} and '
                                  'stored.(200, %s)["unknown_keys"] == [] and stored.(200, %s)["version"] == 2'
                                  % (N, N, N)),
    "P4_not_json_digest": 'stored.(200, %s)["value_sha256"] == %s' % (N, ex(st.value_sha256(None))),
    "P4_status_503_same_projection": ('stored.(503, %s)["value"] == %s and stored.(503, %s)["value_sha256"] == %s'
                                      % (V, ex(PAYMENT), V, ex(st.value_sha256(PAYMENT)))),
    # P5: digest parity, Elixir writer against Python, for an ASCII and a non-ASCII value (D6B-58, limit L4).
    "P5_ascii_parity": 'stored.(200, %s)["value_sha256"] == %s' % (V, ex(st.value_sha256(PAYMENT))),
    "P5_non_ascii_parity": ('stored.(200, %s)["value_sha256"] == %s and replay.(stored.(200, %s)) == {:ok, %s}'
                            % (b(NON_ASCII_BODY), ex(st.value_sha256(NON_ASCII)), b(NON_ASCII_BODY), ex(NON_ASCII))),
}


def version_error(version, source, line=1):
    """D6B-59 text (plan repair O1)."""
    return ("error: stored RESPONSE RECORD has record version %s; this build reads record version 2 only (DL-105)\n"
            "  record source: %s:%d (line %d)" % (version, source, line, line))


class Slice6Record(unittest.TestCase):
    maxDiff = None
    setUp = sf.Slice6Failure.setUp
    compile = sf.Slice6Failure.compile
    run_runtime = sd.Slice6Decode.run_runtime

    def assert_rejected(self, stored, message):
        code, stdout, stderr = self.compile(ORDERS, ["--stored", str(stored)])
        self.assertEqual((1, "", message), (code, stdout, stderr.strip()),
                         "expected exit 1, no stdout and the exact message")

    def test_runtime_record_version_2(self):
        self.run_runtime(CASES, source=ORDERS, script=HELPERS, stored=sf.EMPTY_STORED)

    def test_P6_version_1_record_blocks_the_build(self):
        self.assert_rejected(V1_RECORD, version_error(1, V1_RECORD))

    def test_P6_record_without_version_blocks_the_build(self):
        record = {k: v for k, v in json.loads(V1_LINE).items() if k != "version"}
        stored = self.work / "stored-none.jsonl"
        stored.write_text(json.dumps(record, separators=(",", ":")) + "\n")
        self.assert_rejected(stored, version_error("none", stored))

    def test_P6_version_1_record_after_a_version_2_record_blocks_at_its_line(self):
        stored = self.work / "stored-mixed.jsonl"
        stored.write_text((EXPERIMENT / "stored" / "v1.jsonl").read_text() + V1_LINE + "\n")
        self.assert_rejected(stored, version_error(1, stored, 2))

    def test_P6_version_2_record_builds(self):
        # Guard: the converted stored/v1.jsonl (version 2, TYPE VERSION Payment 1) is no version error.
        code, stdout, stderr = self.compile(EXPERIMENT / "slice2" / "N-chain" / "orders.beaml",
                                            ["--stored", str(EXPERIMENT / "stored" / "v1.jsonl")])
        self.assertEqual((0, ""), (code, stderr.strip()))


if __name__ == "__main__":
    unittest.main()
