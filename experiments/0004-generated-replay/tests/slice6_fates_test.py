"""EXPERIMENT 0004 fates-a1: the fate lines `quarantine`, `map`, `redact`, `retire` and `enum E vN` (DL-125, DL-155,
DL-156, DL-157), their checks and `--stored` (step a1 of the FATE slice).

Ledger: experiments/0004-generated-replay/workflow/2026-11-08/fates/ (plan.md with "Plan repair after plan check",
decisions.md PF-01 to PF-24, the rulings and the RED decisions, plan-review.md, red-plan.md, red-output.md).
Form A (QF-3 ruled): `type Amount v2 { ... }` + `migrate Amount v1 -> v2 { quarantine value }`; the enum form
`enum Channel v2 { ... }` + `migrate Channel v1 -> v2 { map "app" -> Mobile }`.
a1 lifts the DL-102 and DL-122 blocks and prints the `fate:` line, then exits 1 with a "not built yet" line until a2
builds the run-time side (ruling on O2). a2 removes NOT_BUILT_Q and NOT_BUILT_M and expects exit 0 there.
Expected texts come from the plan, the rulings and the RED decisions, never from the new compiler. Fixtures stand under
slice6/db/fates/ (db sources, N13 filter); wrong forms stay inline. A compile error may carry an `error: ` prefix or not
(both forms exist in main.rs today); the tests accept both and pin the rest exactly.
DL-147: this file joins run.py in the GREEN commit (step slice6-fates).
Run: python3 -B experiments/0004-generated-replay/tests/slice6_fates_test.py [-k NAME]
Scratch compiler: BEAML_SPIKE=<git archive HEAD build>/target/release/beaml-spike (other workers write main.rs).
"""
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slice6_db_stored_test as sds  # noqa: E402
import slice6_db_test as sd  # noqa: E402

FATES = sd.FIX / "fates"
STRICTER_V1, AMOUNT_V2, TWO_CTOR = (FATES / n / "orders.beaml" for n in ("stricter_v1", "amount_v2", "two_ctor"))
CHANNEL_V1, CHANNEL_V2, ORDER_MAP = (FATES / n / "orders.beaml" for n in ("channel_v1", "channel_v2", "order_map"))
CHANNEL_SWAP = FATES / "channel_swap" / "orders.beaml"  # DL-161: Web and App swap their literals at v2
DECODE = sd.EXPERIMENT / "slice6" / "decode"
DECODE_CTOR = sd.EXPERIMENT / "slice6" / "decode-ctor"
type_of, row, db_record, counted = sd.type_of, sds.row, sds.db_record, sds.counted
WIRE1, ZERO, APP, EUR = sd.WIRE1, sds.ZERO, sds.APP, sd.EUR
PLACE_TYPE = type_of("PlaceForm", 1, [["order_id", "String"], ["amount", "Amount"], ["channel", "Channel"]])
ORDER_V3 = type_of("Order", 3, [["order_id", "String"], ["amount", "Amount"], ["channel", "Channel"], ["note", "String"]])
TIP_ORDER = type_of("Order", 1, [["order_id", "String"], ["amount", "Amount"], ["tip", "Tip"], ["channel", "Channel"]])
NO_CURRENCY = dict(WIRE1, order_id="order-nocur", amount={"value": "12.50", "currency": ""})
BOTH = {"order_id": "order-both", "amount": {"value": "0", "currency": "EUR"}, "channel": "tv"}
FORM_ZERO = {"order_id": "order-form-zero", "amount": {"value": "0", "currency": "EUR"}, "channel": "web"}
FORM_APP = {"order_id": "order-form-app", "amount": EUR, "channel": "app"}
ZERO2 = dict(ZERO, order_id="order-zero-two")
TABLET = dict(WIRE1, order_id="order-tablet", channel="tablet")
WEB_ROW = dict(WIRE1, order_id="order-web")
# DL-155 (ruling by Fable on Q1, DL-161): the previous enum declaration stays in the source while v1 values exist.
V1_DECL = 'enum Channel v1 {\n  Web = "web"\n  App = "app"\n  Unknown(String)\n}\n'
NO_V1_DECL = "error: enum Channel v1 is not declared; keep the previous declaration while v1 values exist (DL-155)"
ENUM_STEP_ONLY = "migrate Channel v1 -> v2: an enum MIGRATE STEP holds bare map and quarantine lines only (PF-06, DL-162)"

Q_LINE = "migrate Amount v1 -> v2 { quarantine value }"
M_LINE = 'migrate Channel v1 -> v2 { map "app" -> Mobile }'
QM_LINE = 'migrate Order v2 -> v3 { map channel "app" -> Mobile }'
Q_STEP, M_STEP, QM_STEP = "migrate Amount v1 -> v2", "migrate Channel v1 -> v2", "migrate Order v2 -> v3"

# Ruling on O2 (plan repair 3 b): a hit fate line stops the a1 build. a2 removes both lines.
NOT_BUILT_Q = "error: a quarantine line is hit, but quarantine at run time is not built yet (fates-a2, DL-157)"
NOT_BUILT_M = "error: a map line is hit, but map at run time is not built yet (fates-a2)"


def fate(count, noun, place, verb, step, line):
    """PF-13: one `fate:` line per step, stream place and fate line; source text only, never a stored value."""
    return "fate: %d stored %s%s of %s %s by %s (%s)" % (count, noun, "" if count == 1 else "S", place, verb, step, line)


def help_q(ctor, newest, param):
    """DL-155 help, QF-5 A, PF-21: the next TYPE VERSION of the constructor TYPE and its quarantine line."""
    return ("  help: declare the next TYPE VERSION and a fate (DL-155): type %s v%d and migrate %s v%d -> v%d "
            "{ quarantine %s }" % (ctor, newest + 1, ctor, newest, newest + 1, param))


def help_m(enum, newest):
    """DL-155 help for a lost ENUM LITERAL; the old String is a stored value and stays a placeholder (DL-124)."""
    return ('  help: declare the next TYPE VERSION and a fate (DL-155): enum %s v%d and migrate %s v%d -> v%d '
            '{ map "<old literal>" -> <Variant> }' % (enum, newest + 1, enum, newest, newest + 1))


ENUM_CTOR_HELP = ("  help: no fate line covers an ENUM CONSTRUCTOR yet (D041 open); restore a signature of fn %s that "
                  "reads these records")
NO_SIGNATURE_HELP = ("  help: no fate line covers a value that matches no signature of %s (a decode fault); restore a "
                     "signature of fn %s that reads these records")
OLD_DL102_HELP = "  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of %s (DL-102)"


def ctor_block(place, noun, ty, ctor, field, failure, source, line):
    return ["error: TYPE %s: 1 stored %s of %s fails the constructor of %s for field %s with %s"
            % (ty, noun, place, ctor, field, failure), "  record source: %s:%d (line %d)" % (source, line, line)]


def literal_block(ty, noun, place, source, line):
    return ["error: TYPE %s v1: 1 stored %s of %s has a value of field channel that is no ENUM LITERAL of Channel now "
            "(DL-122)" % (ty, noun, place), "  record source: %s:%d (line %d)" % (source, line, line)]


def told(lines):
    """The message lines without the count lines (rows:, the P2 and DL-138 counts); a block may print them."""
    return [l for l in lines if l.startswith(("error", "warning", "note", "fate:", "  "))]


def swap(text, old, new):
    assert text.count(old) == 1, "setup: %r stands %d times" % (old, text.count(old))
    return text.replace(old, new)


def entry(value, unknown_fields=()):
    """An ENTRY RECORD of ui.place (DL-134, DL-138): the v3 core with trace ids."""
    rec = sd.core(value, PLACE_TYPE, unknown_fields, "ui.place")
    rec.update(trace_id="%032x" % 0xe17e0001, span_id="%016x" % 0xe17e0001)
    return rec


AMT, CH, OM = AMOUNT_V2.read_text(), CHANNEL_V2.read_text(), ORDER_MAP.read_text()
SW = CHANNEL_SWAP.read_text()
SW_LINE = 'migrate Channel v1 -> v2 { quarantine "fax" }'
BARE_AND_QUALIFIED = swap(swap(OM, "  Unknown(String)\n}\n", "  Unknown(String)\n}\n" + M_LINE + "\n"),
                          "enum Channel {", V1_DECL + "enum Channel v2 {")
NOT_LAST = swap(OM, 'migrate Order v1 -> v2 { add note: String = "" }\n' + QM_LINE,
                'migrate Order v1 -> v2 { add note: String = "", map channel "app" -> Mobile }\n'
                "migrate Order v2 -> v3 { drop legacy: String }")
CTOR_ENUM = swap((DECODE_CTOR / "orders.beaml").read_text(),
                 "enum PaymentState { Authorized  Pending  Declined(DeclineReason)  Unknown(String) }\n",
                 "enum PaymentState v2 { Authorized  Pending  Declined(DeclineReason)  Unknown(String) }\n"
                 'migrate PaymentState v1 -> v2 { map "x" -> Authorized }\n')

# F5 (PF-08, PF-11, PF-06, PF-23, plan-review repair 9, RED decisions RF-*): one compile error per wrong form.
REJECTS = {
    "quarantine_no_field": (AMT, Q_LINE, "migrate Amount v1 -> v2 { quarantine nope }",
                            "migrate Amount v1 -> v2: quarantine nope names no field of Amount"),
    "quarantine_no_rule": (OM, QM_LINE, "migrate Order v2 -> v3 { quarantine order_id }",
                           "migrate Order v2 -> v3: quarantine order_id: the field order_id has no rule to fail "
                           "(no constructor, no ENUM LITERAL)"),
    "quarantine_owner_form": (OM, QM_LINE, "migrate Order v2 -> v3 { quarantine amount }",
                              "migrate Order v2 -> v3: quarantine amount: write the quarantine line in the MIGRATE STEP "
                              "of the constructor TYPE: type Amount v2 and migrate Amount v1 -> v2 "
                              "{ quarantine <parameter> } (QF-3 A)"),
    # DL-162 (supersedes RF-03): a quarantine line on an enum field names the literal.
    "quarantine_enum_field": (OM, QM_LINE, "migrate Order v2 -> v3 { quarantine channel }",
                              'migrate Order v2 -> v3: quarantine channel: a quarantine line on an enum field names the '
                              'literal: quarantine channel "<old literal>" (DL-162)'),
    "map_no_field": (OM, QM_LINE, 'migrate Order v2 -> v3 { map nope "app" -> Mobile }',
                     "migrate Order v2 -> v3: map nope names no field of Order"),
    "map_not_enum_field": (OM, QM_LINE, 'migrate Order v2 -> v3 { map order_id "app" -> Mobile }',
                           "migrate Order v2 -> v3: map order_id: the field order_id is no literal enum field"),
    "map_no_variant": (CH, M_LINE, 'migrate Channel v1 -> v2 { map "app" -> Tv }',
                       'migrate Channel v1 -> v2: map "app" -> Tv: Tv is no variant of Channel'),
    "map_keep_value_variant": (CH, M_LINE, 'migrate Channel v1 -> v2 { map "app" -> Unknown }',
                               'migrate Channel v1 -> v2: map "app" -> Unknown: Unknown carries a payload; map to a '
                               'variant without payload (QF-6 A)'),
    # DL-161: a fate line on a current literal is valid only when the literal moved to another variant.
    "map_current_literal": (CH, M_LINE, 'migrate Channel v1 -> v2 { map "web" -> Mobile }',
                            'migrate Channel v1 -> v2: map "web" -> Mobile: "web" is a current ENUM LITERAL of Channel '
                            'that keeps its variant; a fate line names a literal that left or moved (DL-161)'),
    "quarantine_current_literal": (CH, M_LINE, 'migrate Channel v1 -> v2 { quarantine "web" }',
                                   'migrate Channel v1 -> v2: quarantine "web": "web" is a current ENUM LITERAL of '
                                   'Channel that keeps its variant; a fate line names a literal that left or moved '
                                   '(DL-161)'),
    "map_current_literal_qualified": (OM, QM_LINE, 'migrate Order v2 -> v3 { map channel "web" -> Mobile }',
                                      'migrate Order v2 -> v3: map channel "web" -> Mobile: "web" is a current ENUM '
                                      'LITERAL of Channel that keeps its variant; a fate line names a literal that '
                                      'left or moved (DL-161)'),
    # DL-162: a map line and a quarantine line on one literal.
    "map_and_quarantine_bare": (CH, M_LINE, 'migrate Channel v1 -> v2 { map "app" -> Mobile, quarantine "app" }',
                                'migrate Channel v1 -> v2: "app" has a map line and a quarantine line; keep one '
                                '(DL-162)'),
    "map_and_quarantine_qualified": (OM, QM_LINE,
                                     'migrate Order v2 -> v3 { map channel "app" -> Mobile, quarantine channel "app" }',
                                     'migrate Order v2 -> v3: "app" of field channel has a map line and a quarantine '
                                     'line; keep one (DL-162)'),
    "bare_quarantine_in_record_step": (OM, QM_LINE, 'migrate Order v2 -> v3 { quarantine "app" }',
                                       'migrate Order v2 -> v3: a bare quarantine stands only in the MIGRATE STEP of '
                                       'an enum; write quarantine <field> "app"'),
    "quarantine_literal_not_enum_field": (OM, QM_LINE, 'migrate Order v2 -> v3 { quarantine order_id "app" }',
                                          "migrate Order v2 -> v3: quarantine order_id: the field order_id is no "
                                          "literal enum field"),
    # DL-155 (ruling by Fable on Q1): an enum chain needs its previous declaration; an old declaration needs its step.
    "enum_chain_without_old_declaration": (CH, V1_DECL, "", NO_V1_DECL[len("error: "):]),
    "old_declaration_without_step": (CH, M_LINE + "\n", "",
                                     "enum Channel v1 has no MIGRATE STEP to v2; add migrate Channel v1 -> v2 "
                                     "{ ... } or remove enum Channel v1 (DL-155)"),
    "map_enum_constructor": (CTOR_ENUM, None, None,
                             "migrate PaymentState v1 -> v2: map: PaymentState has an ENUM CONSTRUCTOR; map works on "
                             "ENUM LITERALS only (D041 open)"),
    "bare_map_in_record_step": (OM, QM_LINE, 'migrate Order v2 -> v3 { map "app" -> Mobile }',
                                'migrate Order v2 -> v3: a bare map stands only in the MIGRATE STEP of an enum; write '
                                'map <field> "app" -> Mobile'),
    "two_maps_one_literal_qualified": (OM, QM_LINE,
                                       'migrate Order v2 -> v3 { map channel "app" -> Mobile, map channel "app" -> Web }',
                                       'migrate Order v2 -> v3: two map lines name "app" of field channel'),
    "two_maps_one_literal_bare": (CH, M_LINE, 'migrate Channel v1 -> v2 { map "app" -> Mobile, map "app" -> Web }',
                                  'migrate Channel v1 -> v2: two map lines name "app"'),
    "two_fate_lines_one_field": (AMT, Q_LINE, "migrate Amount v1 -> v2 { quarantine value, quarantine value }",
                                 "migrate Amount v1 -> v2: two fate lines name the field value"),
    "bare_and_qualified_map_one_literal": (BARE_AND_QUALIFIED, None, None,
                                           'migrate Order v2 -> v3: map channel "app" -> Mobile: "app" has a map line '
                                           "in migrate Channel v1 -> v2 too; keep one"),
    "fate_not_in_last_step": (NOT_LAST, None, None,
                              "migrate Order v1 -> v2: a fate line stands only in the last MIGRATE STEP of Order (v3)"),
    "enum_step_add": (CH, M_LINE, 'migrate Channel v1 -> v2 { add label: String = "" }',
                      ENUM_STEP_ONLY),
    "enum_step_qualified_map": (CH, M_LINE, 'migrate Channel v1 -> v2 { map channel "app" -> Mobile }',
                                ENUM_STEP_ONLY),
}
# QF-6 A: a payload after the map target is a parse error.
PAYLOAD_PARSE = re.compile(r"(error: )?a map target takes no payload \(QF-6 A\) at byte \d+")
# fates-a1b (DL-172, plan "Repairs" O1, QB-2 default): a failed rule with no literal pattern is lifted by no line.
NO_LITERAL_HELP = ("  help: no fate line covers a failed rule that tests no parameter with a literal (QB-2 open); restore "
                   "the rule of fn %s that reads these records")
NESTED = sd.EXPERIMENT / "slice6" / "stored-elixir" / "nested.beaml"
NESTED_FAIL = sd.EXPERIMENT / "slice6" / "stored-elixir" / "nested-fail.jsonl"
ENUM_MARK_GAP = ("error: enum Channel v3 disagrees with its MIGRATE CHAIN: the last MIGRATE STEP is migrate Channel "
                 "v1 -> v2\n  help: the VERSION MARK and the MIGRATE CHAIN must agree; add migrate Channel v2 -> v3 "
                 "{ ... }, or write enum Channel v2 if no record of v3 exists")


class Fates(unittest.TestCase):
    maxDiff = None
    setUp = sds.Slice6DbStored.setUp
    compile = sds.Slice6DbStored.compile
    built = sd.Slice6Db.built
    snapshot = sds.Slice6DbStored.snapshot

    def orders(self, text):
        """An inline source as orders.beaml, so the module is Orders (P5: the module name comes from the stem)."""
        path = self.work / "inline" / str(next(self.dirs)) / "orders.beaml"
        path.parent.mkdir(parents=True)
        path.write_text(text)
        return path

    def run_stored(self, source, rows=(), responses=(), entries=()):
        """--stored with rows.jsonl, responses.jsonl and (DL-134) entries.jsonl beside it."""
        resp, rows_path = self.snapshot(rows, responses)
        entries_path = resp.parent / "entries.jsonl"
        if entries:
            entries_path.write_text("".join(json.dumps(e, separators=(",", ":")) + "\n" for e in entries))
            for e in entries:
                self.words.update(w for w in sds.leaves(e["value"]) if len(w) >= 5)
                self.words.update(e[k] for k in ("trace_id", "span_id"))
        code, stdout, stderr = self.compile(source, ["--stored", str(resp)])
        return code, stdout, stderr.strip().splitlines(), {"rows": rows_path, "resp": resp, "entries": entries_path}

    def rejects(self, source, extra=sd.STORED):
        """Exit, stdout and stderr; a leading `error: ` is dropped (the derive_versions texts print without it)."""
        code, stdout, stderr = self.compile(source, extra)
        text = stderr.strip()
        return code, stdout, text[len("error: "):] if text.startswith("error: ") else text

    def assert_fated(self, source, fates, errors, rows_line=None, **kw):
        """a1: the block is lifted, the fate lines print, the a1 stop line follows (exit 1, no module)."""
        code, stdout, got, _ = self.run_stored(source, **kw)
        self.assertEqual((1, "", fates + errors), (code, stdout, told(got)), "\n".join(got))
        counts = [i for i, l in enumerate(got) if l.startswith("rows: ")]
        if counts:  # PF-13: the fate lines stand before the rows count line; PF-14: a quarantined row is checked.
            self.assertEqual((rows_line or got[counts[0]], True), (got[counts[0]], got.index(fates[0]) < counts[0]),
                             "\n".join(got))

    def assert_block(self, source, block, **kw):
        code, stdout, got, paths = self.run_stored(source, **kw)
        lines = block(paths)
        self.assertEqual((1, "", lines), (code, stdout, told(got)), "\n".join(got))
        return got

    # F1 to F4: the new forms build (an empty store: no stored value hits a fate line).

    def test_F1_quarantine_line_builds(self):
        self.built(AMOUNT_V2)

    def test_F2_enum_version_and_bare_map_build(self):
        self.built(CHANNEL_V2)
        with self.subTest("two literals, two map lines"):  # RF-04: two map lines on two literals are valid
            self.built(self.orders(swap(CH, M_LINE, 'migrate Channel v1 -> v2 { map "app" -> Mobile, map "tablet" -> Web }')))

    def test_F3_qualified_map_builds(self):
        self.built(ORDER_MAP)

    def test_F4_fate_only_step_is_valid(self):
        with self.subTest("record TYPE step with one fate line"):
            self.built(ORDER_MAP)
        with self.subTest("constructor TYPE step with one fate line"):
            self.built(AMOUNT_V2)
        with self.subTest("an empty step names the fate lines"):  # PF-05
            self.assertEqual((1, "", "migrate Order v2 -> v3: a MIGRATE STEP needs at least one rename, add, drop or "
                                     "fate line"), self.rejects(swap(OM, QM_LINE, "migrate Order v2 -> v3 { }")))

    # F5: one compile error per wrong form.

    def test_F5_rejects(self):
        for name, (base, old, new, message) in REJECTS.items():
            with self.subTest(name):
                source = base if old is None else swap(base, old, new)
                extra = sd.EMPTY if base is CTOR_ENUM else sd.STORED
                self.assertEqual((1, "", message), self.rejects(source, extra))
        with self.subTest("map_payload_parse_error"):
            code, stdout, text = self.compile(swap(CH, M_LINE, 'migrate Channel v1 -> v2 { map "app" -> Unknown("x") }'))
            self.assertEqual((1, "", True), (code, stdout, PAYLOAD_PARSE.fullmatch(text.strip()) is not None), text)

    # F6 (PF-09): redact and retire parse, and the checker says their meaning waits.

    def test_F6_redact_and_retire_parse_and_wait(self):
        cases = {
            "redact": ("migrate Order v2 -> v3 { redact order_id }",
                       "migrate Order v2 -> v3: redact order_id: the meaning for stored values is not built yet "
                       "(fates-b, QF-9)"),
            "retire": ("migrate Order v2 -> v3 { retire order_id keep 30 days }",
                       "migrate Order v2 -> v3: retire order_id keep 30 days: the meaning for stored values waits on "
                       "M5 (QF-4)"),
        }
        for name, (line, message) in cases.items():
            with self.subTest(name):
                self.assertEqual((1, "", message), self.rejects(swap(OM, QM_LINE, line)))

    # F7, F7b (ruling on O1): a step with a fate line is never a DEAD LINE; --remove-dead keeps it.

    def test_F7_no_dead_line_for_a_fate_step(self):
        rows = [row(WIRE1)]
        code, _, got, _ = self.run_stored(swap(AMT, Q_LINE, "migrate Amount v1 -> v2 { drop note: String }"), rows=rows)
        self.assertIn("warning: DEAD LINE: migrate Amount v1 -> v2", got, "setup: the W2 rule must see a nested step")
        for name, source in (("amount_v2", AMOUNT_V2), ("channel_v2", CHANNEL_V2)):
            with self.subTest(name):
                code, stdout, got, _ = self.run_stored(source, rows=rows)
                self.assertEqual((0, True, [counted(1, 1, 0)]), (code, "defmodule Orders do" in stdout, got))
        with self.subTest("order_map"):  # RED repair R-3: Order v3 rows only, so the W2 rule fires on v1 -> v2
            v3 = [row(dict(WIRE1, note=""), ORDER_V3)]
            code, stdout, got, _ = self.run_stored(ORDER_MAP, rows=v3)
            self.assertEqual((0, True, True, []), (
                code, "defmodule Orders do" in stdout, "warning: DEAD LINE: migrate Order v1 -> v2" in got,
                [l for l in got if l.startswith("warning: DEAD LINE: " + QM_STEP)]), "\n".join(got))

    def test_F7b_remove_dead_keeps_a_fate_step(self):
        with self.subTest("order_map: the dead v1 -> v2 step goes, the fate step stays"):  # RED repair R-3
            resp, _ = self.snapshot([row(dict(WIRE1, note=""), ORDER_V3)])
            path = self.work / "dead" / "order_map" / "orders.beaml"
            path.parent.mkdir(parents=True)
            path.write_text(OM)
            code, _, stderr = self.compile(path, ["--stored", str(resp), "--remove-dead", "--assume-complete"])
            after = path.read_text()
            self.assertEqual((0, False, True), (code, "migrate Order v1 -> v2" in after, QM_LINE in after), stderr)
        cases = {"control drop step": (swap(AMT, Q_LINE, "migrate Amount v1 -> v2 { drop note: String }"), False),
                 "quarantine step": (AMT, True)}
        for name, (text, kept) in cases.items():
            with self.subTest(name):
                resp, _ = self.snapshot([row(WIRE1)])
                path = self.work / "dead" / name.replace(" ", "_") / "orders.beaml"
                path.parent.mkdir(parents=True)
                path.write_text(text)
                code, _, stderr = self.compile(path, ["--stored", str(resp), "--remove-dead", "--assume-complete"])
                after = path.read_text()
                step = text.splitlines()[[l.startswith(Q_STEP) for l in text.splitlines()].index(True)]
                self.assertEqual((0, kept, kept), (code, step in after, after == text), stderr)

    # F8: the enum VERSION MARK agrees with its chain (the TYPE text with `enum`).

    def test_F8_enum_mark_disagrees_with_its_chain(self):
        code, stdout, stderr = self.compile(swap(CH, "enum Channel v2 {", "enum Channel v3 {"))
        self.assertEqual((1, "", ENUM_MARK_GAP), (code, stdout, stderr.strip()))

    # S1 to S1f (DL-102, DL-155, PF-12): quarantine over rows, RESPONSE RECORDS and ENTRY RECORDS.

    def test_S1_quarantine_lifts_the_constructor_block_over_rows(self):
        with self.subTest("one row"):
            self.assert_fated(AMOUNT_V2, [fate(1, "ROW", "table records", "quarantined", Q_STEP, "quarantine value")],
                              [NOT_BUILT_Q], rows_line=counted(2, 2, 0), rows=[row(WIRE1), row(ZERO)])
        with self.subTest("two rows (RED repair R-2)"):
            self.assert_fated(AMOUNT_V2, [fate(2, "ROW", "table records", "quarantined", Q_STEP, "quarantine value")],
                              [NOT_BUILT_Q], rows_line=counted(3, 3, 0), rows=[row(ZERO), row(WIRE1), row(ZERO2)])
        with self.subTest("rows and RESPONSE RECORDS (RED repair R-2)"):
            rec = db_record("orders.list", sds.list_items(WIRE1, ZERO), sd.LIST_TYPE, {})
            code, stdout, got, _ = self.run_stored(AMOUNT_V2, rows=[row(ZERO2)], responses=[rec])
            fates = {fate(1, "ROW", "table records", "quarantined", Q_STEP, "quarantine value"),
                     fate(1, "RESPONSE RECORD", "operation orders.list", "quarantined", Q_STEP, "quarantine value")}
            lines = told(got)
            self.assertEqual((1, "", fates, [NOT_BUILT_Q], 3), (code, stdout, set(lines[:-1]), lines[-1:], len(lines)),
                             "\n".join(got))

    def test_S1b_control_without_the_line_blocks_with_the_version_help(self):
        cases = {
            "rows_value": ({"rows": [row(WIRE1), row(ZERO)]}, lambda p: ctor_block(
                "table records", "ROW", "Order", "Amount", "amount", "BadAmount", p["rows"], 2)
                + [help_q("Amount", 1, "value")]),
            "rows_currency": ({"rows": [row(NO_CURRENCY)]}, lambda p: ctor_block(
                "table records", "ROW", "Order", "Amount", "amount", "BadAmount", p["rows"], 1)
                + [help_q("Amount", 1, "currency")]),
            "response_record": ({"responses": [db_record("orders.list", sds.list_items(WIRE1, ZERO), sd.LIST_TYPE, {})]},
                                lambda p: ctor_block("operation orders.list", "RESPONSE RECORD", "Order", "Amount",
                                                     "amount", "BadAmount", p["resp"], 1)
                                + [help_q("Amount", 1, "value")]),
            "entry_record": ({"entries": [entry(FORM_ZERO)]}, lambda p: ctor_block(
                "operation ui.place", "ENTRY RECORD", "PlaceForm", "Amount", "amount", "BadAmount", p["entries"], 1)
                + [help_q("Amount", 1, "value")]),
        }
        for name, (kw, block) in cases.items():
            with self.subTest(name):
                self.assert_block(STRICTER_V1, block, **kw)

    def test_S1c_quarantine_over_response_records(self):
        rec = db_record("orders.list", sds.list_items(WIRE1, ZERO), sd.LIST_TYPE, {})
        with self.subTest("one failing item"):
            self.assert_fated(AMOUNT_V2, [fate(1, "RESPONSE RECORD", "operation orders.list", "quarantined", Q_STEP,
                                               "quarantine value")], [NOT_BUILT_Q], responses=[rec])
        with self.subTest("two failing items count once (PF-17, RED repair R-2)"):
            two = db_record("orders.list", sds.list_items(ZERO, WIRE1, ZERO2), sd.LIST_TYPE, {})
            self.assert_fated(AMOUNT_V2, [fate(1, "RESPONSE RECORD", "operation orders.list", "quarantined", Q_STEP,
                                               "quarantine value")], [NOT_BUILT_Q], responses=[two])
        with self.subTest("two records"):
            two = db_record("orders.list", sds.list_items(ZERO2), sd.LIST_TYPE, {})
            self.assert_fated(AMOUNT_V2, [fate(2, "RESPONSE RECORD", "operation orders.list", "quarantined", Q_STEP,
                                               "quarantine value")], [NOT_BUILT_Q], responses=[rec, two])

    def test_S1d_quarantine_over_entry_records(self):
        self.assert_fated(AMOUNT_V2, [fate(1, "ENTRY RECORD", "operation ui.place", "quarantined", Q_STEP,
                                           "quarantine value")], [NOT_BUILT_Q], entries=[entry(FORM_ZERO)])

    def test_S1e_line_lifts_only_its_type(self):
        tip_ok = {"value": "1.00", "currency": "EUR"}
        rows = [row({"order_id": "order-zero", "amount": {"value": "0", "currency": "EUR"}, "tip": tip_ok,
                     "channel": "web"}, TIP_ORDER),
                row({"order_id": "order-tip-zero", "amount": EUR, "tip": {"value": "0", "currency": "EUR"},
                     "channel": "web"}, TIP_ORDER)]
        code, stdout, got, paths = self.run_stored(TWO_CTOR, rows=rows)
        block = ctor_block("table records", "ROW", "Order", "Tip", "tip", "BadTip", paths["rows"], 2) + [
            help_q("Tip", 1, "value")]
        lines = told(got)
        self.assertEqual((1, "", True, []), (code, stdout, any(lines[i:i + 3] == block for i in range(len(lines))),
                                             [l for l in lines if "constructor of Amount" in l]), "\n".join(got))

    def test_S1f_a_quarantined_value_with_a_lost_literal_still_blocks(self):
        code, stdout, got, paths = self.run_stored(AMOUNT_V2, rows=[row(BOTH)])
        block = literal_block("Order", "ROW", "table records", paths["rows"], 1) + [help_m("Channel", 1)]
        lines = told(got)
        self.assertEqual((1, "", True), (code, stdout, any(lines[i:i + 3] == block for i in range(len(lines)))),
                         "\n".join(got))

    # S1g to S1j (fates-a1b, DL-172): a quarantine line lifts only a failed clause that tests its field (PB-03).

    def test_S1g_quarantine_value_does_not_lift_a_currency_rule(self):
        """AC 5: NO_CURRENCY fails the clause `_, ""` (currency); `quarantine value` does not lift it."""
        self.assert_block(AMOUNT_V2, lambda p: ctor_block("table records", "ROW", "Order", "Amount", "amount", "BadAmount",
                                                          p["rows"], 1) + [help_q("Amount", 2, "currency")],
                          rows=[row(NO_CURRENCY)])

    def test_S1h_two_quarantine_lines_count_apart(self):
        """AC 6: two quarantine lines on one constructor TYPE are valid (PF-11 retired); each counts its own rows."""
        text = swap(AMT, Q_LINE, "migrate Amount v1 -> v2 { quarantine value, quarantine currency }")
        self.assertNotEqual(AMT, text, "setup: the quarantine line of amount_v2 changed")
        code, stdout, got, _ = self.run_stored(self.orders(text), rows=[row(ZERO), row(NO_CURRENCY)])
        fates = {fate(1, "ROW", "table records", "quarantined", Q_STEP, "quarantine value"),
                 fate(1, "ROW", "table records", "quarantined", Q_STEP, "quarantine currency")}
        lines = told(got)
        self.assertEqual((1, "", fates, [NOT_BUILT_Q], 3), (code, stdout, set(lines[:-1]), lines[-1:], len(lines)),
                         "\n".join(got))

    def test_S1i_first_matching_clause_decides(self):
        """AC 7: {"0", ""} fails the first matching clause `"0", _` (value), so `quarantine currency` does not lift it."""
        text = swap(AMT, Q_LINE, "migrate Amount v1 -> v2 { quarantine currency }")
        both = dict(WIRE1, order_id="order-both-bad", amount={"value": "0", "currency": ""})
        with self.subTest("value clause first: blocks"):
            self.assert_block(self.orders(text), lambda p: ctor_block(
                "table records", "ROW", "Order", "Amount", "amount", "BadAmount", p["rows"], 1)
                + [help_q("Amount", 2, "value")], rows=[row(both)])
        with self.subTest("guard: the currency clause is lifted"):
            self.assert_fated(self.orders(text), [fate(1, "ROW", "table records", "quarantined", Q_STEP,
                                                       "quarantine currency")], [NOT_BUILT_Q], rows=[row(NO_CURRENCY)])

    def test_S1k_either_tested_parameter_lifts(self):
        """fates-a1b TEST, QB-1 built default PB-03 (open): a clause `"0", ""` tests both parameters; either line lifts."""
        clause = 'fn Amount "0",           _                -> Amount ! BadAmount = BadAmount {}'
        both = dict(WIRE1, order_id="order-both-bad", amount={"value": "0", "currency": ""})
        for param in ("value", "currency"):
            with self.subTest("quarantine " + param):
                text = swap(swap(AMT, clause, clause.replace('_     ', '""    ', 1)), Q_LINE,
                            "migrate Amount v1 -> v2 { quarantine %s }" % param)
                self.assert_fated(self.orders(text), [fate(1, "ROW", "table records", "quarantined", Q_STEP,
                                                           "quarantine " + param)], [NOT_BUILT_Q], rows=[row(both)])

    def test_S1j_a_rule_without_a_literal_is_not_lifted(self):
        """Plan "Repairs" O1 (QB-2 default): nested.beaml `fn Amount value, c` fails in Code; no line names a tested field."""
        source = NESTED.read_text()
        old = "type Amount { value: String currency: String }\n"
        for param in ("value", "currency"):
            with self.subTest("quarantine " + param):
                text = swap(source, old, "type Amount v2 { value: String currency: String }\n"
                            "migrate Amount v1 -> v2 { quarantine %s }\n" % param)
                code, stdout, stderr = self.compile(self.orders(text), ["--stored", str(NESTED_FAIL)])
                self.assertEqual((1, "", ["error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize "
                                          "fails the constructor of Amount for field amount with NoCurrency",
                                          "  record source: %s:1 (line 1)" % NESTED_FAIL, NO_LITERAL_HELP % "Amount"]),
                                 (code, stdout, told(stderr.strip().splitlines())), stderr)

    # S2 to S2c (DL-122, DL-142, DL-155): map over lost ENUM LITERALS.

    def test_S2_map_lifts_the_lost_literal_block(self):
        with self.subTest("bare map in the enum step"):
            self.assert_fated(CHANNEL_V2, [fate(1, "ROW", "table records", "mapped", M_STEP, 'map "app" -> Mobile')],
                              [NOT_BUILT_M], rows_line=counted(2, 2, 0), rows=[row(WIRE1), row(APP)])
        with self.subTest("field-qualified map in the owner chain"):
            self.assert_fated(ORDER_MAP, [fate(1, "ROW", "table records", "mapped", QM_STEP,
                                               'map channel "app" -> Mobile')], [NOT_BUILT_M], rows=[row(APP)])

    def test_S2d_map_lifts_only_its_literal(self):
        """RED repair R-1: a lost "tablet" beside the mapped "app" still blocks; the map line counts 1."""
        code, stdout, got, paths = self.run_stored(CHANNEL_V2, rows=[row(APP), row(TABLET)])
        expected = ([fate(1, "ROW", "table records", "mapped", M_STEP, 'map "app" -> Mobile')]
                    + literal_block("Order", "ROW", "table records", paths["rows"], 2) + [help_m("Channel", 2)])
        self.assertEqual((1, "", expected), (code, stdout, told(got)), "\n".join(got))

    def test_S2b_control_without_map_blocks_with_the_version_help(self):
        cases = {
            "rows": ({"rows": [row(APP)]},
                     lambda p: literal_block("Order", "ROW", "table records", p["rows"], 1) + [help_m("Channel", 1)]),
            "entry_record": ({"entries": [entry(FORM_APP)]},
                             lambda p: literal_block("PlaceForm", "ENTRY RECORD", "operation ui.place", p["entries"], 1)
                             + [help_m("Channel", 1)]),
        }
        for name, (kw, block) in cases.items():
            with self.subTest(name):
                got = self.assert_block(CHANNEL_V1, block, **kw)
                self.assertNotIn('"app"', "\n".join(got), "DL-124: the help holds no stored String")

    def test_S2c_kept_value_is_neither_mapped_nor_blocked(self):
        kept = row(APP, unknown_fields=["channel"])
        with self.subTest("a kept and a lost value: only the lost one is mapped"):
            self.assert_fated(CHANNEL_V2, [fate(1, "ROW", "table records", "mapped", M_STEP, 'map "app" -> Mobile')],
                              [NOT_BUILT_M], rows_line=counted(2, 2, 0), rows=[kept, row(APP)])
        with self.subTest("a kept value alone"):
            code, stdout, got, _ = self.run_stored(CHANNEL_V2, rows=[row(APP, unknown_fields=["channel"])])
            self.assertEqual((0, True, [counted(1, 1, 0)]), (code, "defmodule Orders do" in stdout, got))

    # S3, S3b (DL-155 gate): affected values without the next version and a fate line block; none affected is free.

    def test_S3_gate_affected_values_need_the_next_version(self):
        cases = {
            "no mark": (STRICTER_V1, [row(ZERO)], lambda p: ctor_block(
                "table records", "ROW", "Order", "Amount", "amount", "BadAmount", p["rows"], 1)
                + [help_q("Amount", 1, "value")]),
            "type mark without a step": (swap(AMT, Q_LINE + "\n", ""), [row(ZERO)], lambda p: ctor_block(
                "table records", "ROW", "Order", "Amount", "amount", "BadAmount", p["rows"], 1)
                + [help_q("Amount", 2, "value")]),
            "enum mark without a step": (swap(swap(CH, M_LINE + "\n", ""), V1_DECL, ""), [row(APP)], lambda p: literal_block(
                "Order", "ROW", "table records", p["rows"], 1) + [help_m("Channel", 2)]),
        }
        for name, (source, rows, block) in cases.items():
            with self.subTest(name):
                self.assert_block(source, block, rows=rows)

    def test_S3b_gate_without_affected_values_is_free(self):
        for name, source in (("stricter_v1", STRICTER_V1), ("channel_v1", CHANNEL_V1), ("amount_v2", AMOUNT_V2),
                             ("channel_v2", CHANNEL_V2)):
            with self.subTest(name):
                code, stdout, got, _ = self.run_stored(source, rows=[row(WIRE1)])
                self.assertEqual((0, True, [counted(1, 1, 0)]), (code, "defmodule Orders do" in stdout, got))

    # S4 (DL-124): no fate line, help or a1 stop line holds a stored String, a row id or a trace id.

    def test_S4_no_stored_value_in_any_text(self):
        list_rec = db_record("orders.list", sds.list_items(WIRE1, ZERO), sd.LIST_TYPE, {})
        cases = {
            "rows_quarantine": (AMOUNT_V2, {"rows": [row(WIRE1), row(ZERO)]}, "fate: 1 stored ROW"),
            "response_quarantine": (AMOUNT_V2, {"responses": [list_rec]}, "fate: 1 stored RESPONSE RECORD"),
            "entry_quarantine": (AMOUNT_V2, {"entries": [entry(FORM_ZERO)]}, "fate: 1 stored ENTRY RECORD"),
            "rows_map": (CHANNEL_V2, {"rows": [row(APP)]}, "fate: 1 stored ROW"),
            "rows_block": (STRICTER_V1, {"rows": [row(ZERO)]}, "help: declare the next TYPE VERSION"),
            "literal_block": (CHANNEL_V1, {"rows": [row(APP)]}, "help: declare the next TYPE VERSION"),
        }
        for name, (source, kw, anchor) in cases.items():
            with self.subTest(name):
                _, _, got, _ = self.run_stored(source, **kw)
                text = "\n".join(got)
                # The anchor must stand in stderr, so a parse error cannot pass this test.
                # RED repair R-4: stored Strings under 5 chars that are no source text of these lines.
                short = [w for w in ('"0"', "EUR", "tv", "order-") if w in text]
                self.assertEqual((True, [], []), (anchor in text, [w for w in sorted(self.words) if w in text], short),
                                 text)

    # S5 (plan repair 5): the help where no fates-a line lifts the block.

    def test_S5_help_where_no_fate_line_lifts_the_block(self):
        nomatch, fail = DECODE_CTOR / "stored-nomatch.jsonl", DECODE / "stored-fail.jsonl"
        with self.subTest("ENUM CONSTRUCTOR, no signature (D041 open)"):
            code, stdout, stderr = self.compile(DECODE_CTOR / "orders.beaml", ["--stored", str(nomatch)])
            self.assertEqual((1, "", ["error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize "
                                      "matches no signature of PaymentState for field state",
                                      "  record source: %s:2 (line 2)" % nomatch, ENUM_CTOR_HELP % "PaymentState"]),
                             (code, stdout, told(stderr.strip().splitlines())))
        with self.subTest("constructor TYPE, no signature (a decode fault)"):
            string_amount = dict(WIRE1, order_id="order-string", amount="12.50")
            self.assert_block(STRICTER_V1, lambda p: [
                "error: TYPE Order: 1 stored ROW of table records matches no signature of Amount for field amount",
                "  record source: %s:1 (line 1)" % p["rows"], NO_SIGNATURE_HELP % ("Amount", "Amount")],
                rows=[row(string_amount)])
        with self.subTest("guard: no variant keeps the DL-102 help"):
            code, stdout, stderr = self.compile(DECODE / "orders.beaml", ["--stored", str(fail)])
            self.assertEqual((1, "", ["error: TYPE Payment: 2 stored RESPONSE RECORDS of operation payments.authorize "
                                      "have no variant of PaymentState for field state",
                                      "  record source: %s:2 (line 2)" % fail, OLD_DL102_HELP % "Payment"]),
                             (code, stdout, told(stderr.strip().splitlines())))

    def test_S5b_quarantine_lifts_no_decode_or_shape_fault(self):
        """RED repair R-1: under amount_v2 a no-signature or shape fault still blocks, with no fate line."""
        with self.subTest("no signature (a decode fault)"):
            self.assert_block(AMOUNT_V2, lambda p: [
                "error: TYPE Order: 1 stored ROW of table records matches no signature of Amount for field amount",
                "  record source: %s:1 (line 1)" % p["rows"], NO_SIGNATURE_HELP % ("Amount", "Amount")],
                rows=[row(dict(WIRE1, order_id="order-string", amount="12.50"))])
        with self.subTest("no String value (a shape fault)"):
            self.assert_block(AMOUNT_V2, lambda p: [
                "error: TYPE Order: 1 stored ROW of table records has no String value for field order_id",
                "  record source: %s:1 (line 1)" % p["rows"], OLD_DL102_HELP % "Order"],
                rows=[row(dict(ZERO, order_id=7))])

    # W1 to W5 (DL-140, DL-161): a literal that moved to another variant blocks until a fate line names it.

    def moved(self, literal, old, new, source, lines):
        return (['error: TYPE Order v1: %d stored ROW%s of table records %s the ENUM LITERAL "%s" of field channel, '
                 "which was %s in enum Channel v1 and is %s now (DL-140)"
                 % (len(lines), "" if len(lines) == 1 else "S", "has" if len(lines) == 1 else "have", literal, old, new)]
                + ["  record source: %s:%d (line %d)" % (source, n, n) for n in lines]
                + ['  help: declare the fate of "%s" in migrate Channel v1 -> v2 (DL-161): map "%s" -> <Variant> or '
                   'quarantine "%s"' % (literal, literal, literal)])

    def test_W1_swap_blocks_and_names_both_literals(self):
        code, stdout, got, paths = self.run_stored(CHANNEL_SWAP, rows=[row(WEB_ROW), row(APP), row(WIRE1)])
        expected = (self.moved("app", "App", "Web", paths["rows"], [2])
                    + self.moved("web", "Web", "App", paths["rows"], [1, 3]))
        self.assertEqual((1, "", expected), (code, stdout, told(got)), "\n".join(got))

    def test_W2_swap_with_both_fate_lines_is_lifted(self):
        rows = [row(WEB_ROW), row(APP)]
        with self.subTest("two map lines"):
            text = swap(SW, SW_LINE, 'migrate Channel v1 -> v2 { map "web" -> App, map "app" -> Web, quarantine "fax" }')
            self.assert_fated(self.orders(text), [
                fate(1, "ROW", "table records", "mapped", M_STEP, 'map "app" -> Web'),
                fate(1, "ROW", "table records", "mapped", M_STEP, 'map "web" -> App')], [NOT_BUILT_M],
                rows_line=counted(2, 2, 0), rows=rows)
        with self.subTest("two quarantine lines (DL-162)"):
            text = swap(SW, SW_LINE, 'migrate Channel v1 -> v2 { quarantine "web", quarantine "app", quarantine "fax" }')
            self.assert_fated(self.orders(text), [
                fate(1, "ROW", "table records", "quarantined", M_STEP, 'quarantine "app"'),
                fate(1, "ROW", "table records", "quarantined", M_STEP, 'quarantine "web"')], [NOT_BUILT_Q],
                rows_line=counted(2, 2, 0), rows=rows)
        with self.subTest("one line only: the other literal still blocks"):
            text = swap(SW, SW_LINE, 'migrate Channel v1 -> v2 { map "web" -> App, quarantine "fax" }')
            code, stdout, got, paths = self.run_stored(self.orders(text), rows=rows)
            expected = ([fate(1, "ROW", "table records", "mapped", M_STEP, 'map "web" -> App')]
                        + self.moved("app", "App", "Web", paths["rows"], [2]))
            self.assertEqual((1, "", expected), (code, stdout, told(got)), "\n".join(got))

    def test_W3_swap_without_stored_values_is_free(self):
        """DL-155 gate: no stored value of the field, no block; the fate step is no DEAD LINE."""
        with self.subTest("no rows"):
            code, stdout, got, _ = self.run_stored(CHANNEL_SWAP)
            self.assertEqual((0, True, [counted(0, 0, 0)]), (code, "defmodule Orders do" in stdout, got))
        with self.subTest("a kept value only"):
            kept = row(dict(WIRE1, channel="tv"), unknown_fields=["channel"])  # kept, no literal now: no DL-103 note
            code, stdout, got, _ = self.run_stored(CHANNEL_SWAP, rows=[kept])
            self.assertEqual((0, True, [counted(1, 1, 0)]), (code, "defmodule Orders do" in stdout, got))

    def test_W4_the_previous_table_comes_from_the_previous_declaration(self):
        """DL-161: without enum Channel v1 in the source the swap check cannot run; the build says so."""
        old = 'enum Channel v1 {\n  Web = "web"\n  App = "app"\n  Fax = "fax"\n  Unknown(String)\n}\n'
        code, stdout, stderr = self.compile(self.orders(swap(SW, old, "")))
        self.assertEqual((1, "", NO_V1_DECL), (code, stdout, stderr.strip()))
        with self.subTest("the old table decides: no swap when v1 had the same literals"):
            same = swap(SW, old, 'enum Channel v1 {\n  Web = "app"\n  App = "web"\n  Fax = "fax"\n  Unknown(String)\n}\n')
            code, stdout, got, _ = self.run_stored(self.orders(same), rows=[row(WEB_ROW), row(APP)])
            self.assertEqual((0, True, [counted(2, 2, 0)]), (code, "defmodule Orders do" in stdout, got))

    # Q1 to Q4 (DL-162): quarantine parks a lost ENUM LITERAL.

    def test_Q1_bare_quarantine_parks_a_lost_literal(self):
        text = swap(CH, M_LINE, 'migrate Channel v1 -> v2 { quarantine "app" }')
        with self.subTest("rows"):
            self.assert_fated(self.orders(text), [fate(1, "ROW", "table records", "quarantined", M_STEP,
                                                       'quarantine "app"')], [NOT_BUILT_Q],
                              rows_line=counted(2, 2, 0), rows=[row(WIRE1), row(APP)])
        with self.subTest("ENTRY RECORDS"):
            self.assert_fated(self.orders(text), [fate(1, "ENTRY RECORD", "operation ui.place", "quarantined", M_STEP,
                                                       'quarantine "app"')], [NOT_BUILT_Q], entries=[entry(FORM_APP)])

    def test_Q2_qualified_quarantine_parks_a_lost_literal(self):
        text = swap(OM, QM_LINE, 'migrate Order v2 -> v3 { quarantine channel "app" }')
        self.assert_fated(self.orders(text), [fate(1, "ROW", "table records", "quarantined", QM_STEP,
                                                   'quarantine channel "app"')], [NOT_BUILT_Q], rows=[row(APP)])

    def test_Q3_quarantine_of_one_literal_lifts_only_that_literal(self):
        text = swap(CH, M_LINE, 'migrate Channel v1 -> v2 { quarantine "app" }')
        code, stdout, got, paths = self.run_stored(self.orders(text), rows=[row(APP), row(TABLET)])
        expected = ([fate(1, "ROW", "table records", "quarantined", M_STEP, 'quarantine "app"')]
                    + literal_block("Order", "ROW", "table records", paths["rows"], 2) + [help_m("Channel", 2)])
        self.assertEqual((1, "", expected), (code, stdout, told(got)), "\n".join(got))

    def test_Q4_quarantine_and_map_lines_print_both_stop_lines(self):
        text = swap(CH, M_LINE, 'migrate Channel v1 -> v2 { map "app" -> Mobile, quarantine "tablet" }')
        self.assert_fated(self.orders(text), [
            fate(1, "ROW", "table records", "mapped", M_STEP, 'map "app" -> Mobile'),
            fate(1, "ROW", "table records", "quarantined", M_STEP, 'quarantine "tablet"')], [NOT_BUILT_Q, NOT_BUILT_M],
            rows=[row(APP), row(TABLET)])


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
