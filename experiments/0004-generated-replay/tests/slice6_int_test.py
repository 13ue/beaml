"""EXPERIMENT 0004 slice 6b step 1: the Int TYPE and integer literals (plan step 1, D6B-02, D6B-03).

Build cases: the fixture slice6/int/int.beaml compiles to the planned Elixir shape. Runtime cases: the generated
module compiles with `elixirc --warnings-as-errors`; integer literal clauses, an Int field and a map decoded from
JSON pass the validity check; a non-integer value raises ArgumentError "invalid BEAML input".
Reject cases: one source each, so that the first error is the tested one; the exact message text is asserted
(plan-review.md (5), step 1). Expected text comes from the plan and the compiler messages of today, never from
the new compiler.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_int_test.py [-k NAME]
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

FIXTURE = EXPERIMENT / "slice6" / "int" / "int.beaml"
INT = "<<73,110,116>>"  # the BEAML string "Int" as the emitter writes it

# Runtime asserts. Each line prints "<name> PASS" or "<name> FAIL"; the script exits 1 on any FAIL.
RUNTIME = r'''
invalid = fn fun ->
  try do
    fun.()
    false
  rescue
    e in ArgumentError -> e.message == "invalid BEAML input"
  end
end

cases = [
  {"f_zero", fn -> BeamlSpike.f(0) == "zero" end},
  {"f_other", fn -> BeamlSpike.f(7) == "other" end},
  {"f_string_rejects", fn -> invalid.(fn -> BeamlSpike.f("0") end) end},
  {"f_float_rejects", fn -> invalid.(fn -> BeamlSpike.f(0.0) end) end},
  {"size_literal_in_record", fn -> BeamlSpike.size(%{"n" => 0}) == "empty" end},
  {"size_other", fn -> BeamlSpike.size(%{"n" => 3}) == "full" end},
  {"pick_two_columns", fn -> BeamlSpike.pick(0, "s") == "s" and BeamlSpike.pick(1, "s") == "other" end},
  {"seven_literal_expression", fn -> BeamlSpike.seven() == 7 end},
  {"wrap_builds_record", fn -> BeamlSpike.wrap(5) == %{"n" => 5} end},
  {"decode_integer_passes", fn -> BeamlSpike.unbox(:json.decode(~s({"n": 7}))) == 7 end},
  {"decode_string_rejects", fn -> invalid.(fn -> BeamlSpike.unbox(:json.decode(~s({"n": "7"}))) end) end},
  {"decode_float_rejects", fn -> invalid.(fn -> BeamlSpike.unbox(:json.decode(~s({"n": 7.0}))) end) end},
  {"decode_null_rejects", fn -> invalid.(fn -> BeamlSpike.unbox(:json.decode(~s({"n": null}))) end) end}
]

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
RUNTIME_CASES = ("f_zero", "f_other", "f_string_rejects", "f_float_rejects", "size_literal_in_record", "size_other",
                 "pick_two_columns", "seven_literal_expression", "wrap_builds_record", "decode_integer_passes",
                 "decode_string_rejects", "decode_float_rejects", "decode_null_rejects")

EFFECT_TAIL = ('effect payments.authorize I -> P ! O = http.post("payments/authorize")\n'
               "fn g i: I -> P ! O = i |> payments.authorize\n")


class Slice6Int(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6int-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def compile(self, source):
        """`source`: a Path or BEAML text. Return (code, stdout, stderr)."""
        if not isinstance(source, Path):
            path = self.work / "src" / "case.beaml"
            path.parent.mkdir(exist_ok=True)
            path.write_text(source)
            source = path
        result = subprocess.run([st.compiler(), str(source)], cwd=self.work / "cwd", capture_output=True, text=True)
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

    # Build cases.

    def test_fixture_compiles_to_the_planned_shape(self):
        stdout = self.assert_built(FIXTURE)
        lines = [line.strip() for line in stdout.splitlines()]
        expected = [
            "defp __beaml_valid__(v, %s), do: is_integer(v)" % INT,
            "defp __beaml_f(0), do: <<122,101,114,111>>",
            "defp __beaml_f(_), do: <<111,116,104,101,114>>",
            "defp __beaml_valid__(v, <<66,111,120>>) when is_map(v) and map_size(v) == 1, "
            "do: __beaml_valid__(Map.get(v, <<110>>), %s)" % INT,
        ]
        self.assertEqual([], [e for e in expected if e not in lines], "missing lines; stdout:\n" + stdout)

    def test_literal_clause_and_int_parameter_compile(self):
        # plan.json first_red_test (main.rs unit test int_literals_and_patterns, source 1).
        self.assert_built('fn f 0 -> String = "zero"\nfn f n: Int -> String = "other"\n')

    def test_int_output_and_literal_expression_compile(self):
        self.assert_built("fn seven -> Int = 7\n")

    def test_runtime(self):
        stdout = self.assert_built(FIXTURE)
        out = self.work / "beam"
        out.mkdir()
        (out / "generated.ex").write_text(stdout)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "generated.ex")],
                              capture_output=True, text=True)
        self.assertEqual(0, beam.returncode, "elixirc failed:\n" + beam.stdout + beam.stderr)
        (out / "checks.exs").write_text(RUNTIME)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in RUNTIME_CASES:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout + run.stderr)

    # Reject cases (exact text, one source each).

    def test_literal_alone_is_non_exhaustive(self):
        # plan.json source 2. Today: "expected expression or pattern at byte 5".
        self.assert_rejected('fn f 0 -> String = "zero"\n', "non-exhaustive function: f")

    def test_string_body_for_int_output(self):
        # plan.json source 3. Today: "unknown type: Int".
        self.assert_rejected('fn g -> Int = "x"\n', "type mismatch: expected Int, got String")

    def test_int_body_for_string_output(self):
        self.assert_rejected("fn g -> String = 5\n", "type mismatch: expected String, got Int")

    def test_int_literal_against_string_parameter(self):
        self.assert_rejected('fn f s: String -> String = s\nfn f 0 -> String = "z"\n',
                             "type mismatch: expected String, got Int")

    def test_literal_after_catch_all_is_unreachable(self):
        self.assert_rejected('fn f n: Int -> String = "a"\nfn f 0 -> String = "b"\n', "unreachable clause: f")

    def test_equal_literals_are_unreachable(self):
        self.assert_rejected('fn f 0 -> String = "a"\nfn f 0 -> String = "b"\nfn f n: Int -> String = "c"\n',
                             "unreachable clause: f")

    def test_no_plus_on_int(self):
        # D6B-03: no arithmetic. `+` stays String concatenation.
        self.assert_rejected("fn g -> Int = 1 + 2\n", "type mismatch: expected String, got Int")

    def test_no_negative_literal(self):
        # D6B-03. Today the same text; it must stay.
        self.assert_rejected("fn g -> Int = -1\n", "unsupported token at byte 14")

    def test_int_is_not_a_declared_type_name(self):
        # `Int` is built in, like `String`.
        self.assert_rejected("type Int { n: String }\nfn g x: Int -> Int = x\n", "invalid type name: Int")

    def test_is_integer_is_a_reserved_function_name(self):
        # The generated module imports is_integer/1 (plan Elixir shape), like is_binary/1.
        self.assert_rejected("fn is_integer s: String -> String = s\n", "invalid function name: is_integer")

    def test_no_int_in_effect_output(self):
        # D6B-03. The slice 1 rule names the field. Today: "unknown type: Int".
        self.assert_rejected("type O { reason: String }\ntype P { n: Int }\ntype I { id: String }\n" + EFFECT_TAIL,
                             "effect payments.authorize: slice 1 decodes String fields only, not P.n")

    def test_no_int_in_effect_input(self):
        # D6B-03. Message text is a RED decision (notes.md, decision 6). Today: "unknown type: Int".
        self.assert_rejected("type O { reason: String }\ntype P { id: String }\ntype I { n: Int }\n" + EFFECT_TAIL,
                             "effect payments.authorize: slice 6b sends String fields only, not I.n")


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
