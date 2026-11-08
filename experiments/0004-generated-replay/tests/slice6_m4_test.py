"""EXPERIMENT 0004 M4 step 1: lift D6B-39, run the MIGRATE STEPS first and the checks after (DL-152, DL-153).

Ledger: experiments/0004-generated-replay/workflow/2026-11-08/m4-lift-d6b39/ (plan.md with "Plan repair after plan
check", decisions.md PM4-01 to PM4-19 and QM4-1 to QM4-4, plan-review.md, red-plan.md, red-output.md).
Defaults pinned here (open for the OWNER): QM4-3 A (the DL-122 help keeps its D6B-39 words). fates-a1b (DL-166) retires
QM4-1 A and QM4-4 A: a rename onto an enum or constructor field builds; --stored reads an old row by its old key
(ledger workflow/2026-11-08/fates-a1b/, plan.md "Repairs" O2: stored_key walks the newest step first).
Expected values come from the plan and the digest and fingerprint code of slice6_db_test (stored_types_test), never
from the new compiler. The cases that pin the old D6B-39 texts stay in slice6_db_test.py and slice6_decode_test.py
until the GREEN retires them (red-plan.md, "Retired by GREEN").
DL-147: this file joins run.py in the GREEN commit (step slice6-m4).
Run: python3 -B experiments/0004-generated-replay/tests/slice6_m4_test.py [-k NAME]
"""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slice6_db_stored_test as sds  # noqa: E402
import slice6_db_test as sd  # noqa: E402
import slice6_decode_test as sdec  # noqa: E402
import slice6_failure_test as sf  # noqa: E402

ORDER_V2 = sd.ORDER_V2
BAD_RENAME = sd.FIX / "bad_rename"
ex, b, jb, core, type_of = sd.ex, sf.b, sd.jb, sd.core, sd.type_of
counted = sds.counted
ORDER_V1 = sd.ORDER_TYPE
ORDER_V2_TYPE = type_of("Order", 2, [["order_id", "String"], ["amount", "Amount"], ["channel", "Channel"],
                                     ["note", "String"]])
WIRE1, TV_WIRE, EUR = sd.WIRE1, sd.TV_WIRE, sd.EUR
WIRE2_V2 = dict(sd.WIRE2, note="second")
V1_ROW = core(WIRE1)
V1_TV_ROW = core(TV_WIRE, unknown_fields=["channel"])
V1_BAD_CURRENCY = core(dict(WIRE1, amount={"value": "12.50", "currency": ""}))
V1_NO_AMOUNT = core({"order_id": "order-1", "channel": "web"})
V1_AMOUNT_STRING = core(dict(WIRE1, amount="12.50"))

# fates-a1b (DL-166): the two bad_rename/ fixtures build. A db.list tail with an ENTRY LINE gives them a live read and
# the module Orders (Q6E-1 C: without an ENTRY LINE the module is BeamlSpike) (plan AC 2).
RENAMES = ("row_rename_enum", "row_rename_constructor")
RENAME_ENUM, RENAME_CTOR = ((BAD_RENAME / ("%s.beaml" % n)).read_text() for n in RENAMES)
LIST_TAIL = ("type OrderQuery {}\ntype OrderList { items: [Order] }\n"
             'effect orders.list OrderQuery -> OrderList ! StoreError = db.list("records")\n'
             'effect ui.orders OrderQuery -> OrderList ! StoreError = ui.event("orders") |> list_orders\n'
             "fn list_orders q: OrderQuery -> OrderList ! StoreError = q |> orders.list\n")
ENUM_STEP = "migrate Order v1 -> v2 { rename via -> channel }"
# The v1 TYPES of the fixtures: the newest fields with the rename undone (field TYPE text unchanged).
ENUM_V1 = type_of("Order", 1, [["order_id", "String"], ["via", "Channel"]])
ENUM_V2 = type_of("Order", 2, [["order_id", "String"], ["channel", "Channel"]])
CTOR_V1 = type_of("Order", 1, [["order_id", "String"], ["price", "Amount"]])
# Plan review O2: a chain v1 -> v2 -> v3 of two renames onto channel.
CHAIN_V1 = type_of("Order", 1, [["order_id", "String"], ["via", "Channel"]])
CHAIN_V2 = type_of("Order", 2, [["order_id", "String"], ["ch", "Channel"]])
CHAINED = "migrate Order v1 -> v2 { rename via -> ch }\nmigrate Order v2 -> v3 { rename ch -> channel }"
RENAME_MAP = 'migrate Order v1 -> v2 { rename via -> channel, map channel "tv" -> Web }'
# slice6_fates_test (fates-a1): the a1 stop line of a hit map line, and the PF-13 fate line.
NOT_BUILT_M = "error: a map line is hit, but map at run time is not built yet (fates-a2)"
MAP_FATE = 'fate: 1 stored ROW of table records mapped by migrate Order v1 -> v2 (map channel "tv" -> Web)'


def want(setup, actual, expected):
    """A case that prints the actual term when it differs (the TAIL of slice6_db_test prints a non-true result)."""
    return "%s; r = %s; if r == %s, do: true, else: r" % (setup, actual, expected)


M1 = 'Map.put(o1.(), "note", "")'
SEED_V1 = 'fresh.(); BeamlDb.seed("Order", 1, %s)' % jb(V1_ROW)
N33_CASES = {
    # DL-153: the generated Elixir decodes a v1 row of Order into v2 (Amount struct, Web tuple, note "").
    "N33_v1_row_lists_migrated": want(SEED_V1, "Orders.list_orders(%{})", '{:ok, %%{"items" => [%s]}}' % M1),
    "N33_v1_row_loads_migrated": want(SEED_V1, "Orders.load(key1)", "{:ok, %s}" % M1),
    # DL-127 lazy: the read leaves the stored v1 row as it was.
    "N33_v1_row_stays_v1": want(SEED_V1 + "; Orders.list_orders(%{})", "BeamlDb.rows()",
                                '[%%{"id" => 1, "type" => "Order", "version" => 1, "value" => %s}]' % jb(V1_ROW)),
    "N33_save_writes_v2": want('fresh.(); Orders.save(Map.put(o2.(), "note", "second")); [{_, head, _}] = puts.()',
                               '{head, Map.take(last_core.(), ["type", "value"])}',
                               '{{"Order", 2}, %s}' % ex({"type": ORDER_V2_TYPE, "value": WIRE2_V2})),
    "N33_list_holds_both_versions": want(SEED_V1 + '; Orders.save(Map.put(o2.(), "note", "second"))',
                                         "Orders.list_orders(%{})",
                                         '{:ok, %%{"items" => [Map.put(o2.(), "note", "second"), %s]}}' % M1),
    # DL-109, PDB-18 (plan repair 6): a kept channel of a v1 row; the list record names items.0.channel.
    # GREEN repair: the list call and the record read stand in the setup, so `r` is the tuple, not only `l`.
    "N33_v1_unknown_channel": want('fresh.(); BeamlDb.seed("Order", 1, %s); Process.put(:captures, []); '
                                   'l = Orders.list_orders(%%{}); [rec] = resp.()' % jb(V1_TV_ROW),
                                   '{l, rec["unknown_fields"]}',
                                   '{{:ok, %{"items" => [Map.put(tv.(), "note", "")]}}, ["items.0.channel"]}'),
    # PM4-07: the DL-101 tail runs after the steps and rejects bad wire values of a v1 row.
    "N33_v1_constructor_reject": want('fresh.(); BeamlDb.seed("Order", 1, %s)' % jb(V1_BAD_CURRENCY),
                                      "Orders.list_orders(%{})", 'fail.("constructor")'),
    "N33_v1_row_without_amount": want('fresh.(); BeamlDb.seed("Order", 1, %s)' % jb(V1_NO_AMOUNT),
                                      "Orders.list_orders(%{})", 'fail.("decode")'),
    # Plan repair 10 (optional, taken): an amount that matches no signature of Amount.
    "N33_v1_amount_no_signature": want('fresh.(); BeamlDb.seed("Order", 1, %s)' % jb(V1_AMOUNT_STRING),
                                       "Orders.list_orders(%{})", 'fail.("decode")'),
    # The REPLAY RUN of the orders.list record of a v1 read gives the live value without BeamlDb.
    "N33_replay_list": want(SEED_V1 + '; Process.put(:captures, []); live = Orders.list_orders(%{}); recs = resp.(); '
                            "BeamlDb.reset(); BeamlDb.mode(:forbid); "
                            'r2 = Orders.Replay.run("orders.list", %{}, hd(recs)["trace_id"], recs); BeamlDb.mode(:ok)',
                            "{r2, live, BeamlDb.calls()}",
                            '{{:ok, %%{"items" => [%s]}}, {:ok, %%{"items" => [%s]}}, []}' % (M1, M1)),
}

# R8 (http stream): `add` and `drop` beside an enum field; the joined key list (plan repair 4: the decode return).
CHAIN_ADD = (sdec.PS_LITERALS + "type Payment { order_id: String state: PaymentState note: String }\n"
             'migrate Payment v1 -> v2 { add note: String = "", drop legacy: String }\n' + sdec.REST)
PAYMENT_V1 = type_of("Payment", 1, [["order_id", "String"], ["state", "PaymentState"], ["legacy", "String"]])
V1_BODY = {"order_id": "o-1", "state": "ok", "legacy": "x", "extra": "y"}
R8_CASE = ('r = BeamlSpike.__beaml_decode_payment(:json.encode(%s) |> IO.iodata_to_binary(), %s); '
           'IO.puts("got R8: " <> inspect(r)); '
           'r == {:ok, %%{"order_id" => "o-1", "state" => {"PaymentState", "Authorized", []}, "note" => ""}, ["extra"]}'
           % (ex(V1_BODY), ex({k: PAYMENT_V1[k] for k in ("name", "version", "fingerprint")})))
# R8b (RED review O1): a chained constructor output; the joined key list holds the nested `amount.extra` and the
# top-level `extra`, sorted as the plain decode of the same body sorts them (checked against the HEAD plain decode).
CTOR_SOURCE = (sdec.EXPERIMENT / "slice6" / "decode-ctor" / "orders.beaml").read_text()
CTOR_CHAIN = CTOR_SOURCE.replace(
    "type Payment { order_id: String state: PaymentState amount: Amount }\n",
    "type Payment { order_id: String state: PaymentState amount: Amount note: String }\n"
    'migrate Payment v1 -> v2 { add note: String = "" }\n')
PAYMENT_CTOR_V1 = type_of("Payment", 1, [["order_id", "String"], ["state", "PaymentState"], ["amount", "Amount"]])
CTOR_BODY = {"order_id": "o-1", "state": {"status": "ok", "decline_reason": ""},
             "amount": {"value": "12.50", "currency": "EUR", "extra": "y"}, "extra": "z"}
R8B_CASE = ('r = BeamlSpike.__beaml_decode_payment(:json.encode(%s) |> IO.iodata_to_binary(), %s); '
            'IO.puts("got R8b: " <> inspect(r)); '
            'r == {:ok, %%{"order_id" => "o-1", "state" => {"PaymentState", "Authorized", []}, '
            '"amount" => %%BeamlSpike.Amount{value: "12.50", currency: "EUR"}, "note" => ""}, ["amount.extra", "extra"]}'
            % (ex(CTOR_BODY), ex({k: PAYMENT_CTOR_V1[k] for k in ("name", "version", "fingerprint")})))
# R14 (RED review O2): the kept redacted D6B-39 branch (PM4-05). A guard: it passes at HEAD and after GREEN.
REDACTED_CHAIN = ((sdec.EXPERIMENT / "slice6" / "redacted" / "output_redacted.beaml").read_text()
                  .replace("card_holder: redacted String }\n",
                           'card_holder: redacted String }\nmigrate Payment v1 -> v2 { add status: String = "x" }\n'))
REDACTED_TEXT = ("error: effect payments.authorize: the redacted field Payment.card_holder cannot stand in a TYPE with a "
                 "MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)\n  help: remove the MIGRATE CHAIN and the VERSION "
                 "MARK of Payment")
# R3 flipped (fates-a1b, AC 3): a v1 body of the CHAIN reads status into state.
PAYMENT_CHAIN_V1 = type_of("Payment", 1, [["order_id", "String"], ["status", "PaymentState"]])
R3_CASE = ('r = BeamlSpike.__beaml_decode_payment(:json.encode(%s) |> IO.iodata_to_binary(), %s); '
           'IO.puts("got R3: " <> inspect(r)); '
           'r == {:ok, %%{"order_id" => "o-1", "state" => {"PaymentState", "Authorized", []}}, []}'
           % (ex({"order_id": "o-1", "status": "ok"}),
              ex({k: PAYMENT_CHAIN_V1[k] for k in ("name", "version", "fingerprint")})))


def decode_body(stdout, name):
    """The body of `def NAME(a0, type_version) do` up to its `  end` line."""
    match = re.search(r"^  def %s\(a0, type_version\) do\n(.*?)^  end$" % name, stdout, re.S | re.M)
    return match.group(1) if match else None


class M4Db(unittest.TestCase):
    """The db stream: compile, live decode over the fake BeamlDb, and --stored over rows and records."""
    maxDiff = None
    setUp = sds.Slice6DbStored.setUp
    compile = sds.Slice6DbStored.compile
    built = sd.Slice6Db.built
    runtime = sd.Slice6Db.runtime
    snapshot = sds.Slice6DbStored.snapshot
    run_stored = sds.Slice6DbStored.run_stored
    assert_built = sds.Slice6DbStored.assert_built
    blocked = sds.Slice6DbStored.blocked

    # R1: `add` beside an enum and a constructor field builds.

    def test_N33_order_v2_builds(self):
        self.built(ORDER_V2)

    # R2 flipped (fates-a1b, DL-166): a rename onto an enum or constructor field builds.

    def orders(self, text):
        """An inline source as orders.beaml, so the module is Orders (P5: the module name comes from the stem)."""
        path = self.work / "inline" / str(next(self.dirs)) / "orders.beaml"
        path.parent.mkdir(parents=True)
        path.write_text(text)
        return path

    def test_N12_rename_onto_builds(self):
        self.assertEqual(sorted(RENAMES), sorted(p.stem for p in BAD_RENAME.glob("*.beaml")),
                         "setup: bad_rename/ and the table differ")
        for name, text in zip(RENAMES, (RENAME_ENUM, RENAME_CTOR)):
            with self.subTest(name):
                code, stdout, stderr = self.compile(BAD_RENAME / ("%s.beaml" % name))
                self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout), stderr)
            with self.subTest(name + " with the db.list tail"):
                self.built(self.orders(text + LIST_TAIL))

    def test_N12_rename_onto_runtime(self):
        # AC 2 (plan review note: the enum fixture has no amount field, so the v1 row has none).
        enum_row = core({"order_id": "order-1", "via": "web"}, ENUM_V1)
        self.runtime(self.orders(RENAME_ENUM + LIST_TAIL), {"N12_v1_enum_row_renamed": want(
            'fresh.(); BeamlDb.seed("Order", 1, %s)' % jb(enum_row), "Orders.list_orders(%{})",
            '{:ok, %{"items" => [%{"order_id" => "order-1", "channel" => {"Channel", "Web", []}}]}}')})
        ctor_row = core({"order_id": "order-1", "price": EUR}, CTOR_V1)
        self.runtime(self.orders(RENAME_CTOR + LIST_TAIL), {"N12_v1_ctor_row_renamed": want(
            'fresh.(); BeamlDb.seed("Order", 1, %s)' % jb(ctor_row), "Orders.list_orders(%{})",
            '{:ok, %{"items" => [%{"order_id" => "order-1", "amount" => amount.("12.50")}]}}')})

    def test_N12_rename_onto_stored(self):
        """AC 4 and plan review O2: --stored reads an old row by its old key (stored_key, newest step first)."""
        enum, ctor = self.orders(RENAME_ENUM + LIST_TAIL), self.orders(RENAME_CTOR + LIST_TAIL)
        lost = lambda version: ["error: TYPE Order v%d: 1 stored ROW of table records has a value of field channel that "
                                "is no ENUM LITERAL of Channel now (DL-122)" % version]
        builds = {
            "web": (enum, [sds.row({"order_id": "order-web", "via": "web"}, ENUM_V1)]),
            "tv kept": (enum, [sds.row({"order_id": "order-tv", "via": "tv"}, ENUM_V1, unknown_fields=["via"])]),
        }
        for name, (source, rows) in builds.items():
            with self.subTest(name):
                self.assert_built(source, [counted(1, 1, 0)], rows=rows)
        with self.subTest("v2 control"):  # no v1 row: the W2 DEAD LINE warning may print; no error line
            code, stdout, got, _, _ = self.run_stored(enum, rows=[sds.row({"order_id": "order-v2", "channel": "web"},
                                                                          ENUM_V2)])
            self.assertEqual((0, True, True, []), (code, "defmodule Orders do" in stdout, counted(1, 1, 0) in got,
                                                   [l for l in got if l.startswith("error")]), "\n".join(got))
        with self.subTest("tv lost"):
            code, stdout, got, rows_path, _ = self.blocked(enum, rows=[sds.row({"order_id": "order-tv", "via": "tv"},
                                                                               ENUM_V1)])
            self.assertEqual((1, "", lost(1) + ["  record source: %s:1 (line 1)" % rows_path, sds.LITERAL_HELP]),
                             (code, stdout, got))
        with self.subTest("bad currency"):
            bad = {"order_id": "order-bad", "price": {"value": "12.50", "currency": ""}}
            code, stdout, got, rows_path, _ = self.blocked(ctor, rows=[sds.row(bad, CTOR_V1)])
            self.assertEqual((1, "", ["error: TYPE Order: 1 stored ROW of table records fails the constructor of Amount for "
                                      "field amount with BadAmount", "  record source: %s:1 (line 1)" % rows_path,
                                      sds.CTOR_HELP_PREFIX + "currency }"]), (code, stdout, got))
        chain_text = RENAME_ENUM.replace(ENUM_STEP, CHAINED) + LIST_TAIL
        self.assertNotEqual(RENAME_ENUM + LIST_TAIL, chain_text, "setup: the rename step of row_rename_enum changed")
        chain = self.orders(chain_text)
        with self.subTest("chain: a v1 row reads via"):
            self.assert_built(chain, [counted(1, 1, 0)], rows=[sds.row({"order_id": "order-c1", "via": "web"}, CHAIN_V1)])
        with self.subTest("chain: a v2 row reads ch"):
            code, stdout, got, rows_path, _ = self.blocked(chain, rows=[sds.row({"order_id": "order-c2", "ch": "tv"},
                                                                                CHAIN_V2)])
            self.assertEqual((1, "", lost(2) + ["  record source: %s:1 (line 1)" % rows_path, sds.LITERAL_HELP]),
                             (code, stdout, got))
        map_text = RENAME_ENUM.replace(ENUM_STEP, RENAME_MAP) + LIST_TAIL
        self.assertNotEqual(RENAME_ENUM + LIST_TAIL, map_text, "setup: the rename step of row_rename_enum changed")
        with self.subTest("rename and map in one step"):
            code, stdout, got, _, _ = self.blocked(self.orders(map_text),
                                                   rows=[sds.row({"order_id": "order-tv", "via": "tv"}, ENUM_V1)])
            self.assertEqual((1, "", [MAP_FATE, NOT_BUILT_M]), (code, stdout, got))

    # R13 (plan repair 3): DL-152 effect (1), the MIGRATE CHANGES stand before the DL-101 tail.

    def test_N33_order_v2_steps_before_the_tail(self):
        body = decode_body(self.built(ORDER_V2), "__beaml_decode_order")
        self.assertIsNotNone(body, "no def __beaml_decode_order(a0, type_version) in the module")
        put_text = "Map.put(value, %s, %s)" % (b("note"), b(""))
        # RED review O3: one put only, and no comment line in the body that could hold a dead copy of it.
        self.assertEqual((1, []), (body.count(put_text), [l for l in body.splitlines() if l.lstrip().startswith("#")]),
                         "the note MIGRATE CHANGE must stand once, with no comment line in the decode body")
        put = body.find(put_text)
        uses = [body.find(name) for name in ("__beaml_literal_Channel", "__beaml_from_Amount")]
        self.assertEqual((True, True, True), (put >= 0, all(u >= 0 for u in uses), all(put < u for u in uses)),
                         "the note MIGRATE CHANGE must stand before the literal map and the constructor call")
        versions = [l for l in body.splitlines() if re.match(r"\s+\d+ -> \{:ok, \[", l)]
        self.assertTrue(versions, "setup: no per-version field list in the decode")
        self.assertEqual([], [l for l in versions if b("Channel") in l or b("Amount") in l],
                         "the per-version check must take enum and constructor fields raw (PM4-07)")

    # N33: the live decode of order_v2 over the fake BeamlDb.

    def test_N33_order_v2_runtime(self):
        self.runtime(ORDER_V2, N33_CASES)

    # N34 (R4 to R6b): --stored over a chained Order reads the same keys before and after the steps (PM4-08).

    def test_N34_order_v2_rows_of_both_versions_build(self):
        self.assert_built(ORDER_V2, [counted(2, 2, 0)], rows=[sds.row(WIRE1, ORDER_V1), sds.row(WIRE2_V2, ORDER_V2_TYPE)])

    def test_N34_v1_row_lost_literal_blocks(self):
        code, stdout, got, rows_path, _ = self.blocked(ORDER_V2, rows=[sds.row(TV_WIRE, ORDER_V1)])
        self.assertEqual((1, "", ["error: TYPE Order v1: 1 stored ROW of table records has a value of field channel that "
                                  "is no ENUM LITERAL of Channel now (DL-122)",
                                  "  record source: %s:1 (line 1)" % rows_path, sds.LITERAL_HELP]), (code, stdout, got))

    def test_N34_control_kept_v1_value_builds(self):
        self.assert_built(ORDER_V2, [counted(1, 1, 0)], rows=[sds.row(TV_WIRE, ORDER_V1, unknown_fields=["channel"])])

    def test_N34_v1_row_constructor_blocks(self):
        zero = dict(WIRE1, amount={"value": "12.50", "currency": ""})
        code, stdout, got, rows_path, _ = self.blocked(ORDER_V2, rows=[sds.row(zero, ORDER_V1)])
        self.assertEqual((1, "", ["error: TYPE Order: 1 stored ROW of table records fails the constructor of Amount for "
                                  "field amount with BadAmount", "  record source: %s:1 (line 1)" % rows_path], True),
                         (code, stdout, got[:2], len(got) == 3 and got[2].startswith(sds.CTOR_HELP_PREFIX)), "\n".join(got))

    def test_N34_v1_record_of_a_chained_output_builds(self):
        rec = sds.db_record("orders.load", WIRE1, ORDER_V1, {"order_id": "order-1"})
        code, stdout, got, _, _ = self.run_stored(ORDER_V2, rows=[], responses=[rec])
        self.assertEqual((0, True, True, []), (code, "defmodule Orders do" in stdout, counted(0, 0, 0) in got,
                                               [l for l in got if l.startswith("error")]), "\n".join(got))


class M4Decode(unittest.TestCase):
    """The http stream (slice6_decode_test harness): CHAIN, MARK and CHAIN_ADD."""
    maxDiff = None
    setUp = sdec.Slice6Decode.setUp
    compile = sdec.Slice6Decode.compile
    assert_rejected = sdec.Slice6Decode.assert_rejected
    run_runtime = sdec.Slice6Decode.run_runtime

    def test_enum_output_field_rename_in_a_chain(self):
        # R3 flipped (fates-a1b, DL-166, AC 3): the rename onto PaymentState builds; a v1 body reads status.
        code, stdout, stderr = self.compile(sdec.CHAIN, sdec.EMPTY)
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout), stderr)
        self.run_runtime({"R3_v1_body": R3_CASE}, sdec.CHAIN, stored=sf.EMPTY_STORED)

    def test_enum_output_field_with_a_version_mark_builds(self):
        # R3b (PM4-04): a VERSION MARK alone has no step that names a field.
        code, stdout, stderr = self.compile(sdec.MARK, sdec.EMPTY)
        self.assertEqual((0, True), (code, "defmodule BeamlSpike do" in stdout), stderr)

    def test_chained_enum_output_reads_a_v1_body(self):
        # R8: a v1 body with its v1 type: Authorized tuple, note "", no legacy, unknown keys ["extra"].
        self.run_runtime({"R8_v1_body": R8_CASE}, CHAIN_ADD, stored=sf.EMPTY_STORED)

    def test_chained_constructor_output_reads_a_v1_body(self):
        # R8b: a v1 body with a stray key inside amount and at the top: both keys, sorted, and note "".
        self.assertNotEqual(CTOR_SOURCE, CTOR_CHAIN, "setup: the Payment line of decode-ctor changed")
        self.run_runtime({"R8b_v1_body": R8B_CASE}, CTOR_CHAIN, stored=sf.EMPTY_STORED)

    def test_redacted_output_field_with_a_chain_still_rejects(self):
        # R14 (guard): a redacted field in a chained output keeps the D6B-39 text (PM4-05, DL-125).
        self.assertIn("migrate Payment", REDACTED_CHAIN, "setup: the Payment line of output_redacted changed")
        self.assert_rejected(REDACTED_CHAIN, REDACTED_TEXT, sdec.EMPTY)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
