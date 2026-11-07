"""EXPERIMENT 0004 slice 6b step 11: constructor TYPES are structs at the host, `T.new/1` (DL-106, DL-117).

Ledger: workflow/2026-11-07/slice6b-host-structs/ (plan.md, decisions.md, spec.md, notes.md). Fixture:
slice6/host-struct/nonzero.beaml (a pure module, no EFFECT, so no RESPONSE RECORD and no ProbeSupport).
DL-117: `T.new/1` takes one map with atom keys; the key set picks the signature. Failure shape for a map that matches
no signature: notes.md default D6B-97. Expected values come from the plan, the decision log and notes.md, never from
the new compiler. H1g, H5, H6 and H8 are guards: they pass before and after the step.
Run: python3 -B experiments/0004-generated-replay/tests/slice6_host_struct_test.py [-k NAME]
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import COMPILER_PATH, EXPERIMENT, REPO  # noqa: E402

FIXTURE = EXPERIMENT / "slice6" / "host-struct" / "nonzero.beaml"
EMPTY_STORED = EXPERIMENT / "stored" / "empty.jsonl"
PAYMENTS = REPO / "experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml"
PAYMENTS_SNAPSHOT = EXPERIMENT / "tests" / "payments.generated.snapshot"
_BINARY = []

# D6B-97: a map that matches no signature gives {:error, {:no_signature, text}}; the help line only for a non-atom key.
NO_SIGNATURE = "%s.new/1: no signature takes these keys"
ATOM_HELP = "\\n  help: keys must be atoms; decode outside data through the EFFECT"


def no_signature(ty, help_line=False):
    return '{:error, {:no_signature, "%s%s"}}' % (NO_SIGNATURE % ty, ATOM_HELP if help_line else "")


NZ = "BeamlSpike.NonZeroInt"
CASES = {
    # H1 (first RED, plan O1): a valid-value map is not a NonZeroInt. Today keep returns the map.
    "h1_string_key_map_rejected": 'invalid.(fn -> BeamlSpike.keep(%{"value" => 4}) end)',
    # H1g (guard): an atom-key map without __struct__ is not the struct either.
    "h1g_atom_key_map_rejected": "invalid.(fn -> BeamlSpike.keep(%{value: 4}) end)",
    # M2 (RED review, GREEN tightening): the struct with a wrong field TYPE is not a NonZeroInt.
    "m2_struct_wrong_field_type_rejected": 'invalid.(fn -> BeamlSpike.keep(st.(%s, value: "4")) end)' % NZ,
    "h1_struct_passes": "s = st.(%s, value: 4)\nBeamlSpike.keep(s) == s" % NZ,
    # H2 under DL-117: one map with atom keys, the parameter name n of the signature.
    "h2_new_ok": "%s.new(%%{n: 3}) == {:ok, st.(%s, value: 3)}" % (NZ, NZ),
    "h2_new_constructor_failure": "%s.new(%%{n: 0}) == {:error, st.(BeamlSpike.IsZero, [])}" % NZ,
    "h2_new_wrong_value_type": 'invalid.(fn -> %s.new(%%{n: "3"}) end)' % NZ,
    "h2_new_naked_value_is_not_a_form": "invalid.(fn -> %s.new(3) end)" % NZ,
    "h2_new_string_keys_help": '%s.new(%%{"n" => 3}) == %s' % (NZ, no_signature("NonZeroInt", True)),
    "h2_new_unknown_atom_key": "%s.new(%%{m: 3}) == %s" % (NZ, no_signature("NonZeroInt")),
    "h2_new_extra_atom_key": "%s.new(%%{n: 3, m: 4}) == %s" % (NZ, no_signature("NonZeroInt")),
    # H3 (nested field, D6B-76). A valid value, so a GREEN that runs the constructor on the map cannot pass.
    "h3_nested_map_rejected": 'invalid.(fn -> BeamlSpike.unbox(%{"n" => %{"value" => 4}}) end)',
    # M2: a nested atom-key map of the struct shape is not the struct.
    "m2_nested_atom_key_map_rejected": "invalid.(fn -> BeamlSpike.unbox(%{\"n\" => %{value: 4}}) end)",
    "h3_nested_struct_passes": '{:ok, s} = %s.new(%%{n: 4})\nBeamlSpike.unbox(%%{"n" => s}) == s' % NZ,
    # H3e (enum payload depth, plan O2). The tag is the binary form that the compiler writes.
    "h3e_payload_map_rejected": 'invalid.(fn -> BeamlSpike.wrapped({"Wrap", "Has", [%{"value" => 4}]}) end)',
    "h3e_payload_struct_passes": ('{:ok, s} = %s.new(%%{n: 4})\nw = {"Wrap", "Has", [s]}\n'
                                  'BeamlSpike.wrapped(w) == w' % NZ),
    # H4: the success value of a constructor TYPE is the struct.
    "h4_wrap_gives_struct": "BeamlSpike.wrap(5) == {:ok, st.(%s, value: 5)}" % NZ,
    # H5 (guard): a plain record keeps the String-key map form (DL-106).
    "h5_plain_record_keeps_map": 'BeamlSpike.same(%{"value" => 0}) == %{"value" => 0}',
    # H6 (guard, D6B-77): a constructor TYPE failure through a pipe keeps its fields.
    "h6_pipe_failure_keeps_fields": "BeamlSpike.twice(4) == {:error, st.(%s, value: 4)}" % NZ,
    "h6_pipe_failure_constructor_error": "BeamlSpike.twice(0) == {:error, st.(BeamlSpike.IsZero, [])}",
    # H9 (DL-117): two parameters; the keys pick the signature.
    "h9_pair_new": 'BeamlSpike.Pair.new(%{x: "x", y: "y"}) == {:ok, st.(BeamlSpike.Pair, a: "x", b: "y")}',
    "h9_pair_missing_key": 'BeamlSpike.Pair.new(%%{x: "x"}) == %s' % no_signature("Pair"),
    "h9_label_first_signature": 'BeamlSpike.Label.new(%{text: "a"}) == {:ok, st.(BeamlSpike.Label, text: "a")}',
    "h9_label_second_signature": ('BeamlSpike.Label.new(%{first: "a", last: "b"}) == '
                                  '{:ok, st.(BeamlSpike.Label, text: "a b")}'),
}
# H7: the DL-106 limit, kept apart so that its name says what it records.
LIMIT_CASES = {"h7_deliberate_struct_literal": "s = st.(%s, value: 0)\nBeamlSpike.keep(s) == s" % NZ}

RUNTIME_HEAD = r'''
invalid = fn fun ->
  try do
    fun.()
    false
  rescue
    e in ArgumentError -> e.message == "invalid BEAML input"
  end
end
# struct!/2 at run time: a missing struct module fails one case, not the whole script.
st = fn mod, fields -> struct!(mod, fields) end
'''
RUNTIME_TAIL = r'''
for {name, check} <- cases do
  {ok, why} =
    try do
      r = check.()
      {r == true, inspect(r)}
    rescue
      e -> {false, Exception.format_banner(:error, e) |> String.split("\n") |> hd()}
    end

  IO.puts("#{name} #{if ok, do: "PASS", else: "FAIL"}")
  if not ok, do: IO.puts("  reason #{name}: #{why}")
end
'''

# H8: stdout sha256 of the pre-step compiler (HEAD 52550d4f, scratch `git archive` build), `--stored stored/empty.jsonl`.
# No source here has a record constructor. Exit 1 sources keep exit 1 and an empty stdout.
# Slice 6b step 12 (DL-119): the 36 rows with "changed" in slice6/effect-reach/byte-guard.json take its sha256.
# Slice 6b step 6b (D6B-172): the EFFECT rows take the dotted unknown_keys projection (slice6b-redacted-fields/notes.md).
BYTE_GUARD = {
    "arms/gen/orders.beaml": (0, "f8998ed508b056d36debe444c8539f8ab20f2840710b48e452751d4d87ec9871"),
    "slice2/N-chain/orders.beaml": (0, "d7bccf7eba4d6816662686eb911dff1e134ee9b2f889377644d1ef5b8aa9b2b8"),
    "slice2/N-statuz/orders.beaml": (0, "ece06065c682c451da9750fb93ffa0783cbdb2a7f6955529776e57e3985aab75"),
    "slice2/N2-chain/orders.beaml": (0, "5f799772a35ab70e6969367f80399f67137b51102eed567f8a603b48d09e078e"),
    "slice2/N2/orders.beaml": (0, "72f7af619dc1e88b406821ee62d34585a8ffc9d26965c47dc0f00de4638aebdc"),
    "slice2/reuse/orders.beaml": (0, "586e1943b3c863a996834b95ade5f89da308703014a9331092f921e3e112266a"),
    "slice2/rotation/orders.beaml": (0, "f3ce2f8ad1aacea3ec6921e91ecf5816ab66f77c9ade5117c871de3420967d7e"),
    "slice3/D-drop/orders.beaml": (0, "41d9c975ef48194986d5bf9b58e86edb3730e1e621b3e91289fb833125a52387"),
    "slice3/D/orders.beaml": (0, "b837576a4108a99d43a3bded42dd6d00a2bae64162a373d0afcdc89bf9e6fba4"),
    "slice3/D15/orders.beaml": (0, "07a3a07337619f6c809412a1fbd3f5dfe3013ffbc39e136f1a9c9683a3444d47"),
    "slice3/D7/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice3/M-nodrop/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice3/M/orders.beaml": (0, "9d99e95283498959ad79bb930e9299561497c271d08d7f020c517a654ad8ff2c"),
    "slice3/R-add/orders.beaml": (0, "f78b847c277aa41c8f18a2e0d2370943556704c1f6a0542428327761911d9271"),
    "slice3/R2/orders.beaml": (0, "f377087ebf831c7798c9ad709fa409109359c16ae7ac92a734655fb9a0ead8de"),
    "slice3/RD/orders.beaml": (0, "43d4b67850e40cbeaf0c67f79f4a136885aff5b9cdbc07cf67d2e57418fc62b6"),
    "slice3/RR/orders.beaml": (0, "5d0a42b9857001356bc3abfbba3438a3d530fbc0610e883b70dad7517c8f8c86"),
    "slice3/SAR/orders.beaml": (0, "af340840a484ea30bfae7246bb45ed54d5493f0d60fc69f566826faefad2d276"),
    "slice3/Z/orders.beaml": (0, "337081451576796f4b5c9a1ac25939b4d54f416fd17bff163b59b767457ddd53"),
    "slice4/B+r/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice4/B/orders.beaml": (0, "9470820cc703c763a39e63331e501a291c7908ea554dd8fb80fc7b6148c4d354"),
    "slice4/C2/orders.beaml": (0, "a70c23d05cc372a716b5705e0ecd905bb1ef616f8869e7d4e628c6374213ac40"),
    "slice4/G+r/orders.beaml": (0, "1cebddca3b0253dc5198113a6e7db0b05e6c952c74709f9817146c73fa735f22"),
    "slice4/G+r0/orders.beaml": (0, "c2103aff00aa448bcb663fa47d98f5ede57d0e7a9a77e6551ac02d065f9fdd99"),
    "slice4/G/orders.beaml": (0, "92307f003f3cda8df377cbd3a84e02712cfb98bf79cb9315d88afe45dfd61002"),
    "slice4/P+r/orders.beaml": (0, "6361955f463c448bb03836ba8390cf38c2a18c1b93b8c6ba29f624244d4258a7"),
    "slice4/P/orders.beaml": (0, "b06f8428c3243bffa3c3fb61bc1766eb718271fee71196b60a558aa73ea360b5"),
    "slice4/Q4-crlf/orders.beaml": (0, "d8441e928d2c31bbccd7ceeb73d2e759dd69e657ab713f64aacd138aead065ea"),
    "slice4/Q4-oneline/orders.beaml": (0, "2daf5a5f7255dfe249f87632044150fe1efd352826c88982cbd615bb9e32668f"),
    "slice4/Q4/orders.beaml": (0, "fd48d34c4f564ff29c6348e3d328ad6ae213d1ccd5ac3a4e6df5b07919487e50"),
    "slice4/Q4g+r/orders.beaml": (0, "0e413cc55dcdd9fb4c14e0ac43ecab1474c230793582b86bfe42931a563d8fda"),
    "slice4/Q4s-crlf/orders.beaml": (0, "9c8e9d8f1b5f66679e4c102734b35a7772954d20b6c539545c9b7e0be13e135b"),
    "slice4/Q4s/orders.beaml": (0, "282f3dd67735e1b763ad7f9da97692bcab15f1942a93fa4432586fd32412ba54"),
    "slice5/B5/orders.beaml": (0, "f8998ed508b056d36debe444c8539f8ab20f2840710b48e452751d4d87ec9871"),
    "slice5/C2/orders.beaml": (0, "2da3cced10acaf3640ef38b58329ee6c3a8c8118476ae2ce3ff3b9f32a617d02"),
    "slice5/M3/orders.beaml": (0, "cf145abde7720abfb344ba77ac2e3acca17e81cee2b528a0aa51e8b6429276ea"),
    "slice5/Q4-crlf/orders.beaml": (0, "cc697a012be04141e2d8e8123c72e40ef8f03e8720f3516a93350222aeaee7d9"),
    "slice5/Q4/orders.beaml": (0, "ee7b80587479e1b50accac044ec5899438a900787e1e5c75cde2a17d10df36ee"),
    "slice5/Q4s/orders.beaml": (0, "c793f6277e72cb982bbbcb4004c8cd06d395fe7ae1312101f5cf43aba6bf005f"),
    "slice5/Q4z/orders.beaml": (0, "e21a7392deaa4ee3b43b85b17b0a943dcae09c1d1bac6e81d071ab8a4756be30"),
    "slice6/int/int.beaml": (0, "803e304e2064bf46ba6f6a7a36c419efc6678f6ffd59823b6840a99f168d4c18"),
    "slice6/failure/body.beaml": (0, "b926d4c2601a01c7ed247473c441e3dbfbf238329bdda492e7a1e8c0dd84e41f"),
    "slice6/failure/overlap.beaml": (0, "9ad10e7f7f456512fc51083783b67e1276479ea8afecdffc431a703f627af31c"),
    "slice6/decode/orders.beaml": (0, "69e144b22cfce342246ad1090679204c2f9bacf06a71ff90292d26bd41c075e9"),
    "slice6/enum/literals.beaml": (0, "63c60e1e36109b77d7b059741ebd1b6a582f57ff16b2d98c714472b7a671a1fb"),
}


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


class Slice6HostStruct(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        holder = tempfile.mkdtemp(prefix="beaml-0004-s6host-")
        self.addCleanup(shutil.rmtree, holder)
        self.work = Path(holder)
        (self.work / "cwd").mkdir()

    def build(self, source, extra=()):
        """Compile one source. Return (code, stdout, stderr). Events hold no source path and no source text."""
        result = subprocess.run([compiler(), str(source), *extra], cwd=self.work / "cwd", capture_output=True,
                                text=True)
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            text = log.read_text()
            self.assertNotIn(str(source.parent), text, "action events must not record the source path")
            self.assertNotIn("fn ", text, "action events must not record source text")
        return result.returncode, result.stdout, result.stderr

    def run_runtime(self, cases):
        """Generated module only: `elixirc --warnings-as-errors`, then one `elixir` script with every case."""
        code, stdout, stderr = self.build(FIXTURE)
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout), "setup: compile failed: " + stderr)
        self.assertNotIn("ProbeSupport", stdout, "setup: a pure module must not call ProbeSupport")
        out = self.work / "beam"
        out.mkdir()
        (out / "generated.ex").write_text(stdout)
        beam = subprocess.run(["elixirc", "--warnings-as-errors", "-o", str(out), str(out / "generated.ex")],
                              capture_output=True, text=True)
        self.assertEqual(0, beam.returncode, "setup: elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn ->\n%s\nend}' % item for item in cases.items())
        (out / "checks.exs").write_text(RUNTIME_HEAD + "\ncases = [\n" + listed + "\n]\n" + RUNTIME_TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True)
        self.assertEqual(0, run.returncode, "setup: checks.exs did not run:\n" + run.stdout + run.stderr)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in cases:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout)

    def test_host_structs_and_new(self):
        # H1 to H6 and H9. Today: maps pass the input check, T.new/1 is absent.
        self.run_runtime(CASES)

    def test_limit_deliberate_struct_literal_is_not_caught(self):
        """H7 records the DL-106 limit, not a wanted outcome: Elixir has no private constructors, so a host can write
        the struct literal on purpose and it passes. Today it fails: the input check wants a String-key map."""
        self.run_runtime(LIMIT_CASES)

    def test_sources_without_a_record_constructor_stay_byte_equal(self):
        # H8 (guard): passes today and must pass after GREEN.
        for relative, (want_code, digest) in BYTE_GUARD.items():
            with self.subTest(relative):
                code, stdout, stderr = self.build(EXPERIMENT / relative, ["--stored", str(EMPTY_STORED)])
                self.assertEqual((want_code, digest), (code, hashlib.sha256(stdout.encode()).hexdigest()), stderr)
        with self.subTest("payments.beaml"):
            code, stdout, stderr = self.build(PAYMENTS)
            self.assertEqual((0, PAYMENTS_SNAPSHOT.read_text()), (code, stdout), stderr)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
