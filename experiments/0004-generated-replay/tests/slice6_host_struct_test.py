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
BYTE_GUARD = {
    "arms/gen/orders.beaml": (0, "009d8ab3127b8734e14555d7c87cc337e438cda8ae583a7cbbb2c8d065c92343"),
    "slice2/N-chain/orders.beaml": (0, "43d16c8293010327c7e40a3edc210db24a9f55050656df5bfa6d031ac2cb068a"),
    "slice2/N-statuz/orders.beaml": (0, "65e6839964f18e873f65be4d48da12bb4ba186800d9f2e5603c56a135c37b791"),
    "slice2/N2-chain/orders.beaml": (0, "aa9da6879c6095c715af618d40609871b2b7018c698e14409d5544c9563a4669"),
    "slice2/N2/orders.beaml": (0, "b285e7e6d4f51f41c07e7c2d47c4829afab5fadc07465a8eecdaa9d90747bf9a"),
    "slice2/reuse/orders.beaml": (0, "e7899cc35816804ac7a1d5f26654a7c23558a33e1403daa2023a942567650d31"),
    "slice2/rotation/orders.beaml": (0, "dde976e98969edd769fbebf635677025e6c9c7c24ebbba37f1916202d0f030ee"),
    "slice3/D-drop/orders.beaml": (0, "c39267654b631bd0e9b728ee2fd17eeff5d05cfca4270ca36e297a9e6075d4fe"),
    "slice3/D/orders.beaml": (0, "804bfcb6b2e95d2684ae733ac3ba29a5eab5e27f3b00f451f7d045fbe90b0cc2"),
    "slice3/D15/orders.beaml": (0, "ffbc9670bcdf4839a7d1c8314af9b6687946fd863d023da39297aa829b44cc7e"),
    "slice3/D7/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice3/M-nodrop/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice3/M/orders.beaml": (0, "e639c3dbd1b7ad0faabe4070572e5cb196110001899fa440727376e564abd051"),
    "slice3/R-add/orders.beaml": (0, "686444d6e2ae7c627ae17c493b28973910d7ffd6f28f77e6cac5ea22d65a535b"),
    "slice3/R2/orders.beaml": (0, "e4298672fbacd265969715bf4f730fa82fefdcc50531a1cc0a7d0f2dcb9912ba"),
    "slice3/RD/orders.beaml": (0, "e7d8cb7ff3bc732e61be1f086e8480d903fc452cf5b288b1ce620a1fd8e39d6d"),
    "slice3/RR/orders.beaml": (0, "6183ff36e1366760a7f7270dd1f9aa080eab276f8790b48d522726dbd390b343"),
    "slice3/SAR/orders.beaml": (0, "ddc3f9ffe1990d7df870582b9b981344a69535e0855288b25811a0c43ab9f886"),
    "slice3/Z/orders.beaml": (0, "a48dacbaf8dd4151b4a43dc0cd37f8aa5fec32afdae64c492df3d21a92e648a3"),
    "slice4/B+r/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice4/B/orders.beaml": (0, "980c87e3e5a23eb49124ae1745844d229cde2030937d32f2d53ed51d1e4b1c6e"),
    "slice4/C2/orders.beaml": (0, "9fb3a40a098c919c2db422831c8cf78f952e7e0b4abc5c4ec8bef0b79f21f21e"),
    "slice4/G+r/orders.beaml": (0, "73a2fbf343c91d38df73c259c5547e989294f0f96005edd8da8f529e901fff1d"),
    "slice4/G+r0/orders.beaml": (0, "0f7ab8d67a3e153bb4411da0d93db626eb211cbf64b176ed29c5895d59e1c610"),
    "slice4/G/orders.beaml": (0, "b6ecaeee15c574d12d8cf9979515605937fc8d3d760633d67854f5375dc67de4"),
    "slice4/P+r/orders.beaml": (0, "6361955f463c448bb03836ba8390cf38c2a18c1b93b8c6ba29f624244d4258a7"),
    "slice4/P/orders.beaml": (0, "b06f8428c3243bffa3c3fb61bc1766eb718271fee71196b60a558aa73ea360b5"),
    "slice4/Q4-crlf/orders.beaml": (0, "3f095d608f1694b422f1be0de412742eea95ab701c4a6b1c7c52d50333ab52aa"),
    "slice4/Q4-oneline/orders.beaml": (0, "0bd1437e360942e01a49a335943a4d235caac61179299fa33f1f74bc6d59ce4f"),
    "slice4/Q4/orders.beaml": (0, "b5ff2e0526078f7407d36014196da56740211028c7cd6504b7119d48b1389d13"),
    "slice4/Q4g+r/orders.beaml": (0, "cf8aa6034c24c4927e84a48e27c6e69c21696586fc9e7eeb66ab1624d0985143"),
    "slice4/Q4s-crlf/orders.beaml": (0, "6598527e7218fd0c2c4589c8a7cbb4f797fcaf730abf96f788cb5aea0f7e1b54"),
    "slice4/Q4s/orders.beaml": (0, "75916d515e06ef5ff08a18dda1c8723e5c057e809318d39a29a186043c37be8e"),
    "slice5/B5/orders.beaml": (0, "009d8ab3127b8734e14555d7c87cc337e438cda8ae583a7cbbb2c8d065c92343"),
    "slice5/C2/orders.beaml": (0, "622ba2fb5301eb04ecbad935efdee2134017d61f0cca030d5966c1a2e8641bf6"),
    "slice5/M3/orders.beaml": (0, "eee561811c32291beef2a194cd5110e503dae475039f31d041c8f726d8010531"),
    "slice5/Q4-crlf/orders.beaml": (0, "50c08c945c007df7fb58b00d4ee9c559d1f5b20b37adff7b3a4e93cd06740e34"),
    "slice5/Q4/orders.beaml": (0, "3808c72d2ac438f28491e63a03f347e2c637cf46df16c06890b9b4e4216d245a"),
    "slice5/Q4s/orders.beaml": (0, "bd559de91a7462bdc890cfae1e1dd899395d16a2bc56cf725c70b12a3f04cf04"),
    "slice5/Q4z/orders.beaml": (0, "74a92fe6f6fcaadf4326465cb976486d35f40089f99ea257751f228411851bd4"),
    "slice6/int/int.beaml": (0, "803e304e2064bf46ba6f6a7a36c419efc6678f6ffd59823b6840a99f168d4c18"),
    "slice6/failure/body.beaml": (0, "b926d4c2601a01c7ed247473c441e3dbfbf238329bdda492e7a1e8c0dd84e41f"),
    "slice6/failure/overlap.beaml": (0, "9ad10e7f7f456512fc51083783b67e1276479ea8afecdffc431a703f627af31c"),
    "slice6/decode/orders.beaml": (0, "5f3cb9e25beba00ca66d8ac3487f1d61dc70c471dfc18ba592e1493ff9a2e035"),
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
