"""EXPERIMENT 0005 prerequisite P4b: `--stored` over the ROW SNAPSHOT rows.jsonl (DL-102, DL-122, DL-124, DL-134,
DL-136, DL-137, DL-140, DL-143; 0005 Q5-4 B).

Ledger: experiments/0004-generated-replay/workflow/2026-11-07/db-transport/ (plan.md with "Plan repair" and "Plan
repair 2": N17 to N27, N20b; decisions.md PDB-21 to PDB-36, QDB-7 A, QDB-8 B; red-plan.md and red-output.md, section P4b).
rows.jsonl stands beside the --stored file. Each line is a ROW CORE (the v3 core of DL-143) plus `source: "db"` and
`row_id` (PDB-21). snapshot-meta.json (P5-19) holds table, database, query_time, row_count and the sorted row_ids; the
compiler reads row_count only (PDB-22). Row read order: TYPE name, digest, TYPE VERSION, MIGRATE CHAIN, DL-101 tail.
A row of no ROW TYPE, a bad digest or an outcome other than `accepted` is counted as not decodable (DL-136, DL-137,
PDB-26, QV3-8 B). An off-chain TYPE VERSION blocks with the path text (N20, N20b).
Expected texts come from the plan and the built RESPONSE RECORD texts with `stored ROW` for `stored RESPONSE RECORD`
and `of table records` for `of operation <op>`. Rows are built here with the digest and fingerprint code of
slice6_db_test (stored_types_test), never by the compiler. Row files live in a temp directory per test.
Defaults pinned here (open for the OWNER, red-plan.md P4b): the rows count line always prints (PDB-24, N17), the P2
RESPONSE count lines keep QV3-7 A; orphan rows (operation with no EFFECT, TYPE with no reader) block as DL-040.
Skipped: DL-140 swap and `map` free (no stored variant, no fate form, D036), RETIRE LINE free of rows (M5, D036).

Depends on P2 (v3 reader, count lines), P3/P5 (several EFFECTS, module Orders) and P4a GREEN (db KINDS, LIST TYPE).
Run: python3 -B experiments/0004-generated-replay/tests/slice6_db_stored_test.py [-k NAME]
Scratch compiler: BEAML_SPIKE=<git archive HEAD build>/target/debug/beaml-spike (other workers write main.rs).
"""
import copy
import itertools
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slice6_db_test as sd  # noqa: E402
import slice6_entry_test as se  # noqa: E402
import stored_types_test as st  # noqa: E402

FIX = sd.FIX
ORDERS, NO_APP, PLAIN_V2, TWO_ROWS = sd.ORDERS, sd.NO_APP, sd.PLAIN_V2, sd.TWO_ROWS
STRICTER, PUT_ONLY = FIX / "stricter" / "orders.beaml", FIX / "put_only" / "orders.beaml"
META = FIX / "stored" / "meta"  # a sample ROW SNAPSHOT as 0005 `mix beaml.stored` writes it (P5-19)
type_of, EUR, WIRE1, WIRE2, TV = sd.type_of, sd.EUR, sd.WIRE1, sd.WIRE2, sd.TV_WIRE
NOTE_V1 = type_of("Note", 1, [["text", "String"]])
NOTE_V2 = type_of("Note", 2, [["text", "String"], ["tag", "String"]])
INVOICE = type_of("Invoice", 1, [["invoice_id", "String"]])
ZERO = {"order_id": "order-zero", "amount": {"value": "0", "currency": "EUR"}, "channel": "web"}
APP = {"order_id": "order-app", "amount": EUR, "channel": "app"}
PLAIN_ROW, V3_ROW = sd.PLAIN_ROW, sd.V3_ROW
OFF_CHAIN = "0" * 64
ROW_IDS = itertools.count(7001)

UNKNOWN_STORE = ("error: stored ROWS unknown: a source with db.get or db.list needs rows.jsonl beside --stored "
                 "(an unknown store is not an empty store)")
# PDB-32, PDB-36: the built RESPONSE RECORD help, compared as a prefix up to the DL reference (one site, M4 open).
HELP_PREFIX = "  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of Order"
LITERAL_HELP = ("  help: declare the fate in a MIGRATE STEP (DL-122); slice 6b has no MIGRATE STEP form for an enum field "
                "(D6B-39), so restore the removed or changed ENUM LITERAL of Channel")


def counted(n, k, m):
    """PDB-24: the rows count line. Never a value, never a row id."""
    return "rows: %d rows, %d checked, %d not decodable" % (n, k, m)


def row(value, type_=sd.ORDER_TYPE, unknown_fields=(), operation="orders.save", **over):
    """A ROW SNAPSHOT line (PDB-21): the ROW CORE (PDB-14, v3 words) plus source "db" and row_id."""
    rid = next(ROW_IDS)
    line = sd.core(value, type_, unknown_fields, operation)
    line.update(trace_id="%032x" % (0x5eed0000 + rid), span_id="%016x" % (0xc0de0000 + rid), artifact_id="e" * 64,
                source="db", row_id="row-%d" % rid)  # P4c RED repair M2: a String id, no digit run a `ts` can hold
    line.update(over)
    return line


def retyped(type_, **over):
    return dict(copy.deepcopy(type_), **over)


def db_record(operation, value, type_, request, **over):
    """A db call record in responses.jsonl (PDB-17): the v3 core plus request."""
    rec = dict(sd.core(value, type_, (), operation), request=request, trace_id="%032x" % 0xfacade01,
               span_id="%016x" % 0xfacade01)
    rec.update(over)
    return rec


def list_items(*items):
    return {"items": list(items)}


def leaves(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from leaves(v)
    elif isinstance(value, str):
        yield value


class Slice6DbStored(unittest.TestCase):
    maxDiff = None
    runtime = sd.Slice6Db.runtime
    built = sd.Slice6Db.built

    def setUp(self):
        se.Slice6Entry.setUp(self)
        self.words = set()  # N26, N27: stored Strings (5 chars or more), row ids and trace ids that this test wrote
        self.dirs = itertools.count(1)

    def compile(self, source, extra=sd.STORED, binary=None):
        """N27 (N14 for P4b): events hold no path, no source text and no value, row id or trace id of the rows."""
        code, stdout, stderr = sd.Slice6Db.compile(self, source, extra, binary)
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            text = log.read_text()
            self.assertEqual([], [w for w in sorted(self.words) if w in text], "N27: events hold a stored value")
            self.assertNotIn(str(self.work / "stored"), text, "N27: events hold the --stored path")
        return code, stdout, stderr

    def snapshot(self, rows=(), responses=(), meta=None, with_rows=True):
        """A --stored directory: responses.jsonl, rows.jsonl (a dict is a JSON line, a str is a raw line), meta."""
        holder = self.work / "stored" / str(next(self.dirs))
        holder.mkdir(parents=True)
        lines = [r if isinstance(r, str) else json.dumps(r, separators=(",", ":")) for r in rows]
        if with_rows:
            (holder / "rows.jsonl").write_text("".join(line + "\n" for line in lines))
        resp = holder / "responses.jsonl"
        resp.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in responses))
        if meta is not None:
            (holder / "snapshot-meta.json").write_text(json.dumps(meta))
        for r in [r for r in rows if isinstance(r, dict)] + list(responses):
            self.words.update(w for w in leaves(r.get("value")) if len(w) >= 5)
            self.words.update(str(r[k]) for k in ("row_id", "trace_id", "span_id") if r.get(k))
        return resp, holder / "rows.jsonl"

    def run_stored(self, source, rows=(), responses=(), meta=None, with_rows=True):
        resp, rows_path = self.snapshot(rows, responses, meta, with_rows)
        code, stdout, stderr = self.compile(source, ["--stored", str(resp)])
        return code, stdout, stderr.strip().splitlines(), rows_path, resp

    def assert_built(self, source, lines, **kw):
        """Exit 0, the module Orders, and exactly these stderr lines."""
        code, stdout, got, _, _ = self.run_stored(source, **kw)
        self.assertEqual((0, True, lines), (code, "defmodule Orders do" in stdout, got))

    def blocked(self, source, **kw):
        """Exit, stdout, stderr lines without the rows count line (a block may print it, it need not), rows, resp."""
        code, stdout, got, rows_path, resp = self.run_stored(source, **kw)
        return code, stdout, [l for l in got if not l.startswith("rows: ")], rows_path, resp

    def assert_path_block(self, source, type_name, line=1, **kw):
        """The no_path text with ROW (N20, N20b): first line exact, the record source line present."""
        code, stdout, got, rows_path, _ = self.blocked(source, **kw)
        self.assertEqual((1, "", "error: TYPE %s cannot read 1 stored ROW of table records" % type_name, True),
                         (code, stdout, got[0] if got else None,
                          "  record source: %s (first at line %d)" % (rows_path, line) in got), "\n".join(got))
        return got

    # N17: clean rows build and print the count line.

    def test_N17_clean_rows(self):
        self.assert_built(ORDERS, [counted(2, 2, 0)], rows=[row(WIRE1), row(WIRE2)])

    def test_N17b_empty_row_snapshot(self):
        # A known empty store: 0 rows (QV3-7 A is the P2 rule for RESPONSE RECORDS; the rows line always prints).
        self.assert_built(ORDERS, [counted(0, 0, 0)], rows=[])

    # N18 (DL-102): a stricter constructor over a stored row blocks; two controls.

    def test_N18_stricter_constructor_blocks(self):
        code, stdout, got, rows_path, _ = self.blocked(STRICTER, rows=[row(ZERO)])
        self.assertEqual((1, "", ["error: TYPE Order: 1 stored ROW of table records fails the constructor of Amount for "
                                  "field amount with BadAmount", "  record source: %s:1 (line 1)" % rows_path], True),
                         (code, stdout, got[:2], len(got) == 3 and got[2].startswith(HELP_PREFIX)), "\n".join(got))

    def test_N18b_two_rows_fail_counted_with_the_first_line(self):
        code, _, got, rows_path, _ = self.blocked(STRICTER, rows=[row(WIRE1), row(ZERO), row(dict(ZERO, order_id="order-zero-2"))])
        self.assertEqual((1, ["error: TYPE Order: 2 stored ROWS of table records fail the constructor of Amount for "
                              "field amount with BadAmount", "  record source: %s:2 (line 2)" % rows_path]),
                         (code, got[:2]), "\n".join(got))

    def test_N18_control_old_source_builds(self):
        self.assert_built(ORDERS, [counted(1, 1, 0)], rows=[row(ZERO)])

    def test_N18_control_stricter_without_the_row_builds(self):
        self.assert_built(STRICTER, [counted(1, 1, 0)], rows=[row(WIRE1)])

    # N19 (DL-122, DL-124): a lost ENUM LITERAL in a row blocks; a kept value does not.

    def test_N19_lost_literal_blocks(self):
        code, stdout, got, rows_path, _ = self.blocked(NO_APP, rows=[row(APP)])
        self.assertEqual((1, "", ["error: TYPE Order v1: 1 stored ROW of table records has a value of field channel that "
                                  "is no ENUM LITERAL of Channel now (DL-122)",
                                  "  record source: %s:1 (line 1)" % rows_path, LITERAL_HELP]), (code, stdout, got))

    def test_N19_control_kept_value_builds(self):
        self.assert_built(NO_APP, [counted(1, 1, 0)], rows=[row(TV, unknown_fields=["channel"])])

    def test_N19_control_the_row_builds_where_the_literal_stands(self):
        self.assert_built(ORDERS, [counted(1, 1, 0)], rows=[row(APP)])

    # N20 (DL-043, DL-127 lazy): rows on the chain build; a row off the chain blocks with the ROW path text.

    def test_N20_chain_rows_build(self):
        # The v1 row passes the DL-101 shape check only after the MIGRATE CHAIN (read order: chain before DL-101).
        self.assert_built(PLAIN_V2, [counted(2, 2, 0)],
                          rows=[row(PLAIN_ROW, sd.PLAIN_V1), row(V3_ROW, sd.PLAIN_V2_TYPE)])

    def test_N20_off_chain_row_blocks(self):
        self.assert_path_block(PLAIN_V2, "Order", rows=[row(PLAIN_ROW, retyped(sd.PLAIN_V1, fingerprint=OFF_CHAIN))])

    def test_N20_newer_version_blocks(self):
        self.assert_path_block(ORDERS, "Order", line=2, rows=[row(WIRE1), row(WIRE2, retyped(sd.ORDER_TYPE, version=7))])

    # N20b (QDB-8 B, PDB-34, PDB-35): two ROW TYPES in one rows.jsonl, each checked by the TYPE its type.name names.

    def note(self, text, type_=NOTE_V1, **over):
        return row({"text": text}, type_, operation="notes.save", **over)

    def test_N20b_two_row_types_build(self):
        self.assert_built(TWO_ROWS, [counted(3, 3, 0)],
                          rows=[row(WIRE1), self.note("first-note"), row({"text": "second-note", "tag": "second-tag"},
                                                                        NOTE_V2, operation="notes.save")])

    def test_N20b_control_note_row_under_the_order_type_blocks(self):
        got = self.assert_path_block(TWO_ROWS, "Order", rows=[row(WIRE1), self.note("under-order",
                                                                                     retyped(NOTE_V1, name="Order"))],
                                     line=2)
        self.assertNotIn("TYPE Note", "\n".join(got))

    def test_N20b_control_note_row_off_its_chain_blocks(self):
        self.assert_path_block(TWO_ROWS, "Note", rows=[self.note("off-chain", retyped(NOTE_V1, fingerprint=OFF_CHAIN))])

    # N21 (DL-136, DL-137): a bad digest and a TYPE with no reader are counted, not checked.

    def test_N21_not_decodable_rows_are_counted(self):
        bad_digest = row(WIRE2, value_sha256=st.value_sha256(WIRE1))
        invoice = row({"invoice_id": "invoice-1"}, INVOICE)
        self.assert_built(ORDERS, [counted(3, 1, 2)], rows=[row(WIRE1), bad_digest, invoice])

    def test_N21b_rows_not_accepted_are_counted_QV3_8_B(self):
        # PDB-26: a row with an outcome other than "accepted" is counted, not checked, also off its chain (QV3-8 B).
        rejected = row(None, outcome="rejected", reason="decode")
        off = row(WIRE2, retyped(sd.ORDER_TYPE, fingerprint=OFF_CHAIN), outcome="rejected", reason="decode")
        self.assert_built(ORDERS, [counted(3, 1, 2)], rows=[row(WIRE1), rejected, off])

    def test_N21b_rejected_row_skips_the_constructor_check(self):
        self.assert_built(STRICTER, [counted(1, 0, 1)], rows=[row(ZERO, outcome="rejected", reason="constructor")])

    # Read order (PDB-15): TYPE name, digest, TYPE VERSION, MIGRATE CHAIN, DL-101 tail.

    def test_N29_read_order_digest_before_type_version(self):
        # A bad digest with an off-chain fingerprint is counted; a reader that path-checks first blocks.
        bad = row(WIRE1, retyped(sd.ORDER_TYPE, fingerprint=OFF_CHAIN), value_sha256=st.value_sha256(WIRE2))
        self.assert_built(ORDERS, [counted(1, 0, 1)], rows=[bad])

    def test_N29_read_order_type_name_before_type_version(self):
        self.assert_built(ORDERS, [counted(1, 0, 1)], rows=[row({"invoice_id": "invoice-7"}, retyped(INVOICE, version=7))])

    def test_N29_read_order_type_version_before_DL101(self):
        # An off-chain row whose value also fails the stricter constructor: the path text only.
        got = self.assert_path_block(STRICTER, "Order", rows=[row(ZERO, retyped(sd.ORDER_TYPE, fingerprint=OFF_CHAIN))])
        self.assertNotIn("fails the constructor", "\n".join(got))

    # N22 (PDB-23): an unknown store is not an empty store.

    def test_N22_no_row_snapshot_blocks_a_reader(self):
        code, stdout, got, _, _ = self.run_stored(ORDERS, with_rows=False)
        self.assertEqual((1, "", [UNKNOWN_STORE]), (code, stdout, got))

    def test_N22_control_put_only_needs_no_row_snapshot(self):
        code, stdout, got, _, _ = self.run_stored(PUT_ONLY, with_rows=False)
        self.assertEqual((0, True, []), (code, "def orders_save(" in stdout, got))

    # N23: line form of rows.jsonl (line 1 good, line 2 bad).

    def test_N23_line_form(self):
        no_source = row(WIRE2)
        del no_source["source"]
        cases = {
            "not_json": ("{not json", "error: stored ROW is not JSON"),
            "no_source": (no_source, 'error: stored ROW has no source "db"'),
            "version_2": (row(WIRE2, version=2),
                          "error: stored ROW has record version 2; this build reads record version 3 only (DL-143)"),
        }
        for name, (line, text) in cases.items():
            with self.subTest(name):
                code, stdout, got, rows_path, _ = self.blocked(ORDERS, rows=[row(WIRE1), line])
                self.assertEqual((1, "", [text, "  record source: %s:2 (line 2)" % rows_path]), (code, stdout, got))

    # N24 (PDB-22, P5-19): snapshot-meta.json row_count must equal the row lines.

    def meta(self, rows, row_count):
        return {"table": "records", "database": "beaml_dev", "query_time": "2026-11-07T20:00:00.000000Z",
                "row_count": row_count, "row_ids": sorted(r["row_id"] for r in rows)}

    def test_N24_partial_row_snapshot_blocks(self):
        rows = [row(WIRE1), row(WIRE2)]
        code, stdout, got, _, _ = self.blocked(ORDERS, rows=rows, meta=self.meta(rows, 3))
        self.assertEqual((1, "", ["error: rows.jsonl holds 2 rows but snapshot-meta.json counts 3; the ROW SNAPSHOT is "
                                  "partial"]), (code, stdout, got))

    def test_N24_row_count_below_lines_blocks(self):
        # P4b RED review M2: PDB-22 says "differs", so a row_count below the row lines blocks too (appended rows).
        rows = [row(WIRE1), row(WIRE2)]
        code, stdout, got, _, _ = self.blocked(ORDERS, rows=rows, meta=self.meta(rows, 1))
        self.assertEqual((1, "", ["error: rows.jsonl holds 2 rows but snapshot-meta.json counts 1; the ROW SNAPSHOT is "
                                  "partial"]), (code, stdout, got))

    def test_N24_control_matching_meta_builds(self):
        rows = [row(WIRE1), row(WIRE2)]
        self.assert_built(ORDERS, [counted(2, 2, 0)], rows=rows, meta=self.meta(rows, 2))

    def test_N24_sample_meta_form(self):
        # Guard (passes today): the sample holds the P5-19 keys, sorted row ids of its rows, row_count = row lines.
        meta = json.loads((META / "snapshot-meta.json").read_text())
        rows = [json.loads(l) for l in (META / "rows.jsonl").read_text().splitlines() if l.strip()]
        self.assertEqual((["database", "query_time", "row_count", "row_ids", "table"], "records", len(rows),
                          sorted(r["row_id"] for r in rows), meta["row_ids"], ["db"] * len(rows)),
                         (sorted(meta), meta["table"], meta["row_count"], meta["row_ids"], sorted(meta["row_ids"]),
                          [r["source"] for r in rows]))
        for r in rows:
            self.assertEqual(st.value_sha256(r["value"]), r["value_sha256"], "setup: the sample digest")

    def test_N24_sample_builds(self):
        code, stdout, stderr = self.compile(ORDERS, ["--stored", str(META / "responses.jsonl")])
        self.assertEqual((0, True, [counted(2, 2, 0)]), (code, "defmodule Orders do" in stdout, stderr.strip().splitlines()))

    # N25 (PDB-17, QV3-8 B): db call records in responses.jsonl get the RESPONSE RECORD checks.

    def test_N25_list_record_constructor_blocks(self):
        rec = db_record("orders.list", list_items(ZERO), sd.LIST_TYPE, {})
        code, stdout, got, _, resp = self.blocked(STRICTER, rows=[], responses=[rec])
        self.assertEqual((1, "", ["error: TYPE Order: 1 stored RESPONSE RECORD of operation orders.list fails the "
                                  "constructor of Amount for field amount with BadAmount",
                                  "  record source: %s:1 (line 1)" % resp], True),
                         (code, stdout, got[:2], len(got) == 3 and got[2].startswith(HELP_PREFIX)), "\n".join(got))

    def test_N25_save_record_constructor_blocks(self):
        rec = db_record("orders.save", ZERO, sd.ORDER_TYPE, ZERO)
        code, stdout, got, _, resp = self.blocked(STRICTER, rows=[], responses=[rec])
        self.assertEqual((1, "", ["error: TYPE Order: 1 stored RESPONSE RECORD of operation orders.save fails the "
                                  "constructor of Amount for field amount with BadAmount",
                                  "  record source: %s:1 (line 1)" % resp]), (code, stdout, got[:2]), "\n".join(got))

    def test_N25_control_rejected_record_is_counted(self):
        # QV3-8 B and the P2 count lines (QV3-7 A: printed when M > 0), beside the rows count line.
        rec = db_record("orders.list", None, sd.LIST_TYPE, {}, outcome="rejected", reason="transport")
        code, stdout, got, _, _ = self.run_stored(STRICTER, rows=[], responses=[rec])
        p2 = ["1 records, 0 checked, 1 rejected at capture", "digest not verified (P2b)"]
        self.assertEqual((0, True, sorted(p2 + [counted(0, 0, 0)]), True),
                         (code, "defmodule Orders do" in stdout, sorted(got),
                          any(got[i:i + 2] == p2 for i in range(len(got)))), "\n".join(got))

    # N26 (DL-124): no message holds a stored String, a row id or a trace id.

    def test_N26_no_stored_value_in_any_text(self):
        cases = {
            "constructor": (STRICTER, {"rows": [row(ZERO)]}, "stored ROW"),
            "literal": (NO_APP, {"rows": [row(APP)]}, "stored ROW"),
            "path": (TWO_ROWS, {"rows": [self.note("hidden-note-text", retyped(NOTE_V1, name="Order"))]}, "stored ROW"),
            "orphan": (ORDERS, {"rows": [self.note("orphan-note-text")]}, "stored ROW"),
            "list_record": (STRICTER, {"rows": [], "responses": [db_record("orders.list", list_items(ZERO), sd.LIST_TYPE,
                                                                           {})]}, "stored RESPONSE RECORD"),
            "count_line": (ORDERS, {"rows": [row(WIRE1), row({"invoice_id": "invoice-count"}, INVOICE)]}, "rows: 2 rows"),
        }
        for name, (source, kw, anchor) in cases.items():
            with self.subTest(name):
                code, _, got, _, _ = self.run_stored(source, **kw)
                text = "\n".join(got)
                # The anchor must stand in stderr, so a parse error cannot pass this test.
                self.assertEqual((True, []), (anchor in text, [w for w in sorted(self.words) if w in text]), text)

    # N27 (N14 for P4b): the events of a clean build and of a block (checked in compile()).

    def test_N27_events_hold_no_row_value(self):
        # P4c (TEST O3): String row ids; a 4-digit int id can stand in the digits of an event `ts` (false fail).
        self.assert_built(ORDERS, [counted(1, 1, 0)], rows=[row(WIRE1, row_id="row-n27-a")])
        self.assertEqual(1, self.blocked(STRICTER, rows=[row(ZERO, row_id="row-n27-b")])[0])
        self.assertTrue((self.work / "cwd" / ".beaml" / "actions.jsonl").is_file(), "setup: no action log written")

    # N28 (DL-040 parity, as 6d O3): a row whose operation has no EFFECT and whose TYPE has no reader blocks.

    def test_N28_orphan_rows_of_a_removed_db_effect_block(self):
        code, stdout, got, rows_path, _ = self.blocked(ORDERS, rows=[row(WIRE1), self.note("orphan-a"),
                                                                     self.note("orphan-b")])
        # The help line is not compared: it would offer a RETIRE LINE for rows (M5 parked) and its text is M4.
        self.assertEqual((1, "", ["error: stored ROW of operation notes.save has no effect in the source",
                                  "  record source: %s:2 (line 2)" % rows_path,
                                  "  stored ROWS of operation notes.save: 2"]), (code, stdout, got[:3]), "\n".join(got))

    def test_N28_control_row_of_a_removed_writer_with_a_reader_is_checked(self):
        # DL-137: orders.list still decodes the row, so it is checked, not an orphan.
        self.assert_built(ORDERS, [counted(1, 1, 0)], rows=[row(WIRE1, operation="orders.import")])

    @unittest.skip("blocked: the RETIRE LINE meaning for rows is M5, parked by D036 (plan Parked items); no test here")
    def test_N28b_retire_line_frees_orphan_rows(self):
        pass

    # DL-140: a stored literal that falls on another known variant blocks; a `map` MIGRATE STEP frees it.

    @unittest.skip("blocked: a ROW CORE holds the wire literal, not the stored variant (plan Limits), and DL-140 is the "
                   "fate slice with DL-125 (D036); cannot turn green in P4b")
    def test_N30_literal_swap_on_a_row_blocks(self):
        pass

    @unittest.skip("blocked: no `map` MIGRATE STEP form exists (DL-140, DL-125, fate slice P6, D036)")
    def test_N30b_map_migrate_step_frees_the_swap(self):
        pass

    # M1 of the P4a RED review: a row constructor failure writes a rejected/constructor db call record.

    def test_N10_constructor_record(self):
        bad = sd.jb(sd.FAULTS["constructor"][0])
        want = sd.ex({"value": None, "outcome": "rejected", "reason": "constructor"})
        self.runtime(ORDERS, {
            "N10_constructor_record_list": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.list_orders(%%{}); [r] = resp.(); '
                                            'Map.take(r, ["value", "outcome", "reason"]) == %s' % (bad, want)),
            "N10_constructor_record_load": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.load(key1); [r] = resp.(); '
                                            'Map.take(r, ["value", "outcome", "reason"]) == %s' % (bad, want)),
        })

    # QDB-8 B: the Note v1 -> v2 `add` chain read at run time, beside Order rows in one table.

    def test_N31_note_chain_read_runtime(self):
        v1 = sd.jb(sd.core({"text": "n1"}, NOTE_V1, (), "notes.save"))
        self.runtime(TWO_ROWS, {
            "N31_note_v1_reads_with_tag": ('fresh.(); BeamlDb.seed("Note", 1, %s); '
                                           'Orders.list_notes(%%{}) == {:ok, %%{"items" => [%%{"text" => "n1", "tag" => ""}]}}'
                                           % v1),
            "N31_save_note_writes_v2": ('fresh.(); Orders.save_note(%%{"text" => "n2", "tag" => "t"}); '
                                        '[{_, head, _}] = puts.(); {head, last_core.()["type"]} == '
                                        '{{"Note", 2}, %s}' % sd.ex(NOTE_V2)),
            "N31_order_rows_stay_beside": ('fresh.(); Orders.save(o1.()); BeamlDb.seed("Note", 1, %s); '
                                           '{Orders.list_orders(%%{}), Orders.list_notes(%%{})} == {{:ok, %%{"items" => '
                                           '[o1.()]}}, {:ok, %%{"items" => [%%{"text" => "n1", "tag" => ""}]}}}' % v1),
        })

    # P4c (TEST O1, owner-review "Row shape check", default A): a String field of the ROW TYPE that is missing or
    # holds no String blocks with the DL-102 text, for rows and for RESPONSE RECORDS. The digest is the row's own,
    # so only the shape fault stays. Proposed text (RED P4c, default, open): "has no String value for field <f>".
    NO_ID = {"amount": EUR, "channel": "web"}
    INT_ID = {"order_id": 90817, "amount": EUR, "channel": "web"}

    def assert_shape_block(self, noun, where, got, source_path):
        text = "\n".join(got)
        self.assertEqual(["error: TYPE Order: 1 stored %s of %s has no String value for field order_id" % (noun, where),
                          "  record source: %s:1 (line 1)" % source_path], got[:2], text)
        self.assertTrue(len(got) == 3 and got[2].startswith(HELP_PREFIX), text)
        self.assertNotIn("90817", text.replace(str(source_path), ""), "DL-124: the stored number is in the text")

    def test_N32_row_missing_string_field(self):
        code, stdout, got, rows_path, _ = self.blocked(ORDERS, rows=[row(self.NO_ID)])
        self.assertEqual((1, ""), (code, stdout), "\n".join(got))
        self.assert_shape_block("ROW", "table records", got, rows_path)

    def test_N32b_row_wrong_type_string_field(self):
        code, stdout, got, rows_path, _ = self.blocked(ORDERS, rows=[row(self.INT_ID)])
        self.assertEqual((1, ""), (code, stdout), "\n".join(got))
        self.assert_shape_block("ROW", "table records", got, rows_path)

    def test_N32_control_complete_row_builds(self):
        self.assert_built(ORDERS, [counted(1, 1, 0)], rows=[row(WIRE1)])

    def test_N32c_response_record_shape_blocks(self):
        # The same two faults in a db.list RESPONSE RECORD (item 0), beside an empty rows.jsonl.
        # P4c TEST repair O2: `item_1` pins every item (a check of item 0 only passes the first two).
        cases = {"missing": [self.NO_ID], "wrong_type": [self.INT_ID], "item_1": [WIRE1, self.NO_ID]}
        for name, items in cases.items():
            with self.subTest(name):
                rec = db_record("orders.list", list_items(*items), sd.LIST_TYPE, {})
                code, stdout, got, _, resp = self.blocked(ORDERS, rows=[], responses=[rec])
                self.assertEqual((1, ""), (code, stdout), "\n".join(got))
                self.assert_shape_block("RESPONSE RECORD", "operation orders.list", got, resp)

    def test_N32c_control_complete_list_record_builds(self):
        """P4c RED repair O1: a complete orders.list RESPONSE RECORD with two complete items builds and is counted.

        Guard: passes at HEAD and must pass after a correct GREEN. A GREEN that checks the ROW TYPE Order against the
        top-level value {"items": [...]} instead of each item finds no order_id, blocks this record and fails here.
        Two items, so a check of item 0 only stays visible in a later case if needed."""
        rec = db_record("orders.list", list_items(WIRE1, WIRE2), sd.LIST_TYPE, {})
        self.assert_built(ORDERS, [counted(0, 0, 0)], rows=[], responses=[rec])

    def test_N32c_two_bad_items_count_one_record(self):
        """P4c TEST repair O2: the text counts RESPONSE RECORDS, not items; one record with two bad items is 1."""
        rec = db_record("orders.list", list_items(self.NO_ID, self.INT_ID), sd.LIST_TYPE, {})
        code, stdout, got, _, resp = self.blocked(ORDERS, rows=[], responses=[rec])
        self.assertEqual((1, ""), (code, stdout), "\n".join(got))
        self.assert_shape_block("RESPONSE RECORD", "operation orders.list", got, resp)

    def test_N32d_old_version_row_shape_blocks(self):
        """P4c TEST O1: a row is checked against the fields of its own stored TYPE VERSION, not only the newest.

        PLAIN_V2 source; a v1 row without `label` (a v1 field no MIGRATE STEP fills) or with an Int `label` blocks.
        Control: N20_chain_rows_build (a complete v1 row builds)."""
        for name, value in {"missing": {"order_id": "order-n32d"}, "wrong_type": dict(PLAIN_ROW, label=90817)}.items():
            with self.subTest(name):
                code, stdout, got, rows_path, _ = self.blocked(PLAIN_V2, rows=[row(value, sd.PLAIN_V1)])
                text = "\n".join(got)
                self.assertEqual((1, ""), (code, stdout), text)
                self.assertEqual(["error: TYPE Order: 1 stored ROW of table records has no String value for field label",
                                  "  record source: %s:1 (line 1)" % rows_path], got[:2], text)
                self.assertTrue(len(got) == 3 and got[2].startswith(HELP_PREFIX), text)
                self.assertNotIn("90817", text.replace(str(rows_path), ""), "DL-124: the stored number is in the text")

    def test_N32e_http_record_shape_gap_builds(self):
        """P4c TEST O3, documented gap (Migrate, default A, open): an http RESPONSE RECORD without the String field
        `status` still builds. This guard flips when the OWNER chooses B (check http after the version fix)."""
        rec = json.loads((sd.EXPERIMENT / "stored" / "v1.jsonl").read_text().splitlines()[0])
        del rec["value"]["status"]
        rec["value_sha256"] = st.value_sha256(rec["value"], rec.get("unknown_keys", ()), rec.get("redacted", ()))
        holder = self.work / "stored" / "http"
        holder.mkdir(parents=True)
        (holder / "v1.jsonl").write_text(json.dumps(rec, separators=(",", ":")) + "\n")
        code, stdout, stderr = self.compile(sd.EXPERIMENT / "arms" / "gen" / "orders.beaml",
                                            ["--stored", str(holder / "v1.jsonl")])
        self.assertEqual((0, True), (code, "defmodule " in stdout), stderr)


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
