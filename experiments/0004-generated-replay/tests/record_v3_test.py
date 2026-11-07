"""EXPERIMENT 0005 prerequisite P2: RECORD FORMAT v3, one record core for every EFFECT stream (DL-143).

Ledger: experiments/0004-generated-replay/workflow/2026-11-07/record-format-v3/ (plan.md with "Plan repair",
decisions.md, plan-review.md with the re-check notes N1 to N3, red-plan.md). Defaults: QV3-1 to QV3-6 A, QV3-7 A
(count lines only when M > 0), QV3-8 B (a rejected RESPONSE RECORD skips the value, path and W2 checks; the orphan
and held checks still read it). Expected values come from the plan, DL-143 and `stored_types_test.value_sha256`, or
from the P2 base compiler where the plan says "text unchanged" (V15, V18, V24); never from the new compiler.
Fixtures: slice6/record-v3/ (written in RED); the converter convert_v3.py lives in the ledger (GREEN runs it once).

Five pin sites move together with the P2 bytes (RV3-09, RV3-14; byte-pin memory note):
  1. tests/slice5_syntax_test.py PIN               -> the P2 GREEN commit hash, in the commit after GREEN
  2. tests/slice6_pipe_test.py EFFECT_OUTPUTS      -> P2 bytes, in GREEN (also read by slice6_struct_order_test.py)
  3. tests/slice6_host_struct_test.py BYTE_GUARD   -> P2 bytes, in GREEN
  4. slice6/effect-reach/byte-guard.json           -> P2 bytes, in GREEN (keep the (71, 40) setup invariant)
  5. tests/slice6_entry_test.py BASE (N13)         -> the P2 GREEN commit hash, in the commit after GREEN
V18 is the diff proof: it compares against P2_BASE, the HEAD at RED (the slice 6d commits are in it).
Run: python3 -B experiments/0004-generated-replay/tests/record_v3_test.py [-k NAME]
Scratch compiler: BEAML_SPIKE=<git archive build>/target/debug/beaml-spike (another worker may run the full run.py).
"""
import difflib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT, REPO  # noqa: E402
import slice5_syntax_test as s5  # noqa: E402
import slice6_decode_ctor_test as sdc  # noqa: E402
import slice6_decode_test as sd  # noqa: E402
import slice6_entry_test as se  # noqa: E402
import slice6_record_test as sr  # noqa: E402
import slice6_redacted_test as srd  # noqa: E402
import stored_types_test as st  # noqa: E402

P2_BASE = "545dded0"  # HEAD at GREEN start (RED: 31d83754); V18 and V18b compile with it (git archive build)
LEDGER = EXPERIMENT / "workflow" / "2026-11-07" / "record-format-v3"
FIX = EXPERIMENT / "slice6" / "record-v3"
ORDERS = EXPERIMENT / "arms" / "gen" / "orders.beaml"
CTOR = EXPERIMENT / "slice6" / "decode-ctor" / "orders.beaml"
DECODE = EXPERIMENT / "slice6" / "decode" / "orders.beaml"
REDACTED = EXPERIMENT / "slice6" / "redacted" / "orders.beaml"
N_CHAIN = EXPERIMENT / "slice2" / "N-chain" / "orders.beaml"
EMPTY = ["--stored", str(EXPERIMENT / "stored" / "empty.jsonl")]
ex = sr.ex

# DL-143 core (QV3-1 A, QV3-2 A, RV3-03), the same 14 keys in every stream; HTTP extras flat (QV3-3 A).
CORE = sorted(["version", "trace_id", "span_id", "artifact_id", "operation", "attempt", "type", "value", "value_sha256",
               "redacted", "unknown_keys", "unknown_fields", "outcome", "reason"])
HTTP = sorted(CORE + ["request", "status"])
DIGEST_LINE = "digest not verified (P2b)"  # O3: stays until P2b (D035)
ENTRY_COUNT = "5 entries, 3 checked, 2 rejected at capture"  # the 6d line, unchanged


def count_lines(total, checked, rejected):
    """QV3-7 (O3 text): one form `N records`, no singular (RV3-16), then the P2b marker."""
    return "%d records, %d checked, %d rejected at capture\n%s" % (total, checked, rejected, DIGEST_LINE)


def version_error(stream, version, source, line=1):
    """D6B-59 form with record version 3 and DL-143 (RV3-06, RV3-11)."""
    return ("error: stored %s RECORD has record version %s; this build reads record version 3 only (DL-143)\n"
            "  record source: %s:%d (line %d)" % (stream, version, source, line, line))


def without_counts(stderr):
    """A block may print the count lines, it need not (6d `blocked()`)."""
    return "\n".join(l for l in stderr.strip().splitlines()
                     if "rejected at capture" not in l and l != DIGEST_LINE)


def git_show(path):
    return subprocess.run(["git", "-C", str(REPO), "show", "%s:%s" % (P2_BASE, path.relative_to(REPO))],
                          capture_output=True, text=True, check=True).stdout


def to_v2(record):
    """The v2 twin of a v3 RESPONSE RECORD, for the P2 base compiler (N3)."""
    out = {("client_span_id" if k == "span_id" else k): v for k, v in record.items() if k not in ("outcome", "reason")}
    return dict(out, version=2)


def converter():
    spec = importlib.util.spec_from_file_location("convert_v3", LEDGER / "convert_v3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Runtime bodies. arms/gen/orders.beaml: no enum, no constructor. decode-ctor: Amount fails on currency "".
U, V, M, N = (sr.b(sr.UNKNOWN_KEY_BODY), sr.b(sr.VALID_BODY), sr.b(sr.MISSING_KEY_BODY), sr.b(sr.NOT_JSON_BODY))
CTOR_OK = sr.b(b'{"order_id":"order-1","state":"pending","amount":{"value":"1","currency":"EUR"}}')
CTOR_FAIL = sr.b(b'{"order_id":"order-1","state":"pending","amount":{"value":"1","currency":""}}')
KEPT = sr.b(b'{"order_id":"order-1","state":"refunded"}')
SCRIPT = sr.HELPERS + r'''
live = fn bytes -> BeamlSpike.__beaml_attempt__(fn -> BeamlSpike.__beaml_result_payments_authorize(bytes) end) end
oc = fn record -> Map.take(record, ["outcome", "reason"]) end
'''
ACCEPTED, STATUS = ex({"outcome": "accepted", "reason": None}), ex({"outcome": "rejected", "reason": "status"})
DECODE_R, CTOR_R = ex({"outcome": "rejected", "reason": "decode"}), ex({"outcome": "rejected", "reason": "constructor"})
PARITY = 'live.(%s) == {:error, struct(BeamlSpike.PaymentError, reason: stored.(200, %s)["reason"])}'
ORDERS_CASES = {
    "V1_version_is_3": 'stored.(200, %s)["version"] == 3' % U,
    "V2_key_set_is_the_core_and_the_http_extras": 'Enum.sort(Map.keys(stored.(200, %s))) == %s' % (U, ex(HTTP)),
    "V3_span_id_only": ('(fn r -> Map.has_key?(r, "span_id") and not Map.has_key?(r, "client_span_id") and '
                        'not Map.has_key?(r, "server_span_id") end).(stored.(200, %s))' % U),
    "V4_accepted": 'oc.(stored.(200, %s)) == %s' % (V, ACCEPTED),
    "V5_status": 'oc.(stored.(503, %s)) == %s' % (V, STATUS),
    "V5_status_wins_over_decode": 'oc.(stored.(503, %s)) == %s' % (M, STATUS),
    "V6_decode": 'oc.(stored.(200, %s)) == %s' % (M, DECODE_R),
    "V6_not_json_is_decode": 'oc.(stored.(200, %s)) == %s' % (N, DECODE_R),
    "V8_decode_reason_is_the_live_reason": PARITY % (M, M),
    "V9_unknown_fields_always": 'Map.fetch(stored.(200, %s), "unknown_fields") == {:ok, []}' % V,
    # Guards (pass before and after P2): the digest rule and the replay stay (QV3-6 A, RV3-04, D6B-57).
    "V10_guard_digest_accepted": 'stored.(200, %s)["value_sha256"] == %s' % (V, ex(st.value_sha256(sr.PAYMENT))),
    "V10_guard_digest_status": ('stored.(503, %s)["value"] == %s and stored.(503, %s)["value_sha256"] == %s'
                                % (V, ex(sr.PAYMENT), V, ex(st.value_sha256(sr.PAYMENT)))),
    "V10_guard_digest_decode": ('stored.(200, %s)["value_sha256"] == %s'
                                % (M, ex(st.value_sha256({"order_id": "order-1"})))),
    "V10_guard_replay": 'replay.(stored.(200, %s)) == {:ok, %s}' % (V, ex(sr.PAYMENT)),
}
CTOR_VALUE = {"order_id": "order-1", "state": "pending", "amount": {"value": "1", "currency": ""}}
CTOR_CASES = {
    "V4_accepted_through_the_constructor": 'oc.(stored.(200, %s)) == %s' % (CTOR_OK, ACCEPTED),
    "V7_constructor": 'oc.(stored.(200, %s)) == %s' % (CTOR_FAIL, CTOR_R),
    "V8_constructor_reason_is_the_live_reason": PARITY % (CTOR_FAIL, CTOR_FAIL),
    "V10_guard_digest_constructor": ('stored.(200, %s)["value_sha256"] == %s'
                                     % (CTOR_FAIL, ex(st.value_sha256(CTOR_VALUE)))),
}
DECODE_CASES = {
    "V2_key_set_with_a_keep_value_variant": 'Enum.sort(Map.keys(stored.(200, %s))) == %s' % (KEPT, ex(HTTP)),
    "V9_guard_kept_value_names_the_field": 'stored.(200, %s)["unknown_fields"] == ["state"]' % KEPT,
}
ENTRY = "(%s |> elem(2) |> entries.() |> hd())" % se.CSRF
RESPONSE = "(%s |> elem(2) |> responses.() |> hd())" % se.CSRF
ENTRY_CASES = {
    "V11_entry_version_is_3": '%s["version"] == 3' % ENTRY,
    "V11_entry_key_set_is_the_core": "Enum.sort(Map.keys(%s)) == %s" % (ENTRY, ex(CORE)),
    "V11_entry_span_id_only": ('Map.has_key?(%s, "span_id") and not Map.has_key?(%s, "server_span_id")'
                               % (ENTRY, ENTRY)),
    "V11_guard_entry_outcome": 'Map.take(%s, ["outcome", "reason"]) == %s' % (ENTRY, ACCEPTED),
    "V2_response_of_the_flow_key_set": "Enum.sort(Map.keys(%s)) == %s" % (RESPONSE, ex(HTTP)),
    "V4_response_of_the_flow_accepted": 'Map.take(%s, ["outcome", "reason"]) == %s' % (RESPONSE, ACCEPTED),
}

# V17, V18b: the 15 converted fixtures; per fixture the sources that existing tests build with it. rec-loop.jsonl
# has no pair here: its source runs into the stored-elixir time limit (slice6_stored_elixir_test owns that case).
PAIRS = {
    "stored/v1.jsonl": ["arms/gen/orders.beaml", "slice2/N-chain/orders.beaml"],
    "stored/v1-v2.jsonl": ["slice2/N-chain/orders.beaml"],
    "slice6/decode/stored.jsonl": ["slice6/decode/orders.beaml"],
    "slice6/decode/stored-fail.jsonl": ["slice6/decode/orders.beaml"],
    "slice6/decode/stored-resolved.jsonl": ["slice6/decode/orders.beaml"],
    "slice6/decode-ctor/stored.jsonl": ["slice6/decode-ctor/orders.beaml"],
    "slice6/decode-ctor/stored-fail.jsonl": ["slice6/decode-ctor/orders.beaml"],
    "slice6/decode-ctor/stored-nomatch.jsonl": ["slice6/decode-ctor/orders.beaml"],
    "slice6/redacted/stored-unredacted.jsonl": ["slice6/redacted/output_redacted.beaml"],
    "slice6/redacted/stored-request-unredacted.jsonl": ["slice6/redacted/orders.beaml"],
    "slice6/stored-elixir/order.jsonl": ["slice6/stored-elixir/order.beaml"],
    "slice6/stored-elixir/nested-fail.jsonl": ["slice6/stored-elixir/nested.beaml"],
    "slice6/stored-elixir/pipe-fail.jsonl": ["slice6/stored-elixir/pipe.beaml"],
    "slice6/stored-elixir/rec-loop.jsonl": [],
    "slice6/entry/stored/entries.jsonl": ["slice6/entry/orders.beaml"],
}
STORED_WORDS = se.STORED_WORDS + (srd.STORED_HOLDER, "order-1", "pending")
# V18: the only generated functions whose lines may change (plan, "Pin sites and diff proof").
ALLOWED = ("def record(request, status, bytes)", "def entry_record(bytes, decoded)")
HEADER = re.compile(r"^\s*(defmodule|defp|def)\s")


def owner(lines, at):
    """The nearest `def`, `defp` or `defmodule` line at or above `at` (repin.md method)."""
    for line in reversed(lines[:at + 1]):
        if HEADER.match(line):
            return line.strip()
    return "(top)"


def hunk_owners(old, new):
    a, b = old.splitlines(), new.splitlines()
    owners = set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            owners.update([owner(a, i1)] if i2 > i1 else [])
            owners.update([owner(b, j1)] if j2 > j1 else [])
    return owners


class RecordV3(unittest.TestCase):
    maxDiff = None
    setUp = se.Slice6Entry.setUp
    compile = se.Slice6Entry.compile  # V19: events hold no path, no source text, no stored value (6d N12 check)
    built = se.Slice6Entry.built
    elixirc = se.Slice6Entry.elixirc
    runtime = se.Slice6Entry.runtime
    run_runtime = sd.Slice6Decode.run_runtime

    def write(self, name, text):
        path = self.work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    # V1 to V10: the RESPONSE RECORD writer `Replay.record/3` (release-free harness of slice6_record_test).

    def test_V1_to_V10_response_record(self):
        self.run_runtime(ORDERS_CASES, source=ORDERS, script=SCRIPT, stored=sd.sf.EMPTY_STORED)

    def test_V4_V7_V8_constructor_outcome(self):
        self.run_runtime(CTOR_CASES, source=CTOR, script=SCRIPT, stored=sd.sf.EMPTY_STORED)

    def test_V2_V9_keep_value_source(self):
        self.run_runtime(DECODE_CASES, source=DECODE, script=SCRIPT, stored=sd.sf.EMPTY_STORED)

    def test_V8_guard_live_status_reason(self):
        # Guard: the live non-200 branch fails with reason "status", the reason V5 writes into the record.
        stdout, _ = self.built(ORDERS, EMPTY, "BeamlSpike")  # arms/gen has no ENTRY LINE (Q6E-1 C)
        self.assertIn("else: __beaml_fail_payments_authorize(%s)" % sr.b(b"status"), stdout)

    # V11: the ENTRY RECORD writer `Replay.entry_record/2` and the RESPONSE RECORD of the same flow (6d harness).

    def test_V11_entry_record(self):
        self.runtime(se.ORDERS, ENTRY_CASES, se.EMPTY)

    # V12, V13: the version check of both readers (RV3-06).

    def assert_rejected(self, source, stored, message):
        code, stdout, stderr = self.compile(source, ["--stored", str(stored)])
        self.assertEqual((1, "", message), (code, stdout, stderr.strip()), "expected exit 1, no stdout, the exact text")

    def test_V12_response_record_version_2_blocks(self):
        stored = self.write("v2.jsonl", git_show(EXPERIMENT / "stored" / "v1.jsonl"))
        self.assert_rejected(ORDERS, stored, version_error("RESPONSE", 2, stored))

    def test_V12_response_record_version_1_blocks(self):
        self.assert_rejected(ORDERS, sr.V1_RECORD, version_error("RESPONSE", 1, sr.V1_RECORD))

    def test_V12_response_record_without_version_blocks(self):
        record = {k: v for k, v in json.loads(sr.V1_LINE).items() if k != "version"}
        stored = self.write("none.jsonl", json.dumps(record, separators=(",", ":")) + "\n")
        self.assert_rejected(ORDERS, stored, version_error("RESPONSE", "none", stored))

    def test_V13_entry_record_version_2_blocks(self):
        self.assert_rejected(se.ORDERS, FIX / "entry-v2" / "responses.jsonl",
                             version_error("ENTRY", 2, FIX / "entry-v2" / "entries.jsonl"))

    # V14, V22, V23: rejected RESPONSE RECORDS are counted and skip the value and path checks (QV3-7, QV3-8 B).

    def test_V14_count_lines(self):
        code, stdout, stderr = self.compile(CTOR, ["--stored", str(FIX / "stored-mixed.jsonl")])
        self.assertEqual((0, True, count_lines(3, 1, 2)), (code, "defmodule BeamlSpike do" in stdout, stderr.strip()))

    def test_V14b_control_an_accepted_record_still_blocks(self):
        stored = FIX / "stored-mixed-fail.jsonl"
        code, stdout, stderr = self.compile(CTOR, ["--stored", str(stored)])
        block = ("error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize fails the constructor of "
                 "Amount for field amount with NoCurrency\n  record source: %s:1 (line 1)\n%s" % (stored, sdc.HELP_MIGRATE))
        self.assertEqual((1, "", block), (code, stdout, without_counts(stderr)))

    def test_V14c_response_count_lines_before_the_entry_count_line(self):
        # Change step 5: the RESPONSE lines come first on stderr; the 6d ENTRY line stays.
        _, stderr = self.built(se.ORDERS, ["--stored", str(FIX / "order" / "responses.jsonl")])
        self.assertEqual(count_lines(1, 0, 1) + "\n" + ENTRY_COUNT, stderr.strip())

    def assert_skipped(self, name):
        _, empty_stdout, _ = self.compile(CTOR, EMPTY)
        code, stdout, stderr = self.compile(CTOR, ["--stored", str(FIX / name)])
        self.assertEqual((0, empty_stdout, count_lines(1, 0, 1)), (code, stdout, stderr.strip()))

    def test_V22_status_record_without_a_path_builds(self):
        self.assert_skipped("stored-503-nopath.jsonl")

    def test_V23_rejected_200_record_without_a_path_builds(self):
        self.assert_skipped("stored-200-rejected-nopath.jsonl")

    def test_V24_control_accepted_record_without_a_path_blocks(self):
        # The TYPE path text is unchanged (V21): the P2 base compiler over the v2 twin gives it.
        stored = FIX / "stored-accepted-nopath.jsonl"
        twin = self.write("twin/" + stored.name, json.dumps(to_v2(json.loads(stored.read_text())),
                                                            separators=(",", ":")) + "\n")
        _, _, base = self.compile(CTOR, ["--stored", str(twin)], s5.compiler_at(P2_BASE))
        self.assertTrue(base.startswith("error: TYPE Payment cannot read 1 stored RESPONSE RECORD"), "setup: " + base)
        code, stdout, stderr = self.compile(CTOR, ["--stored", str(stored)])
        self.assertEqual((1, "", base.strip().replace(str(twin), str(stored))), (code, stdout, stderr.strip()))

    def test_V25_held_check_reads_a_rejected_record(self):
        stored = FIX / "stored-held-rejected.jsonl"
        code, stdout, stderr = self.compile(REDACTED, ["--stored", str(stored)])
        self.assertEqual((1, "", srd.d6b_72("Order", 1, "card_holder", "request", stored, 1)),
                         (code, stdout, without_counts(stderr)))

    def test_O1_orphan_check_reads_a_rejected_record(self):
        # RED review O1: a rejected record of an operation with no EFFECT and no RETIRE LINE still blocks (DL-040).
        record = dict(json.loads((FIX / "stored-503-nopath.jsonl").read_text()), operation="payments.gone")
        stored = self.write("orphan/stored.jsonl", json.dumps(record, separators=(",", ":")) + "\n")
        twin = self.write("twin/orphan.jsonl", json.dumps(to_v2(record), separators=(",", ":")) + "\n")
        _, _, base = self.compile(CTOR, ["--stored", str(twin)], s5.compiler_at(P2_BASE))
        self.assertIn("has no effect in the source", base, "setup: " + base)
        code, stdout, stderr = self.compile(CTOR, ["--stored", str(stored)])
        self.assertEqual((1, "", base.strip().replace(str(twin), str(stored))), (code, stdout, without_counts(stderr)))

    def test_O2_missing_or_unknown_outcome_blocks(self):
        # RED review O2: only "accepted" or "rejected" passes; anything else is the DL-138 error, not a skip.
        record = json.loads((FIX / "stored-accepted-nopath.jsonl").read_text())
        for name, outcome in (("missing", None), ("unknown", "maybe")):
            with self.subTest(name):
                changed = {k: v for k, v in record.items() if k != "outcome"}
                if outcome:
                    changed["outcome"] = outcome
                stored = self.write("outcome/%s.jsonl" % name, json.dumps(changed, separators=(",", ":")) + "\n")
                self.assert_rejected(CTOR, stored, "error: stored RESPONSE RECORD has no capture outcome accepted or "
                                     "rejected (DL-138)\n  record source: %s:1 (line 1)" % stored)

    def test_N2_w2_skips_a_rejected_record(self):
        # Re-check N2: a rejected v1 record leaves snapshot.oldest, so `migrate Payment v1 -> v2` is a DEAD LINE.
        code, _, stderr = self.compile(N_CHAIN, ["--stored", str(FIX / "stored-w2-rejected.jsonl")])
        self.assertEqual((0, True, True), (code, "warning: DEAD LINE: migrate Payment v1 -> v2" in stderr,
                                           count_lines(1, 0, 1) in stderr), stderr)

    def test_N2b_control_an_accepted_record_keeps_the_migrate_step(self):
        code, _, stderr = self.compile(N_CHAIN, ["--stored", str(FIX / "stored-w2-accepted.jsonl")])
        self.assertEqual((0, ""), (code, stderr.strip()))

    def test_V16_no_stored_value_in_stderr(self):
        # DL-124: names and counts only. The marker proves the planned text stands, so a version error cannot pass.
        for source, name, marker in ((CTOR, "stored-mixed.jsonl", "rejected at capture"),
                                     (CTOR, "stored-mixed-fail.jsonl", "fails the constructor"),
                                     (CTOR, "stored-503-nopath.jsonl", "rejected at capture"),
                                     (CTOR, "stored-200-rejected-nopath.jsonl", "rejected at capture"),
                                     (REDACTED, "stored-held-rejected.jsonl", "redacted field")):
            with self.subTest(name):
                _, _, stderr = self.compile(source, ["--stored", str(FIX / name)])
                self.assertEqual((True, []), (marker in stderr, [w for w in STORED_WORDS if w in stderr]), stderr)

    # V17: the tracked fixtures are v3 and equal the converter output over the P2 base files.

    def test_V17_tracked_fixtures_are_v3(self):
        for name in PAIRS:
            with self.subTest(name):
                records = [json.loads(l) for l in (EXPERIMENT / name).read_text().splitlines() if l.strip()]
                keys = CORE if name.endswith("entries.jsonl") else HTTP
                self.assertEqual([(3, keys, r["value_sha256"]) for r in records],
                                 [(r.get("version"), sorted(r), st.value_sha256(r["value"], r["unknown_keys"],
                                                                                r["redacted"])) for r in records])

    def test_V17b_tracked_fixtures_equal_the_converter_output(self):
        convert = converter()
        self.assertEqual(sorted(PAIRS), sorted(convert.FILES), "setup: the converter and this test list other files")
        for name in PAIRS:
            with self.subTest(name):
                self.assertEqual(convert.convert_text(git_show(EXPERIMENT / name), name.endswith("entries.jsonl")),
                                 (EXPERIMENT / name).read_text())

    # V18: the diff proof against the P2 base compiler (plan "Pin sites and diff proof", RV3-14).

    def test_V18_only_the_two_writers_change(self):
        listed = subprocess.run(["git", "-C", str(REPO), "ls-files", "experiments/0001-syntax-to-beam/*.beaml",
                                 "experiments/0002-http-correlation/apps/*.beaml",
                                 "experiments/0004-generated-replay/arms/*.beaml",
                                 "experiments/0004-generated-replay/slice*/*.beaml",
                                 "experiments/0004-generated-replay/drift/*.beaml",
                                 "experiments/0004-generated-replay/bad/*.beaml"],
                                capture_output=True, text=True, check=True).stdout.split()
        guard = json.loads((EXPERIMENT / "slice6" / "effect-reach" / "byte-guard.json").read_text())
        sources = sorted(set(listed) | set(guard))
        self.assertGreater(len(sources), 100, "setup: too few tracked sources")
        base = s5.compiler_at(P2_BASE)
        writers = 0
        for relative in sources:
            with self.subTest(relative):
                old = self.compile(REPO / relative, EMPTY, base)
                new = self.compile(REPO / relative, EMPTY)
                self.assertEqual((old[0], old[2]), (new[0], new[2]), "exit and stderr must be equal")
                owners = hunk_owners(old[1], new[1])
                self.assertEqual([], sorted(o for o in owners if not o.startswith(ALLOWED)), "hunk outside the writers")
                present = [w for w in ALLOWED if "    %s do" % w in old[1]]
                writers += len(present)
                self.assertEqual([], [w for w in present if not any(o.startswith(w) for o in owners)],
                                 "these writers must change (v3)")
        self.assertGreater(writers, 50, "setup: too few EFFECT sources")

    # V18b (re-check N3) and V15: over each converted fixture, the P2 base compiler reads the v2 original (git show
    # P2_BASE) and the P2 compiler reads the tracked v3 file; exit and stderr are equal (paths mapped).

    def assert_converted_stderr(self, name, relative):
        tracked = EXPERIMENT / name
        self.assertTrue(all(json.loads(l).get("version") == 3 for l in tracked.read_text().splitlines() if l.strip()),
                        "fixture is not converted to v3 (V17)")
        entry = name.endswith("entries.jsonl")
        original = self.write("base/" + name, git_show(tracked))
        stored = original.parent / "responses.jsonl" if entry else original
        if entry:
            stored.write_text("")
        tracked_stored = tracked.parent / "responses.jsonl" if entry else tracked
        code, _, stderr = self.compile(REPO / "experiments/0004-generated-replay" / relative, ["--stored", str(stored)],
                                       s5.compiler_at(P2_BASE))
        expected = (code, stderr.replace(str(original.parent), str(tracked.parent)))
        new = self.compile(REPO / "experiments/0004-generated-replay" / relative, ["--stored", str(tracked_stored)])
        self.assertEqual(expected, (new[0], new[2]))
        return new[2]

    def test_V18b_converted_fixtures_keep_exit_and_stderr(self):
        for name, sources in PAIRS.items():
            for relative in sources:
                with self.subTest(fixture=name, source=relative):
                    self.assert_converted_stderr(name, relative)

    def test_V15_no_count_lines_when_nothing_is_rejected(self):
        stderr = self.assert_converted_stderr("stored/v1.jsonl", "arms/gen/orders.beaml")
        self.assertNotIn(DIGEST_LINE, stderr)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
