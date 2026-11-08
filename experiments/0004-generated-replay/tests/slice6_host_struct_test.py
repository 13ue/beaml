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
    "arms/gen/orders.beaml": (0, "0e2dff8a6854833b56cce9384bec7af5307536965ef55a6b1df410854d780f1f"),
    "slice2/N-chain/orders.beaml": (0, "d95d1006769ed16ece2ae7a24f30533773ef027c70f10c47018a532e705f287b"),
    "slice2/N-statuz/orders.beaml": (0, "59215dcb9d92140acd2b119e032d3b38610e091d2b48d1746e04e76c75a2efcc"),
    "slice2/N2-chain/orders.beaml": (0, "645f223ab8a83a81d77e7d174850d58e8df53b38fa8ce5e89883b5338381749a"),
    "slice2/N2/orders.beaml": (0, "1a72a60849ee2f805f8a3935031ce4decdb26b7f2c10959072a1833f63d21758"),
    "slice2/reuse/orders.beaml": (0, "4beb087b12d79f95fc373ca8f5669b809bf23d96b6aa695c73a5be4193ed0f36"),
    "slice2/rotation/orders.beaml": (0, "6abe409bcd39942ccd731362c61e0b64c65b5afba0d9adb264ecccba5485d005"),
    "slice3/D-drop/orders.beaml": (0, "4dd97d1a6cccdaa71665afc73909b92fb6511b74f350beab4994d6e74a130519"),
    "slice3/D/orders.beaml": (0, "c16ef954372c6e64d911b3c1a9eb30ced18de217e93dfd441020c5e0eddad688"),
    "slice3/D15/orders.beaml": (0, "55364128684f0db4f25d316e3f91afffe59d3693313ac67c35d9aad919d2621e"),
    "slice3/D7/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice3/M-nodrop/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice3/M/orders.beaml": (0, "01c353a8123eb51dffd68542985a110c5579cb7994a06bca0006dad6c12a797d"),
    "slice3/R-add/orders.beaml": (0, "7af4c0f72152f1cfeab99c44b7f6214b7da46029f0875dbb2f49a4a36c3cc1c4"),
    "slice3/R2/orders.beaml": (0, "fb76abdf03c2fe68e4a263a074b480fb1d39b775efaf6b656bda4e46d3e27902"),
    "slice3/RD/orders.beaml": (0, "4434b62fb44436b8d2f1728f7503b16dbece0ce6a3cd9156c35cce80bb289ebb"),
    "slice3/RR/orders.beaml": (0, "3cc26b6cbcffc64b0f8c212e5d8d850f693bf4cacb997b9d2798c39ef99fdf3d"),
    "slice3/SAR/orders.beaml": (0, "ac06d83d9c6602e05577494603d7e03cd2fa9f94970dba69744017d31f49b245"),
    "slice3/Z/orders.beaml": (0, "d5d6a0a5727af97cba1182912e0be6dafc2431925158612ee0359f8fe305bc3e"),
    "slice4/B+r/orders.beaml": (1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "slice4/B/orders.beaml": (0, "dcc04b0fda6024cd96fcb5bcb60a05577479137ee56932f2f583d74514ea61e6"),
    "slice4/C2/orders.beaml": (0, "893fd983dbdb532143677f06ec0d1a765f2023750535e7b6265824702c254b79"),
    "slice4/G+r/orders.beaml": (0, "aa84c9605843184b4a69fe60059c36370218be76e4f0c676fa0f4068121f5076"),
    "slice4/G+r0/orders.beaml": (0, "946310992592466cd9bd28be43842f1d5b1b6ebb113ca4224bcbc96ef0e46259"),
    "slice4/G/orders.beaml": (0, "a2ff09353c20bc4f28fe741fd026ec661dafba7067037481a909480b52d6b058"),
    "slice4/P+r/orders.beaml": (0, "6361955f463c448bb03836ba8390cf38c2a18c1b93b8c6ba29f624244d4258a7"),
    "slice4/P/orders.beaml": (0, "b06f8428c3243bffa3c3fb61bc1766eb718271fee71196b60a558aa73ea360b5"),
    "slice4/Q4-crlf/orders.beaml": (0, "39447dbdb7200c520c67b48a451ede7cdb308f0777ac1fd14d1aec63eca9f17f"),
    "slice4/Q4-oneline/orders.beaml": (0, "9cf6b403677d2e1e68fbe77f747103ece7c5cecc72a22e4a51cea811a196c3dd"),
    "slice4/Q4/orders.beaml": (0, "4475b9193ca0132219f09f097fef404a5071b7cc03dbf50c197a741f006f85b5"),
    "slice4/Q4g+r/orders.beaml": (0, "39f3e890b527d5f997193c511b97d431dce6aec499b266ed1daf56652d62d73f"),
    "slice4/Q4s-crlf/orders.beaml": (0, "e8cc8b999bbd5cef5e18951e20c0ac261b562ff96fc8e1f29bd0ca8b5a6ba4fa"),
    "slice4/Q4s/orders.beaml": (0, "728e8ae3b1d7564573605cdae1437383b9c965b3cffdf622ce12b3d80303ee8a"),
    "slice5/B5/orders.beaml": (0, "0e2dff8a6854833b56cce9384bec7af5307536965ef55a6b1df410854d780f1f"),
    "slice5/C2/orders.beaml": (0, "99c55fe302ba6b6ac791803785c8916264687bd30c5cc88de907cb5e4db8e471"),
    "slice5/M3/orders.beaml": (0, "9f3e4fe30bd9bcab17d320ae63ea962a5be81481840d04ab71247a5d8511ee65"),
    "slice5/Q4-crlf/orders.beaml": (0, "bace6a1f9aa50c206e171d21ca79eb2e9e21020b8f688a9a499e2c422cc70e92"),
    "slice5/Q4/orders.beaml": (0, "485ec2c48571bc03b93f02ac9d8a8c0ee7cd7d3c33af72a58e38226592e705fd"),
    "slice5/Q4s/orders.beaml": (0, "63173a4d64744c3d83384deff6563547faa5413185afcaa02813cad88bc88607"),
    "slice5/Q4z/orders.beaml": (0, "a8bb80e3af450442362b6bf3d806b13dc19d26ce33d1cce482f209c4ebf15cd0"),
    "slice6/int/int.beaml": (0, "803e304e2064bf46ba6f6a7a36c419efc6678f6ffd59823b6840a99f168d4c18"),
    "slice6/failure/body.beaml": (0, "b926d4c2601a01c7ed247473c441e3dbfbf238329bdda492e7a1e8c0dd84e41f"),
    "slice6/failure/overlap.beaml": (0, "9ad10e7f7f456512fc51083783b67e1276479ea8afecdffc431a703f627af31c"),
    "slice6/decode/orders.beaml": (0, "f07ddeaec0adb1c389883f96dedc711d6e6ed3156f412f9960a75e031e74f836"),
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
