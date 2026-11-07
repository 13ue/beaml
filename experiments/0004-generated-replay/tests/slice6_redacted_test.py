"""EXPERIMENT 0004 slice 6b step 6b: `redacted` on fields, `with` on EFFECTS, the projections, marked fields, the echo
test and the stored-value block (DL-059, DL-089, DL-105, DL-111, DL-113, DL-115, DL-116; D6B-29 to D6B-33, D6B-55,
D6B-56, D6B-64, D6B-65, D6B-70, D6B-72).

Plan: workflow/2026-11-07/slice6b-redacted/plan.md, "First failing test per sub-step", 6b (R1 to R8). Ledger:
workflow/2026-11-07/slice6b-redacted-fields/ (spec.md, notes.md). Fixtures: slice6/redacted/.

Runtime harness (plan 6b, D6B-70): the generated module compiles with `elixirc --warnings-as-errors` beside file-backed
stubs. `ProbeSupport.json/1` encodes for real; `ProbeSupport.config(:payments_port)` reads the port of a loopback HTTP
stub from an environment variable; `ProbeSupport.span/5`, `ProbeSupport.event/2` and `:otel_span.set_attribute/3`
append their arguments to files in the RUN DIRECTORY; `ProbeSupport.Capture.write/2` appends the record JSON to
`responses.jsonl` there. The loopback stub keeps each request and response in memory (positive control). The MARKER
goes to the harness only through the environment variable BEAML_MARKER, never through a file.
The scan looks for the MARKER in every file of the RUN DIRECTORY and in `.beaml/actions.jsonl`: plain text, base64 at
the three byte offsets, lower-case hex and the decimal byte list of the emitter (D6B-155).
Expected values come from the plan, the decision log and notes.md, never from the new compiler.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_redacted_test.py [-k NAME]
"""
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT, REPO  # noqa: E402
import slice6_failure_test as sf  # noqa: E402
import slice6_record_test as sr  # noqa: E402
import stored_types_test as st  # noqa: E402

COMPILER_PATH = "experiments/0001-syntax-to-beam"
_BINARY = []
FIX = EXPERIMENT / "slice6" / "redacted"
BAD = FIX / "bad"
EMPTY = ["--stored", str(sf.EMPTY_STORED)]
STORED_HOLDER = "STORED-HOLDER-3e9d1c"  # the stored value of R7 and R8 (D6B-150); it must reach no stderr byte
ex = sr.ex

PAYMENT = {"order_id": "order-1", "status": "authorized"}
ECHO_NAMES = ["echo", "echo.card_holder", "echo.order_id"]  # D6B-56 amendment: a dotted name per level
DECODE_ERROR = '{:error, %BeamlSpike.PaymentError{reason: "decode"}}'


def compiler():
    """The 0001 compiler binary, built once. BEAML_SPIKE points at a scratch build instead."""
    if not _BINARY:
        if os.environ.get("BEAML_SPIKE"):
            _BINARY.append(os.environ["BEAML_SPIKE"])
        else:
            manifest = REPO / COMPILER_PATH / "Cargo.toml"
            subprocess.run(["cargo", "build", "--offline", "--quiet", "--manifest-path", str(manifest)], check=True)
            _BINARY.append(str(REPO / COMPILER_PATH / "target/debug/beaml-spike"))
        print("compiler:", _BINARY[0], file=sys.stderr)
    return _BINARY[0]


def fingerprint(fields):
    """The TYPE VERSION fingerprint of `main.rs` (sorted [field, TYPE text] pairs, compact JSON, SHA-256)."""
    return hashlib.sha256(json.dumps(sorted(fields), separators=(",", ":")).encode()).hexdigest()


# D6B-148 (DL-111 option 1A, D6B-66 text): the TYPE text of a redacted field is `redacted String`.
REDACTED_PAYMENT_FIELDS = [["card_holder", "redacted String"], ["order_id", "String"], ["status", "String"]]


def forms(marker):
    """D6B-70, D6B-155: every byte form of the MARKER that the scan looks for."""
    raw = marker.encode()
    found = {"plain": raw, "hex": raw.hex().encode(),
             "bytes": ",".join(str(c) for c in raw).encode(), "bytes_spaced": ", ".join(str(c) for c in raw).encode()}
    for k in range(3):
        # The MARKER after k prefix bytes: keep only the characters that depend on MARKER bytes alone.
        text = base64.b64encode(b"\0" * k + raw).decode().rstrip("=")
        found["base64_%d" % k] = text[-(-8 * k // 6):(8 * (k + len(raw))) // 6].encode()
    return found


def scan(paths, marker):
    """Sorted (file name, form) hits of the MARKER in the given files and directories."""
    hits = set()
    wanted = forms(marker)
    for path in paths:
        files = [p for p in Path(path).rglob("*") if p.is_file()] if Path(path).is_dir() else [Path(path)]
        for file in files:
            if not file.is_file():
                continue
            data = file.read_bytes()
            hits.update((file.name, name) for name, form in wanted.items() if form in data)
    return sorted(hits)


def dotted(value, prefix=""):
    """Key names of a JSON object, dotted per level (labels for failure messages, never values)."""
    if not isinstance(value, dict):
        return []
    return [n for k, v in value.items() for n in [prefix + k] + dotted(v, prefix + k + ".")]


class Stub(ThreadingHTTPServer):
    """Loopback HTTP stub. `echo` answers with the request at the top level and under `echo` (plan R4)."""

    def __init__(self, echo):
        self.echo, self.requests, self.responses = echo, [], []
        super().__init__(("127.0.0.1", 0), Handler)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        self.server.requests.append(body)
        request = json.loads(body)
        answer = dict(PAYMENT, **request, echo=request) if self.server.echo else PAYMENT
        data = json.dumps(answer, separators=(",", ":")).encode()
        self.server.responses.append(data)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


STUBS = r'''
defmodule ProbeSupport do
  def span(name, kind, input, function, f) do
    dump("spans.txt", {name, kind, input, function})
    f.()
  end

  def event(name, step), do: dump("events.txt", {name, step})
  def config(:payments_port), do: String.to_integer(System.fetch_env!("STUB_PORT"))
  def config(_), do: nil
  def json(v), do: v |> :json.encode() |> IO.iodata_to_binary()
  def increment, do: :ok
  def beam_hash(_), do: ""

  def dump(file, term) do
    text = inspect(term, limit: :infinity, printable_limit: :infinity)
    File.write!(Path.join(System.fetch_env!("RUN_DIR"), file), text <> "\n", [:append])
  end
end
defmodule ProbeSupport.Capture do
  def write(_, record) do
    File.write!(Path.join(System.fetch_env!("RUN_DIR"), "responses.jsonl"), ProbeSupport.json(record) <> "\n", [:append])
  end
end
defmodule OpenTelemetry.Tracer do
  def current_span_ctx, do: nil
end
defmodule OpenTelemetry.Span do
  def hex_trace_id(_), do: ""
  def hex_span_id(_), do: ""
end
defmodule :otel_span do
  def set_attribute(_, key, value), do: ProbeSupport.dump("attributes.txt", {key, value})
end
defmodule :otel_propagator_text_map do
  def inject(carrier), do: carrier
end
'''
# One live call of `place`, then the captured record and the REPLAY RUN. Nothing prints a value (PASS/FAIL lines only).
FLOW = r'''
marker = System.fetch_env!("BEAML_MARKER")
order = ORDER
live = BeamlSpike.place(order)
record =
  Path.join(System.fetch_env!("RUN_DIR"), "responses.jsonl") |> File.read!() |> String.split("\n", trim: true)
  |> Enum.map(&:json.decode/1) |> hd()
replay = fn rec -> BeamlSpike.Replay.run(order, rec["trace_id"], [rec]) end
'''
PAYMENT_OK = "{:ok, %s}" % ex(PAYMENT)
FLAT_ORDER = '%{"order_id" => "order-1", "card_holder" => marker}'
# RED repair O1: the redacted field inside a nested input record (orders_nested.beaml).
NESTED_ORDER = '%{"order_id" => "order-1", "card" => %{"holder" => marker, "number" => "4111"}}'
NESTED_REQUEST = {"order_id": "order-1", "card": {"number": "4111"}}
HOLDER_MAP = ex(PAYMENT)[:-1] + ', "card_holder" => marker}'  # the Payment map with the live value of the MARKER
HOLDER_OK = "{:ok, %s}" % HOLDER_MAP


def record_cases(prefix, value, unknown_keys, redacted):
    """The captured record: projection keys and the Python digest (D6B-55, D6B-56, D6B-58)."""
    return {
        prefix + "_record_value": 'record["value"] == %s' % value,
        prefix + "_record_unknown_keys": 'record["unknown_keys"] == %s' % ex(unknown_keys),
        prefix + "_record_redacted": 'record["redacted"] == %s' % ex(redacted),
        prefix + "_record_request_has_no_card_holder": 'record["request"] == %s' % ex({"order_id": "order-1"}),
    }


# R1 (first RED): no `with`, the wire body and the record `request` hold no card_holder.
R1_CASES = dict({"R1_live_result": "live == %s" % PAYMENT_OK},
                **record_cases("R1", ex(PAYMENT), [], []))
# R2, R3: `with card_holder` sends it; record, span and event hold it never; the request compare uses the projection.
R2_CASES = dict({
    "R2_live_result": "live == %s" % PAYMENT_OK,
    "R3_record_replays": "replay.(record) == %s" % PAYMENT_OK,
    "R3_record_request_without_card_holder_replays": (
        'replay.(Map.put(record, "request", %s)) == %s' % (ex({"order_id": "order-1"}), PAYMENT_OK)),
    # The full host input (with the MARKER) in `request` is no match: the compare uses the projection (D6B-32).
    "R3_record_request_with_card_holder_is_request_mismatch": (
        'replay.(Map.put(record, "request", order)) == {:error, :request_mismatch}'),
}, **record_cases("R2", ex(PAYMENT), [], []))
R1_REPLAY_CASES = {
    "R3_no_with_record_replays": "replay.(record) == %s" % PAYMENT_OK,
    "R3_no_with_request_with_card_holder_is_request_mismatch": (
        'replay.(Map.put(record, "request", order)) == {:error, :request_mismatch}'),
}
# R4 declared, R5: the output TYPE declares card_holder redacted; DL-115 marks it with the atom :redacted.
DECLARED_CASES = dict({
    "R4_declared_live_gets_the_real_value": "live == %s" % HOLDER_OK,
    "R4_declared_record_digest": 'record["value_sha256"] == %s' % ex(st.value_sha256(PAYMENT, ECHO_NAMES,
                                                                                      ["card_holder"])),
    "R4_declared_record_type_fields": 'record["type"]["fields"] == %s' % ex(REDACTED_PAYMENT_FIELDS),
    "R4_declared_record_type_fingerprint": 'record["type"]["fingerprint"] == %s' % ex(fingerprint(
        REDACTED_PAYMENT_FIELDS)),
    "R5_replay_marks_the_field": 'replay.(record) == {:ok, %s}' % HOLDER_MAP.replace("marker}", ":redacted}"),
    # D6B-55: a record whose `redacted` list lacks the field replays as the typed reject decode, like live.
    "R5_record_without_the_mark_is_decode": (
        'replay.(Map.merge(record, %%{"redacted" => [], "value_sha256" => %s})) == %s'
        % (ex(st.value_sha256(PAYMENT, ECHO_NAMES)), DECODE_ERROR)),
}, **record_cases("R4_declared", ex(PAYMENT), ECHO_NAMES, ["card_holder"]))
UNDECLARED_CASES = dict({"R4_undeclared_live_result": "live == %s" % PAYMENT_OK},
                        **record_cases("R4_undeclared", ex(PAYMENT), ["card_holder"] + ECHO_NAMES, []))
# R4c (DL-113, option C): a plain output field of the same name keeps the echoed value; the declaration decides.
PLAIN_CASES = dict({
    "R4c_live_gets_the_value": "live == %s" % HOLDER_OK,
    "R4c_replay_gives_the_value": "replay.(record) == %s" % HOLDER_OK,
}, **record_cases("R4c", HOLDER_MAP, ECHO_NAMES, []))
CONTROL_CASES = {"control_live_result": "live == %s" % PAYMENT_OK}
# RED repair O1: no value at any depth in the record `request`; the compare uses the nested projection (D6B-32).
NESTED_CASES = {
    "N1_live_result": "live == %s" % PAYMENT_OK,
    "N1_record_request_has_no_holder": 'record["request"] == %s' % ex(NESTED_REQUEST),
    "N1_record_replays": "replay.(record) == %s" % PAYMENT_OK,
    "N1_request_with_holder_is_request_mismatch": 'replay.(Map.put(record, "request", order)) == {:error, :request_mismatch}',
}

D6B_64 = "error: redacted stands only before a field TYPE in a type (D6B-29)"


def d6b_72(ty, count, field, place, source, line):
    """D6B-72 text, with D6B-151 (singular for one record) and the D6B-152 help line (DL-111, DL-125)."""
    records = "RECORD" if count == 1 else "RECORDS"
    verb = "holds" if count == 1 else "hold"
    return ("error: TYPE %s: %d stored RESPONSE %s of operation payments.authorize %s a value of the redacted field %s "
            "in %s\n  record source: %s:%d (line %d)\n"
            "  help: declare the fate in a MIGRATE STEP: redact %s (DL-111); slice 6b has no form for it yet (DL-125)"
            % (ty, count, records, verb, field, place, source, line, line, field))


def dl_116(output, field):
    """D6B-154: the DL-116 interim text (Q6B-15 option A text, widened to Int, in the D6B-39 style)."""
    return ("error: effect payments.authorize: the redacted field %s.%s must be a String or Int field of a TYPE "
            "without a constructor in slice 6b (DL-116)\n"
            "  help: remove redacted from %s.%s; the limit holds until a rule over an absent value exists (DL-116)"
            % (output, field, output, field))


class Slice6Redacted(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6red-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()
        self.marker = "MARKER-" + secrets.token_hex(8)

    def compile(self, source, extra=()):
        result = subprocess.run([compiler(), str(source), *extra], cwd=self.work / "cwd", capture_output=True,
                                text=True)
        log = self.actions()
        if log.is_file():
            text = log.read_text()
            self.assertNotIn(str(Path(source).parent), text, "action events must not record the source path")
            self.assertNotIn(STORED_HOLDER, text, "action events must not record a stored value")
        return result.returncode, result.stdout, result.stderr

    def actions(self):
        return self.work / "cwd" / ".beaml" / "actions.jsonl"

    def build(self, source, extra=EMPTY):
        code, stdout, stderr = self.compile(source, list(extra))
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout),
                         "expected exit 0 and Elixir on stdout; stderr: " + stderr)
        return stdout

    def rejected(self, source, extra=EMPTY):
        code, stdout, stderr = self.compile(source, list(extra))
        self.assertEqual((1, ""), (code, stdout), "expected exit 1 and no stdout; stderr: " + stderr)
        self.assertNotIn(STORED_HOLDER, stderr, "DL-032: no stored value in compiler output")
        return stderr.strip()

    def flow(self, source, cases, echo, order=FLAT_ORDER):
        """Build, run one live call and its REPLAY RUN against the loopback stub; returns (run dir, stub)."""
        stdout = self.build(source)
        run = self.work / "run"
        run.mkdir()
        (run / "generated.ex").write_text(stdout)
        (run / "stubs.ex").write_text(STUBS)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(run), str(run / "stubs.ex"),
                               str(run / "generated.ex")], capture_output=True, text=True, cwd=run)
        self.assertEqual(0, beam.returncode, "elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn -> %s end}' % item for item in cases.items())
        (run / "checks.exs").write_text(sf.RUNTIME_HEAD + FLOW.replace("ORDER", order) + "\ncases = [\n" + listed + "\n]\n" + sf.RUNTIME_TAIL)
        stub = Stub(echo)
        threading.Thread(target=stub.serve_forever, daemon=True).start()
        self.addCleanup(stub.server_close)
        self.addCleanup(stub.shutdown)
        env = dict(os.environ, BEAML_MARKER=self.marker, STUB_PORT=str(stub.server_address[1]), RUN_DIR=str(run))
        done = subprocess.run(["elixir", "-pa", str(run), str(run / "checks.exs")], capture_output=True, text=True,
                              env=env, cwd=run, timeout=120)
        (run / "stdout.txt").write_text(done.stdout)
        (run / "stderr.txt").write_text(done.stderr)
        results = dict(line.rsplit(" ", 1) for line in done.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in cases:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), self.masked(done.stdout + done.stderr))
        return run, stub

    def masked(self, text):
        """RED repair O2: no form of the MARKER in a failure message, so no ledger log holds it."""
        for form in forms(self.marker).values():
            text = text.replace(form.decode(), "<M>")
        return text

    def assert_wire(self, stub, expected):
        """The one request body equals `expected`; a failure prints a label and key names, never values."""
        self.assertEqual(1, len(stub.requests), "the stub must receive one request")
        body = json.loads(stub.requests[0])
        self.assertTrue(body == expected, "wire body differs from the expected projection; keys: %s"
                        % sorted(dotted(body)))

    def assert_marker_in(self, data, channel):
        self.assertTrue(self.marker.encode() in data, "positive control: MARKER not found in " + channel)

    def assert_no_leak(self, run):
        hits = scan([run, self.actions()], self.marker)
        self.assertTrue(hits == [], "MARKER found in " + ", ".join("%s (%s)" % hit for hit in hits))

    def assert_channels_clean(self, run, key="card_holder"):
        """R2: the span and event dumps exist (the stubs ran) and hold no key of the redacted field."""
        for name in ("spans.txt", "events.txt"):
            with self.subTest(name):
                self.assertTrue((run / name).is_file(), name + " was not written")
                self.assertTrue(key not in (run / name).read_text(), "key %s found in %s" % (key, name))

    # Runtime cases.

    def test_R1_no_with_never_sends_the_redacted_field(self):
        run, stub = self.flow(FIX / "orders.beaml", dict(R1_CASES, **R1_REPLAY_CASES), echo=False)
        self.assert_wire(stub, {"order_id": "order-1"})
        self.assert_channels_clean(run)
        self.assert_no_leak(run)

    def test_N1_nested_redacted_input_field_reaches_no_channel(self):
        # RED repair O1: DL-089 at any depth; a nested field is never sent (D6B-31), so no `with` is possible.
        run, stub = self.flow(FIX / "orders_nested.beaml", NESTED_CASES, echo=False, order=NESTED_ORDER)
        self.assert_wire(stub, NESTED_REQUEST)
        self.assert_channels_clean(run, key="holder")
        self.assert_no_leak(run)

    def test_R2_R3_with_sends_the_field_on_the_wire_only(self):
        run, stub = self.flow(FIX / "orders_with.beaml", R2_CASES, echo=False)
        self.assert_wire(stub, {"order_id": "order-1", "card_holder": self.marker})
        self.assert_channels_clean(run)
        self.assert_no_leak(run)

    def test_R4_R5_echo_into_a_declared_redacted_output_field(self):
        run, stub = self.flow(FIX / "echo_declared.beaml", DECLARED_CASES, echo=True)
        self.assert_marker_in(stub.requests[0], "the wire request")
        self.assert_marker_in(stub.responses[0], "the stub response")
        self.assert_no_leak(run)

    def test_R4_echo_into_an_output_type_without_the_field(self):
        run, stub = self.flow(FIX / "orders_with.beaml", UNDECLARED_CASES, echo=True)
        self.assert_marker_in(stub.responses[0], "the stub response")
        self.assert_no_leak(run)

    def test_R4c_same_named_plain_output_field_keeps_the_value(self):
        # DL-113 (Q6B-13 C): allowed; the record `value` holds the echoed value, and no other file does.
        run, stub = self.flow(FIX / "echo_plain.beaml", PLAIN_CASES, echo=True)
        self.assert_marker_in(stub.responses[0], "the stub response")
        self.assertEqual([("responses.jsonl", "plain")], scan([run, self.actions()], self.marker))

    def test_control_plain_input_leaks_and_the_scan_finds_it(self):
        # Harness control (passes today): a plain card_holder reaches the record and the span; the scan sees it.
        run, stub = self.flow(FIX / "control.beaml", CONTROL_CASES, echo=True)
        self.assert_wire(stub, {"order_id": "order-1", "card_holder": self.marker})
        files = {name for name, _ in scan([run], self.marker)}
        self.assertTrue({"responses.jsonl", "spans.txt"} <= files, files)

    def test_scan_finds_each_planted_form(self):
        # D6B-70 self-check: one planted file per form, outside the RUN DIRECTORY.
        planted = self.work / "planted"
        planted.mkdir()
        raw = self.marker.encode()
        for name, form in forms(self.marker).items():
            (planted / name).write_bytes(b"x " + form + b" y")
        for k in range(3):
            (planted / ("b64_real_%d" % k)).write_bytes(base64.b64encode(b"ab"[:k] + raw + b"tail"))
        hits = set(scan([planted], self.marker))
        for name in forms(self.marker):
            self.assertIn((name, name), hits)
        for k in range(3):
            self.assertIn(("b64_real_%d" % k, "base64_%d" % k), hits)
        (self.work / "clean").mkdir()
        (self.work / "clean" / "f").write_bytes(b"MARKER-" + secrets.token_hex(8).encode())
        self.assertEqual([], scan([self.work / "clean"], self.marker))

    # R6: rejects (D6B-64, D6B-65, DL-116 with D6B-154).

    def test_R6_redacted_outside_a_type_field(self):
        for name in ("enum_payload", "signature", "migrate_change"):
            with self.subTest(name):
                # D6B-153: the first line is exact; a later `  at byte N` line is allowed.
                self.assertEqual(D6B_64, self.rejected(BAD / (name + ".beaml")).splitlines()[0])

    def test_R6_with_rejects(self):
        for name, line in (("with_unknown", "error: with names holder, which is not a field of Order"),
                           ("with_plain", "error: with names order_id, which is not a redacted field of Order"),
                           ("with_twice", "error: with names card_holder twice")):
            with self.subTest(name):
                self.assertEqual(line, self.rejected(BAD / (name + ".beaml")).splitlines()[0])

    def test_R6_dl116_interim_limit(self):
        for name, output, field in (("output_enum", "Payment", "state"), ("output_record", "Payment", "holder"),
                                    ("output_constructor_field", "Payment", "amount"),
                                    ("output_constructor_type", "Amount", "value")):
            with self.subTest(name):
                self.assertEqual(dl_116(output, field), self.rejected(BAD / (name + ".beaml")))

    def test_R6_redacted_int_output_passes_dl116(self):
        # DL-116 allows Int; only the existing slice 1 decode limit for Int output fields stays (D6B-156).
        self.assertEqual("effect payments.authorize: slice 1 decodes String fields only, not Payment.attempts",
                         self.rejected(BAD / "output_int.beaml"))

    def test_R6_fixtures_build_without_redacted_and_with(self):
        # Setup control (passes today): each reject fixture is valid once `redacted` and the `with` tail are gone.
        for path in sorted(BAD.glob("*.beaml")):
            if path.stem in ("output_int", "output_record"):
                continue  # the slice 1 decode limit (String output fields only) holds without `redacted` too
            with self.subTest(path.stem):
                lines = [ln for ln in path.read_text().splitlines() if not ln.startswith("//")]
                text = "\n".join(re.sub(r"\) with .*", ")", re.sub(r"\bredacted ", "", ln)) for ln in lines) + "\n"
                plain = self.work / "src" / path.name
                plain.parent.mkdir(exist_ok=True)
                plain.write_text(text)
                self.build(plain)

    # R7, R8: the stored-value block (D6B-72; DL-111 1A + 2A; P = `value` or `request`).

    def test_R7_stored_output_value_under_a_field_that_is_now_redacted(self):
        # D6B-149: the D6B-72 head line must show; under DL-111 1A the fingerprint error may show too.
        stored = FIX / "stored-unredacted.jsonl"
        stderr = self.rejected(FIX / "output_redacted.beaml", ["--stored", str(stored)])
        self.assertIn(d6b_72("Payment", 1, "card_holder", "value", stored, 1).splitlines()[0], stderr.splitlines())

    def test_R7_stored_value_with_the_redacted_fingerprint_gets_the_exact_block(self):
        # The fingerprint already matches (D6B-148), so only D6B-72 applies: the exact text.
        record = json.loads((FIX / "stored-unredacted.jsonl").read_text())
        record["type"] = dict(record["type"], fields=REDACTED_PAYMENT_FIELDS,
                              fingerprint=fingerprint(REDACTED_PAYMENT_FIELDS))
        stored = self.work / "stored-redacted-fingerprint.jsonl"
        stored.write_text(json.dumps(record, separators=(",", ":")) + "\n")
        self.assertEqual(d6b_72("Payment", 1, "card_holder", "value", stored, 1),
                         self.rejected(FIX / "output_redacted.beaml", ["--stored", str(stored)]))

    def test_R8_stored_request_value_of_a_now_redacted_input_field(self):
        stored = FIX / "stored-request-unredacted.jsonl"
        for name in ("orders", "orders_with"):  # `with` sends the value; the stored request still must not hold it
            with self.subTest(name):
                self.assertEqual(d6b_72("Order", 1, "card_holder", "request", stored, 1),
                                 self.rejected(FIX / (name + ".beaml"), ["--stored", str(stored)]))

    def nested_stored(self):
        record = json.loads((FIX / "stored-request-unredacted.jsonl").read_text())
        record["request"] = {"order_id": "order-1", "card": {"holder": STORED_HOLDER, "number": "4111"}}
        stored = self.work / "stored-request-nested.jsonl"
        stored.write_text(json.dumps(record, separators=(",", ":")) + "\n")
        return stored

    def test_R8_nested_stored_request_value(self):
        # RED repair O1: D6B-72 counts at any depth; D6B-163: T is the EFFECT input TYPE, F the dotted path.
        stored = self.nested_stored()
        self.assertEqual(d6b_72("Order", 1, "card.holder", "request", stored, 1),
                         self.rejected(FIX / "orders_nested.beaml", ["--stored", str(stored)]))

    def test_R8_count_and_first_line(self):
        clean = (EXPERIMENT / "stored" / "v1.jsonl").read_text().splitlines()[0]
        hit = json.loads((FIX / "stored-request-unredacted.jsonl").read_text())
        second = dict(hit, trace_id="0" * 31 + "2")
        stored = self.work / "stored-two.jsonl"
        stored.write_text("\n".join([clean, json.dumps(hit), json.dumps(second)]) + "\n")
        self.assertEqual(d6b_72("Order", 2, "card_holder", "request", stored, 2),
                         self.rejected(FIX / "orders.beaml", ["--stored", str(stored)]))

    def test_R7_R8_fixtures_build_without_redacted(self):
        # Setup control (passes today): the fixtures are valid records for the plain sources.
        for source, stored in (("output_plain", "stored-unredacted.jsonl"),
                               ("control", "stored-request-unredacted.jsonl")):
            with self.subTest(source):
                self.build(FIX / (source + ".beaml"), ["--stored", str(FIX / stored)])
        with self.subTest("orders_nested"):
            plain = self.work / "plain" / "orders_nested.beaml"
            plain.parent.mkdir()
            plain.write_text((FIX / "orders_nested.beaml").read_text().replace("redacted ", ""))
            self.build(plain, ["--stored", str(self.nested_stored())])


if __name__ == "__main__":
    unittest.main()
