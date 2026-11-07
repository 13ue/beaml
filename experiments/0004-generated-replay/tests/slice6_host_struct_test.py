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
BYTE_GUARD = {
    "arms/gen/orders.beaml": (0, "2b8dc63670aa2a9a3bcd889ec680e5bbc5a66ea789676d98045964cf50909fed"),
    "slice2/N-chain/orders.beaml": (0, "bc0fed27b4ae292fe28244980d28e074e68f9cc7a58226cd8d30828c08830003"),
    "slice2/N-statuz/orders.beaml": (0, "649c94c907164c60406e844b54090ef4d75aea307b7f9225d25743a9e3e57baa"),
    "slice2/N2-chain/orders.beaml": (0, "32f9379f63bb1538c2aa7106869fa1e9c422c8abffcfc389c4401924824a64e2"),
    "slice2/N2/orders.beaml": (0, "16ad1fd51ad647773dc52402e341f61a1440a64108ead7df89e8a8ec6e676578"),
    "slice2/reuse/orders.beaml": (0, "597ad5824fca31814599e47e2761d191fbe190c0e728962687d1a71e2d045ab8"),
    "slice2/rotation/orders.beaml": (0, "afa2f40e351709ec1040edb89f33c369ca1af5db47956aae8a0852fcbdf4ac1e"),
    "slice3/D-drop/orders.beaml": (0, "2e7b908277ce23a46652355fcb327d86b5215fdc7a71da70c857cbbd078aea43"),
    "slice3/D/orders.beaml": (0, "07e861253a1f3d4556f8715aa52e133f601c6e9a6b44e1bc41536bff3076a610"),
    "slice3/D15/orders.beaml": (0, "9b1b10fdc941d22148e3a1f510bf613adb1596478aad746283d9af3180735002"),
    "slice3/D7/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice3/M-nodrop/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice3/M/orders.beaml": (0, "64e3272933a422025f85ca2bef6192a6f0334b19b535890dd180056d5ce5123d"),
    "slice3/R-add/orders.beaml": (0, "d6f98d5c03a24bcc3a716ce0b73b9feb6ed2ae39d8f2dfa0da792599f4a50f35"),
    "slice3/R2/orders.beaml": (0, "bc7e36a25386f6d944891c23ed3b351bb72f7128b1db7d76fac3dfa99f63775a"),
    "slice3/RD/orders.beaml": (0, "d0556ebb709ba0238588c20712111e627839b3cf6cf66bfee9c586bd2fcc79e1"),
    "slice3/RR/orders.beaml": (0, "4118343ff120b48de43116112724da063e6159bda1d3a1aab22f98938c521a2c"),
    "slice3/SAR/orders.beaml": (0, "af959bf7fb48b906bd97b7c6925a6a33b5d778f711cbb38e73b638c33c29c12d"),
    "slice3/Z/orders.beaml": (0, "8368a52714e7650a201d46d7d4f06b593f94259120c683267008cce7f6920788"),
    "slice4/B+r/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice4/B/orders.beaml": (0, "6c5ac80008c6d27cc26a8c83cd511040ecd62b32a3d739d0891d8151045e0ec6"),
    "slice4/C2/orders.beaml": (0, "dc941f3f3cb45e357e9cc72f8400c684a6df179c5eece9be857b5b5830477e32"),
    "slice4/G+r/orders.beaml": (0, "f7382715f8f5295dfa9852c11fb4dca2d9d57575ae8abef75beff161787f3874"),
    "slice4/G+r0/orders.beaml": (0, "9a57ae63450e5a8981c956f885f70972dca1852a363d7b87946a86b3e8f309c6"),
    "slice4/G/orders.beaml": (0, "e56c6f3b55baeee0eef67363e0d6b41d7fe53fc005dc87e410b42b5ada6ddc58"),
    "slice4/P+r/orders.beaml": (0, "6361955f463c448bb03836ba8390cf38c2a18c1b93b8c6ba29f624244d4258a7"),
    "slice4/P/orders.beaml": (0, "b06f8428c3243bffa3c3fb61bc1766eb718271fee71196b60a558aa73ea360b5"),
    "slice4/Q4-crlf/orders.beaml": (0, "08b23ab21cdd00a4b8234dcf6ad3853562b8c58f1202cbfceba8e5a99f92cd59"),
    "slice4/Q4-oneline/orders.beaml": (0, "ed4cf364eff87c16604225680b587d05505683cba59afc1d6a5e295175a738df"),
    "slice4/Q4/orders.beaml": (0, "914ef6f951f1bbcd7eb2a8a39affe6f9826af66a29dbdff5e436f53aea52384d"),
    "slice4/Q4g+r/orders.beaml": (0, "4d9e109c6b0b1e9ceca8f9cbcfe8a9afe947f50f16902fdd8dc17907032ea8e2"),
    "slice4/Q4s-crlf/orders.beaml": (0, "3060300e1204b5f283f9665afa4d5378e857ebb57d149531c5cc3a92517c22c2"),
    "slice4/Q4s/orders.beaml": (0, "5311067f2d648f1c62fe4f44f308b431dee9bcda779b9a22860fc802b4222bac"),
    "slice5/B5/orders.beaml": (0, "2b8dc63670aa2a9a3bcd889ec680e5bbc5a66ea789676d98045964cf50909fed"),
    "slice5/C2/orders.beaml": (0, "46396760cf6a58d8f1f344be11939b9779bf3beb91bd65c7f8ea66af476dfcd5"),
    "slice5/M3/orders.beaml": (0, "912a8a39dd1d275c56587d82140f3e723b2fdea9b3cec112fdb6d5c28cf98335"),
    "slice5/Q4-crlf/orders.beaml": (0, "301dedf429f995d51a49b29f853212b9422f84278d683769f24cb361e6efa7f0"),
    "slice5/Q4/orders.beaml": (0, "b06c03acea202e331a7700e25ec760f2e1950dcbe1173c650d5ccc14f3da66ed"),
    "slice5/Q4s/orders.beaml": (0, "4905217c957a60bd14ef3f326966c6bc0e8df0ed12202f7f6b5b1302f7c8dad6"),
    "slice5/Q4z/orders.beaml": (0, "f2456bb9a1c283d3bd7e3cc44b9766e0ce28c9c2ec7a3a5d979b4d0887395471"),
    "slice6/int/int.beaml": (0, "803e304e2064bf46ba6f6a7a36c419efc6678f6ffd59823b6840a99f168d4c18"),
    "slice6/failure/body.beaml": (0, "b926d4c2601a01c7ed247473c441e3dbfbf238329bdda492e7a1e8c0dd84e41f"),
    "slice6/failure/overlap.beaml": (0, "9ad10e7f7f456512fc51083783b67e1276479ea8afecdffc431a703f627af31c"),
    "slice6/decode/orders.beaml": (0, "9ce8c077a261102c95b8add89347408173acbe3ede8a194b188b11a6af691f92"),
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
