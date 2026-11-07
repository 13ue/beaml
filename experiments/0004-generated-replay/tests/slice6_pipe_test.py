"""EXPERIMENT 0004 slice 6b step 5: a pipe in any expression position (DL-086).

Plan step 5, D6B-25 to D6B-28. Build case: slice6/pipe/pipe.beaml compiles; nested pipes are plain nested calls.
Runtime cases: the module compiles with `elixirc --warnings-as-errors` WITHOUT a ProbeSupport stub (step 3 harness).
Reject cases: one source each, the exact message text is asserted. Expected text comes from the plan and the step 5
notes, never from the new compiler. Guards: the bad/*.beaml texts and the EFFECT fixture outputs stay byte-equal
(sha256 from the baseline compiler of commit 80bd33cd, notes.md decision S12).
Run: python3 -B experiments/0004-generated-replay/tests/slice6_pipe_test.py [-k NAME]
"""
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT, REPO  # noqa: E402
import slice6_constructor_test as sc  # noqa: E402

PIPE = EXPERIMENT / "slice6" / "pipe" / "pipe.beaml"
ORDERS = sc.ORDERS
EMPTY_STORED = sc.EMPTY_STORED
HEAD = sc.HEAD
b = sc.b

PIPE_CASES = {
    "argument_ends_at_comma": 'BeamlSpike.g(%{"id" => "a"}, "t") == %{"id" => "a!", "tag" => "t"}',
    "argument_ends_at_paren": 'BeamlSpike.last("a", "c") == "c-(a)"',
    "plus_binds_stronger": 'BeamlSpike.cat("a", "b", "c") == "(ab)-c"',
    "record_field_in_constructor": 'BeamlSpike.new_Pair_1("x", "y") == %BeamlSpike.Pair{a: "(x)", b: "y"}',
    "variant_step_in_record_field": ('BeamlSpike.box("r") == '
                                     '%{"note" => "r", "state" => {"Outcome", "Declined", ["(r)"]}}'),
    "failing_step_first_clause": "BeamlSpike.pick(\"a\", 0) == {:error, %BeamlSpike.IsZero{}}",
    "failing_step_stops_the_pipe": "BeamlSpike.pick(\"b\", 0) == {:error, %BeamlSpike.IsZero{}}",
    "first_clause_ok": 'BeamlSpike.pick("a", 2) == {:ok, %BeamlSpike.NonZeroInt{value: 2}}',
    "second_clause_ok": 'BeamlSpike.pick("b", 3) == {:ok, %BeamlSpike.NonZeroInt{value: 3}}',
}

NESTED_HELP = "  help: make the pipe the whole body"
SMALL = ("type P { id: String }\ntype R { id: String tag: String }\n"
         "fn prepare P { id } -> P = P { id: id }\n"
         "fn build P { id }, x: String -> R = R { id: id, tag: x }\n")
OUTCOME = "enum Outcome { Approved()  Declined(String)  Two(String, String) }\n"

# Guard S12: stdout sha256, --stored stored/empty.jsonl. Re-pinned to the step 6a compiler (commit 0747c315), see
# slice6b-records-v2/repin.md; before: the baseline compiler (commit 80bd33cd).
EFFECT_OUTPUTS = {
    "arms/gen/orders.beaml": "009d8ab3127b8734e14555d7c87cc337e438cda8ae583a7cbbb2c8d065c92343",
    "slice2/reuse/orders.beaml": "e7899cc35816804ac7a1d5f26654a7c23558a33e1403daa2023a942567650d31",
}
PAYMENTS = REPO / "experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml"
PAYMENTS_SNAPSHOT = EXPERIMENT / "tests" / "payments.generated.snapshot"
# Guard S13: the bad/*.beaml texts of the baseline compiler. Each file gives its own first error.
BAD = {
    "field_not_in_type.beaml": "unknown field: Payment.amount",
    "pipe_type_mismatch.beaml": "type mismatch in pipe step finish: expected Payment, got Order",
    "undeclared_failure.beaml": "pipe step payments.authorize can fail with PaymentError, which is not in the ! list of place",
    "unknown_pipe_step.beaml": "unknown pipe step: charge",
    "unsupported_effect_kind.beaml": "unsupported effect kind: db.get in effect payments.authorize (slice 1 supports http.post)",
}


class Slice6Pipe(unittest.TestCase):
    maxDiff = None
    setUp = sc.Slice6Constructor.setUp
    compile = sc.Slice6Constructor.compile
    assert_built = sc.Slice6Constructor.assert_built
    assert_rejected = sc.Slice6Constructor.assert_rejected
    assert_lines = sc.Slice6Constructor.assert_lines
    run_runtime = sc.Slice6Constructor.run_runtime

    # Build and runtime cases.

    def test_pipe_fixture_compiles_to_plain_calls(self):
        # D6B-28: a nested pipe is plain nested calls; a failing whole-body pipe is a `with`. Today: "expected ')'".
        self.assert_lines(self.assert_built(PIPE), [
            "defp __beaml_g(v_p, v_x), do: __MODULE__.build(__MODULE__.prepare(v_p), v_x)",
            "defp __beaml_cat(v_a, v_b, v_c), do: __MODULE__.join(__MODULE__.paren((v_a <> v_b)), v_c)",
            "with {:ok, p1} <- __MODULE__.new_NonZeroInt_1(p0) do",
        ])

    def test_runtime_pipe(self):
        self.run_runtime(PIPE, PIPE_CASES)

    # Reject cases: D6B-27, a nested pipe with an EFFECT step or a failing step.

    def test_effect_step_in_an_argument_pipe(self):
        self.assert_rejected(ORDERS.read_text()
                             + "fn wrap o: Order -> Payment ! PaymentError = finish(o |> payments.authorize)\n",
                             "error: fn wrap: a nested pipe has the EFFECT step payments.authorize\n" + NESTED_HELP)

    def test_failing_step_in_an_argument_pipe(self):
        # The `!` list matches, so nesting is the only reason.
        self.assert_rejected(HEAD + "fn keep x: NonZeroInt -> NonZeroInt = x\n"
                             "fn w n: Int -> NonZeroInt ! IsZero = keep(n |> NonZeroInt)\n",
                             "error: fn w: a nested pipe has the failing step NonZeroInt\n" + NESTED_HELP)

    def test_failing_step_in_a_record_field_pipe(self):
        # RED review O2: the D6B-27 check also covers a record field value, not only a call argument.
        self.assert_rejected(HEAD + "type B { v: NonZeroInt }\n"
                             "fn w n: Int -> B ! IsZero = B { v: n |> NonZeroInt }\n",
                             "error: fn w: a nested pipe has the failing step NonZeroInt\n" + NESTED_HELP)

    # Reject cases: the `!` rule and the step kinds (DL-086, D6B-26).

    def test_failing_step_without_a_matching_failure(self):
        # A pure several-clause fn with a `!` list without IsZero. Existing text (bad/undeclared_failure.beaml form).
        self.assert_rejected(HEAD + "type Other { reason: String }\n"
                             "fn pick s: String, n: Int -> NonZeroInt ! Other\n"
                             'fn pick "a", n -> NonZeroInt ! Other = n |> NonZeroInt\n'
                             "fn pick _, n -> NonZeroInt ! Other = n |> NonZeroInt\n",
                             "pipe step NonZeroInt can fail with IsZero, which is not in the ! list of pick")

    def test_lowercase_non_fn_step_in_an_argument_pipe(self):
        # `x` is a variable, not a fn. Existing text (bad/unknown_pipe_step.beaml form).
        self.assert_rejected(SMALL + "fn g p: P, x: String -> R = build(p |> x, x)\n", "unknown pipe step: x")

    def test_variant_step_without_a_payload(self):
        self.assert_rejected(OUTCOME + "fn z s: String -> Outcome = s |> Approved\n",
                             "pipe step Approved must take one argument")

    def test_variant_step_with_two_payloads(self):
        self.assert_rejected(OUTCOME + "fn z s: String -> Outcome = s |> Two\n",
                             "pipe step Two must take one argument")

    def test_variant_step_with_a_wrong_payload_type(self):
        self.assert_rejected(OUTCOME + "fn z n: Int -> Outcome = n |> Declined\n",
                             "type mismatch in pipe step Declined: expected String, got Int")

    # Guards: pass today.

    def test_bad_fixtures_keep_their_texts(self):
        for name, message in BAD.items():
            with self.subTest(name):
                self.assert_rejected(EXPERIMENT / "bad" / name, message)

    def test_effect_fixture_outputs_stay_byte_equal(self):
        for relative, digest in EFFECT_OUTPUTS.items():
            with self.subTest(relative):
                code, stdout, stderr = self.compile(EXPERIMENT / relative, extra=["--stored", str(EMPTY_STORED)])
                self.assertEqual((0, digest), (code, hashlib.sha256(stdout.encode()).hexdigest()), stderr)
        with self.subTest("payments.beaml"):
            code, stdout, stderr = self.compile(PAYMENTS)
            self.assertEqual((0, PAYMENTS_SNAPSHOT.read_text()), (code, stdout), stderr)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
