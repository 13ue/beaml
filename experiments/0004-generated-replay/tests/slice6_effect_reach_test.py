"""EXPERIMENT 0004 slice 6b step 12 (spans follow the EFFECT reach, DL-108, DL-119) and 12b (a pure constructor, DL-120).

Ledger: workflow/2026-11-07/slice6b-effect-reach/ (plan.md E1 to E10, decisions.md, spec.md, notes.md).
DL-119 (OWNER, option S): a step gets a span only when it is an EFFECT or reaches one. A pure step has no span, also in
the EFFECT flow. The prepared event stays after the step before a direct EFFECT step (D6B-89, form D6B-114).
DL-120 (OWNER, option a): a constructor that reaches an EFFECT is a compile error (text D6B-112, path D6B-113).
Fixture: slice6/effect-reach/orders.beaml. E8 table: slice6/effect-reach/byte-guard.json (D6B-117).
Expected values come from the plan, the decision log and notes.md, never from the new compiler.
Guards pass before and after the step: E3, E7, the E8 rows of unchanged sources, the 12b accept case.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_effect_reach_test.py [-k NAME]
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import COMPILER_PATH, EXPERIMENT, REPO  # noqa: E402

FIXTURE = EXPERIMENT / "slice6" / "effect-reach" / "orders.beaml"
BYTE_GUARD = EXPERIMENT / "slice6" / "effect-reach" / "byte-guard.json"
PIPE = EXPERIMENT / "slice6" / "pipe" / "pipe.beaml"
REUSE = EXPERIMENT / "slice2" / "reuse" / "orders.beaml"
EMPTY_STORED = EXPERIMENT / "stored" / "empty.jsonl"
_BINARY = []


def b(text):
    """A BEAML string as the emitter writes it."""
    return "<<%s>>" % ",".join(str(c) for c in text.encode())


def unb(binary):
    return bytes(int(c) for c in binary[2:-2].split(",") if c).decode()


def span(name, step, arg, call, tail):
    """D6B-90: an indirect step span has the form of a pure step span of slice 1."""
    return "ProbeSupport.span(%s, :internal, %s, %s, fn -> %s end)%s" % (b("orders." + name), arg, b(step), call, tail)


# E1 to E6, E4c: the exact span names per clause, in order. An empty list: the clause has no span (DL-119 S).
SPANS = {
    "prepare#1": [], "finish#1": [], "tag#1": [], "status_of#1": [], "to_order#1": [],
    "place#1": [],  # E2: prepare and finish are pure; the EFFECT span lives in payments_authorize.
    "checkout#1": ["orders.place"],  # E1, E2: not orders.prepare, not orders.tag.
    "label#1": [],  # E3
    "ping#1": ["orders.pong"], "pong#1": ["orders.ping"], "pong#2": ["orders.place"],  # E4
    "a#1": [], "b#1": [],  # E5
    "by_id#1": ["orders.place"],  # E6: not orders.to_order.
    "c1#1": ["orders.c2"], "c2#1": ["orders.c3"], "c3#1": ["orders.place"],  # E4c
}
EVENT = "ProbeSupport.event(%s, %s)" % (b("payment_request_prepared"), b("prepare"))
# Exact lines per clause (stripped). D6B-88: the span input is p0 for a plain record head, nil for a String head.
LINES = {
    "checkout#1": ["with p1 = __MODULE__.prepare(p0),",  # E1
                   "{:ok, p2} <- " + span("place", "place", "p0", "__MODULE__.place(p1)", ","),
                   "p3 = __MODULE__.tag(p2) do"],
    "place#1": ["with p1 = __MODULE__.prepare(p0),",  # E2, D6B-89 and D6B-114
                "_ = %s," % EVENT,
                "{:ok, p2} <- __MODULE__.payments_authorize(p1),",
                "p3 = __MODULE__.finish(p2) do"],
    "by_id#1": ["with p1 = __MODULE__.to_order(p0),",  # E6
                "{:ok, p2} <- " + span("place", "place", "nil", "__MODULE__.place(p1)", " do")],
    "pong#1": ["with {:ok, p1} <- " + span("ping", "ping", "p0", "__MODULE__.ping(p0)", " do")],  # E4
    "ping#1": ["with {:ok, p1} <- " + span("pong", "pong", "p0", "__MODULE__.pong(p0)", " do")],
    "c1#1": ["with {:ok, p1} <- " + span("c2", "c2", "p0", "__MODULE__.c2(p0)", " do")],  # E4c
}

# Runtime: Access-faithful span stub (reads order["order_id"] like ProbeSupport.span/5), a span stack for the parent,
# and a local TCP payments stub, so the EFFECT runs its generated transport. Log rows: {:span, name, order_id, parent}
# and {:event, event, operation, parent}.
STUBS = r'''
defmodule ProbeSupport do
  def span(name, _kind, order, _function, f) do
    stack = Process.get(:stack, [])
    log({:span, name, order["order_id"], List.first(stack)})
    Process.put(:stack, [name | stack])

    try do
      f.()
    after
      Process.put(:stack, stack)
    end
  end

  def event(event, operation), do: log({:event, event, operation, List.first(Process.get(:stack, []))})
  defp log(row), do: Process.put(:log, Process.get(:log, []) ++ [row])
  def config(:payments_port), do: :persistent_term.get(:payments_port)
  def config(_), do: nil
  def json(v), do: IO.iodata_to_binary(:json.encode(v))
  def increment, do: :ok
  def beam_hash(_), do: ""
end
defmodule ProbeSupport.Capture do
  def write(_, record), do: Process.put(:capture, record)
end
defmodule OpenTelemetry.Tracer do
  def current_span_ctx, do: nil
end
defmodule OpenTelemetry.Span do
  def hex_trace_id(_), do: ""
  def hex_span_id(_), do: ""
end
defmodule :otel_span do
  def set_attribute(_, key, value), do: Process.put({:attr, key}, value)
end
defmodule :otel_propagator_text_map do
  def inject(carrier), do: carrier
end
'''
RUNTIME_HEAD = r'''
{:ok, listen} = :gen_tcp.listen(0, [:binary, active: false, reuseaddr: true])
{:ok, port} = :inet.port(listen)
:persistent_term.put(:payments_port, port)
reply = ~s({"order_id":"order-1","status":"authorized"})
drain = fn drain, s -> case :gen_tcp.recv(s, 0, 2000) do {:ok, _} -> drain.(drain, s); _ -> :ok end end
serve = fn serve ->
  {:ok, s} = :gen_tcp.accept(listen)
  {:ok, _} = :gen_tcp.recv(s, 0, 2000)
  :ok = :gen_tcp.send(s, "HTTP/1.1 200 OK\r\nContent-Length: #{byte_size(reply)}\r\nConnection: close\r\n\r\n" <> reply)
  :gen_tcp.shutdown(s, :write)
  drain.(drain, s)
  :gen_tcp.close(s)
  serve.(serve)
end
spawn(fn -> serve.(serve) end)
order = fn id -> %{"order_id" => id} end
paid = {:ok, %{"order_id" => "order-1", "status" => "authorized"}}
logged = fn f ->
  Process.put(:log, [])
  r = f.()
  {r, Process.get(:log)}
end
'''
RUNTIME_TAIL = r'''
for {name, check, want} <- cases do
  {ok, got} =
    try do
      got = check.()
      {got == want, inspect(got)}
    rescue
      e -> {false, Exception.format_banner(:error, e) |> String.split("\n") |> hd()}
    end

  IO.puts("#{name} #{if ok, do: "PASS", else: "FAIL"}")
  if not ok, do: IO.puts("  got #{name}: #{got}")
end
'''
AUTH = '{:span, "orders.payments.authorize", "order-1", %s}'
PREPARED = '{:event, "payment_request_prepared", "prepare", %s}'
RUNTIME = {
    # E2: no span for prepare and finish; the event and the EFFECT span stand in the caller's span (here none).
    "place": ('logged.(fn -> BeamlSpike.place(order.("order-1")) end)',
              "{paid, [%s, %s]}" % (PREPARED % "nil", AUTH % "nil")),
    # E1: the span of place is the parent of the event and of the EFFECT span.
    "checkout": ('logged.(fn -> BeamlSpike.checkout(order.("order-1")) end)',
                 '{paid, [{:span, "orders.place", "order-1", nil}, %s, %s]}'
                 % (PREPARED % '"orders.place"', AUTH % '"orders.place"')),
    # E6 (D6B-88, O3): the outer span has order_id nil; the inner EFFECT span keeps "order-1". p0 would raise here.
    "by_id": ('logged.(fn -> BeamlSpike.by_id("order-1") end)',
              '{paid, [{:span, "orders.place", nil, nil}, %s, %s]}'
              % (PREPARED % '"orders.place"', AUTH % '"orders.place"')),
    # E4: the spans nest by call through the cycle ping -> pong -> ping -> pong -> place.
    "ping": ('logged.(fn -> BeamlSpike.ping(order.("loop")) end)',
             '{paid, [{:span, "orders.pong", "loop", nil}, {:span, "orders.ping", "order-1", "orders.pong"}, '
             '{:span, "orders.pong", "order-1", "orders.ping"}, {:span, "orders.place", "order-1", "orders.pong"}, '
             '%s, %s]}' % (PREPARED % '"orders.place"', AUTH % '"orders.place"')),
    # E4c: c1 -> c2 -> c3 -> place.
    "c1": ('logged.(fn -> BeamlSpike.c1(order.("order-1")) end)',
           '{paid, [{:span, "orders.c2", "order-1", nil}, {:span, "orders.c3", "order-1", "orders.c2"}, '
           '{:span, "orders.place", "order-1", "orders.c3"}, %s, %s]}'
           % (PREPARED % '"orders.place"', AUTH % '"orders.place"')),
    # E3 (guard): a pure pipe writes no span.
    "label": ('logged.(fn -> BeamlSpike.label(%{"order_id" => "order-1", "status" => "authorized"}) end)',
              '{"authorized", []}'),
}

# 12b (DL-120): one source per case. HEAD has no place; WITH_PLACE adds the EFFECT flow place.
HEAD = ("type Order { order_id: String }\ntype Payment { order_id: String status: String }\n"
        "type PaymentError { reason: String }\n"
        'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n'
        'fn to_order Payment { order_id, status } -> Order = Order { order_id: "done" }\n'
        "type Ticket { id: String }\nenum Settled { Done(Payment) }\n")
WITH_PLACE = HEAD + "fn place order: Order -> Payment ! PaymentError = order |> payments.authorize\n"
# A record literal is legal only in its constructor (DL-092), so the record constructor ends in a call of itself.
TICKET = ("fn Ticket o: Order -> Ticket ! PaymentError\n"
          'fn Ticket Order { order_id: "done" } -> Ticket ! PaymentError = Ticket { id: "done" }\n'
          "fn Ticket o -> Ticket ! PaymentError = o |> settle |> Ticket\n"
          "fn settle o: Order -> Order ! PaymentError = o |> place |> to_order\n")
REACH = {
    "record_direct": (HEAD + "fn Ticket o: Order -> Ticket ! PaymentError = o |> payments.authorize |> to_order |> Ticket\n",
                      "Ticket", "Ticket -> payments.authorize"),
    "record_through_helpers": (WITH_PLACE + TICKET, "Ticket", "Ticket -> settle -> place -> payments.authorize"),
    "enum_direct": (HEAD + "fn Settled order: Order -> Settled ! PaymentError = order |> payments.authorize |> Done\n",
                    "Settled", "Settled -> payments.authorize"),
    "enum_through_helper": (WITH_PLACE + "fn Settled order: Order -> Settled ! PaymentError = order |> place |> Done\n",
                            "Settled", "Settled -> place -> payments.authorize"),
    # O3 (RED review): two paths of length 3; D6B-113 takes h1, the first step in source order.
    "enum_equal_paths": (WITH_PLACE + "fn h1 o: Order -> Order ! PaymentError = o |> place |> to_order\n"
                         "fn h2 o: Order -> Payment ! PaymentError = o |> place\n"
                         "fn Settled order: Order -> Settled ! PaymentError = order |> h1 |> h2 |> Done\n",
                         "Settled", "Settled -> h1 -> place -> payments.authorize"),
}
# DL-120: a fn may call the EFFECT and pipe its result into a pure constructor.
PURE_CONSTRUCTOR = (HEAD + "type Receipt { status: String }\nfn Receipt s: String -> Receipt = Receipt { status: s }\n"
                    "fn status_of Payment { order_id, status } -> String = status\n"
                    "fn settle order: Order -> Receipt ! PaymentError = order |> payments.authorize |> status_of |> Receipt\n")


def reach_error(ctor, path):
    """D6B-112 text; D6B-113 path (shortest, first in source order)."""
    return ("error: fn %s: a constructor cannot reach an EFFECT: %s (DL-120)\n"
            "  help: call the EFFECT in a lowercase fn, then pipe its result into fn %s" % (ctor, path, ctor))


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


def clauses(stdout):
    """`name#i` -> the text of the i-th `defp __beaml_name` clause of the BeamlSpike module."""
    found, current, count = {}, None, {}
    for line in stdout.splitlines():
        head = re.match(r"  defp __beaml_(\w+)\(", line)
        if head and not head.group(1).startswith(("new_", "valid", "decode", "project", "result", "fail", "attempt")):
            name = head.group(1)
            count[name] = count.get(name, 0) + 1
            current = "%s#%d" % (name, count[name])
            found[current] = [line]
            if ", do: " in line:
                current = None
        elif current:
            found[current].append(line)
            if line == "  end":
                current = None
    return {key: "\n".join(lines) for key, lines in found.items()}


def span_names(text):
    return [unb(m) for m in re.findall(r"ProbeSupport\.span\((<<[\d,]*>>)", text)]


class Slice6EffectReach(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6reach-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def build(self, source, extra=("--stored", str(EMPTY_STORED))):
        """`source`: a Path or BEAML text. Return (code, stdout, stderr). E10: events hold no path and no source text."""
        if not isinstance(source, Path):
            path = self.work / "src" / "case.beaml"
            path.parent.mkdir(exist_ok=True)
            path.write_text(source)
            source = path
        result = subprocess.run([compiler(), str(source), *extra], cwd=self.work / "cwd", capture_output=True,
                                text=True)
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            text = log.read_text()
            self.assertNotIn(str(source.parent), text, "action events must not record the source path")
            self.assertNotIn("fn ", text, "action events must not record source text")
        return result.returncode, result.stdout, result.stderr

    def built(self, source=FIXTURE):
        code, stdout, stderr = self.build(source)
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout), "setup: compile failed: " + stderr)
        return stdout

    # Step 12, build cases.

    def test_span_names_per_clause(self):
        # E1 to E6, E4c under DL-119 S. Today: place keeps orders.prepare and orders.finish; no reaching step has a span.
        found = clauses(self.built())
        self.assertEqual(sorted(SPANS), sorted(found), "setup: the clause parser found other clauses")
        for key, names in SPANS.items():
            with self.subTest(key):
                self.assertEqual(names, span_names(found[key]), found[key])

    def test_exact_lines_per_clause(self):
        # E1 (first RED), E2, E4, E4c, E6: the exact text of the span and of the prepared event.
        found = clauses(self.built())
        for key, want in LINES.items():
            with self.subTest(key):
                lines = [line.strip() for line in found.get(key, "").splitlines()]
                self.assertEqual([], [w for w in want if w not in lines], found.get(key))
        with self.subTest("checkout has no prepared event (D6B-89)"):
            self.assertNotIn("ProbeSupport.event", found["checkout#1"])

    def test_runtime_spans_follow_the_reach(self):
        # E1, E2, E4, E4c, E6 at run time; label (E3) is a guard.
        stdout = self.built()
        out = self.work / "beam"
        out.mkdir()
        (out / "generated.ex").write_text(stdout)
        (out / "stubs.ex").write_text(STUBS)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "stubs.ex"),
                               str(out / "generated.ex")], capture_output=True, text=True)
        self.assertEqual(0, beam.returncode, "setup: elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn -> %s end, %s}' % (name, call, want) for name, (call, want) in RUNTIME.items())
        (out / "checks.exs").write_text(RUNTIME_HEAD + "\ncases = [\n" + listed + "\n]\n" + RUNTIME_TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(0, run.returncode, "setup: checks.exs did not run:\n" + run.stdout + run.stderr)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in RUNTIME:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout)

    def test_sources_keep_their_bytes_except_pure_step_spans(self):
        # E8 under DL-119: the pre-step output with every pure-step span removed (D6B-114, D6B-117). Unchanged rows
        # are guards; the 40 rows with "changed" fail today.
        table = json.loads(BYTE_GUARD.read_text())
        # O2 (RED review): the table of the pre-step base has 71 rows and 40 changed ones. A table regenerated with a
        # GREEN build has 0 changed rows and fails here.
        self.assertEqual((71, 40), (len(table), sum(row["changed"] for row in table.values())),
                         "setup: byte-guard.json is not the table of the pre-step base")
        for relative, row in table.items():
            with self.subTest(relative):
                code, stdout, stderr = self.build(REPO / relative)
                self.assertEqual((row["code"], row["sha256"]), (code, hashlib.sha256(stdout.encode()).hexdigest()),
                                 stderr)

    # Step 12, guards.

    def test_pure_pipes_stay_silent(self):
        # E3, E5 (guard): no ProbeSupport in a pure clause; a pure module has no ProbeSupport at all (step 5 S14).
        found = clauses(self.built())
        for key in ("label#1", "a#1", "b#1"):
            with self.subTest(key):
                self.assertNotIn("ProbeSupport", found[key])
        with self.subTest("pipe.beaml"):
            self.assertNotIn("ProbeSupport", self.built(PIPE))

    def test_one_clause_rule_stays_for_a_direct_effect_step(self):
        # E7 (guard, D6B-87): the step 4 text; pong (two clauses, indirect) compiles (every build above).
        code, stdout, stderr = self.build(REUSE.read_text()
                                          + "fn auth code: String, order: Order -> Payment ! PaymentError\n"
                                          'fn auth "a", order -> Payment ! PaymentError = order |> payments.authorize\n'
                                          "fn auth _, order -> Payment ! PaymentError = order |> prepare |> payments.authorize\n",
                                          ())
        self.assertEqual((1, "", "a function with a pipe body has one clause in slice 1: auth"),
                         (code, stdout, stderr.strip()))

    # Step 12b (DL-120), reject cases and one guard.

    def test_constructor_that_reaches_an_effect_is_rejected(self):
        for name, (source, ctor, path) in REACH.items():
            with self.subTest(name):
                code, stdout, stderr = self.build(source)
                self.assertEqual((1, "", reach_error(ctor, path)), (code, stdout, stderr.strip()),
                                 "expected exit 1, no stdout and the exact message")

    def test_fn_may_pipe_an_effect_result_into_a_pure_constructor(self):
        # Guard: DL-120 allows the EFFECT in a lowercase fn before the constructor.
        self.built(PURE_CONSTRUCTOR)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
