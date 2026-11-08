# fmt layout (DL-148): GREEN output

By: Opus (fmt-layout, GREEN). Date: 2026-11-08. Base: HEAD 7638b75a plus the working tree. Compiler change only in
`experiments/0001-syntax-to-beam/src/main.rs` (`fn bodies` new, `fn aligned` rewritten, `SignatureLine.end`, the
`changed` count of `fmt_file`). Codegen is not touched.

## Result

| Test file | Tests | Result |
|---|---|---|
| slice6_fmt_test.py | 30 | OK |
| slice5_syntax_test.py (PIN) | 60 | OK |
| slice6_pipe_test.py (EFFECT_OUTPUTS) | 12 | OK |
| slice6_host_struct_test.py (BYTE_GUARD) | 3 | OK |
| slice6_db_test.py (P4_BASE N13) | 16 | 6 subtest failures: N15 (5 fixtures), N15b |
| slice6_entry_test.py (BASE) | 20 | 3 failures: n11 (2 fixtures), n11b |
| slice6_multi_test.py (BASE) | 14 | 2 failures: n11, n11b |
| slice6_redacted_failure_test.py | 8 | 26 subtest failures: `fmt_keeps_every_fixture` |
| slice6_effect_reach_test.py (byte-guard.json) | 8 | 1 subtest failure: row `slice6/fmt/header.formatted.beaml` |
| record_v3_test.py | all | OK (1 skipped) |
| cargo test (0001) | 22 + 14 | OK |
| cargo clippy -D warnings, cargo fmt --check | | clean |

## STOP: one byte pin moves, and 37 fmt fixed-point subtests fail

→ byte-guard.json row `experiments/0004-generated-replay/slice6/fmt/header.formatted.beaml` (sha256 82bb06ec...) moves
⠀⠀↳ cause: the expected file changes by DL-148 (signature line joins the table)
⠀⠀↳ compiled diff: only two `# beaml-declaration-v1 grade` byte offsets (280 319 -> 280 335, 320 359 -> 336 391)
⠀⠀↳ codegen unchanged; no other pin moves (PIN, EFFECT_OUTPUTS, BYTE_GUARD, BASE, P4_BASE pass)
→ Fixed-point tests (db N15/N15b, entry n11/n11b, multi n11/n11b, redacted_failure) fail with exit 0 and a new layout
⠀⠀↳ cause: their fixtures hold multi-field TYPES and ENUMS on one line, and unaligned blocks
⠀⠀↳ not changed here: reformatting those fixtures moves their declaration offsets (see notes.md Q1)

## 0005 sources

`beaml-spike fmt` on `app/beaml/orders.beaml` and `app/beaml/variants/{no_place,note_v2,stricter}/orders.beaml`:
exit 0 each, a second run prints nothing (idempotent). Applied in place.

Generated Elixir check (no DB run: `run.py run` needs Postgres; the gen step was reproduced with the retained snapshot
`results/20261108T003757953791Z/stored-orders/responses.jsonl` and `stored-note_v2` for note_v2):
→ HEAD `orders.beaml` reproduces the committed `app/lib/generated/orders.ex` byte for byte
→ working-tree source before fmt vs after fmt: 64 diff lines, all `# beaml-declaration-v1` offset lines
→ with the offsets masked: identical for orders.beaml and all three variants
→ `git diff --stat app/lib/generated`: empty (not regenerated); a regenerate moves only the offset comment lines
⠀⠀↳ the OWNER edit already in the working tree (before this step) moves them too

note_v2: `type Note v2 {` becomes `type Note {` by the existing DL-104 rule (D6B-43: a chain from v1 implies v2).

### Diff of app/beaml/orders.beaml against HEAD (includes the OWNER's uncommitted edit of the Amount block)

```diff
diff --git a/experiments/0005-prototype-fullstack/app/beaml/orders.beaml b/experiments/0005-prototype-fullstack/app/beaml/orders.beaml
index f094e5c6..9dc3fdaa 100644
--- a/experiments/0005-prototype-fullstack/app/beaml/orders.beaml
+++ b/experiments/0005-prototype-fullstack/app/beaml/orders.beaml
@@ -1,14 +1,30 @@
 // EXPERIMENT 0005: the PROTOTYPE domain. BEAML owns the TYPES, the entries, the flow and the rows.
 type BadAmount {}
-type Amount { value: String currency: String }
-fn Amount value: String, currency: String -> Amount ! BadAmount
-fn Amount _,     ""       -> Amount ! BadAmount = BadAmount {}
-fn Amount value, currency -> Amount ! BadAmount = Amount { value: value, currency: currency }
-
-enum Channel { Web = "web"  App = "app"  Unknown(String) }
+type Amount {
+  value: String
+  currency: String
+}
 
-type PlaceForm { order_id: String amount: Amount channel: Channel }
-type Order { order_id: String amount: Amount channel: Channel }
+fn Amount value: String, currency: String -> Amount ! BadAmount
+fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
+fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
+
+enum Channel {
+  Web = "web"
+  App = "app"
+  Unknown(String)
+}
+
+type PlaceForm {
+  order_id: String
+  amount: Amount
+  channel: Channel
+}
+type Order {
+  order_id: String
+  amount: Amount
+  channel: Channel
+}
 type OrderQuery {}
 type OrderList { items: [Order] }
 type StoreError { reason: String }
@@ -20,23 +36,23 @@ type NoteQuery {}
 type NoteList { items: [Note] }
 
 // DB TRANSPORTS leave the module. The host implements BeamlDb.
-effect orders.save Order -> Order ! StoreError = db.put("records")
+effect orders.save Order      -> Order     ! StoreError = db.put("records")
 effect orders.list OrderQuery -> OrderList ! StoreError = db.list("records")
-effect notes.save Note -> Note ! StoreError = db.put("records")
-effect notes.list NoteQuery -> NoteList ! StoreError = db.list("records")
+effect notes.save  Note       -> Note      ! StoreError = db.put("records")
+effect notes.list  NoteQuery  -> NoteList  ! StoreError = db.list("records")
 
 // ENTRY LINES enter the module. The LiveView pages call Orders.ui_<event>(params).
-effect ui.place PlaceForm -> Order ! StoreError = ui.event("place") |> place
+effect ui.place  PlaceForm  -> Order     ! StoreError = ui.event("place") |> place
 effect ui.orders OrderQuery -> OrderList ! StoreError = ui.event("orders") |> list_orders
-effect ui.note NoteForm -> Note ! StoreError = ui.event("note") |> save_note
-effect ui.notes NoteQuery -> NoteList ! StoreError = ui.event("notes") |> list_notes
+effect ui.note   NoteForm   -> Note      ! StoreError = ui.event("note") |> save_note
+effect ui.notes  NoteQuery  -> NoteList  ! StoreError = ui.event("notes") |> list_notes
 
 fn to_order PlaceForm { order_id, amount, channel } -> Order =
   Order { order_id: order_id, amount: amount, channel: channel }
 
-fn place f: PlaceForm -> Order ! StoreError = f |> to_order |> orders.save
+fn place       f: PlaceForm  -> Order     ! StoreError = f |> to_order |> orders.save
 fn list_orders q: OrderQuery -> OrderList ! StoreError = q |> orders.list
 
-fn to_note NoteForm { text } -> Note = Note { text: text }
-fn save_note f: NoteForm -> Note ! StoreError = f |> to_note |> notes.save
-fn list_notes q: NoteQuery -> NoteList ! StoreError = q |> notes.list
+fn to_note    NoteForm { text } -> Note                  = Note { text: text }
+fn save_note  f: NoteForm       -> Note     ! StoreError = f |> to_note |> notes.save
+fn list_notes q: NoteQuery      -> NoteList ! StoreError = q |> notes.list
```

### fmt diffs of the three variants

```diff
--- app/beaml/variants/no_place/orders.beaml
+++ app/beaml/variants/no_place/orders.beaml
@@ -3 +3,4 @@
-type Amount { value: String currency: String }
+type Amount {
+  value: String
+  currency: String
+}
@@ -5,2 +8,2 @@
-fn Amount _,     ""       -> Amount ! BadAmount = BadAmount {}
-fn Amount value, currency -> Amount ! BadAmount = Amount { value: value, currency: currency }
+fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
+fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
@@ -8 +11,5 @@
-enum Channel { Web = "web"  App = "app"  Unknown(String) }
+enum Channel {
+  Web = "web"
+  App = "app"
+  Unknown(String)
+}
@@ -10,2 +17,10 @@
-type PlaceForm { order_id: String amount: Amount channel: Channel }
-type Order { order_id: String amount: Amount channel: Channel }
+type PlaceForm {
+  order_id: String
+  amount: Amount
+  channel: Channel
+}
+type Order {
+  order_id: String
+  amount: Amount
+  channel: Channel
+}
@@ -23 +38 @@
-effect orders.save Order -> Order ! StoreError = db.put("records")
+effect orders.save Order      -> Order     ! StoreError = db.put("records")
@@ -25,2 +40,2 @@
-effect notes.save Note -> Note ! StoreError = db.put("records")
-effect notes.list NoteQuery -> NoteList ! StoreError = db.list("records")
+effect notes.save  Note       -> Note      ! StoreError = db.put("records")
+effect notes.list  NoteQuery  -> NoteList  ! StoreError = db.list("records")
@@ -30,2 +45,2 @@
-effect ui.note NoteForm -> Note ! StoreError = ui.event("note") |> save_note
-effect ui.notes NoteQuery -> NoteList ! StoreError = ui.event("notes") |> list_notes
+effect ui.note   NoteForm   -> Note      ! StoreError = ui.event("note") |> save_note
+effect ui.notes  NoteQuery  -> NoteList  ! StoreError = ui.event("notes") |> list_notes
@@ -36 +51 @@
-fn place f: PlaceForm -> Order ! StoreError = f |> to_order |> orders.save
+fn place       f: PlaceForm  -> Order     ! StoreError = f |> to_order |> orders.save
@@ -39,3 +54,3 @@
-fn to_note NoteForm { text } -> Note = Note { text: text }
-fn save_note f: NoteForm -> Note ! StoreError = f |> to_note |> notes.save
-fn list_notes q: NoteQuery -> NoteList ! StoreError = q |> notes.list
+fn to_note    NoteForm { text } -> Note                  = Note { text: text }
+fn save_note  f: NoteForm       -> Note     ! StoreError = f |> to_note |> notes.save
+fn list_notes q: NoteQuery      -> NoteList ! StoreError = q |> notes.list
--- app/beaml/variants/note_v2/orders.beaml
+++ app/beaml/variants/note_v2/orders.beaml
@@ -3 +3,4 @@
-type Amount { value: String currency: String }
+type Amount {
+  value: String
+  currency: String
+}
@@ -5,2 +8,2 @@
-fn Amount _,     ""       -> Amount ! BadAmount = BadAmount {}
-fn Amount value, currency -> Amount ! BadAmount = Amount { value: value, currency: currency }
+fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
+fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
@@ -8 +11,5 @@
-enum Channel { Web = "web"  App = "app"  Unknown(String) }
+enum Channel {
+  Web = "web"
+  App = "app"
+  Unknown(String)
+}
@@ -10,2 +17,10 @@
-type PlaceForm { order_id: String amount: Amount channel: Channel }
-type Order { order_id: String amount: Amount channel: Channel }
+type PlaceForm {
+  order_id: String
+  amount: Amount
+  channel: Channel
+}
+type Order {
+  order_id: String
+  amount: Amount
+  channel: Channel
+}
@@ -18 +33,4 @@
-type Note v2 { text: String tag: String }
+type Note {
+  text: String
+  tag: String
+}
@@ -24 +42 @@
-effect orders.save Order -> Order ! StoreError = db.put("records")
+effect orders.save Order      -> Order     ! StoreError = db.put("records")
@@ -26,2 +44,2 @@
-effect notes.save Note -> Note ! StoreError = db.put("records")
-effect notes.list NoteQuery -> NoteList ! StoreError = db.list("records")
+effect notes.save  Note       -> Note      ! StoreError = db.put("records")
+effect notes.list  NoteQuery  -> NoteList  ! StoreError = db.list("records")
@@ -30 +48 @@
-effect ui.place PlaceForm -> Order ! StoreError = ui.event("place") |> place
+effect ui.place  PlaceForm  -> Order     ! StoreError = ui.event("place") |> place
@@ -32,2 +50,2 @@
-effect ui.note NoteForm -> Note ! StoreError = ui.event("note") |> save_note
-effect ui.notes NoteQuery -> NoteList ! StoreError = ui.event("notes") |> list_notes
+effect ui.note   NoteForm   -> Note      ! StoreError = ui.event("note") |> save_note
+effect ui.notes  NoteQuery  -> NoteList  ! StoreError = ui.event("notes") |> list_notes
@@ -38 +56 @@
-fn place f: PlaceForm -> Order ! StoreError = f |> to_order |> orders.save
+fn place       f: PlaceForm  -> Order     ! StoreError = f |> to_order |> orders.save
@@ -41,3 +59,3 @@
-fn to_note NoteForm { text } -> Note = Note { text: text, tag: "" }
-fn save_note f: NoteForm -> Note ! StoreError = f |> to_note |> notes.save
-fn list_notes q: NoteQuery -> NoteList ! StoreError = q |> notes.list
+fn to_note    NoteForm { text } -> Note                  = Note { text: text, tag: "" }
+fn save_note  f: NoteForm       -> Note     ! StoreError = f |> to_note |> notes.save
+fn list_notes q: NoteQuery      -> NoteList ! StoreError = q |> notes.list
--- app/beaml/variants/stricter/orders.beaml
+++ app/beaml/variants/stricter/orders.beaml
@@ -3 +3,4 @@
-type Amount { value: String currency: String }
+type Amount {
+  value: String
+  currency: String
+}
@@ -5,3 +8,3 @@
-fn Amount "0",   _        -> Amount ! BadAmount = BadAmount {}
-fn Amount _,     ""       -> Amount ! BadAmount = BadAmount {}
-fn Amount value, currency -> Amount ! BadAmount = Amount { value: value, currency: currency }
+fn Amount "0",           _                -> Amount ! BadAmount = BadAmount {}
+fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
+fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
@@ -9 +12,5 @@
-enum Channel { Web = "web"  App = "app"  Unknown(String) }
+enum Channel {
+  Web = "web"
+  App = "app"
+  Unknown(String)
+}
@@ -11,2 +18,10 @@
-type PlaceForm { order_id: String amount: Amount channel: Channel }
-type Order { order_id: String amount: Amount channel: Channel }
+type PlaceForm {
+  order_id: String
+  amount: Amount
+  channel: Channel
+}
+type Order {
+  order_id: String
+  amount: Amount
+  channel: Channel
+}
@@ -24 +39 @@
-effect orders.save Order -> Order ! StoreError = db.put("records")
+effect orders.save Order      -> Order     ! StoreError = db.put("records")
@@ -26,2 +41,2 @@
-effect notes.save Note -> Note ! StoreError = db.put("records")
-effect notes.list NoteQuery -> NoteList ! StoreError = db.list("records")
+effect notes.save  Note       -> Note      ! StoreError = db.put("records")
+effect notes.list  NoteQuery  -> NoteList  ! StoreError = db.list("records")
@@ -30 +45 @@
-effect ui.place PlaceForm -> Order ! StoreError = ui.event("place") |> place
+effect ui.place  PlaceForm  -> Order     ! StoreError = ui.event("place") |> place
@@ -32,2 +47,2 @@
-effect ui.note NoteForm -> Note ! StoreError = ui.event("note") |> save_note
-effect ui.notes NoteQuery -> NoteList ! StoreError = ui.event("notes") |> list_notes
+effect ui.note   NoteForm   -> Note      ! StoreError = ui.event("note") |> save_note
+effect ui.notes  NoteQuery  -> NoteList  ! StoreError = ui.event("notes") |> list_notes
@@ -38 +53 @@
-fn place f: PlaceForm -> Order ! StoreError = f |> to_order |> orders.save
+fn place       f: PlaceForm  -> Order     ! StoreError = f |> to_order |> orders.save
@@ -41,3 +56,3 @@
-fn to_note NoteForm { text } -> Note = Note { text: text }
-fn save_note f: NoteForm -> Note ! StoreError = f |> to_note |> notes.save
-fn list_notes q: NoteQuery -> NoteList ! StoreError = q |> notes.list
+fn to_note    NoteForm { text } -> Note                  = Note { text: text }
+fn save_note  f: NoteForm       -> Note     ! StoreError = f |> to_note |> notes.save
+fn list_notes q: NoteQuery      -> NoteList ! StoreError = q |> notes.list
```

## Raw test output (fmt, db, slice5)

### slice6_fmt_test
```
compiler: /Users/lennart/Projects/beaml/experiments/0001-syntax-to-beam/target/debug/beaml-spike
..............................
----------------------------------------------------------------------
Ran 30 tests in 0.908s

OK
```
### slice6_db_test
```
test_N12_order_v2_chain_with_constructor_and_enum_fields (__main__.Slice6Db.test_N12_order_v2_chain_with_constructor_and_enum_fields) ... compiler: /Users/lennart/Projects/beaml/experiments/0001-syntax-to-beam/target/debug/beaml-spike
ok
test_N12_rejects (__main__.Slice6Db.test_N12_rejects) ... ok
test_N12_s13_db_get_is_a_kind_now (__main__.Slice6Db.test_N12_s13_db_get_is_a_kind_now) ... ok
test_N13_sources_without_a_db_effect_keep_their_bytes (__main__.Slice6Db.test_N13_sources_without_a_db_effect_keep_their_bytes) ... compiler 060a075d: /var/folders/0y/gcbfrs51401ghzf3hxdm3l5c0000gp/T/beaml-0004-s5-060a075d-w671cknc/target/debug/beaml-spike
ok
test_N15_fmt_keeps_the_fixtures (__main__.Slice6Db.test_N15_fmt_keeps_the_fixtures) ... 
  test_N15_fmt_keeps_the_fixtures (__main__.Slice6Db.test_N15_fmt_keeps_the_fixtures) [orders.beaml] ... FAIL
  test_N15_fmt_keeps_the_fixtures (__main__.Slice6Db.test_N15_fmt_keeps_the_fixtures) [plain/orders.beaml] ... FAIL
  test_N15_fmt_keeps_the_fixtures (__main__.Slice6Db.test_N15_fmt_keeps_the_fixtures) [plain_v2/orders.beaml] ... FAIL
  test_N15_fmt_keeps_the_fixtures (__main__.Slice6Db.test_N15_fmt_keeps_the_fixtures) [two_rows/orders.beaml] ... FAIL
  test_N15_fmt_keeps_the_fixtures (__main__.Slice6Db.test_N15_fmt_keeps_the_fixtures) [no_app/orders.beaml] ... FAIL
test_N15b_fmt_aligns_the_db_effect_lines (__main__.Slice6Db.test_N15b_fmt_aligns_the_db_effect_lines) ... FAIL
test_N16_grammar_list_type (__main__.Slice6Db.test_N16_grammar_list_type) ... ok
test_N1_db_source_builds (__main__.Slice6Db.test_N1_db_source_builds) ... ok
test_N1b_variants_build (__main__.Slice6Db.test_N1b_variants_build) ... ok
test_N25b_control_kept_value_builds (__main__.Slice6Db.test_N25b_control_kept_value_builds) ... ok
test_N25b_control_the_record_builds_where_the_literal_stands (__main__.Slice6Db.test_N25b_control_the_record_builds_where_the_literal_stands) ... ok
test_N25b_lost_literal_in_a_list_item_blocks (__main__.Slice6Db.test_N25b_lost_literal_in_a_list_item_blocks) ... ok
test_N2_to_N11_orders_runtime (__main__.Slice6Db.test_N2_to_N11_orders_runtime) ... ok
test_N2c_jsonb_typeof_reason_is_null (__main__.Slice6Db.test_N2c_jsonb_typeof_reason_is_null) ... skipped "0005 only: jsonb_typeof(value->'reason') = 'null' needs Postgres (0005 N2c, PDB-30)"
test_N5_control_plain_v1_writer (__main__.Slice6Db.test_N5_control_plain_v1_writer) ... ok
test_N5_migrate_chain_on_read (__main__.Slice6Db.test_N5_migrate_chain_on_read) ... ok

======================================================================
FAIL: test_N15_fmt_keeps_the_fixtures (__main__.Slice6Db.test_N15_fmt_keeps_the_fixtures) [orders.beaml]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_db_test.py", line 510, in test_N15_fmt_keeps_the_fixtures
    self.assertEqual((0, source.read_text()), (code, after), stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, '[142 chars]unt { value: String currency: String }\nfn Amo[1166 chars]t\n') != (0, '[142 chars]unt {\n  value: String\n  currency: String\n}\[1223 chars]t\n')

First differing element 1:
'// S[138 chars]unt { value: String currency: String }\nfn Amo[1165 chars]st\n'
'// S[138 chars]unt {\n  value: String\n  currency: String\n}\[1222 chars]st\n'

  (0,
   '// Slice 6 db: the DB TRANSPORTS db.put, db.get, db.list over the one table '
   '"records" (DL-127, DL-129, 0005 P4a).\n'
   'type BadAmount {}\n'
-  'type Amount { value: String currency: String }\n'
+  'type Amount {\n'
+  '  value: String\n'
+  '  currency: String\n'
+  '}\n'
   'fn Amount value: String, currency: String -> Amount ! BadAmount\n'
-  'fn Amount _,     ""       -> Amount ! BadAmount = BadAmount {}\n'
?                                                               ----

+  'fn Amount _,             ""               -> Amount ! BadAmount = BadAmount '
?                    ++++++++         ++++++++

+  '{}\n'
-  'fn Amount value, currency -> Amount ! BadAmount = Amount { value: value, '
?                                                              --------------

+  'fn Amount value,         currency         -> Amount ! BadAmount = Amount { '
?                   ++++++++          ++++++++

-  'currency: currency }\n'
+  'value: value, currency: currency }\n'
?   ++++++++++++++

   '\n'
-  'enum Channel { Web = "web"  App = "app"  Unknown(String) }\n'
+  'enum Channel {\n'
+  '  Web = "web"\n'
+  '  App = "app"\n'
+  '  Unknown(String)\n'
+  '}\n'
   '\n'
-  'type Order { order_id: String amount: Amount channel: Channel }\n'
+  'type Order {\n'
+  '  order_id: String\n'
+  '  amount: Amount\n'
+  '  channel: Channel\n'
+  '}\n'
   'type OrderKey { order_id: String }\n'
   'type OrderQuery {}\n'
   'type OrderList { items: [Order] }\n'
   'type StoreError { reason: String }\n'
   '\n'
   '// Three DB TRANSPORTS leave the module. Each call is recorded live and '
   'substituted in a REPLAY RUN.\n'
-  'effect orders.save Order      -> Order ! StoreError     = db.put("records")\n'
?                                                       ----

+  'effect orders.save Order      -> Order     ! StoreError = db.put("records")\n'
?                                          ++++

-  'effect orders.load OrderKey   -> Order ! StoreError     = db.get("records")\n'
?                                                       ----

+  'effect orders.load OrderKey   -> Order     ! StoreError = db.get("records")\n'
?                                          ++++

   'effect orders.list OrderQuery -> OrderList ! StoreError = '
   'db.list("records")\n'
   '\n'
   '// Enters the module. The host calls Orders.ui_orders(params).\n'
   'effect ui.orders OrderQuery -> OrderList ! StoreError = ui.event("orders") '
   '|> list_orders\n'
   '\n'
   'fn save o: Order -> Order ! StoreError = o |> orders.save\n'
   '\n'
   'fn load k: OrderKey -> Order ! StoreError = k |> orders.load\n'
   '\n'
   'fn list_orders q: OrderQuery -> OrderList ! StoreError = q |> orders.list\n') : 

======================================================================
FAIL: test_N15_fmt_keeps_the_fixtures (__main__.Slice6Db.test_N15_fmt_keeps_the_fixtures) [plain/orders.beaml]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_db_test.py", line 510, in test_N15_fmt_keeps_the_fixtures
    self.assertEqual((0, source.read_text()), (code, after), stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, '[98 chars]der { order_id: String label: String }\ntype O[647 chars]t\n') != (0, '[98 chars]der {\n  order_id: String\n  label: String\n}\[654 chars]t\n')

First differing element 1:
'// S[94 chars]der { order_id: String label: String }\ntype O[646 chars]st\n'
'// S[94 chars]der {\n  order_id: String\n  label: String\n}\[653 chars]st\n'

  (0,
   '// Slice 6 db variant plain: a String-only ROW TYPE, TYPE VERSION 1 (N5 '
   'control, PDB-31).\n'
-  'type Order { order_id: String label: String }\n'
+  'type Order {\n'
+  '  order_id: String\n'
+  '  label: String\n'
+  '}\n'
   'type OrderKey { order_id: String }\n'
   'type OrderQuery {}\n'
   'type OrderList { items: [Order] }\n'
   'type StoreError { reason: String }\n'
   '\n'
-  'effect orders.save Order      -> Order ! StoreError     = db.put("records")\n'
?                                                       ----

+  'effect orders.save Order      -> Order     ! StoreError = db.put("records")\n'
?                                          ++++

-  'effect orders.load OrderKey   -> Order ! StoreError     = db.get("records")\n'
?                                                       ----

+  'effect orders.load OrderKey   -> Order     ! StoreError = db.get("records")\n'
?                                          ++++

   'effect orders.list OrderQuery -> OrderList ! StoreError = '
   'db.list("records")\n'
```
### slice5_syntax_test
```
test_F01_B5_builds_and_equals_the_base_output (__main__.Fixture.test_F01_B5_builds_and_equals_the_base_output) ... compiler f29e3f12: /var/folders/0y/gcbfrs51401ghzf3hxdm3l5c0000gp/T/beaml-0004-s5-f29e3f12-smtmsgy2/target/debug/beaml-spike
compiler 4a7cffba: /var/folders/0y/gcbfrs51401ghzf3hxdm3l5c0000gp/T/beaml-0004-s5-4a7cffba-0x_ggtns/target/debug/beaml-spike
compiler: /Users/lennart/Projects/beaml/experiments/0001-syntax-to-beam/target/debug/beaml-spike
compiler ca09d361: /var/folders/0y/gcbfrs51401ghzf3hxdm3l5c0000gp/T/beaml-0004-s5-ca09d361-vo3q0krp/target/debug/beaml-spike
ok
test_F02_fallback_error_names_every_declaration_word (__main__.Fixture.test_F02_fallback_error_names_every_declaration_word) ... ok
test_F02_interface_is_an_error_with_a_help_line_at_each_position (__main__.Fixture.test_F02_interface_is_an_error_with_a_help_line_at_each_position) ... ok
test_F03_plain_numbers_in_migrate_are_an_error (__main__.Fixture.test_F03_plain_numbers_in_migrate_are_an_error) ... ok
test_F03b_mixed_numbers_name_v2 (__main__.Fixture.test_F03b_mixed_numbers_name_v2) ... ok
test_F03b_plain_number_on_the_type_line_is_an_error (__main__.Fixture.test_F03b_plain_number_on_the_type_line_is_an_error) ... ok
test_F03c_control_v_numbers_build (__main__.Fixture.test_F03c_control_v_numbers_build) ... ok
test_F04_version_faults_on_the_type_line_and_in_migrate (__main__.Fixture.test_F04_version_faults_on_the_type_line_and_in_migrate) ... ok
test_F05_fields_named_like_versions_stay_fields (__main__.Fixture.test_F05_fields_named_like_versions_stay_fields) ... ok
test_F06_control_the_same_chain_with_another_mark_is_M1 (__main__.Fixture.test_F06_control_the_same_chain_with_another_mark_is_M1) ... ok
test_F06_mark_beside_a_chain_from_v1_builds (__main__.Fixture.test_F06_mark_beside_a_chain_from_v1_builds) ... ok
test_F07_Q4s_with_records_of_its_chain_start_builds_without_warning (__main__.Fixture.test_F07_Q4s_with_records_of_its_chain_start_builds_without_warning) ... ok
test_F08_mark_below_the_chain_end_is_M1 (__main__.Fixture.test_F08_mark_below_the_chain_end_is_M1) ... ok
test_F08b_mark_above_the_chain_end_is_M1 (__main__.Fixture.test_F08b_mark_above_the_chain_end_is_M1) ... ok
test_F08c_chain_with_a_gap_is_an_error (__main__.Fixture.test_F08c_chain_with_a_gap_is_an_error) ... ok
test_F09_M3_builds_and_writes_its_mark_as_the_version (__main__.Fixture.test_F09_M3_builds_and_writes_its_mark_as_the_version) ... ok
test_F10_M3_with_older_records_names_the_missing_steps (__main__.Fixture.test_F10_M3_with_older_records_names_the_missing_steps) ... ok
test_F11_M3_with_records_of_its_mark_builds_without_warning (__main__.Fixture.test_F11_M3_with_records_of_its_mark_builds_without_warning) ... ok
test_F11b_other_fingerprint_gets_a_help_line_with_the_step_and_the_mark (__main__.Fixture.test_F11b_other_fingerprint_gets_a_help_line_with_the_step_and_the_mark) ... ok
test_F12_control_the_same_record_against_a_higher_mark_builds (__main__.Fixture.test_F12_control_the_same_record_against_a_higher_mark_builds) ... ok
test_F12_record_newer_than_the_mark_is_N1 (__main__.Fixture.test_F12_record_newer_than_the_mark_is_N1) ... ok
test_F12b_lowered_mark_without_chain_is_N1 (__main__.Fixture.test_F12b_lowered_mark_without_chain_is_N1) ... ok
test_F12c_record_newer_than_a_source_without_mark_and_chain_is_N1 (__main__.Fixture.test_F12c_record_newer_than_a_source_without_mark_and_chain_is_N1) ... ok
test_F12d_record_of_another_name_newer_than_the_mark_is_N1 (__main__.Fixture.test_F12d_record_of_another_name_newer_than_the_mark_is_N1) ... ok
test_F13_control_a_v2_record_against_mark_v1_is_N1 (__main__.Fixture.test_F13_control_a_v2_record_against_mark_v1_is_N1) ... ok
test_F13_mark_v1_without_chain_builds (__main__.Fixture.test_F13_mark_v1_without_chain_builds) ... ok
test_F14_chain_above_v1_without_mark_builds (__main__.Fixture.test_F14_chain_above_v1_without_mark_builds) ... ok
test_F15_largest_version_has_no_newer_version_and_no_panic (__main__.Fixture.test_F15_largest_version_has_no_newer_version_and_no_panic) ... ok
test_fixtures_equal_the_template_byte_for_byte (__main__.Fixture.test_fixtures_equal_the_template_byte_for_byte) ... ok
test_A2_rewritten_sources_build_like_the_base (__main__.Rewrite.test_A2_rewritten_sources_build_like_the_base) ... ok
test_A3_stored_fixtures_are_unchanged (__main__.Rewrite.test_A3_stored_fixtures_are_unchanged) ... ok
test_P1_payments_snapshot_differs_in_one_offset_line_and_matches_the_build (__main__.Rewrite.test_P1_payments_snapshot_differs_in_one_offset_line_and_matches_the_build) ... ok
test_F01_B5_builds_and_equals_the_base_output (__main__.Template.test_F01_B5_builds_and_equals_the_base_output) ... ok
test_F02_fallback_error_names_every_declaration_word (__main__.Template.test_F02_fallback_error_names_every_declaration_word) ... ok
test_F02_interface_is_an_error_with_a_help_line_at_each_position (__main__.Template.test_F02_interface_is_an_error_with_a_help_line_at_each_position) ... ok
test_F03_plain_numbers_in_migrate_are_an_error (__main__.Template.test_F03_plain_numbers_in_migrate_are_an_error) ... ok
test_F03b_mixed_numbers_name_v2 (__main__.Template.test_F03b_mixed_numbers_name_v2) ... ok
test_F03b_plain_number_on_the_type_line_is_an_error (__main__.Template.test_F03b_plain_number_on_the_type_line_is_an_error) ... ok
test_F03c_control_v_numbers_build (__main__.Template.test_F03c_control_v_numbers_build) ... ok
test_F04_version_faults_on_the_type_line_and_in_migrate (__main__.Template.test_F04_version_faults_on_the_type_line_and_in_migrate) ... ok
test_F05_fields_named_like_versions_stay_fields (__main__.Template.test_F05_fields_named_like_versions_stay_fields) ... ok
test_F06_control_the_same_chain_with_another_mark_is_M1 (__main__.Template.test_F06_control_the_same_chain_with_another_mark_is_M1) ... ok
test_F06_mark_beside_a_chain_from_v1_builds (__main__.Template.test_F06_mark_beside_a_chain_from_v1_builds) ... ok
test_F07_Q4s_with_records_of_its_chain_start_builds_without_warning (__main__.Template.test_F07_Q4s_with_records_of_its_chain_start_builds_without_warning) ... ok
test_F08_mark_below_the_chain_end_is_M1 (__main__.Template.test_F08_mark_below_the_chain_end_is_M1) ... ok
test_F08b_mark_above_the_chain_end_is_M1 (__main__.Template.test_F08b_mark_above_the_chain_end_is_M1) ... ok
test_F08c_chain_with_a_gap_is_an_error (__main__.Template.test_F08c_chain_with_a_gap_is_an_error) ... ok
test_F09_M3_builds_and_writes_its_mark_as_the_version (__main__.Template.test_F09_M3_builds_and_writes_its_mark_as_the_version) ... ok
test_F10_M3_with_older_records_names_the_missing_steps (__main__.Template.test_F10_M3_with_older_records_names_the_missing_steps) ... ok
test_F11_M3_with_records_of_its_mark_builds_without_warning (__main__.Template.test_F11_M3_with_records_of_its_mark_builds_without_warning) ... ok
test_F11b_other_fingerprint_gets_a_help_line_with_the_step_and_the_mark (__main__.Template.test_F11b_other_fingerprint_gets_a_help_line_with_the_step_and_the_mark) ... ok
test_F12_control_the_same_record_against_a_higher_mark_builds (__main__.Template.test_F12_control_the_same_record_against_a_higher_mark_builds) ... ok
test_F12_record_newer_than_the_mark_is_N1 (__main__.Template.test_F12_record_newer_than_the_mark_is_N1) ... ok
test_F12b_lowered_mark_without_chain_is_N1 (__main__.Template.test_F12b_lowered_mark_without_chain_is_N1) ... ok
test_F12c_record_newer_than_a_source_without_mark_and_chain_is_N1 (__main__.Template.test_F12c_record_newer_than_a_source_without_mark_and_chain_is_N1) ... ok
test_F12d_record_of_another_name_newer_than_the_mark_is_N1 (__main__.Template.test_F12d_record_of_another_name_newer_than_the_mark_is_N1) ... ok
test_F13_control_a_v2_record_against_mark_v1_is_N1 (__main__.Template.test_F13_control_a_v2_record_against_mark_v1_is_N1) ... ok
test_F13_mark_v1_without_chain_builds (__main__.Template.test_F13_mark_v1_without_chain_builds) ... ok
test_F14_chain_above_v1_without_mark_builds (__main__.Template.test_F14_chain_above_v1_without_mark_builds) ... ok
test_F15_largest_version_has_no_newer_version_and_no_panic (__main__.Template.test_F15_largest_version_has_no_newer_version_and_no_panic) ... ok

----------------------------------------------------------------------
Ran 60 tests in 9.058s

OK
```

## Fixtures and pins (Q1 = A, Q2 = re-pin, Q3 = yes; By: Fable, Repair)

By: Opus (fmt-layout-pins). Date: 2026-11-08. Compiler: `cargo build` and `cargo build --release` of 0001 (no change
after the GREEN above). Decisions P1 to P6: [notes.md](notes.md).

### Fixtures formatted (35 listed, 34 changed)

`beaml-spike fmt` in place, exit 0 each; a second run prints nothing for all 35.
→ slice6/db: `orders.beaml`, `plain/`, `plain_v2/`, `two_rows/`, `no_app/` (N15, N15b)
→ slice6/entry: `orders.beaml`, `echo.beaml` (`count.beaml` was already stable) (n11, n11b)
→ slice6/multi: `orders.beaml` (n11, n11b)
→ slice6/redacted-failure: all 26 (`fmt_keeps_every_fixture`)

Compiled output, HEAD file vs formatted file (`--stored stored/empty.jsonl`, stdout + stderr + exit code), with
`# beaml-declaration-v1` offsets and `at byte N` masked: 19 byte-equal, 16 equal after the mask, 0 differ.
18 of the 35 are RED cases (exit 1) and keep their exit and message.

Test anchors moved with the fixtures (P2): `slice6_entry_test.py` `APP`, `AMOUNT_EMPTY`, the O1 replace;
`slice6_multi_test.py` `STOCK_LINE`, `PAYMENT_TYPE`. Before this, S2, S3, S3b, S4 and N9, N11b failed: the old
anchors did not match, so the replace did nothing (S2/S3 built with exit 0).

### Not formatted: 82 tracked sources that fmt also changes (open for the main agent)

Out of scope of P1: no fixed-point test covers them, and several hold their layout on purpose.
→ fmt inputs: `slice6/fmt/{clauses,header,marks}.beaml` (the unformatted side of the fmt test)
→ layout cases: `slice4/Q4-oneline`, `slice4/Q4-crlf`, `slice4/Q4s-crlf`, `slice5/Q4-crlf`
→ templates and snapshots: slice5 (B5, C2, M3, Q4, Q4s, Q4z; PIN, `payments.generated.snapshot`), slice2-4, drift N/Q/R, arms/gen
→ other slice6: constructor, db/put_only, db/stricter, decode, decode-ctor, effect-reach, entry/two_entries, enum, failure, host-struct, int, multi/{bad,copy,no_hold,no_hold_retired}, pipe, redacted (8), stored-elixir (4)
→ outside 0004: 0001 `example.beaml`, 0002 `orders.beaml` and `payments.beaml`, `integrations/zed-beaml/test/highlight/syntax.beaml`
Retained `results/` captures are not touched (raw evidence).

### Digest pins

| Pin | Row | Old | New | Evidence |
|---|---|---|---|---|
| `slice6/effect-reach/byte-guard.json` | `experiments/0004-generated-replay/slice6/fmt/header.formatted.beaml` | `82bb06ec...` | `0fa8a5d2...` | diff: 2 lines, `grade 280 319 -> 280 335`, `grade 320 359 -> 336 391`; masked: equal |
| `EFFECT_OUTPUTS` (slice6_pipe_test.py) | none moved | | | 12 tests OK |
| `BYTE_GUARD` (slice6_host_struct_test.py) | none moved | | | 3 tests OK |

### Hash pins (not touched)

`PIN` ca09d361 (slice5_syntax_test), `BASE` ce190054 (entry, multi), `P4_BASE` 060a075d (db): all their tests pass with
the old hashes. They build an old compiler and compile the current file with both, so a fixture layout change does
not move them. No failure needs the new commit hash; a move to it is only the RV3-14 pin rule.

### Test results

| Test file | Tests | Result |
|---|---|---|
| slice6_db_test.py | 16 | OK (1 skipped) |
| slice6_entry_test.py | 20 | OK |
| slice6_multi_test.py | 14 | OK |
| slice6_redacted_failure_test.py | 8 | OK |
| slice6_pipe_test.py | 12 | OK |
| slice6_host_struct_test.py | 3 | OK |
| slice6_effect_reach_test.py | 8 | OK |
| slice6_fmt_test.py | 30 | OK |

`python3 experiments/0004-generated-replay/run.py`: `{"run": ".../results/20261108T063109487177Z", "status": "pass"}`,
38 of 38 steps pass, 06:31:09 to 06:48:10 UTC.

### 0005

`run.py db-up`: pass (results/20261108T063125509137Z). `BEAML_SPIKE=<0001 debug> run.py run`: pass
(results/20261108T063125878175Z), 16 steps pass, acceptance problems none; N-TESTS 27 tests, 0 failures, 8 excluded,
1 skipped. `mix test` in app (BEAML_SPIKE set, fresh BEAML_RUN_DIR in the scratchpad): 27 tests, 0 failures, 8 excluded,
1 skipped.

`git diff app/lib/generated/orders.ex`: 16 lines changed, all `# beaml-declaration-v1` offset lines (for example
`Amount 229 291 -> 234 312`). With the offsets masked, HEAD and the regenerated file are byte-equal.
