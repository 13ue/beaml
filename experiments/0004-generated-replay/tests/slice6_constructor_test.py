"""EXPERIMENT 0004 slice 6b step 3: the record constructor `fn T ...` (DL-092) and pure pipes without spans (D6B-28).

Plan step 3, D6B-11 to D6B-19, D6B-28 (moved forward, plan-review.md (2)). Build cases: slice6/constructor/nonzero.beaml
(signature line, unannotated clauses) and plain.beaml (corpus form) compile to the planned Elixir shape. Runtime cases:
each generated module compiles with `elixirc --warnings-as-errors` WITHOUT a ProbeSupport stub; the constructor gives
`{:error, %IsZero{}}` or `{:ok, %{"value" => n}}`. Reject cases: one source each, so that the first error is the tested
one; the exact message text is asserted (plan-review.md (5), step 3). Expected text comes from the plan and the RED
notes, never from the new compiler.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_constructor_test.py [-k NAME]
"""
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import slice6_failure_test as sf  # noqa: E402

NONZERO = EXPERIMENT / "slice6" / "constructor" / "nonzero.beaml"
PLAIN = EXPERIMENT / "slice6" / "constructor" / "plain.beaml"
BODY = EXPERIMENT / "slice6" / "failure" / "body.beaml"
ORDERS = sf.ORDERS
EMPTY_STORED = sf.EMPTY_STORED
b = sf.b

HEAD = ("type IsZero {}\ntype NonZeroInt { value: Int }\n"
        "fn NonZeroInt n: Int -> NonZeroInt ! IsZero\n"
        "fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}\n"
        "fn NonZeroInt n -> NonZeroInt ! IsZero = NonZeroInt { value: n }\n")
EFFECT = 'effect payments.authorize %s -> %s ! %s = http.post("payments/authorize")\n'
CONSTRUCTOR_HELP = "  help: call the constructor fn NonZeroInt (as a pipe step, because it can fail)"


def effect_reject(position, ty="NonZeroInt"):
    """notes.md decision S9: the D6B-19 interim text."""
    return ("error: effect payments.authorize: the TYPE %s has a constructor and cannot stand in an EFFECT %s "
            "(interim D6B-19, Q6B-3)\n  help: use a TYPE without a constructor at the EFFECT, then pipe it into "
            "fn %s" % (ty, position, ty))


NONZERO_CASES = {
    "constructor_zero_fails": "BeamlSpike.new_NonZeroInt_1(0) == {:error, %BeamlSpike.IsZero{}}",
    "constructor_ok": 'BeamlSpike.new_NonZeroInt_1(3) == {:ok, %{"value" => 3}}',
    "constructor_input_rejects": 'invalid.(fn -> BeamlSpike.new_NonZeroInt_1("3") end)',
    "wrap_zero_fails": "BeamlSpike.wrap(0) == {:error, %BeamlSpike.IsZero{}}",
    "wrap_ok": 'BeamlSpike.wrap(5) == {:ok, %{"value" => 5}}',
    "read_pattern": 'BeamlSpike.read(%{"value" => 4}) == 4',
    "keep_passes": 'BeamlSpike.keep(%{"value" => 4}) == %{"value" => 4}',
}
PLAIN_CASES = {
    "plain_zero_fails": "BeamlSpike.new_NonZeroInt_1(0) == {:error, %BeamlSpike.IsZero{}}",
    "plain_ok": 'BeamlSpike.new_NonZeroInt_1(2) == {:ok, %{"value" => 2}}',
}
# RED repair, objection 3: a constructor without `!` called as `F(r)` (plan step 3 code list).
CALL_SOURCE = ("type F { reason: String }\nfn F r: String -> F = F { reason: r }\n"
               "fn mk r: String -> F = F(r)\n")
CALL_CASES = {"call_form": 'BeamlSpike.mk("x") == %{"reason" => "x"}'}
# D6B-28: the step 2 fixture keeps its values without spans and without a stub.
BODY_PIPE_CASES = {k: v for k, v in sf.BODY_CASES.items() if k.startswith(("piped", "outer"))}


class Slice6Constructor(unittest.TestCase):
    maxDiff = None
    setUp = sf.Slice6Failure.setUp
    compile = sf.Slice6Failure.compile
    assert_built = sf.Slice6Failure.assert_built
    assert_rejected = sf.Slice6Failure.assert_rejected
    assert_lines = sf.Slice6Failure.assert_lines

    def run_runtime(self, fixture, cases):
        """The step 2 harness without the ProbeSupport stub (notes.md decision S5)."""
        stdout = self.assert_built(fixture)
        self.assertNotIn("ProbeSupport", stdout, "a module without an EFFECT must not call ProbeSupport (D6B-28)")
        out = self.work / "beam"
        out.mkdir()
        (out / "generated.ex").write_text(stdout)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "generated.ex")],
                              capture_output=True, text=True)
        self.assertEqual(0, beam.returncode, "elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn -> %s end}' % item for item in cases.items())
        (out / "checks.exs").write_text(sf.RUNTIME_HEAD + "\ncases = [\n" + listed + "\n]\n" + sf.RUNTIME_TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in cases:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout + run.stderr)

    # Build cases.

    def test_nonzero_fixture_compiles_to_the_planned_shape(self):
        # plan.md step 3, Elixir shape; D6B-15 names; D6B-28 a pure pipe is a plain `with`. Today: "expected '='".
        self.assert_lines(self.assert_built(NONZERO), [
            "def new_NonZeroInt_1(a0) do",
            "defp __beaml_new_NonZeroInt_1(0), do: {:error, %__MODULE__.IsZero{}}",
            "defp __beaml_new_NonZeroInt_1(v_n), do: {:ok, %%{%s => v_n}}" % b("value"),
            "with {:ok, p1} <- __MODULE__.new_NonZeroInt_1(p0) do",
            "defmodule IsZero do",
        ], absent=["def NonZeroInt(a0) do", "defmodule NonZeroInt do"])

    def test_plain_fixture_compiles(self):
        # The corpus form without a signature line. Today: "invalid function name: NonZeroInt".
        self.assert_lines(self.assert_built(PLAIN), [
            "defp __beaml_new_NonZeroInt_1(0), do: {:error, %__MODULE__.IsZero{}}",
            "defp __beaml_new_NonZeroInt_1(v_n), do: {:ok, %%{%s => v_n}}" % b("value"),
        ])

    def test_runtime_nonzero(self):
        self.run_runtime(NONZERO, NONZERO_CASES)

    def test_runtime_plain(self):
        self.run_runtime(PLAIN, PLAIN_CASES)

    def test_runtime_constructor_call_form(self):
        # RED repair, objection 3. Today: "invalid function name: F".
        self.run_runtime(CALL_SOURCE, CALL_CASES)

    # D6B-28 (moved into step 3): spans only for a whole-body pipe with an EFFECT step.

    def test_pure_module_has_no_span(self):
        # The step 2 fixture body.beaml changes (notes.md decision S3). Today: ProbeSupport.span per step.
        self.assert_lines(self.assert_built(BODY), [
            "p1 = __MODULE__.seven(p0)",
            "with {:ok, p1} <- __MODULE__.check(p0) do",
        ])

    def test_runtime_pure_pipe_without_stub(self):
        # Today: UndefinedFunctionError ProbeSupport.span/5 (no stub here).
        self.run_runtime(BODY, BODY_PIPE_CASES)

    def test_pure_pipe_beside_an_effect_has_no_span(self):
        # D6B-28: only the pipe with the EFFECT step keeps spans. Today: a span around echo.
        code, stdout, stderr = self.compile(ORDERS.read_text() + "fn echo s: String -> String = s\n"
                                            "fn twice s: String -> String = s |> echo\n",
                                            extra=["--stored", str(EMPTY_STORED)])
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout),
                         "expected exit 0 and Elixir on stdout; stderr: " + stderr)
        self.assert_lines(stdout, ["p1 = __MODULE__.echo(p0)"])

    def test_effect_pipe_keeps_its_spans(self):
        # Guard: the orders flow keeps ProbeSupport.span (byte-equal output, D6B-07). Passes today.
        code, stdout, stderr = self.compile(ORDERS, extra=["--stored", str(EMPTY_STORED)])
        self.assertEqual(0, code, stderr)
        self.assertIn("ProbeSupport.span(%s, :internal, p0, %s" % (b("orders.prepare"), b("prepare")), stdout)

    # Reject cases: the constructor is the only way in (DL-092, D6B-17, D6B-18).

    def test_record_literal_outside_the_constructor(self):
        self.assert_rejected(HEAD + "fn make n: Int -> NonZeroInt = NonZeroInt { value: n }\n",
                             "error: fn make: the record literal NonZeroInt { ... } is legal only in the clauses of "
                             "the constructor fn NonZeroInt\n" + CONSTRUCTOR_HELP)

    def test_structural_twin_is_not_the_nominal_type(self):
        # D6B-17: equal fields, other name. Today: "expected '='".
        self.assert_rejected(HEAD + "type Plain { value: Int }\nfn same p: Plain -> NonZeroInt = p\n",
                             "type mismatch: expected NonZeroInt, got Plain")

    def test_nominal_type_is_not_its_structural_twin(self):
        # D6B-17: "either side has a constructor".
        self.assert_rejected(HEAD + "type Plain { value: Int }\nfn back x: NonZeroInt -> Plain = x\n",
                             "type mismatch: expected Plain, got NonZeroInt")

    # RED repair, objection 1: the nominal TYPE at the `!` body gate and at the pipe step gate (D6B-17).

    def test_structural_twin_at_the_failing_body(self):
        self.assert_rejected(HEAD + "type Plain { value: Int }\nfn same p: Plain -> NonZeroInt ! IsZero = p\n",
                             "type mismatch: expected NonZeroInt ! IsZero, got Plain")

    def test_structural_twin_into_a_pipe_step(self):
        self.assert_rejected(HEAD + "type Plain { value: Int }\nfn keep x: NonZeroInt -> NonZeroInt = x\n"
                             "fn same p: Plain -> NonZeroInt = p |> keep\n",
                             "type mismatch in pipe step keep: expected NonZeroInt, got Plain")

    # RED repair, objection 2: the literal is legal only in its OWN constructor, also nested (D6B-18).

    def test_nested_literal_in_another_constructor(self):
        self.assert_rejected(HEAD + "type Box { n: NonZeroInt }\n"
                             "fn Box x: Int -> Box = Box { n: NonZeroInt { value: x } }\n",
                             "error: fn Box: the record literal NonZeroInt { ... } is legal only in the clauses of "
                             "the constructor fn NonZeroInt\n" + CONSTRUCTOR_HELP)

    def test_nested_literal_in_a_lowercase_fn(self):
        self.assert_rejected(HEAD + "type Box { n: NonZeroInt }\n"
                             "fn make x: Int -> Box = Box { n: NonZeroInt { value: x } }\n",
                             "error: fn make: the record literal NonZeroInt { ... } is legal only in the clauses of "
                             "the constructor fn NonZeroInt\n" + CONSTRUCTOR_HELP)

    # Reject cases: the signature line and the constructor name (D6B-11 to D6B-14).

    def test_second_signature_line(self):
        # Several signatures come in step 4; an equal one is unreachable there too (D6B-23).
        self.assert_rejected("type IsZero {}\ntype NonZeroInt { value: Int }\n"
                             "fn NonZeroInt n: Int -> NonZeroInt ! IsZero\n"
                             "fn NonZeroInt n: Int -> NonZeroInt ! IsZero\n"
                             "fn NonZeroInt n -> NonZeroInt ! IsZero = NonZeroInt { value: n }\n",
                             "unreachable signature: NonZeroInt\n"
                             "  help: an earlier signature line of fn NonZeroInt has the same parameters; remove this one")

    def test_clause_before_the_signature_line(self):
        # D6B-13.
        self.assert_rejected("type IsZero {}\ntype NonZeroInt { value: Int }\n"
                             "fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}\n"
                             "fn NonZeroInt n: Int -> NonZeroInt ! IsZero\n"
                             "fn NonZeroInt n -> NonZeroInt ! IsZero = NonZeroInt { value: n }\n",
                             "error: fn NonZeroInt: a clause stands before the signature line\n"
                             "  help: move the signature line above the first clause")

    def test_clause_annotation_differs_from_the_signature(self):
        # D6B-12: a clause annotation must equal the signature TYPE.
        self.assert_rejected("type IsZero {}\ntype NonZeroInt { value: Int }\n"
                             "fn NonZeroInt n: Int -> NonZeroInt ! IsZero\n"
                             "fn NonZeroInt n: String -> NonZeroInt ! IsZero = IsZero {}\n",
                             "type mismatch: expected Int, got String")

    def test_uppercase_fn_without_its_type(self):
        # D6B-11. Today: "invalid function name: Missing".
        self.assert_rejected("fn Missing x: String -> String = x\n",
                             "error: fn Missing: a constructor needs a type Missing\n"
                             "  help: declare type Missing { ... }, or write the fn name in lowercase")

    def test_constructor_returns_another_type(self):
        # D6B-11.
        self.assert_rejected("type NonZeroInt { value: Int }\nfn NonZeroInt n: Int -> Int = n\n",
                             "error: fn NonZeroInt: a constructor returns its own TYPE NonZeroInt, not Int")

    # Reject cases: no constructor TYPE at an EFFECT (D6B-19, interim for Q6B-3).

    def test_constructor_type_as_effect_output(self):
        self.assert_rejected(HEAD + "type O { reason: String }\ntype I { id: String }\n"
                             + EFFECT % ("I", "NonZeroInt", "O"), effect_reject("output"))

    def test_constructor_type_as_effect_input(self):
        self.assert_rejected(HEAD + "type O { reason: String }\ntype P { id: String }\n"
                             + EFFECT % ("NonZeroInt", "P", "O"), effect_reject("input"))

    def test_constructor_type_in_an_effect_output_field(self):
        self.assert_rejected(HEAD + "type O { reason: String }\ntype I { id: String }\ntype P { n: NonZeroInt }\n"
                             + EFFECT % ("I", "P", "O"),
                             # Step 8 lifts D6B-19 for output fields (slice6b-decode-constructor S3); an Int
                             # parameter stays out (S4), so the slice 1 field rule names the field (RED repair R3).
                             "effect payments.authorize: slice 1 decodes String fields only, not P.n")

    def test_constructor_type_as_effect_failure(self):
        self.assert_rejected("type F { reason: String }\nfn F r: String -> F = F { reason: r }\n"
                             "type I { id: String }\ntype P { id: String }\n"
                             + EFFECT % ("I", "P", "F"), effect_reject("failure", ty="F"))


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
