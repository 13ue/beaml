"""EXPERIMENT 0004 slice 6b step 4: ENUM LITERALS or an enum constructor (DL-082, DL-084, DL-085, DL-087, DL-088, DL-100).

Plan step 4, D6B-20 to D6B-24. Build cases: slice6/enum/literals.beaml and slice6/enum/constructor.beaml compile to the
planned Elixir shape (one function new_<TYPE>_<k> per signature, clauses in source order). Runtime cases: each module
compiles with `elixirc --warnings-as-errors` WITHOUT a ProbeSupport stub (step 3 harness). Reject cases: one source each,
the exact message text is asserted. Expected text comes from the plan and the step 4 notes, never from the new compiler.
Decode is not tested here (steps 7, 8).
Run: python3 -B experiments/0004-generated-replay/tests/slice6_enum_test.py [-k NAME]
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT  # noqa: E402
import slice6_constructor_test as sc  # noqa: E402

LITERALS = EXPERIMENT / "slice6" / "enum" / "literals.beaml"
CONSTRUCTOR = EXPERIMENT / "slice6" / "enum" / "constructor.beaml"
b = sc.b


def variant(owner, name, args=""):
    """A variant value as the emitter writes it: {owner, variant, [args]}."""
    return "{%s, %s, [%s]}" % (b(owner), b(name), args)


PS = "PaymentState"
LITERAL_CASES = {
    "label_authorized": 'BeamlSpike.label({"PaymentState", "Authorized", []}) == "ok"',
    "label_pending": 'BeamlSpike.label({"PaymentState", "Pending", []}) == "pending"',
    "label_unknown": 'BeamlSpike.label({"PaymentState", "Unknown", ["x"]}) == "x"',
    "bare_variant_in_fn": 'BeamlSpike.pending() == {"PaymentState", "Pending", []}',
}
CONSTRUCTOR_CASES = {
    "pair_ok": 'BeamlSpike.new_PaymentState_1("ok", "") == {"PaymentState", "Authorized", []}',
    "pair_declined_pipe": ('BeamlSpike.new_PaymentState_1("declined", "card") == '
                           '{"PaymentState", "Declined", [%{"text" => "card"}]}'),
    "pair_unknown": 'BeamlSpike.new_PaymentState_1("x", "") == {"PaymentState", "Unknown", ["x"]}',
    "pair_input_rejects": 'invalid.(fn -> BeamlSpike.new_PaymentState_1(1, "") end)',
    "code_ok": 'BeamlSpike.new_PaymentState_2("ok") == {"PaymentState", "Authorized", []}',
    "code_unknown": 'BeamlSpike.new_PaymentState_2("zz") == {"PaymentState", "Unknown", ["zz"]}',
    "int_zero": 'BeamlSpike.new_PaymentState_3(0) == {"PaymentState", "Pending", []}',
    "int_other": 'BeamlSpike.new_PaymentState_3(5) == {"PaymentState", "Unknown", ["int"]}',
    "call_pair": 'BeamlSpike.from_pair("declined", "cvc") == {"PaymentState", "Declined", [%{"text" => "cvc"}]}',
    "call_code": 'BeamlSpike.from_code("ok") == {"PaymentState", "Authorized", []}',
    "call_int": 'BeamlSpike.from_int(0) == {"PaymentState", "Pending", []}',
    "bare_variant_in_fn": 'BeamlSpike.pending() == {"PaymentState", "Pending", []}',
}

# `Approved()` (D6B-20 keeps it legal), so that these sources reach the constructor rules today, not a parse error.
OUTCOME = "enum Outcome { Approved()  Other(String) }\n"
OUTCOME_CODE = ("fn Outcome code: String -> Outcome\n"
                'fn Outcome "ok" -> Outcome = Approved()\n'
                "fn Outcome other -> Outcome = Other(other)\n")
ANY_FN = "fn f x: String -> String = x\n"


class Slice6Enum(unittest.TestCase):
    maxDiff = None
    setUp = sc.Slice6Constructor.setUp
    compile = sc.Slice6Constructor.compile
    assert_built = sc.Slice6Constructor.assert_built
    assert_rejected = sc.Slice6Constructor.assert_rejected
    assert_lines = sc.Slice6Constructor.assert_lines
    run_runtime = sc.Slice6Constructor.run_runtime

    # Build cases.

    def test_literal_enum_compiles(self):
        # D6B-20 bare variant pattern and expression; ENUM LITERALS emit no new function (plan step 4). Today: "expected '('".
        stdout = self.assert_built(LITERALS)
        self.assert_lines(stdout, [
            "defp __beaml_label(%s), do: %s" % (variant(PS, "Authorized"), b("ok")),
            "defp __beaml_label(%s), do: v_s" % variant(PS, "Unknown", "v_s"),
        ])
        self.assertNotIn("__beaml_literal_", stdout, "ENUM LITERALS emit no function in step 4 (decode is step 7)")

    def test_constructor_enum_compiles_to_one_function_per_signature(self):
        # D6B-15 names, D6B-24 source order. Today: "a constructor needs a type PaymentState".
        stdout = self.assert_built(CONSTRUCTOR)
        lines = [line.strip() for line in stdout.splitlines()]
        first = "defp __beaml_new_PaymentState_1(%s, _), do: %s" % (b("ok"), variant(PS, "Authorized"))
        last = "defp __beaml_new_PaymentState_1(v_other, _), do: %s" % variant(PS, "Unknown", "v_other")
        self.assert_lines(stdout, [
            "def new_PaymentState_1(a0, a1) do",
            "def new_PaymentState_2(a0) do",
            "def new_PaymentState_3(a0) do",
            first,
            last,
            "defp __beaml_new_PaymentState_2(%s), do: %s" % (b("ok"), variant(PS, "Authorized")),
            "defp __beaml_new_PaymentState_3(0), do: %s" % variant(PS, "Pending"),
        ], absent=["def PaymentState(a0, a1) do", "def new_PaymentState_1(a0) do"])
        self.assertLess(lines.index(first), lines.index(last), "clauses keep source order (D6B-24)")

    def test_runtime_literal_enum(self):
        self.run_runtime(LITERALS, LITERAL_CASES)

    def test_runtime_constructor_enum(self):
        self.run_runtime(CONSTRUCTOR, CONSTRUCTOR_CASES)

    def test_equal_types_with_other_names_is_reachable(self):
        # D6B-23 compares (name, TYPE) pairs: other keys, so decode can reach it (D6B-16 note). Today: constructor error.
        self.assert_built(OUTCOME + OUTCOME_CODE + "fn Outcome status: String -> Outcome\n"
                          "fn Outcome s -> Outcome = Other(s)\n")

    # Reject cases.

    def test_literals_and_constructor_on_one_enum(self):
        # DL-088, D6B-22 text.
        self.assert_rejected('enum PaymentState { Authorized = "ok"  Unknown(String) }\n'
                             "fn PaymentState status: String -> PaymentState\n"
                             'fn PaymentState "ok" -> PaymentState = Authorized\n'
                             "fn PaymentState other -> PaymentState = Unknown(other)\n",
                             "error: enum PaymentState has literals and a constructor\n"
                             "  help: keep the literals for a 1:1 mapping or the constructor fn PaymentState, not both")

    def test_unreachable_clause_after_a_catch_all(self):
        # DL-087: the existing clause text, now inside an enum constructor signature.
        self.assert_rejected(OUTCOME + "fn Outcome code: String -> Outcome\n"
                             "fn Outcome other -> Outcome = Other(other)\n"
                             'fn Outcome "ok" -> Outcome = Approved()\n',
                             "unreachable clause: Outcome")

    def test_unreachable_signature_with_equal_parameters(self):
        # DL-087, D6B-23; the step 3 text (step 3 notes S10).
        self.assert_rejected(OUTCOME + OUTCOME_CODE + "fn Outcome code: String -> Outcome\n"
                             "fn Outcome x -> Outcome = Other(x)\n",
                             "unreachable signature: Outcome\n"
                             "  help: an earlier signature line of fn Outcome has the same parameters; remove this one")

    def test_unreachable_signature_with_more_parameters(self):
        # D6B-23: every (name, TYPE) of signature 1 is in signature 2, so the decode always takes signature 1.
        self.assert_rejected(OUTCOME + OUTCOME_CODE + "fn Outcome code: String, extra: String -> Outcome\n"
                             "fn Outcome c, _ -> Outcome = Other(c)\n",
                             "unreachable signature: Outcome\n"
                             "  help: an earlier signature line of fn Outcome has a part of these parameters and "
                             "matches first; remove this one")

    def test_literal_on_a_payload_variant(self):
        # DL-098 grammar rule, D6B-21: a payload or a literal, not both.
        self.assert_rejected("type DeclineReason { text: String }\n"
                             'enum PaymentState { Authorized = "ok"  Declined(DeclineReason) = "x"  Unknown(String) }\n'
                             + ANY_FN,
                             "error: enum PaymentState: the variant Declined has a payload and a literal\n"
                             "  help: a variant has a payload or a literal, not both")

    def test_duplicate_literal(self):
        # D6B-23: two equal literals, the second is unreachable.
        self.assert_rejected('enum PaymentState { Authorized = "ok"  Pending = "ok"  Unknown(String) }\n' + ANY_FN,
                             'error: enum PaymentState: the literal "ok" of Pending is unreachable, Authorized has it '
                             "first\n  help: give each variant a literal of its own")

    def test_lowercase_fn_keeps_one_signature_line(self):
        # Guard, D6B-14: several signatures only for constructors. Passes today.
        self.assert_rejected("fn f a: String -> String\nfn f a -> String = a\n"
                             'fn f n: Int -> String\nfn f n -> String = "int"\n',
                             "inconsistent function signature: f")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
