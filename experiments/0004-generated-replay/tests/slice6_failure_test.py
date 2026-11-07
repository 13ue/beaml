"""EXPERIMENT 0004 slice 6b step 2: the failure position `-> T ! E1 | E2` and the overlap check (E1).

Plan step 2, D6B-04 to D6B-10, DL-092, DL-093. Build cases: slice6/failure/body.beaml and overlap.beaml compile
to the planned Elixir shape. Runtime cases: each generated module compiles with `elixirc --warnings-as-errors`;
the TYPE of a clause body decides `{:ok, v}` or `{:error, v}`; a record failure is the failure struct.
Reject cases: one source each, so that the first error is the tested one; the exact message text is asserted
(plan-review.md (5), step 2). Expected text comes from the plan and the RED notes, never from the new compiler.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_failure_test.py [-k NAME]
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import stored_types_test as st  # noqa: E402

BODY = EXPERIMENT / "slice6" / "failure" / "body.beaml"
OVERLAP = EXPERIMENT / "slice6" / "failure" / "overlap.beaml"
ORDERS = EXPERIMENT / "slice2" / "reuse" / "orders.beaml"
EMPTY_STORED = EXPERIMENT / "stored" / "empty.jsonl"


def b(text):
    """A BEAML string as the emitter writes it."""
    return "<<%s>>" % ",".join(str(c) for c in text.encode())


def overlap(owner, success, failure=None, effect=False):
    """D6B-09 text; notes.md decisions 3 to 5 fix the structural and the EFFECT forms."""
    head = "error: %s: the success TYPE %s is also a failure TYPE" % (owner, success)
    if failure:
        head += ": %s has the same fields" % failure
    help_line = "  help: give the failure a TYPE of its own (for example type FError { reason: String })"
    if not effect:
        help_line += ", or remove %s after !" % (failure or success)
    return head + "\n" + help_line


# Slice 1 code wraps each live pipe step in ProbeSupport.span/5. The runtime checks need only the value.
# ponytail: stub; D6B-28 (step 5) removes spans from pure modules, then this stub has no caller.
PROBE_SUPPORT_STUB = "defmodule ProbeSupport do\n  def span(_, _, _, _, f), do: f.()\nend\n"

RUNTIME_HEAD = r'''
invalid = fn fun ->
  try do
    fun.()
    false
  rescue
    e in ArgumentError -> e.message == "invalid BEAML input"
  end
end
'''
RUNTIME_TAIL = r'''
results =
  for {name, check} <- cases do
    ok =
      try do
        check.() == true
      rescue
        _ -> false
      end

    IO.puts("#{name} #{if ok, do: "PASS", else: "FAIL"}")
    ok
  end

if not Enum.all?(results), do: System.halt(1)
'''
BODY_CASES = {
    "check_empty_fails": 'BeamlSpike.check("") == {:error, %BeamlSpike.Empty{}}',
    "check_value_ok": 'BeamlSpike.check("a") == {:ok, "a"}',
    "check_input_rejects": "invalid.(fn -> BeamlSpike.check(5) end)",
    "guard_record_failure": 'BeamlSpike.guard("x") == {:error, %BeamlSpike.Bad{reason: "no x"}}',
    "guard_ok": 'BeamlSpike.guard("y") == {:ok, "y"}',
    "why_enum_failure": 'BeamlSpike.why("") == {:error, {"Why", "Short", ["empty"]}}',
    "why_ok": 'BeamlSpike.why("w") == {:ok, "w"}',
    "piped_ends_in_failure": 'BeamlSpike.piped("a") == {:error, 7}',
    "outer_passes_failure": 'BeamlSpike.outer("") == {:error, %BeamlSpike.Empty{}}',
    "outer_ok": 'BeamlSpike.outer("b") == {:ok, "b"}',
}
OVERLAP_CASES = {
    "f_int_failure": 'BeamlSpike.f("a") == {:error, 5}',
    "g_string_failure": 'BeamlSpike.g(0) == {:error, "zero"}',
    "g_ok": "BeamlSpike.g(3) == {:ok, 3}",
    "h_ok": 'BeamlSpike.h("a") == {:ok, %{"id" => "a"}}',
}

EFFECT_HEAD = 'effect payments.authorize I -> %s = http.post("payments/authorize")\n'
OTHER = "fn other s: String -> String = s\n"  # a fn without the effect: the overlap check runs before the flow check


class Slice6Failure(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6fail-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def compile(self, source, extra=()):
        """`source`: a Path or BEAML text; `extra`: more CLI arguments. Return (code, stdout, stderr)."""
        if not isinstance(source, Path):
            path = self.work / "src" / "case.beaml"
            path.parent.mkdir(exist_ok=True)
            path.write_text(source)
            source = path
        result = subprocess.run([st.compiler(), str(source), *extra], cwd=self.work / "cwd", capture_output=True, text=True)
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            text = log.read_text()
            self.assertNotIn(str(source.parent), text, "action events must not record the source path")
            self.assertNotIn("fn ", text, "action events must not record source text")
        return result.returncode, result.stdout, result.stderr

    def assert_built(self, source):
        code, stdout, stderr = self.compile(source)
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout),
                         "expected exit 0 and Elixir on stdout; stderr: " + stderr)
        return stdout

    def assert_rejected(self, source, message):
        code, stdout, stderr = self.compile(source)
        self.assertEqual((1, "", message), (code, stdout, stderr.strip()),
                         "expected exit 1, no stdout and the exact message")

    def assert_lines(self, stdout, present, absent=()):
        lines = [line.strip() for line in stdout.splitlines()]
        self.assertEqual(([], []), ([p for p in present if p not in lines], [a for a in absent if a in lines]),
                         "missing or unexpected lines; stdout:\n" + stdout)

    def run_runtime(self, fixture, cases):
        stdout = self.assert_built(fixture)
        out = self.work / "beam"
        out.mkdir()
        (out / "generated.ex").write_text(stdout)
        (out / "probe_support.ex").write_text(PROBE_SUPPORT_STUB)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "generated.ex"),
                               str(out / "probe_support.ex")],
                              capture_output=True, text=True)
        self.assertEqual(0, beam.returncode, "elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn -> %s end}' % item for item in cases.items())
        (out / "checks.exs").write_text(RUNTIME_HEAD + "\ncases = [\n" + listed + "\n]\n" + RUNTIME_TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in cases:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout + run.stderr)

    # Build cases.

    def test_body_fixture_compiles_to_the_planned_shape(self):
        # plan.md step 2, Elixir shape; D6B-07 record failure is the struct; D6B-04 no struct for an enum failure.
        self.assert_lines(self.assert_built(BODY), [
            "defp __beaml_check(<<>>), do: {:error, %__MODULE__.Empty{}}",
            "defp __beaml_check(v_x), do: {:ok, v_x}",
            "defp __beaml_guard(%s), do: {:error, %%__MODULE__.Bad{reason: %s}}" % (b("x"), b("no x")),
            "defp __beaml_guard(v_s), do: {:ok, v_s}",
            "defp __beaml_why(<<>>), do: {:error, {%s, %s, [%s]}}" % (b("Why"), b("Short"), b("empty")),
            "defmodule Empty do",
            "defstruct []",
            "defmodule Bad do",
            "defstruct [:reason]",
        ], absent=["defmodule Why do"])

    def test_overlap_fixture_compiles(self):
        # plan.json first_red_test: `fn f x: String -> String ! Int = 5` compiles (DL-093).
        self.assert_lines(self.assert_built(OVERLAP), [
            "defp __beaml_f(_), do: {:error, 5}",
            "defp __beaml_g(0), do: {:error, %s}" % b("zero"),
            "defp __beaml_g(v_n), do: {:ok, v_n}",
            "defmodule Bad do",
        ], absent=["defmodule Int do", "defmodule String do"])

    def test_plan_source_with_int_failure_compiles(self):
        self.assert_built("fn f x: String -> String ! Int = 5\n")

    def test_runtime_body(self):
        self.run_runtime(BODY, BODY_CASES)

    def test_runtime_overlap(self):
        self.run_runtime(OVERLAP, OVERLAP_CASES)

    def test_runtime_pipe_ends_in_record_failure(self):
        # RED review objection 1, D6B-05 and D6B-07: a pipe that ends in a record failure gives the struct.
        # Today: "type mismatch: expected String, got Bad".
        source = ("type Bad { reason: String }\nfn mkbad x: String -> Bad = Bad { reason: x }\n"
                  "fn pbad x: String -> String ! Bad = x |> mkbad\n")
        self.run_runtime(source, {"pbad_record_failure": 'BeamlSpike.pbad("q") == {:error, %BeamlSpike.Bad{reason: "q"}}'})

    def test_effect_beside_int_failure_compiles(self):
        # RED review objection 2: emit_effect must not treat a non-record failure as a record.
        # Today: "unknown type: Int".
        code, stdout, stderr = self.compile(ORDERS.read_text() + "fn extra x: String -> String ! Int = 5\n",
                                            extra=["--stored", str(EMPTY_STORED)])
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout),
                         "expected exit 0 and Elixir on stdout; stderr: " + stderr)
        self.assert_lines(stdout, ["defp __beaml_extra(_), do: {:error, 5}"], absent=["defmodule Int do"])

    # Reject cases: overlap (DL-093, D6B-06, D6B-08, D6B-09).

    def test_same_type_both_sides(self):
        # plan.json source. Today: "unknown type: String".
        self.assert_rejected("fn f x: String -> String ! String = x\n", overlap("fn f", "String"))

    def test_overlap_in_a_list(self):
        # plan.json source. Today: "unknown type: Int".
        self.assert_rejected("fn f x: String -> String ! Int | String = x\n", overlap("fn f", "String"))

    def test_same_int_both_sides(self):
        self.assert_rejected("fn f n: Int -> Int ! Int = n\n", overlap("fn f", "Int"))

    def test_same_record_both_sides(self):
        # Today: exit 0.
        self.assert_rejected("type R { id: String }\nfn f x: R -> R ! R = x\n", overlap("fn f", "R"))

    def test_structural_records_overlap(self):
        # D6B-06: equal fields overlap. Today: exit 0.
        self.assert_rejected("type R { id: String }\ntype S { id: String }\nfn f x: R -> R ! S = x\n",
                             overlap("fn f", "R", failure="S"))

    def test_same_enum_both_sides(self):
        # D6B-10: `-> E ! E` is the enum overlap case. Today: "unknown type: Why".
        self.assert_rejected("enum Why {\n  Short(String)\n}\nfn f x: Why -> Why ! Why = x\n", overlap("fn f", "Why"))

    def test_effect_overlap(self):
        # D6B-08. Today: "slice 1 needs exactly one pipe that calls the effect payments.authorize".
        self.assert_rejected("type O { reason: String }\ntype I { id: String }\n" + EFFECT_HEAD % "O ! O" + OTHER,
                             overlap("effect payments.authorize", "O", effect=True))

    def test_effect_structural_overlap(self):
        # D6B-06 and D6B-08. Today: the flow text as above.
        self.assert_rejected("type O { reason: String }\ntype P { reason: String }\ntype I { id: String }\n"
                             + EFFECT_HEAD % "P ! O" + OTHER,
                             overlap("effect payments.authorize", "P", failure="O", effect=True))

    def test_equal_record_failures_in_a_list(self):
        # RED review objection 3, notes.md RED repair decision R3: plain records are structural, so A and B are
        # the same TYPE. Today: exit 0.
        self.assert_rejected("type A { reason: String }\ntype B { reason: String }\n"
                             "fn f x: String -> String ! A | B = x\n",
                             "error: fn f: the failure TYPE A is also a failure TYPE: B has the same fields\n"
                             "  help: remove B after !")

    def test_duplicate_failure_keeps_its_text(self):
        # Guard: `unique` runs before the overlap check. Today the same text.
        self.assert_rejected("fn f x: String -> String ! String | String = x\n", "duplicate name: String")

    # Reject cases: a body of neither TYPE (D6B-05, notes.md decision 6).

    def test_body_of_neither_type(self):
        # Today: "unknown type: Int".
        self.assert_rejected("type E {}\nfn f x: String -> String ! Int = E {}\n",
                             "type mismatch: expected String ! Int, got E")

    def test_body_of_neither_type_record_failure(self):
        # Today: "type mismatch: expected String, got E".
        self.assert_rejected("type E {}\ntype Bad { reason: String }\nfn f x: String -> String ! Bad = E {}\n",
                             "type mismatch: expected String ! Bad, got E")

    def test_pipe_ends_in_neither_type(self):
        # Today: "type mismatch: expected String, got Int".
        self.assert_rejected("type Bad { reason: String }\nfn seven x: String -> Int = 7\n"
                             "fn p x: String -> String ! Bad = x |> seven\n",
                             "type mismatch: expected String ! Bad, got Int")

    # Reject cases: the rest of the step (D6B-10, notes.md decisions 7 and 8).

    def test_variant_is_no_failure_type(self):
        # D6B-10. Today: "unknown type: Short" without the help line.
        self.assert_rejected("enum Why {\n  Short(String)\n}\nfn f x: String -> String ! Short = x\n",
                             "unknown type: Short\n  help: Short is a variant of the enum Why, not a TYPE; write Why")

    def test_no_int_in_effect_failure(self):
        # Step 1 notes, Limits: EFFECT failure records with an Int field. Today: the --stored text.
        self.assert_rejected("type O { reason: String, code: Int }\ntype P { id: String }\ntype I { id: String }\n"
                             + EFFECT_HEAD % "P ! O" + "fn g i: I -> P ! O = i |> payments.authorize\n",
                             "effect payments.authorize: slice 6b fails with String fields only, not O.code")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
