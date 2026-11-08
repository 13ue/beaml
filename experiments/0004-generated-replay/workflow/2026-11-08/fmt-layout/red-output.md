# fmt layout (DL-148): RED output

By: Opus (fmt-layout, RED). Date: 2026-11-08. Compiler: the debug build of HEAD 7638b75a (no GREEN change yet).

Command: `python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py -v`

## Result

→ 30 tests: 35 failures, 4 errors (subtests counted), 3 pass
→ Pass: `guard_expected_fixtures_compile_like_their_sources` (the hand-written `.formatted.beaml` files build like their sources, offsets aside), `invalid_source_writes_nothing`, `squash_mark_without_chain_is_kept` (a one-field body, unchanged by DL-148)
→ Failures: the old fmt keeps one-line TYPE and ENUM bodies, keeps a lone field on several lines, keeps the signature line out of the table, and aligns only clauses of one fn name
→ Errors (4, IndexError): the old output is shorter than the expected multi-line layout, so the asked line number does not exist (right reason: no body is expanded)

## Fixtures

→ New: `slice6/fmt/layout.beaml`, `slice6/fmt/layout.formatted.beaml` (columns of the expected file computed by a hand oracle in Python from hand-written cells, not by the compiler)
→ Changed expectations: `clauses.formatted.beaml` (enum and two-field TYPE expand, `fn one` / `fn other_name` align), `marks.formatted.beaml` (multi-field TYPES expand), `header.formatted.beaml` (signature line joins the table: DL-148 replaces DL-114)
→ RED also changed the comment text of `clauses` line 44 and `header` line 2; GREEN reverted that (it moved byte-guard.json rows of the source files). The fixture comments still describe DL-083 / DL-114 (notes.md F5)

## Raw output

```
test_action_event_counts_changed_lines (__main__.Slice6Fmt.test_action_event_counts_changed_lines) ... compiler: /Users/lennart/Projects/beaml/experiments/0001-syntax-to-beam/target/debug/beaml-spike
FAIL
test_action_event_counts_changed_lines_of_marks (__main__.Slice6Fmt.test_action_event_counts_changed_lines_of_marks) ... FAIL
test_blank_line_breaks_a_group (__main__.Slice6Fmt.test_blank_line_breaks_a_group) ... FAIL
test_clause_group_aligns_argument_columns_arrow_and_equals (__main__.Slice6Fmt.test_clause_group_aligns_argument_columns_arrow_and_equals) ... FAIL
test_comment_line_and_multi_line_clause_end_a_table (__main__.Slice6Fmt.test_comment_line_and_multi_line_clause_end_a_table) ... ERROR
test_comment_line_breaks_a_group (__main__.Slice6Fmt.test_comment_line_breaks_a_group) ... FAIL
test_comments_stay_byte_for_byte (__main__.Slice6Fmt.test_comments_stay_byte_for_byte) ... FAIL
test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) ... 
  test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) [clauses] ... FAIL
  test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) [marks] ... FAIL
  test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) [header] ... FAIL
  test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) [layout] ... FAIL
test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) ... 
  test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) [clauses] ... FAIL
  test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) [marks] ... FAIL
  test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) [header] ... FAIL
  test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) [layout] ... FAIL
test_effect_line_aligns_arrow_and_equals (__main__.Slice6Fmt.test_effect_line_aligns_arrow_and_equals) ... FAIL
test_enum_body_one_line_up_to_one_variant_else_one_variant_per_line (__main__.Slice6Fmt.test_enum_body_one_line_up_to_one_variant_else_one_variant_per_line) ... FAIL
test_equals_column_aligns_when_only_the_return_text_differs (__main__.Slice6Fmt.test_equals_column_aligns_when_only_the_return_text_differs) ... ERROR
test_extra_spaces_before_equals_become_one_column (__main__.Slice6Fmt.test_extra_spaces_before_equals_become_one_column) ... FAIL
test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) ... 
  test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) [clauses] ... FAIL
  test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) [marks] ... FAIL
  test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) [header] ... FAIL
  test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) [layout] ... FAIL
test_fmt_needs_no_stored_snapshot (__main__.Slice6Fmt.test_fmt_needs_no_stored_snapshot) ... FAIL
test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) ... 
  test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) [clauses] ... FAIL
  test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) [marks] ... FAIL
  test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) [header] ... FAIL
  test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) [layout] ... FAIL
test_guard_expected_fixtures_compile_like_their_sources (__main__.Slice6Fmt.test_guard_expected_fixtures_compile_like_their_sources) ... ok
test_invalid_source_writes_nothing (__main__.Slice6Fmt.test_invalid_source_writes_nothing) ... ok
test_lone_clause_is_a_group_of_one (__main__.Slice6Fmt.test_lone_clause_is_a_group_of_one) ... FAIL
test_mark_kept_beside_a_chain_above_v1_and_chain_from_v1_unchanged (__main__.Slice6Fmt.test_mark_kept_beside_a_chain_above_v1_and_chain_from_v1_unchanged) ... FAIL
test_mark_removed_when_a_chain_from_v1_implies_it (__main__.Slice6Fmt.test_mark_removed_when_a_chain_from_v1_implies_it) ... FAIL
test_mark_written_when_the_chain_starts_above_v1 (__main__.Slice6Fmt.test_mark_written_when_the_chain_starts_above_v1) ... FAIL
test_multi_line_clause_breaks_a_group (__main__.Slice6Fmt.test_multi_line_clause_breaks_a_group) ... FAIL
test_one_line_fns_of_different_names_align (__main__.Slice6Fmt.test_one_line_fns_of_different_names_align) ... ERROR
test_one_table_across_signature_constructor_fn_and_effect_lines (__main__.Slice6Fmt.test_one_table_across_signature_constructor_fn_and_effect_lines) ... ERROR
test_signature_line_is_a_table_row (__main__.Slice6Fmt.test_signature_line_is_a_table_row) ... FAIL
test_squash_mark_without_chain_is_kept (__main__.Slice6Fmt.test_squash_mark_without_chain_is_kept) ... ok
test_type_body_one_line_up_to_one_field_else_one_field_per_line (__main__.Slice6Fmt.test_type_body_one_line_up_to_one_field_else_one_field_per_line) ... FAIL
test_type_body_with_a_comment_stays_as_written (__main__.Slice6Fmt.test_type_body_with_a_comment_stays_as_written) ... FAIL
test_v1_mark_without_chain_is_kept (__main__.Slice6Fmt.test_v1_mark_without_chain_is_kept) ... FAIL

======================================================================
ERROR: test_comment_line_and_multi_line_clause_end_a_table (__main__.Slice6Fmt.test_comment_line_and_multi_line_clause_end_a_table)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 268, in test_comment_line_and_multi_line_clause_end_a_table
    [line(after, n) for n in range(39, 45)])
     ~~~~^^^^^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 49, in line
    return data.split(b"\n")[number - 1].rstrip(b"\r")
           ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
IndexError: list index out of range

======================================================================
ERROR: test_equals_column_aligns_when_only_the_return_text_differs (__main__.Slice6Fmt.test_equals_column_aligns_when_only_the_return_text_differs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 158, in test_equals_column_aligns_when_only_the_return_text_differs
    [line(after, 58), line(after, 59)])
     ~~~~^^^^^^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 49, in line
    return data.split(b"\n")[number - 1].rstrip(b"\r")
           ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
IndexError: list index out of range

======================================================================
ERROR: test_one_line_fns_of_different_names_align (__main__.Slice6Fmt.test_one_line_fns_of_different_names_align)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 151, in test_one_line_fns_of_different_names_align
    [line(after, 53), line(after, 54)])
     ~~~~^^^^^^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 49, in line
    return data.split(b"\n")[number - 1].rstrip(b"\r")
           ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
IndexError: list index out of range

======================================================================
ERROR: test_one_table_across_signature_constructor_fn_and_effect_lines (__main__.Slice6Fmt.test_one_table_across_signature_constructor_fn_and_effect_lines)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 260, in test_one_table_across_signature_constructor_fn_and_effect_lines
    ], [line(after, n) for n in range(31, 39)])
        ~~~~^^^^^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 49, in line
    return data.split(b"\n")[number - 1].rstrip(b"\r")
           ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
IndexError: list index out of range

======================================================================
FAIL: test_action_event_counts_changed_lines (__main__.Slice6Fmt.test_action_event_counts_changed_lines)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 349, in test_action_event_counts_changed_lines
    self.assertEqual([("cli", "ok", CHANGED["clauses"]), ("cli", "ok", 0), ("cli", "error", 0)], events)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('cli', 'ok', 11), ('cli', 'ok', 0), ('cli', 'error', 0)] != [('cli', 'ok', 8), ('cli', 'ok', 0), ('cli', 'error', 0)]

First differing element 0:
('cli', 'ok', 11)
('cli', 'ok', 8)

- [('cli', 'ok', 11), ('cli', 'ok', 0), ('cli', 'error', 0)]
?                ^^

+ [('cli', 'ok', 8), ('cli', 'ok', 0), ('cli', 'error', 0)]
?                ^


======================================================================
FAIL: test_action_event_counts_changed_lines_of_marks (__main__.Slice6Fmt.test_action_event_counts_changed_lines_of_marks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 353, in test_action_event_counts_changed_lines_of_marks
    self.assertEqual([CHANGED["marks"]], [e.get("changed") for e in self.fmt_events()])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [5] != [2]

First differing element 0:
5
2

- [5]
+ [2]

======================================================================
FAIL: test_blank_line_breaks_a_group (__main__.Slice6Fmt.test_blank_line_breaks_a_group)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 167, in test_blank_line_breaks_a_group
    self.assertEqual(b'fn tag "m", x -> String = x', line(after, 24),
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "the clause after the blank line does not align with lines 16 and 17")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: b'fn tag "m", x -> String = x' != b'fn label Authorized -> String = "ok" // keep   this  -> text' : the clause after the blank line does not align with lines 16 and 17

======================================================================
FAIL: test_clause_group_aligns_argument_columns_arrow_and_equals (__main__.Slice6Fmt.test_clause_group_aligns_argument_columns_arrow_and_equals)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 137, in test_clause_group_aligns_argument_columns_arrow_and_equals
    self.assertEqual([
    ~~~~~~~~~~~~~~~~^^
        b'fn PaymentState "ok",       _      -> PaymentState = Authorized',
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        b'fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined',
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        b"fn PaymentState other,      _      -> PaymentState = Unknown(other)",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ], [line(after, n) for n in range(15, 18)], "group A; a comment line separates it from its signature line")
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [b'fn PaymentState "ok",       _      -> Pay[184 chars]er)'] != [b'// Group break by a blank line: the two p[117 chars]"k"']

First differing element 0:
b'fn PaymentState "ok",       _      -> PaymentState = Authorized'
b'// Group break by a blank line: the two parts do not align with each other.'

+ [b'// Group break by a blank line: the two parts do not align with each other.',
+  b'fn tag "a = b",       x -> String = x',
+  b'fn tag "long -> key", x -> String = "k"']
- [b'fn PaymentState "ok",       _      -> PaymentState = Authorized',
-  b'fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason'
-  b' |> Declined',
-  b'fn PaymentState other,      _      -> PaymentState = Unknown(other)'] : group A; a comment line separates it from its signature line

======================================================================
FAIL: test_comment_line_breaks_a_group (__main__.Slice6Fmt.test_comment_line_breaks_a_group)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 172, in test_comment_line_breaks_a_group
    self.assertEqual([b'fn tag "m", x -> String = x', line(source("clauses"), 20),
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      b"fn tag other, y -> String = other"],
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     [line(after, n) for n in (24, 25, 26)])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [b'fn tag "m", x -> String = x', b'// Group bre[68 chars]her'] != [b'fn label Authorized -> String = "ok" // keep[59 chars]/b"']

First differing element 0:
b'fn tag "m", x -> String = x'
b'fn label Authorized -> String = "ok" // keep   this  -> text'

- [b'fn tag "m", x -> String = x',
-  b'// Group break by a comment line:   x  ->   y',
-  b'fn tag other, y -> String = other']
+ [b'fn label Authorized -> String = "ok" // keep   this  -> text',
+  b'fn label Pending -> String =',
+  b'  "a//b"']

======================================================================
FAIL: test_comments_stay_byte_for_byte (__main__.Slice6Fmt.test_comments_stay_byte_for_byte)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 200, in test_comments_stay_byte_for_byte
    self.assertTrue(line(after, after_line(n)).endswith(tail), "line %d keeps its comment bytes" % n)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : line 9 keeps its comment bytes

======================================================================
FAIL: test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) [clauses]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 296, in test_compiled_output_equal_except_declaration_offsets
    self.assertEqual((0, expected(name)), (run["code"], run["after"]), "R2: " + run["stderr"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[306 chars]ate {\n  Authorized\n  Pending\n  Declined(Dec[1914 chars]r\n') != (0, b[306 chars]ate { Authorized  Pending  Declined(DeclineRea[1889 chars]r\n')

First differing element 1:
b'// [302 chars]ate {\n  Authorized\n  Pending\n  Declined(Dec[1913 chars]er\n'
b'// [302 chars]ate { Authorized  Pending  Declined(DeclineRea[1888 chars]er\n'

  (0,
   b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` aligns clause columns (DL-0'
   b'83, D6B-44) and EFFECT lines (DL-013).\n// This comment keeps its spacing'
   b':   a  ->   b  =  c   \ntype DeclineReason { text: String }\nfn DeclineRea'
   b'son text: String -> DeclineReason = DeclineReason { text: text }\n\nenum P'
-  b'aymentState {\n  Authorized\n  Pending\n  Declined(DeclineReason)\n  Unknown'
?                 ---           --         --                         --

+  b'aymentState { Authorized  Pending  Declined(DeclineReason)  Unknown(String) '
?                                                                       +++++++++

-  b'(String)\n}\n\nfn PaymentState status: String, decline_reason: String -> Pa'
?    ----------

+  b'}\n\nfn PaymentState status: String, decline_reason: String -> PaymentStat'
?                                                                     +++++++++

-  b'ymentState\n// Group A: three single-line clauses of one fn. Arguments, `'
?    ---------

+  b'e\n// Group A: three single-line clauses of one fn. Arguments, `->` and `'
?                                                                   +++++++++

-  b'->` and `=` align.\nfn PaymentState "ok",       _      -> PaymentState = '
?    ---------

+  b'=` align.\nfn PaymentState "ok",       _      -> PaymentState = Authorize'
?                                                                    +++++++++

-  b'Authorized\nfn PaymentState "declined", reason -> PaymentState = reason |'
?    ---------

+  b'd\nfn PaymentState "declined", reason -> PaymentState = reason |> Decline'
?                                                                    +++++++++

-  b'> DeclineReason |> Declined\nfn PaymentState other,      _      -> Paymen'
?    ---------

+  b'Reason |> Declined\nfn PaymentState other,      _      -> PaymentState = '
?                                                                    +++++++++

-  b'tState = Unknown(other)\n\nfn tag key: String, x: String -> String\n// Grou'
?    ---------

+  b'Unknown(other)\n\nfn tag key: String, x: String -> String\n// Group break b'
?                                                                      +++++++++

-  b'p break by a blank line: the two parts do not align with each other.\nfn '
?    ^^^^^ ------

+  b'y a blank line: the two parts do not align with each other.\nfn tag "a = '
?    ^^                                                              +++++++++

-  b'tag "a = b",       x -> String = x\nfn tag "long -> key", x -> String = "'
?    ---------

+  b'b",       x -> String = x\nfn tag "long -> key", x -> String = "k"\n\nfn ta'
?                                                                    +++++++++++

-  b'k"\n\nfn tag "m", x -> String = x\n// Group break by a comment line:   x  -'
?    -----------

+  b'g "m", x -> String = x\n// Group break by a comment line:   x  ->   y\nfn '
?                                                                    ++++++++++

-  b'>   y\nfn tag other, y -> String = other\n\n// Group break by a multi-line '
?    ----------

+  b'tag other, y -> String = other\n\n// Group break by a multi-line clause. A'
?                                                                     +++++++++

-  b'clause. A trailing comment stays.\nfn label Authorized -> String = "ok" /'
?    ---------

+  b' trailing comment stays.\nfn label Authorized -> String = "ok" // keep   '
?                                                                    +++++++++

-  b'/ keep   this  -> text\nfn label Pending -> String =\n  "a//b"\nfn label Un'
?    ---------

+  b'this  -> text\nfn label Pending -> String =\n  "a//b"\nfn label Unknown(tex'
?                                                                      +++++++++

-  b'known(text) -> String = text\nfn label Declined(r)   -> String = "decline'
?    ---------

+  b't) -> String = text\nfn label Declined(r)   -> String = "declined"\n\n// A '
?                                                                    +++++++++++

-  b'd"\n\n// A lone single-line clause is a group of one.\nfn lone x: String ->'
?    -----------

+  b'lone single-line clause is a group of one.\nfn lone x: String -> String ='
?                                                                    +++++++++

-  b' String = x\n\ntype Order { order_id: String }\ntype Payment {\n  order_id: '
?    ---------                                                     ---

+  b' x\n\ntype Order { order_id: String }\ntype Payment { order_id: String stat'
?                                                                    +++++++++++

-  b'String\n  state: String\n}\ntype PaymentError { reason: String }\n\n// An'
+  b'e: String }\ntype PaymentError { reason: String }\n\n// An EFFECT line is a'
-  b' EFFECT line is a group of one (slice 1 supports one EFFECT): `->` and `=` g'
?    -----------------

+  b' group of one (slice 1 supports one EFFECT): `->` and `=` get one space befo'
?                                                               +++++++++++++++++

-  b'et one space before them.\neffect payments.authorize Order -> Payment ! P'
?    -----------------

+  b're them.\neffect payments.authorize Order -> Payment ! PaymentError = htt'
?                                                            +++++++++++++++++

-  b'aymentError = http.post("payments/authorize")\n\nfn place order: Order -> '
?    -----------------

+  b'p.post("payments/authorize")\n\nfn place order: Order -> Payment ! Payment'
?                                                             +++++++++++++++++

-  b'Payment ! PaymentError =\n  order\n  |> payments.authorize\n\n// Two adjacen'
?    -----------------

+  b'Error =\n  order\n  |> payments.authorize\n\n// Two adjacent one-line fns of'
?                                                               +++++++++++++++++

-  b't one-line fns of different names: one table since DL-148 (DL-083 kept them '
?    -----------------

+  b' different names: one table since DL-148 (DL-083 kept them apart).\nfn on'
?                                                               ++++++++++++++

-  b'apart).\nfn one        a: String  -> String = a\nfn other_name bb: String '
-  b'-> String = bb\n\nfn check key: String -> String ! PaymentError\n// Only th'
+  b'e a: String -> String = a\nfn other_name bb: String -> String = bb\n\nfn ch'
+  b'eck key: String -> String ! PaymentError\n// Only the `=` column differs:'
-  b'e `=` column differs: the return text of line 51 is one byte longer (`!` gap'
?    ---------------------

+  b' the return text of line 51 is one byte longer (`!` gap stays, U4).\nfn c'
?                                                           ++++++++++++++++++

-  b' stays, U4).\nfn check "abc" -> String ! PaymentError  = "x"\nfn check oth'
?    ------------------

+  b'heck "abc" -> String ! PaymentError  = "x"\nfn check other -> String !  P'
?                                                            +++++++++++++++++

-  b'er -> String !  PaymentError = other\n')
?    -----------------

+  b'aymentError = other\n') : R2: 

======================================================================
FAIL: test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) [marks]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 296, in test_compiled_output_equal_except_declaration_offsets
    self.assertEqual((0, expected(name)), (run["code"], run["after"]), "R2: " + run["stderr"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[183 chars]ned {\n  id: String\n  state: String\n  channe[1156 chars]e\n') != (0, b[183 chars]ned { id: String state: String channel: String[1118 chars]e\n')

First differing element 1:
b'// [179 chars]ned {\n  id: String\n  state: String\n  channe[1155 chars]ze\n'
b'// [179 chars]ned { id: String state: String channel: String[1117 chars]ze\n'

  (0,
   b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` VERSION MARK form (b) by DL'
   b'-104 (D6B-43).\n// Chain from v1 that ends at the mark: the chain implies'
-  b' v3, so the mark goes.\ntype Chained {\n  id: String\n  state: String\n  cha'
?                                          ---           ---              ---

+  b' v3, so the mark goes.\ntype Chained { id: String state: String channel: '
?                                                                       ++++++

-  b'nnel: String\n}\nmigrate Chained v1 -> v2 { rename status -> state }\nmigra'
?    ------      ^^

+  b'String }\nmigrate Chained v1 -> v2 { rename status -> state }\nmigrate Cha'
?          ^                                                             ++++++

-  b'te Chained v2 -> v3 { add channel: String = "web" }\n\n// Mark without a c'
?    ------

+  b'ined v2 -> v3 { add channel: String = "web" }\n\n// Mark without a chain ('
?                                                                        ++++++

-  b'hain (a SQUASH): the mark is the only source of v3, so it stays.\ntype Sq'
?    - -----

+  b'a SQUASH): the mark is the only source of v3, so it stays.\ntype Squashed'
?                                                                       ++++++

-  b'uashed v3 { id: String }\n\n// Chain that starts above v1, no mark: the ma'
?    ------

+  b' v3 { id: String }\n\n// Chain that starts above v1, no mark: the mark v5 '
?                                                                        ++++++

-  b'rk v5 is written after the name.\ntype Shortened v5 {\n  id: String\n  note'
?    ------                                               ---           ---

+  b'is written after the name.\ntype Shortened v5 { id: String note: String }'
?                                                                   ++++++++++

+  b'\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chain that sta'
+  b'rts above v1, with its mark: the mark stays.\ntype Kept v5 { id: String n'
-  b': String\n}\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chai'
?            ^^           ^^^^ ----

+  b'ote: String }\nmigrate Kept v4 -> v5 { add note: String = "" }\n\n// Chain '
?    +++        ^           ^^^                                               ++

-  b'n that starts above v1, with its mark: the mark stays.\ntype Kept v5 {\n  '
-  b'id: String\n  note: String\n}\nmigrate Kept v4 -> v5 { add note: String = "'
-  b'" }\n\n// Chain from v1, no mark: nothing changes.\ntype Plain {\n  id: Stri'
?    ----------------                                                ---

+  b'from v1, no mark: nothing changes.\ntype Plain { id: String state: String'
?                                                             ++++++++++++++++

-  b'ng\n  state: String\n}\nmigrate Plain v1 -> v2 { rename status -> state'
-  b' }\n\n// v1 without a chain, as the EFFECT output: the mark selects the ve'
-  b'rsioned decode, so it stays (O3).\ntype Order { order_id: String }\ntype P'
-  b'ayment v1 {\n  order_id: String\n  state: String\n}\ntype PaymentError { rea'
-  b'son: String }\neffect payments.authorize Order -> Payment ! PaymentError '
-  b'= http.post("payments/authorize")\n\nfn place order: Order -> Payment ! Pa'
-  b'ymentError =\n  order\n  |> payments.authorize\n')
+  b' }\nmigrate Plain v1 -> v2 { rename status -> state }\n\n// v1 without a ch'
+  b'ain, as the EFFECT output: the mark selects the versioned decode, so it stay'
+  b's (O3).\ntype Order { order_id: String }\ntype Payment v1 { order_id: Stri'
+  b'ng state: String }\ntype PaymentError { reason: String }\neffect payments.'
+  b'authorize Order -> Payment ! PaymentError = http.post("payments/authoriz'
+  b'e")\n\nfn place order: Order -> Payment ! PaymentError =\n  order\n  |> paym'
+  b'ents.authorize\n') : R2: 

======================================================================
FAIL: test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) [header]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 296, in test_compiled_output_equal_except_declaration_offsets
    self.assertEqual((0, expected(name)), (run["code"], run["after"]), "R2: " + run["stderr"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[292 chars]",           _             -> String = "top"\n[54 chars]r\n') != (0, b[292 chars]",   _     -> String = "top"\nfn grade other, [22 chars]r\n')

First differing element 1:
b'// [288 chars]",           _             -> String = "top"\n[53 chars]er\n'
b'// [288 chars]",   _     -> String = "top"\nfn grade other, [21 chars]er\n'

  (0,
   b'// EXPERIMENT 0004 slice 6b step 10: OWNER question Q6B-9 (notes.md F4), the'
   b' only case of a signature line above clauses.\n// DL-148 (replaces the F4'
   b' reading of DL-114): the signature line (no `=`) is a row of the table below'
-  b' it.\nfn grade score: String, bonus: String -> String\nfn grade "a",      '
?                                                                           ^

+  b' it.\nfn grade score: String, bonus: String -> String\nfn grade "a",   _  '
?                                                                           ^

+  b'   -> String = "top"\nfn grade other, bonus -> String = other\n')
-  b'     _             -> String = "top"\nfn grade other,         bonus      '
-  b'   -> String = other\n') : R2: 

======================================================================
FAIL: test_compiled_output_equal_except_declaration_offsets (__main__.Slice6Fmt.test_compiled_output_equal_except_declaration_offsets) [layout]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 296, in test_compiled_output_equal_except_declaration_offsets
    self.assertEqual((0, expected(name)), (run["code"], run["after"]), "R2: " + run["stderr"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[99 chars]pty {}\ntype Note { text: String }\ntype Amoun[1530 chars]x\n') != (0, b[99 chars]pty {  }\ntype Note {   text: String   }\ntype[1270 chars]x\n')

First differing element 1:
b'// [95 chars]pty {}\ntype Note { text: String }\ntype Amoun[1529 chars] x\n'
b'// [95 chars]pty {  }\ntype Note {   text: String   }\ntype[1269 chars] x\n'

  (0,
   b'// EXPERIMENT 0004 fmt layout (DL-148): TYPE and ENUM bodies, one clause tab'
-  b'le per block.\ntype Empty {}\ntype Note { text: String }\ntype Amount {\n  v'
?                                                                         -------

+  b'le per block.\ntype Empty {  }\ntype Note {   text: String   }\ntype Amount'
?                               ++              ++             ++

-  b'alue: String\n  currency: String\n}\ntype Order {\n  order_id: String\n  '
?                ---                 ^^

+  b' { value: String currency: String }\ntype Order {\n  order_id: String\n    '
?    ++++                             ^                                       ++

-  b'amount: Amount\n}\ntype One { id: String }\ntype Pair {\n  a: String,\n  '
?                                            ^              ---           ^^^^

+  b'amount: Amount\n}\ntype One {\n  id: String\n}\ntype Pair { a: String, b:'
?                                 +++           ^^                         ^^^

-  b'b: String\n}\ntype Commented {\n    a: String // a comment inside a body ke'
?    --       ^^

+  b' String }\ntype Commented {\n    a: String // a comment inside a body keep'
?           ^                                                                ++

-  b'eps the body as written\n  b: String\n}\nenum Channel {\n  Web = "web"\n '
?    --                                                     ---            ^^^

+  b's the body as written\n  b: String\n}\nenum Channel { Web = "web"  App = "a'
?                                                                     ^^^^^^^^^^

-  b' App = "app"\n  Unknown(String)\n}\nenum Single { Only }\ntype BadAmount'
?    ---------   --                 ^^

+  b'pp"  Unknown(String) }\nenum Single { Only }\ntype BadAmount {}\ntype Store'
?                        ^                                       +++++++++++++++

-  b' {}\ntype StoreError { reason: String }\n\n// One table: a signature line, '
?    ---------------

+  b'Error { reason: String }\n\n// One table: a signature line, constructor cl'
?                                                                ++++++++++++++

-  b'constructor clauses, EFFECT lines, an ENTRY LINE and fn clauses.\nfn Amou'
?    --------------

+  b'auses, EFFECT lines, an ENTRY LINE and fn clauses.\nfn Amount value: Stri'
?                                                               ++++++++++++++

+  b'ng, currency: String -> Amount ! BadAmount\nfn Amount _,     ""       -> '
+  b'Amount ! BadAmount = BadAmount {}\nfn Amount value, currency -> Amount ! '
-  b'nt             value: String, currency: String -> Amount ! BadAmount\nfn '
-  b'Amount             _,             ""               -> Amount ! BadAmount  = '
-  b'BadAmount {}\nfn Amount             value,         currency         -> Am'
-  b'ount ! BadAmount  = Amount { value: value, currency: currency }\neffect o'
?    -------          -

+  b'BadAmount = Amount { value: value, currency: currency }\neffect orders.sa'
?                                                                     ++++++++

+  b've Order   -> Order ! StoreError = db.put("records")\neffect payments.che'
-  b'rders.save    Order                           -> Order  ! StoreError = db.pu'
-  b't("records")\neffect payments.check Note                            -> No'
-  b'te   ! StoreError = http.post("payments/check")\neffect ui.save        Or'
?       ^                                                         ------------

+  b'ck Note -> Note ! StoreError  = http.post("payments/check")\neffect ui.sa'
?    +++++   ^^^^^^^              +

+  b've Order       -> Order ! StoreError = ui.event("save") |> save\nfn check'
+  b'_note n: Note -> Note ! StoreError = n |> payments.check\nfn label c: Cha'
+  b'nnel -> String = "a -> b = c"\n// A comment line ends the block:   x  -> '
+  b'  y\nfn save o: Order -> Order ! StoreError = o |> orders.save\nfn keep n:'
+  b' Note -> Note = n\nfn tidy Only -> String =\n  "a"\nfn tidy_one x: String -'
+  b'> String = x\n')
-  b'der                           -> Order  ! StoreError = ui.event("save") |> s'
-  b'ave\nfn check_note         n: Note                         -> Note   ! St'
-  b'oreError = n |> payments.check\nfn label              c: Channel         '
-  b'             -> String              = "a -> b = c"\n// A comment line end'
-  b's the block:   x  ->   y\nfn save o: Order -> Order ! StoreError = o |> o'
-  b'rders.save\nfn keep n: Note  -> Note               = n\nfn tidy Only -> St'
-  b'ring =\n  "a"\nfn tidy_one x: String -> String = x\n') : R2: 

======================================================================
FAIL: test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) [clauses]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 339, in test_crlf_line_ends_stay
    self.assert_formatted(name, crlf(source(name)), crlf(expected(name)))
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 111, in assert_formatted
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'cod[332 chars]ate {\r\n  Authorized\r\n  Pending\r\n  Declin[2075 chars]alse} != {'cod[332 chars]ate { Authorized  Pending  Declined(DeclineRea[2034 chars]alse}
  {'code': 0,
   'error': False,
   'file': b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` aligns clause colum'
           b'ns (DL-083, D6B-44) and EFFECT lines (DL-013).\r\n// This comment '
           b'keeps its spacing:   a  ->   b  =  c   \r\ntype DeclineReason { te'
           b'xt: String }\r\nfn DeclineReason text: String -> DeclineReason = D'
-          b'eclineReason { text: text }\r\n\r\nenum PaymentState {\r\n  Author'
?                                                                  -----

+          b'eclineReason { text: text }\r\n\r\nenum PaymentState { Authorized  P'
?                                                                         +++++++

+          b'ending  Declined(DeclineReason)  Unknown(String) }\r\n\r\nfn Payment'
+          b'State status: String, decline_reason: String -> PaymentState\r\n//'
+          b' Group A: three single-line clauses of one fn. Arguments, `->` and `'
-          b'ized\r\n  Pending\r\n  Declined(DeclineReason)\r\n  Unknown(String'
-          b')\r\n}\r\n\r\nfn PaymentState status: String, decline_reason: Stri'
-          b'ng -> PaymentState\r\n// Group A: three single-line clauses of one'
-          b' fn. Arguments, `->` and `=` align.\r\nfn PaymentState "ok",      '
-          b' _      -> PaymentState = Authorized\r\nfn PaymentState "declined"'
-          b', reason -> PaymentState = reason |> DeclineReason |> Declined\r\n'
-          b'fn PaymentState other,      _      -> PaymentState = Unknown(oth'
?                             ^^^^                                -----------

+          b'=` align.\r\nfn PaymentState "ok",       _      -> PaymentState = '
?            +++++++++++++                + ^^       +

-          b'er)\r\n\r\nfn tag key: String, x: String -> String\r\n// Group bre'
-          b'ak by a blank line: the two parts do not align with each other.\r'
-          b'\nfn tag "a = b",       x -> String = x\r\nfn tag "long -> key", x '
-          b'-> String = "k"\r\n\r\nfn tag "m", x -> String = x\r\n// Group bre'
-          b'ak by a comment line:   x  ->   y\r\nfn tag other, y -> String = o'
-          b'ther\r\n\r\n// Group break by a multi-line clause. A trailing commen'
-          b't stays.\r\nfn label Authorized -> String = "ok" // keep   this  -'
-          b'> text\r\nfn label Pending -> String =\r\n  "a//b"\r\nfn label Unk'
-          b'nown(text) -> String = text\r\nfn label Declined(r)   -> String = '
-          b'"declined"\r\n\r\n// A lone single-line clause is a group of one'
-          b'.\r\nfn lone x: String -> String = x\r\n\r\ntype Order { order_id:'
-          b' String }\r\ntype Payment {\r\n  order_id: String\r\n  state: Stri'
-          b'ng\r\n}\r\ntype PaymentError { reason: String }\r\n\r\n// An EFFECT '
-          b'line is a group of one (slice 1 supports one EFFECT): `->` and `=` g'
-          b'et one space before them.\r\neffect payments.authorize Order -> Pa'
-          b'yment ! PaymentError = http.post("payments/authorize")\r\n\r\nfn pla'
-          b'ce order: Order -> Payment ! PaymentError =\r\n  order\r\n  |> payme'
-          b'nts.authorize\r\n\r\n// Two adjacent one-line fns of different names'
-          b': one table since DL-148 (DL-083 kept them apart).\r\nfn one      '
+          b'Authorized\r\nfn PaymentState "declined", reason -> PaymentState ='
+          b' reason |> DeclineReason |> Declined\r\nfn PaymentState other,    '
+          b'  _      -> PaymentState = Unknown(other)\r\n\r\nfn tag key: String,'
+          b' x: String -> String\r\n// Group break by a blank line: the two pa'
+          b'rts do not align with each other.\r\nfn tag "a = b",       x -> St'
+          b'ring = x\r\nfn tag "long -> key", x -> String = "k"\r\n\r\nfn tag '
+          b'"m", x -> String = x\r\n// Group break by a comment line:   x  -> '
+          b'  y\r\nfn tag other, y -> String = other\r\n\r\n// Group break by '
+          b'a multi-line clause. A trailing comment stays.\r\nfn label Authori'
+          b'zed -> String = "ok" // keep   this  -> text\r\nfn label Pending -'
+          b'> String =\r\n  "a//b"\r\nfn label Unknown(text) -> String = tex'
+          b't\r\nfn label Declined(r)   -> String = "declined"\r\n\r\n// A lon'
+          b'e single-line clause is a group of one.\r\nfn lone x: String -> St'
+          b'ring = x\r\n\r\ntype Order { order_id: String }\r\ntype Payment { '
+          b'order_id: String state: String }\r\ntype PaymentError { reason: St'
+          b'ring }\r\n\r\n// An EFFECT line is a group of one (slice 1 supports '
+          b'one EFFECT): `->` and `=` get one space before them.\r\neffect pay'
+          b'ments.authorize Order -> Payment ! PaymentError = http.post("payment'
+          b's/authorize")\r\n\r\nfn place order: Order -> Payment ! PaymentError'
+          b' =\r\n  order\r\n  |> payments.authorize\r\n\r\n// Two adjacent one-'
+          b'line fns of different names: one table since DL-148 (DL-083 kept the'
-          b'  a: String  -> String = a\r\nfn other_name bb: String -> String ='
?            ^           -                                      ---------------

+          b'm apart).\r\nfn one a: String -> String = a\r\nfn other_name bb: Str'
?            ^^^^^^^^^^^^^^^^^^^

-          b' bb\r\n\r\nfn check key: String -> String ! PaymentError\r\n// Onl'
?                                                                 -------------

+          b'ing -> String = bb\r\n\r\nfn check key: String -> String ! PaymentEr'
?            +++++++++++++++

-          b'y the `=` column differs: the return text of line 51 is one byte lon'
?                                                                 ---------------

+          b'ror\r\n// Only the `=` column differs: the return text of line 51 '
?            +++++++++++++

-          b'ger (`!` gap stays, U4).\r\nfn check "abc" -> String ! PaymentErro'
?                                                               ---------------

+          b'is one byte longer (`!` gap stays, U4).\r\nfn check "abc" -> Strin'
?            +++++++++++++++

-          b'r  = "x"\r\nfn check other -> String !  PaymentError = other\r\n',
+          b'g ! PaymentError  = "x"\r\nfn check other -> String !  PaymentErro'
+          b'r = other\r\n',
   'renamed': True,
   'temp_left': False} : fmt contract for clauses; stderr: 

======================================================================
FAIL: test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) [marks]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 339, in test_crlf_line_ends_stay
    self.assert_formatted(name, crlf(source(name)), crlf(expected(name)))
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 111, in assert_formatted
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'cod[203 chars]ned {\r\n  id: String\r\n  state: String\r\n  [1297 chars]alse} != {'cod[203 chars]ned { id: String state: String channel: String[1227 chars]alse}
  {'code': 0,
   'error': False,
   'file': b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` VERSION MARK form ('
           b'b) by DL-104 (D6B-43).\r\n// Chain from v1 that ends at the mark: '
-          b'the chain implies v3, so the mark goes.\r\ntype Chained {\r\n  id: S'
?                                                                     -----

+          b'the chain implies v3, so the mark goes.\r\ntype Chained { id: Stri'
?                                                                           +++

-          b'tring\r\n  state: String\r\n  channel: String\r\n}\r\nmigrate Chaine'
?            ---  -----              -----                ^^^^

+          b'ng state: String channel: String }\r\nmigrate Chained v1 -> v2 { r'
?                                            ^                   ++++++++++++++

-          b'd v1 -> v2 { rename status -> state }\r\nmigrate Chained v2 -> v3 '
?            --------------

+          b'ename status -> state }\r\nmigrate Chained v2 -> v3 { add channel:'
?                                                                ++++++++++++++

-          b'{ add channel: String = "web" }\r\n\r\n// Mark without a chain (a SQ'
?            --------------

+          b' String = "web" }\r\n\r\n// Mark without a chain (a SQUASH): the mar'
?                                                                  ++++++++++++++

-          b'UASH): the mark is the only source of v3, so it stays.\r\ntype Squ'
?            ^^^^^^    ------------

+          b'k is the only source of v3, so it stays.\r\ntype Squashed v3 { id:'
?            ^^^^                                                ++++++++++++++

-          b'ashed v3 { id: String }\r\n\r\n// Chain that starts above v1, no mar'
?            --------------

+          b' String }\r\n\r\n// Chain that starts above v1, no mark: the mark v5'
?                                                                  ++++++++++++++

-          b'k: the mark v5 is written after the name.\r\ntype Shortened v5 {\r\n'
?            --------------                                                  ^ ^

+          b' is written after the name.\r\ntype Shortened v5 { id: String note'
?                                                              ^^^^^^^ ^ ++++++

-          b'  id: String\r\n  note: String\r\n}\r\nmigrate Shortened v4 -> v5 '
-          b'{ add note: String = "" }\r\n\r\n// Chain that starts above v1, with'
-          b' its mark: the mark stays.\r\ntype Kept v5 {\r\n  id: String\r\n  '
-          b'note: String\r\n}\r\nmigrate Kept v4 -> v5 { add note: String = "" }'
?            ----        ^^^^             ^ ^^

+          b': String }\r\nmigrate Shortened v4 -> v5 { add note: String = "" }'
?                    ^             ^^^^^ ^^^

-          b'\r\n\r\n// Chain from v1, no mark: nothing changes.\r\ntype Plain '
-          b'{\r\n  id: String\r\n  state: String\r\n}\r\nmigrate Plain v1 -> v2 '
+          b'\r\n\r\n// Chain that starts above v1, with its mark: the mark stays'
+          b'.\r\ntype Kept v5 { id: String note: String }\r\nmigrate Kept v4 -> '
+          b'v5 { add note: String = "" }\r\n\r\n// Chain from v1, no mark: nothi'
+          b'ng changes.\r\ntype Plain { id: String state: String }\r\nmigrate Pl'
-          b'{ rename status -> state }\r\n\r\n// v1 without a chain, as the EFFE'
?                                                                   -------------

+          b'ain v1 -> v2 { rename status -> state }\r\n\r\n// v1 without a chain'
?            +++++++++++++

-          b'CT output: the mark selects the versioned decode, so it stays (O'
?                                                                   ---------

+          b', as the EFFECT output: the mark selects the versioned decode, so it'
?            +++++++++++++

-          b'3).\r\ntype Order { order_id: String }\r\ntype Payment v1 {\r\n  o'
?                                                                       -------

+          b' stays (O3).\r\ntype Order { order_id: String }\r\ntype Payment v1 {'
?            +++++++++

-          b'rder_id: String\r\n  state: String\r\n}\r\ntype PaymentError { rea'
?                           -----              ^^^^

+          b' order_id: String state: String }\r\ntype PaymentError { reason: S'
?            ++                             ^                            ++++++

-          b'son: String }\r\neffect payments.authorize Order -> Payment ! Paym'
?            ------

+          b'tring }\r\neffect payments.authorize Order -> Payment ! PaymentErr'
?                                                                        ++++++

-          b'entError = http.post("payments/authorize")\r\n\r\nfn place order: Or'
?            ------

+          b'or = http.post("payments/authorize")\r\n\r\nfn place order: Order ->'
?                                                                          ++++++

-          b'der -> Payment ! PaymentError =\r\n  order\r\n  |> payments.authoriz'
?            ------

+          b' Payment ! PaymentError =\r\n  order\r\n  |> payments.authorize\r\n',
?                                                                          +++++ +

-          b'e\r\n',
   'renamed': True,
   'temp_left': False} : fmt contract for marks; stderr: 

======================================================================
FAIL: test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) [header]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 339, in test_crlf_line_ends_stay
    self.assert_formatted(name, crlf(source(name)), crlf(expected(name)))
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 111, in assert_formatted
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'cod[314 chars]",           _             -> String = "top"\r[111 chars]alse} != {'cod[314 chars]",   _     -> String = "top"\r\nfn grade other[79 chars]alse}
  {'code': 0,
   'error': False,
   'file': b'// EXPERIMENT 0004 slice 6b step 10: OWNER question Q6B-9 (notes.md '
           b'F4), the only case of a signature line above clauses.\r\n// DL-148'
           b' (replaces the F4 reading of DL-114): the signature line (no `=`) is'
           b' a row of the table below it.\r\nfn grade score: String, bonus: St'
-          b'ring -> String\r\nfn grade "a",           _             -> String '
?                                              -------- --------

+          b'ring -> String\r\nfn grade "a",   _     -> String = "top"\r\nfn grad'
?                                                              ++++++++++++++++++

+          b'e other, bonus -> String = other\r\n',
-          b'= "top"\r\nfn grade other,         bonus         -> String = other'
-          b'\r\n',
   'renamed': True,
   'temp_left': False} : fmt contract for header; stderr: 

======================================================================
FAIL: test_crlf_line_ends_stay (__main__.Slice6Fmt.test_crlf_line_ends_stay) [layout]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 339, in test_crlf_line_ends_stay
    self.assert_formatted(name, crlf(source(name)), crlf(expected(name)))
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 111, in assert_formatted
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'cod[117 chars]pty {}\r\ntype Note { text: String }\r\ntype A[1669 chars]alse} != {'cod[117 chars]pty {  }\r\ntype Note {   text: String   }\r\n[1393 chars]alse}
  {'code': 0,
   'error': False,
   'file': b'// EXPERIMENT 0004 fmt layout (DL-148): TYPE and ENUM bodies, one cl'
-          b'ause table per block.\r\ntype Empty {}\r\ntype Note { text: String }'
?                                                                            ----

+          b'ause table per block.\r\ntype Empty {  }\r\ntype Note {   text: Stri'
?                                                 ++                ++

-          b'\r\ntype Amount {\r\n  value: String\r\n  currency: String\r\n}\r'
?                             -----              -----                     ^^

+          b'ng   }\r\ntype Amount { value: String currency: String }\r\ntype Ord'
?            ++++++                                                ++    ^^^^^^ +

-          b'\ntype Order {\r\n  order_id: String\r\n  amount: Amount\r\n}\r\n'
?            ----------

+          b'er {\r\n  order_id: String\r\n    amount: Amount\r\n}\r\ntype On'
?                                            ++                       +++++++

-          b'type One { id: String }\r\ntype Pair {\r\n  a: String,\r\n  b: Str'
+          b'e {\r\n  id: String\r\n}\r\ntype Pair { a: String, b: String }\r\nty'
-          b'ing\r\n}\r\ntype Commented {\r\n    a: String // a comment inside '
?            --------------

+          b'pe Commented {\r\n    a: String // a comment inside a body keeps t'
?                                                                ++++++++++++++

-          b'a body keeps the body as written\r\n  b: String\r\n}\r\nenum Chann'
?            ^      ---------------

+          b'he body as written\r\n  b: String\r\n}\r\nenum Channel { Web = "we'
?            ^^                                                  ++++++++++++++

+          b'b"  App = "app"  Unknown(String) }\r\nenum Single { Only }\r\ntype B'
+          b'adAmount {}\r\ntype StoreError { reason: String }\r\n\r\n// One ta'
+          b'ble: a signature line, constructor clauses, EFFECT lines, an ENTRY L'
+          b'INE and fn clauses.\r\nfn Amount value: String, currency: String -'
+          b'> Amount ! BadAmount\r\nfn Amount _,     ""       -> Amount ! BadA'
+          b'mount = BadAmount {}\r\nfn Amount value, currency -> Amount ! BadA'
+          b'mount = Amount { value: value, currency: currency }\r\neffect orde'
-          b'el {\r\n  Web = "web"\r\n  App = "app"\r\n  Unknown(String)\r\n}'
-          b'\r\nenum Single { Only }\r\ntype BadAmount {}\r\ntype StoreError {'
-          b' reason: String }\r\n\r\n// One table: a signature line, constructor'
-          b' clauses, EFFECT lines, an ENTRY LINE and fn clauses.\r\nfn Amount'
-          b'             value: String, currency: String -> Amount ! BadAmou'
-          b'nt\r\nfn Amount             _,             ""               -> Amo'
-          b'unt ! BadAmount  = BadAmount {}\r\nfn Amount             value,   '
-          b'      currency         -> Amount ! BadAmount  = Amount { value: valu'
-          b'e, currency: currency }\r\neffect orders.save    Order            '
-          b'               -> Order  ! StoreError = db.put("records")\r\neffec'
?            ^^^^^^^^^^^^^^^^^

+          b'rs.save Order   -> Order ! StoreError = db.put("records")\r\neffec'
?            ^^^^^^^        ++++++++++

+          b't payments.check Note -> Note ! StoreError  = http.post("payments/ch'
+          b'eck")\r\neffect ui.save Order       -> Order ! StoreError = ui.eve'
+          b'nt("save") |> save\r\nfn check_note n: Note -> Note ! StoreError ='
+          b' n |> payments.check\r\nfn label c: Channel -> String = "a -> b = '
-          b't payments.check Note                            -> Note   ! StoreEr'
-          b'ror = http.post("payments/check")\r\neffect ui.save        Order  '
-          b'                         -> Order  ! StoreError = ui.event("save") |'
-          b'> save\r\nfn check_note         n: Note                         ->'
-          b' Note   ! StoreError = n |> payments.check\r\nfn label            '
-          b'  c: Channel                      -> String              = "a -> b ='
-          b' c"\r\n// A comment line ends the block:   x  ->   y\r\nfn save o: O'
?            -

+          b'c"\r\n// A comment line ends the block:   x  ->   y\r\nfn save o: Or'
?                                                                               +

-          b'rder -> Order ! StoreError = o |> orders.save\r\nfn keep n: Note  '
?            -                                                                ^

+          b'der -> Order ! StoreError = o |> orders.save\r\nfn keep n: Note ->'
?                                                                            ^^

-          b'-> Note               = n\r\nfn tidy Only -> String =\r\n  "a"\r\n'
?            --      --------------

+          b' Note = n\r\nfn tidy Only -> String =\r\n  "a"\r\nfn tidy_one x: S'
?                                                              ++++++++++++++++

-          b'fn tidy_one x: String -> String = x\r\n',
+          b'tring -> String = x\r\n',
   'renamed': True,
   'temp_left': False} : fmt contract for layout; stderr: 

======================================================================
FAIL: test_effect_line_aligns_arrow_and_equals (__main__.Slice6Fmt.test_effect_line_aligns_arrow_and_equals)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 190, in test_effect_line_aligns_arrow_and_equals
    self.assertEqual(b'effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")',
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     line(after, 46))
                     ^^^^^^^^^^^^^^^^
AssertionError: b'effect payments.authorize Order -> Paymen[46 chars]ze")' != b'fn other_name bb: String -> String = bb'

======================================================================
FAIL: test_enum_body_one_line_up_to_one_variant_else_one_variant_per_line (__main__.Slice6Fmt.test_enum_body_one_line_up_to_one_variant_else_one_variant_per_line)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 244, in test_enum_body_one_line_up_to_one_variant_else_one_variant_per_line
    self.assertEqual([b"enum Channel {", b'  Web = "web"', b'  App = "app"', b"  Unknown(String)", b"}",
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      b"enum Single { Only }"], [line(after, n) for n in range(21, 27)],
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "literal and payload variants keep their form")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [b'enum Channel {', b'  Web = "web"', b'  Ap[59 chars]y }'] != [b'', b'// One table: a signature line, cons[363 chars]s")']

First differing element 0:
b'enum Channel {'
b''

- [b'enum Channel {',
-  b'  Web = "web"',
-  b'  App = "app"',
-  b'  Unknown(String)',
-  b'}',
-  b'enum Single { Only }']
+ [b'',
+  b'// One table: a signature line, constructor clauses, EFFECT lines, an ENTRY '
+  b'LINE and fn clauses.',
+  b'fn Amount value: String, currency: String -> Amount ! BadAmount',
+  b'fn Amount _,     ""       -> Amount ! BadAmount = BadAmount {}',
+  b'fn Amount value, currency -> Amount ! BadAmount = Amount { value: value, cur'
+  b'rency: currency }',
+  b'effect orders.save Order   -> Order ! StoreError = db.put("records")'] : literal and payload variants keep their form

======================================================================
FAIL: test_extra_spaces_before_equals_become_one_column (__main__.Slice6Fmt.test_extra_spaces_before_equals_become_one_column)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 162, in test_extra_spaces_before_equals_become_one_column
    self.assertEqual([b'fn tag "a = b",       x -> String = x', b'fn tag "long -> key", x -> String = "k"'],
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     [line(after, 21), line(after, 22)], "`->` and `=` inside strings are not columns")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [b'fn tag "a = b",       x -> String = x', b'fn tag[30 chars]"k"'] != [b'fn tag other, y -> String = other', b'']

First differing element 0:
b'fn tag "a = b",       x -> String = x'
b'fn tag other, y -> String = other'

+ [b'fn tag other, y -> String = other', b'']
- [b'fn tag "a = b",       x -> String = x',
-  b'fn tag "long -> key", x -> String = "k"'] : `->` and `=` inside strings are not columns

======================================================================
FAIL: test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) [clauses]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 277, in test_fmt_is_idempotent
    self.assertEqual((0, expected(name)), (first["code"], first["after"]),
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "R2: a no-op fmt must not pass; stderr: " + first["stderr"])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[306 chars]ate {\n  Authorized\n  Pending\n  Declined(Dec[1914 chars]r\n') != (0, b[306 chars]ate { Authorized  Pending  Declined(DeclineRea[1889 chars]r\n')

First differing element 1:
b'// [302 chars]ate {\n  Authorized\n  Pending\n  Declined(Dec[1913 chars]er\n'
b'// [302 chars]ate { Authorized  Pending  Declined(DeclineRea[1888 chars]er\n'

  (0,
   b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` aligns clause columns (DL-0'
   b'83, D6B-44) and EFFECT lines (DL-013).\n// This comment keeps its spacing'
   b':   a  ->   b  =  c   \ntype DeclineReason { text: String }\nfn DeclineRea'
   b'son text: String -> DeclineReason = DeclineReason { text: text }\n\nenum P'
-  b'aymentState {\n  Authorized\n  Pending\n  Declined(DeclineReason)\n  Unknown'
?                 ---           --         --                         --

+  b'aymentState { Authorized  Pending  Declined(DeclineReason)  Unknown(String) '
?                                                                       +++++++++

-  b'(String)\n}\n\nfn PaymentState status: String, decline_reason: String -> Pa'
?    ----------

+  b'}\n\nfn PaymentState status: String, decline_reason: String -> PaymentStat'
?                                                                     +++++++++

-  b'ymentState\n// Group A: three single-line clauses of one fn. Arguments, `'
?    ---------

+  b'e\n// Group A: three single-line clauses of one fn. Arguments, `->` and `'
?                                                                   +++++++++

-  b'->` and `=` align.\nfn PaymentState "ok",       _      -> PaymentState = '
?    ---------

+  b'=` align.\nfn PaymentState "ok",       _      -> PaymentState = Authorize'
?                                                                    +++++++++

-  b'Authorized\nfn PaymentState "declined", reason -> PaymentState = reason |'
?    ---------

+  b'd\nfn PaymentState "declined", reason -> PaymentState = reason |> Decline'
?                                                                    +++++++++

-  b'> DeclineReason |> Declined\nfn PaymentState other,      _      -> Paymen'
?    ---------

+  b'Reason |> Declined\nfn PaymentState other,      _      -> PaymentState = '
?                                                                    +++++++++

-  b'tState = Unknown(other)\n\nfn tag key: String, x: String -> String\n// Grou'
?    ---------

+  b'Unknown(other)\n\nfn tag key: String, x: String -> String\n// Group break b'
?                                                                      +++++++++

-  b'p break by a blank line: the two parts do not align with each other.\nfn '
?    ^^^^^ ------

+  b'y a blank line: the two parts do not align with each other.\nfn tag "a = '
?    ^^                                                              +++++++++

-  b'tag "a = b",       x -> String = x\nfn tag "long -> key", x -> String = "'
?    ---------

+  b'b",       x -> String = x\nfn tag "long -> key", x -> String = "k"\n\nfn ta'
?                                                                    +++++++++++

-  b'k"\n\nfn tag "m", x -> String = x\n// Group break by a comment line:   x  -'
?    -----------

+  b'g "m", x -> String = x\n// Group break by a comment line:   x  ->   y\nfn '
?                                                                    ++++++++++

-  b'>   y\nfn tag other, y -> String = other\n\n// Group break by a multi-line '
?    ----------

+  b'tag other, y -> String = other\n\n// Group break by a multi-line clause. A'
?                                                                     +++++++++

-  b'clause. A trailing comment stays.\nfn label Authorized -> String = "ok" /'
?    ---------

+  b' trailing comment stays.\nfn label Authorized -> String = "ok" // keep   '
?                                                                    +++++++++

-  b'/ keep   this  -> text\nfn label Pending -> String =\n  "a//b"\nfn label Un'
?    ---------

+  b'this  -> text\nfn label Pending -> String =\n  "a//b"\nfn label Unknown(tex'
?                                                                      +++++++++

-  b'known(text) -> String = text\nfn label Declined(r)   -> String = "decline'
?    ---------

+  b't) -> String = text\nfn label Declined(r)   -> String = "declined"\n\n// A '
?                                                                    +++++++++++

-  b'd"\n\n// A lone single-line clause is a group of one.\nfn lone x: String ->'
?    -----------

+  b'lone single-line clause is a group of one.\nfn lone x: String -> String ='
?                                                                    +++++++++

-  b' String = x\n\ntype Order { order_id: String }\ntype Payment {\n  order_id: '
?    ---------                                                     ---

+  b' x\n\ntype Order { order_id: String }\ntype Payment { order_id: String stat'
?                                                                    +++++++++++

-  b'String\n  state: String\n}\ntype PaymentError { reason: String }\n\n// An'
+  b'e: String }\ntype PaymentError { reason: String }\n\n// An EFFECT line is a'
-  b' EFFECT line is a group of one (slice 1 supports one EFFECT): `->` and `=` g'
?    -----------------

+  b' group of one (slice 1 supports one EFFECT): `->` and `=` get one space befo'
?                                                               +++++++++++++++++

-  b'et one space before them.\neffect payments.authorize Order -> Payment ! P'
?    -----------------

+  b're them.\neffect payments.authorize Order -> Payment ! PaymentError = htt'
?                                                            +++++++++++++++++

-  b'aymentError = http.post("payments/authorize")\n\nfn place order: Order -> '
?    -----------------

+  b'p.post("payments/authorize")\n\nfn place order: Order -> Payment ! Payment'
?                                                             +++++++++++++++++

-  b'Payment ! PaymentError =\n  order\n  |> payments.authorize\n\n// Two adjacen'
?    -----------------

+  b'Error =\n  order\n  |> payments.authorize\n\n// Two adjacent one-line fns of'
?                                                               +++++++++++++++++

-  b't one-line fns of different names: one table since DL-148 (DL-083 kept them '
?    -----------------

+  b' different names: one table since DL-148 (DL-083 kept them apart).\nfn on'
?                                                               ++++++++++++++

-  b'apart).\nfn one        a: String  -> String = a\nfn other_name bb: String '
-  b'-> String = bb\n\nfn check key: String -> String ! PaymentError\n// Only th'
+  b'e a: String -> String = a\nfn other_name bb: String -> String = bb\n\nfn ch'
+  b'eck key: String -> String ! PaymentError\n// Only the `=` column differs:'
-  b'e `=` column differs: the return text of line 51 is one byte longer (`!` gap'
?    ---------------------

+  b' the return text of line 51 is one byte longer (`!` gap stays, U4).\nfn c'
?                                                           ++++++++++++++++++

-  b' stays, U4).\nfn check "abc" -> String ! PaymentError  = "x"\nfn check oth'
?    ------------------

+  b'heck "abc" -> String ! PaymentError  = "x"\nfn check other -> String !  P'
?                                                            +++++++++++++++++

-  b'er -> String !  PaymentError = other\n')
?    -----------------

+  b'aymentError = other\n') : R2: a no-op fmt must not pass; stderr: 

======================================================================
FAIL: test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) [marks]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 277, in test_fmt_is_idempotent
    self.assertEqual((0, expected(name)), (first["code"], first["after"]),
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "R2: a no-op fmt must not pass; stderr: " + first["stderr"])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[183 chars]ned {\n  id: String\n  state: String\n  channe[1156 chars]e\n') != (0, b[183 chars]ned { id: String state: String channel: String[1118 chars]e\n')

First differing element 1:
b'// [179 chars]ned {\n  id: String\n  state: String\n  channe[1155 chars]ze\n'
b'// [179 chars]ned { id: String state: String channel: String[1117 chars]ze\n'

  (0,
   b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` VERSION MARK form (b) by DL'
   b'-104 (D6B-43).\n// Chain from v1 that ends at the mark: the chain implies'
-  b' v3, so the mark goes.\ntype Chained {\n  id: String\n  state: String\n  cha'
?                                          ---           ---              ---

+  b' v3, so the mark goes.\ntype Chained { id: String state: String channel: '
?                                                                       ++++++

-  b'nnel: String\n}\nmigrate Chained v1 -> v2 { rename status -> state }\nmigra'
?    ------      ^^

+  b'String }\nmigrate Chained v1 -> v2 { rename status -> state }\nmigrate Cha'
?          ^                                                             ++++++

-  b'te Chained v2 -> v3 { add channel: String = "web" }\n\n// Mark without a c'
?    ------

+  b'ined v2 -> v3 { add channel: String = "web" }\n\n// Mark without a chain ('
?                                                                        ++++++

-  b'hain (a SQUASH): the mark is the only source of v3, so it stays.\ntype Sq'
?    - -----

+  b'a SQUASH): the mark is the only source of v3, so it stays.\ntype Squashed'
?                                                                       ++++++

-  b'uashed v3 { id: String }\n\n// Chain that starts above v1, no mark: the ma'
?    ------

+  b' v3 { id: String }\n\n// Chain that starts above v1, no mark: the mark v5 '
?                                                                        ++++++

-  b'rk v5 is written after the name.\ntype Shortened v5 {\n  id: String\n  note'
?    ------                                               ---           ---

+  b'is written after the name.\ntype Shortened v5 { id: String note: String }'
?                                                                   ++++++++++

+  b'\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chain that sta'
+  b'rts above v1, with its mark: the mark stays.\ntype Kept v5 { id: String n'
-  b': String\n}\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chai'
?            ^^           ^^^^ ----

+  b'ote: String }\nmigrate Kept v4 -> v5 { add note: String = "" }\n\n// Chain '
?    +++        ^           ^^^                                               ++

-  b'n that starts above v1, with its mark: the mark stays.\ntype Kept v5 {\n  '
-  b'id: String\n  note: String\n}\nmigrate Kept v4 -> v5 { add note: String = "'
-  b'" }\n\n// Chain from v1, no mark: nothing changes.\ntype Plain {\n  id: Stri'
?    ----------------                                                ---

+  b'from v1, no mark: nothing changes.\ntype Plain { id: String state: String'
?                                                             ++++++++++++++++

-  b'ng\n  state: String\n}\nmigrate Plain v1 -> v2 { rename status -> state'
-  b' }\n\n// v1 without a chain, as the EFFECT output: the mark selects the ve'
-  b'rsioned decode, so it stays (O3).\ntype Order { order_id: String }\ntype P'
-  b'ayment v1 {\n  order_id: String\n  state: String\n}\ntype PaymentError { rea'
-  b'son: String }\neffect payments.authorize Order -> Payment ! PaymentError '
-  b'= http.post("payments/authorize")\n\nfn place order: Order -> Payment ! Pa'
-  b'ymentError =\n  order\n  |> payments.authorize\n')
+  b' }\nmigrate Plain v1 -> v2 { rename status -> state }\n\n// v1 without a ch'
+  b'ain, as the EFFECT output: the mark selects the versioned decode, so it stay'
+  b's (O3).\ntype Order { order_id: String }\ntype Payment v1 { order_id: Stri'
+  b'ng state: String }\ntype PaymentError { reason: String }\neffect payments.'
+  b'authorize Order -> Payment ! PaymentError = http.post("payments/authoriz'
+  b'e")\n\nfn place order: Order -> Payment ! PaymentError =\n  order\n  |> paym'
+  b'ents.authorize\n') : R2: a no-op fmt must not pass; stderr: 

======================================================================
FAIL: test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) [header]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 277, in test_fmt_is_idempotent
    self.assertEqual((0, expected(name)), (first["code"], first["after"]),
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "R2: a no-op fmt must not pass; stderr: " + first["stderr"])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[292 chars]",           _             -> String = "top"\n[54 chars]r\n') != (0, b[292 chars]",   _     -> String = "top"\nfn grade other, [22 chars]r\n')

First differing element 1:
b'// [288 chars]",           _             -> String = "top"\n[53 chars]er\n'
b'// [288 chars]",   _     -> String = "top"\nfn grade other, [21 chars]er\n'

  (0,
   b'// EXPERIMENT 0004 slice 6b step 10: OWNER question Q6B-9 (notes.md F4), the'
   b' only case of a signature line above clauses.\n// DL-148 (replaces the F4'
   b' reading of DL-114): the signature line (no `=`) is a row of the table below'
-  b' it.\nfn grade score: String, bonus: String -> String\nfn grade "a",      '
?                                                                           ^

+  b' it.\nfn grade score: String, bonus: String -> String\nfn grade "a",   _  '
?                                                                           ^

+  b'   -> String = "top"\nfn grade other, bonus -> String = other\n')
-  b'     _             -> String = "top"\nfn grade other,         bonus      '
-  b'   -> String = other\n') : R2: a no-op fmt must not pass; stderr: 

======================================================================
FAIL: test_fmt_is_idempotent (__main__.Slice6Fmt.test_fmt_is_idempotent) [layout]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 277, in test_fmt_is_idempotent
    self.assertEqual((0, expected(name)), (first["code"], first["after"]),
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "R2: a no-op fmt must not pass; stderr: " + first["stderr"])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[99 chars]pty {}\ntype Note { text: String }\ntype Amoun[1530 chars]x\n') != (0, b[99 chars]pty {  }\ntype Note {   text: String   }\ntype[1270 chars]x\n')

First differing element 1:
b'// [95 chars]pty {}\ntype Note { text: String }\ntype Amoun[1529 chars] x\n'
b'// [95 chars]pty {  }\ntype Note {   text: String   }\ntype[1269 chars] x\n'

  (0,
   b'// EXPERIMENT 0004 fmt layout (DL-148): TYPE and ENUM bodies, one clause tab'
-  b'le per block.\ntype Empty {}\ntype Note { text: String }\ntype Amount {\n  v'
?                                                                         -------

+  b'le per block.\ntype Empty {  }\ntype Note {   text: String   }\ntype Amount'
?                               ++              ++             ++

-  b'alue: String\n  currency: String\n}\ntype Order {\n  order_id: String\n  '
?                ---                 ^^

+  b' { value: String currency: String }\ntype Order {\n  order_id: String\n    '
?    ++++                             ^                                       ++

-  b'amount: Amount\n}\ntype One { id: String }\ntype Pair {\n  a: String,\n  '
?                                            ^              ---           ^^^^

+  b'amount: Amount\n}\ntype One {\n  id: String\n}\ntype Pair { a: String, b:'
?                                 +++           ^^                         ^^^

-  b'b: String\n}\ntype Commented {\n    a: String // a comment inside a body ke'
?    --       ^^

+  b' String }\ntype Commented {\n    a: String // a comment inside a body keep'
?           ^                                                                ++

-  b'eps the body as written\n  b: String\n}\nenum Channel {\n  Web = "web"\n '
?    --                                                     ---            ^^^

+  b's the body as written\n  b: String\n}\nenum Channel { Web = "web"  App = "a'
?                                                                     ^^^^^^^^^^

-  b' App = "app"\n  Unknown(String)\n}\nenum Single { Only }\ntype BadAmount'
?    ---------   --                 ^^

+  b'pp"  Unknown(String) }\nenum Single { Only }\ntype BadAmount {}\ntype Store'
?                        ^                                       +++++++++++++++

-  b' {}\ntype StoreError { reason: String }\n\n// One table: a signature line, '
?    ---------------

+  b'Error { reason: String }\n\n// One table: a signature line, constructor cl'
?                                                                ++++++++++++++

-  b'constructor clauses, EFFECT lines, an ENTRY LINE and fn clauses.\nfn Amou'
?    --------------

+  b'auses, EFFECT lines, an ENTRY LINE and fn clauses.\nfn Amount value: Stri'
?                                                               ++++++++++++++

+  b'ng, currency: String -> Amount ! BadAmount\nfn Amount _,     ""       -> '
+  b'Amount ! BadAmount = BadAmount {}\nfn Amount value, currency -> Amount ! '
-  b'nt             value: String, currency: String -> Amount ! BadAmount\nfn '
-  b'Amount             _,             ""               -> Amount ! BadAmount  = '
-  b'BadAmount {}\nfn Amount             value,         currency         -> Am'
-  b'ount ! BadAmount  = Amount { value: value, currency: currency }\neffect o'
?    -------          -

+  b'BadAmount = Amount { value: value, currency: currency }\neffect orders.sa'
?                                                                     ++++++++

+  b've Order   -> Order ! StoreError = db.put("records")\neffect payments.che'
-  b'rders.save    Order                           -> Order  ! StoreError = db.pu'
-  b't("records")\neffect payments.check Note                            -> No'
-  b'te   ! StoreError = http.post("payments/check")\neffect ui.save        Or'
?       ^                                                         ------------

+  b'ck Note -> Note ! StoreError  = http.post("payments/check")\neffect ui.sa'
?    +++++   ^^^^^^^              +

+  b've Order       -> Order ! StoreError = ui.event("save") |> save\nfn check'
+  b'_note n: Note -> Note ! StoreError = n |> payments.check\nfn label c: Cha'
+  b'nnel -> String = "a -> b = c"\n// A comment line ends the block:   x  -> '
+  b'  y\nfn save o: Order -> Order ! StoreError = o |> orders.save\nfn keep n:'
+  b' Note -> Note = n\nfn tidy Only -> String =\n  "a"\nfn tidy_one x: String -'
+  b'> String = x\n')
-  b'der                           -> Order  ! StoreError = ui.event("save") |> s'
-  b'ave\nfn check_note         n: Note                         -> Note   ! St'
-  b'oreError = n |> payments.check\nfn label              c: Channel         '
-  b'             -> String              = "a -> b = c"\n// A comment line end'
-  b's the block:   x  ->   y\nfn save o: Order -> Order ! StoreError = o |> o'
-  b'rders.save\nfn keep n: Note  -> Note               = n\nfn tidy Only -> St'
-  b'ring =\n  "a"\nfn tidy_one x: String -> String = x\n') : R2: a no-op fmt must not pass; stderr: 

======================================================================
FAIL: test_fmt_needs_no_stored_snapshot (__main__.Slice6Fmt.test_fmt_needs_no_stored_snapshot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 131, in test_fmt_needs_no_stored_snapshot
    self.assertEqual((0, expected("clauses")), (run["code"], run["after"]), run["stderr"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (0, b[306 chars]ate {\n  Authorized\n  Pending\n  Declined(Dec[1914 chars]r\n') != (0, b[306 chars]ate { Authorized  Pending  Declined(DeclineRea[1889 chars]r\n')

First differing element 1:
b'// [302 chars]ate {\n  Authorized\n  Pending\n  Declined(Dec[1913 chars]er\n'
b'// [302 chars]ate { Authorized  Pending  Declined(DeclineRea[1888 chars]er\n'

  (0,
   b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` aligns clause columns (DL-0'
   b'83, D6B-44) and EFFECT lines (DL-013).\n// This comment keeps its spacing'
   b':   a  ->   b  =  c   \ntype DeclineReason { text: String }\nfn DeclineRea'
   b'son text: String -> DeclineReason = DeclineReason { text: text }\n\nenum P'
-  b'aymentState {\n  Authorized\n  Pending\n  Declined(DeclineReason)\n  Unknown'
?                 ---           --         --                         --

+  b'aymentState { Authorized  Pending  Declined(DeclineReason)  Unknown(String) '
?                                                                       +++++++++

-  b'(String)\n}\n\nfn PaymentState status: String, decline_reason: String -> Pa'
?    ----------

+  b'}\n\nfn PaymentState status: String, decline_reason: String -> PaymentStat'
?                                                                     +++++++++

-  b'ymentState\n// Group A: three single-line clauses of one fn. Arguments, `'
?    ---------

+  b'e\n// Group A: three single-line clauses of one fn. Arguments, `->` and `'
?                                                                   +++++++++

-  b'->` and `=` align.\nfn PaymentState "ok",       _      -> PaymentState = '
?    ---------

+  b'=` align.\nfn PaymentState "ok",       _      -> PaymentState = Authorize'
?                                                                    +++++++++

-  b'Authorized\nfn PaymentState "declined", reason -> PaymentState = reason |'
?    ---------

+  b'd\nfn PaymentState "declined", reason -> PaymentState = reason |> Decline'
?                                                                    +++++++++

-  b'> DeclineReason |> Declined\nfn PaymentState other,      _      -> Paymen'
?    ---------

+  b'Reason |> Declined\nfn PaymentState other,      _      -> PaymentState = '
?                                                                    +++++++++

-  b'tState = Unknown(other)\n\nfn tag key: String, x: String -> String\n// Grou'
?    ---------

+  b'Unknown(other)\n\nfn tag key: String, x: String -> String\n// Group break b'
?                                                                      +++++++++

-  b'p break by a blank line: the two parts do not align with each other.\nfn '
?    ^^^^^ ------

+  b'y a blank line: the two parts do not align with each other.\nfn tag "a = '
?    ^^                                                              +++++++++

-  b'tag "a = b",       x -> String = x\nfn tag "long -> key", x -> String = "'
?    ---------

+  b'b",       x -> String = x\nfn tag "long -> key", x -> String = "k"\n\nfn ta'
?                                                                    +++++++++++

-  b'k"\n\nfn tag "m", x -> String = x\n// Group break by a comment line:   x  -'
?    -----------

+  b'g "m", x -> String = x\n// Group break by a comment line:   x  ->   y\nfn '
?                                                                    ++++++++++

-  b'>   y\nfn tag other, y -> String = other\n\n// Group break by a multi-line '
?    ----------

+  b'tag other, y -> String = other\n\n// Group break by a multi-line clause. A'
?                                                                     +++++++++

-  b'clause. A trailing comment stays.\nfn label Authorized -> String = "ok" /'
?    ---------

+  b' trailing comment stays.\nfn label Authorized -> String = "ok" // keep   '
?                                                                    +++++++++

-  b'/ keep   this  -> text\nfn label Pending -> String =\n  "a//b"\nfn label Un'
?    ---------

+  b'this  -> text\nfn label Pending -> String =\n  "a//b"\nfn label Unknown(tex'
?                                                                      +++++++++

-  b'known(text) -> String = text\nfn label Declined(r)   -> String = "decline'
?    ---------

+  b't) -> String = text\nfn label Declined(r)   -> String = "declined"\n\n// A '
?                                                                    +++++++++++

-  b'd"\n\n// A lone single-line clause is a group of one.\nfn lone x: String ->'
?    -----------

+  b'lone single-line clause is a group of one.\nfn lone x: String -> String ='
?                                                                    +++++++++

-  b' String = x\n\ntype Order { order_id: String }\ntype Payment {\n  order_id: '
?    ---------                                                     ---

+  b' x\n\ntype Order { order_id: String }\ntype Payment { order_id: String stat'
?                                                                    +++++++++++

-  b'String\n  state: String\n}\ntype PaymentError { reason: String }\n\n// An'
+  b'e: String }\ntype PaymentError { reason: String }\n\n// An EFFECT line is a'
-  b' EFFECT line is a group of one (slice 1 supports one EFFECT): `->` and `=` g'
?    -----------------

+  b' group of one (slice 1 supports one EFFECT): `->` and `=` get one space befo'
?                                                               +++++++++++++++++

-  b'et one space before them.\neffect payments.authorize Order -> Payment ! P'
?    -----------------

+  b're them.\neffect payments.authorize Order -> Payment ! PaymentError = htt'
?                                                            +++++++++++++++++

-  b'aymentError = http.post("payments/authorize")\n\nfn place order: Order -> '
?    -----------------

+  b'p.post("payments/authorize")\n\nfn place order: Order -> Payment ! Payment'
?                                                             +++++++++++++++++

-  b'Payment ! PaymentError =\n  order\n  |> payments.authorize\n\n// Two adjacen'
?    -----------------

+  b'Error =\n  order\n  |> payments.authorize\n\n// Two adjacent one-line fns of'
?                                                               +++++++++++++++++

-  b't one-line fns of different names: one table since DL-148 (DL-083 kept them '
?    -----------------

+  b' different names: one table since DL-148 (DL-083 kept them apart).\nfn on'
?                                                               ++++++++++++++

-  b'apart).\nfn one        a: String  -> String = a\nfn other_name bb: String '
-  b'-> String = bb\n\nfn check key: String -> String ! PaymentError\n// Only th'
+  b'e a: String -> String = a\nfn other_name bb: String -> String = bb\n\nfn ch'
+  b'eck key: String -> String ! PaymentError\n// Only the `=` column differs:'
-  b'e `=` column differs: the return text of line 51 is one byte longer (`!` gap'
?    ---------------------

+  b' the return text of line 51 is one byte longer (`!` gap stays, U4).\nfn c'
?                                                           ++++++++++++++++++

-  b' stays, U4).\nfn check "abc" -> String ! PaymentError  = "x"\nfn check oth'
?    ------------------

+  b'heck "abc" -> String ! PaymentError  = "x"\nfn check other -> String !  P'
?                                                            +++++++++++++++++

-  b'er -> String !  PaymentError = other\n')
?    -----------------

+  b'aymentError = other\n') : 

======================================================================
FAIL: test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) [clauses]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 125, in test_fmt_rewrites_the_file_and_prints_the_diff
    self.assert_formatted(name)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 111, in assert_formatted
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'cod[322 chars]ate {\n  Authorized\n  Pending\n  Declined(Dec[1967 chars]alse} != {'cod[322 chars]ate { Authorized  Pending  Declined(DeclineRea[1942 chars]alse}
  {'code': 0,
   'error': False,
   'file': b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` aligns clause colum'
           b'ns (DL-083, D6B-44) and EFFECT lines (DL-013).\n// This comment k'
           b'eeps its spacing:   a  ->   b  =  c   \ntype DeclineReason { text'
           b': String }\nfn DeclineReason text: String -> DeclineReason = Decl'
-          b'ineReason { text: text }\n\nenum PaymentState {\n  Authorized\n  Pen'
?                                                           ---           --

+          b'ineReason { text: text }\n\nenum PaymentState { Authorized  Pendin'
?                                                                           +++

-          b'ding\n  Declined(DeclineReason)\n  Unknown(String)\n}\n\nfn Payme'
?            --- --                         --                 ^^

+          b'g  Declined(DeclineReason)  Unknown(String) }\n\nfn PaymentState s'
?                                                       ^             +++++++++

-          b'ntState status: String, decline_reason: String -> PaymentState\n/'
?            ---------

+          b'tatus: String, decline_reason: String -> PaymentState\n// Group A'
?                                                                    +++++++++

-          b'/ Group A: three single-line clauses of one fn. Arguments, `->` and '
?            ---------

+          b': three single-line clauses of one fn. Arguments, `->` and `=` align'
?                                                                       +++++++++

-          b'`=` align.\nfn PaymentState "ok",       _      -> PaymentState = '
?            ---------

+          b'.\nfn PaymentState "ok",       _      -> PaymentState = Authorize'
?                                                                    +++++++++

-          b'Authorized\nfn PaymentState "declined", reason -> PaymentState = '
?            ---------

+          b'd\nfn PaymentState "declined", reason -> PaymentState = reason |>'
?                                                                    +++++++++

-          b'reason |> DeclineReason |> Declined\nfn PaymentState other,      '
?            ---------

+          b' DeclineReason |> Declined\nfn PaymentState other,      _      ->'
?                                                                    +++++++++

-          b'_      -> PaymentState = Unknown(other)\n\nfn tag key: String, x: '
?            ---------

+          b' PaymentState = Unknown(other)\n\nfn tag key: String, x: String ->'
?                                                                     +++++++++

-          b'String -> String\n// Group break by a blank line: the two parts d'
?            ---------

+          b' String\n// Group break by a blank line: the two parts do not ali'
?                                                                    +++++++++

-          b'o not align with each other.\nfn tag "a = b",       x -> String ='
?            ---------

+          b'gn with each other.\nfn tag "a = b",       x -> String = x\nfn tag'
?                                                                    ++++++++++

-          b' x\nfn tag "long -> key", x -> String = "k"\n\nfn tag "m", x -> Str'
?            ----------

+          b' "long -> key", x -> String = "k"\n\nfn tag "m", x -> String = x\n/'
?                                                                     ++++++++++

-          b'ing = x\n// Group break by a comment line:   x  ->   y\nfn tag oth'
?            --------- -

+          b'/ Group break by a comment line:   x  ->   y\nfn tag other, y -> '
?                                                                    +++++++++

-          b'er, y -> String = other\n\n// Group break by a multi-line clause. '
?            ---------

+          b'String = other\n\n// Group break by a multi-line clause. A trailin'
?                                                                     +++++++++

-          b'A trailing comment stays.\nfn label Authorized -> String = "ok" /'
?            ---------

+          b'g comment stays.\nfn label Authorized -> String = "ok" // keep   '
?                                                                    +++++++++

-          b'/ keep   this  -> text\nfn label Pending -> String =\n  "a//b"\nfn '
?            ---------

+          b'this  -> text\nfn label Pending -> String =\n  "a//b"\nfn label Unk'
?                                                                      +++++++++

-          b'label Unknown(text) -> String = text\nfn label Declined(r)   -> S'
?            ---------

+          b'nown(text) -> String = text\nfn label Declined(r)   -> String = "'
?                                                                    +++++++++

-          b'tring = "declined"\n\n// A lone single-line clause is a group of o'
?            ---------

+          b'declined"\n\n// A lone single-line clause is a group of one.\nfn lo'
?                                                                    ++++++++++

-          b'ne.\nfn lone x: String -> String = x\n\ntype Order { order_id: Stri'
?              ----------

+          b'ne x: String -> String = x\n\ntype Order { order_id: String }\ntype'
?                                                                     ++++++++++

-          b'ng }\ntype Payment {\n  order_id: String\n  state: String\n}\ntyp'
?            ----------          ---                 ---              ^^

+          b' Payment { order_id: String state: String }\ntype PaymentError { '
?                                                     ^      +++++++++++++++++

-          b'e PaymentError { reason: String }\n\n// An EFFECT line is a group '
?            -----------------

+          b'reason: String }\n\n// An EFFECT line is a group of one (slice 1 s'
?                                                             +++++++++++++++++

-          b'of one (slice 1 supports one EFFECT): `->` and `=` get one space bef'
?            -----------------

+          b'upports one EFFECT): `->` and `=` get one space before them.\neff'
?                                                               ++++++++++++++

-          b'ore them.\neffect payments.authorize Order -> Payment ! PaymentEr'
?            --------------

+          b'ect payments.authorize Order -> Payment ! PaymentError = http.post("'
?                                                               +++++++++++++++++

-          b'ror = http.post("payments/authorize")\n\nfn place order: Order -> '
?            -----------------

+          b'payments/authorize")\n\nfn place order: Order -> Payment ! Payment'
?                                                             +++++++++++++++++

-          b'Payment ! PaymentError =\n  order\n  |> payments.authorize\n\n// Two'
?            -----------------

+          b'Error =\n  order\n  |> payments.authorize\n\n// Two adjacent one-lin'
?                                                               +++++++++++++++++

-          b' adjacent one-line fns of different names: one table since DL-148 (D'
?            ------ -----------

+          b'e fns of different names: one table since DL-148 (DL-083 kept them a'
?                                                               +++++++++++++++++

+          b'part).\nfn one a: String -> String = a\nfn other_name bb: String -'
+          b'> String = bb\n\nfn check key: String -> String ! PaymentError\n// '
+          b'Only the `=` column differs: the return text of line 51 is one byte '
+          b'longer (`!` gap stays, U4).\nfn check "abc" -> String ! PaymentEr'
+          b'ror  = "x"\nfn check other -> String !  PaymentError = other\n',
-          b'L-083 kept them apart).\nfn one        a: String  -> String = a\nf'
-          b'n other_name bb: String -> String = bb\n\nfn check key: String -> '
-          b'String ! PaymentError\n// Only the `=` column differs: the return'
-          b' text of line 51 is one byte longer (`!` gap stays, U4).\nfn chec'
-          b'k "abc" -> String ! PaymentError  = "x"\nfn check other -> String'
-          b' !  PaymentError = other\n',
   'renamed': True,
   'temp_left': False} : fmt contract for clauses; stderr: 

======================================================================
FAIL: test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) [marks]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 125, in test_fmt_rewrites_the_file_and_prints_the_diff
    self.assert_formatted(name)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 111, in assert_formatted
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'cod[199 chars]ned {\n  id: String\n  state: String\n  channe[1209 chars]alse} != {'cod[199 chars]ned { id: String state: String channel: String[1171 chars]alse}
  {'code': 0,
   'error': False,
   'file': b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` VERSION MARK form ('
           b'b) by DL-104 (D6B-43).\n// Chain from v1 that ends at the mark: t'
-          b'he chain implies v3, so the mark goes.\ntype Chained {\n  id: Stri'
?                                                                  ---

+          b'he chain implies v3, so the mark goes.\ntype Chained { id: String'
?                                                                           ++

-          b'ng\n  state: String\n  channel: String\n}\nmigrate Chained v1 -> v2 '
?            -----              ---                ^^

+          b' state: String channel: String }\nmigrate Chained v1 -> v2 { rena'
?                                          ^                            ++++++

-          b'{ rename status -> state }\nmigrate Chained v2 -> v3 { add channe'
?            ------

+          b'me status -> state }\nmigrate Chained v2 -> v3 { add channel: Str'
?                                                                       ++++++

-          b'l: String = "web" }\n\n// Mark without a chain (a SQUASH): the mar'
?            ------

+          b'ing = "web" }\n\n// Mark without a chain (a SQUASH): the mark is t'
?                                                                        ++++++

-          b'k is the only source of v3, so it stays.\ntype Squashed v3 { id: '
?            ------

+          b'he only source of v3, so it stays.\ntype Squashed v3 { id: String'
?                                                                       ++++++

-          b'String }\n\n// Chain that starts above v1, no mark: the mark v5 is'
?            ------

+          b' }\n\n// Chain that starts above v1, no mark: the mark v5 is writt'
?                                                                        ++++++

-          b' written after the name.\ntype Shortened v5 {\n  id: String\n  note'
?            ------                                       ---           ---

+          b'en after the name.\ntype Shortened v5 { id: String note: String }'
?                                                                   ++++++++++

-          b': String\n}\nmigrate Shortened v4 -> v5 { add note: String = "" }\n'
?            -----------

+          b'\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chain '
?                                                                    +++++++++++

-          b'\n// Chain that starts above v1, with its mark: the mark stays.\nt'
?            -----------

+          b'that starts above v1, with its mark: the mark stays.\ntype Kept v'
?                                                                   ++++++++++

-          b'ype Kept v5 {\n  id: String\n  note: String\n}\nmigrate Kept v4 -> v'
?            ----------   ---           ---             ^^

+          b'5 { id: String note: String }\nmigrate Kept v4 -> v5 { add note: '
?                                       ^                       ++++++++++++++

-          b'5 { add note: String = "" }\n\n// Chain from v1, no mark: nothing '
?            --------------

+          b'String = "" }\n\n// Chain from v1, no mark: nothing changes.\ntype '
?                                                                +++++++++++++++

-          b'changes.\ntype Plain {\n  id: String\n  state: String\n}\nmigrate'
-          b' Plain v1 -> v2 { rename status -> state }\n\n// v1 without a chai'
-          b'n, as the EFFECT output: the mark selects the versioned decode, so i'
+          b'Plain { id: String state: String }\nmigrate Plain v1 -> v2 { rena'
+          b'me status -> state }\n\n// v1 without a chain, as the EFFECT outpu'
+          b't: the mark selects the versioned decode, so it stays (O3).\ntype'
-          b't stays (O3).\ntype Order { order_id: String }\ntype Payment v1 {\n'
?            -------------------                                              ^

+          b' Order { order_id: String }\ntype Payment v1 { order_id: String s'
?                                                          ^^^^^^^^^^^^^^^ +++

-          b'  order_id: String\n  state: String\n}\ntype PaymentError { reason:'
-          b' String }\neffect payments.authorize Order -> Payment ! PaymentEr'
-          b'ror = http.post("payments/authorize")\n\nfn place order: Order -> '
+          b'tate: String }\ntype PaymentError { reason: String }\neffect payme'
+          b'nts.authorize Order -> Payment ! PaymentError = http.post("payments/'
+          b'authorize")\n\nfn place order: Order -> Payment ! PaymentError =\n '
-          b'Payment ! PaymentError =\n  order\n  |> payments.authorize\n',
?            ---------------------------

+          b' order\n  |> payments.authorize\n',
   'renamed': True,
   'temp_left': False} : fmt contract for marks; stderr: 

======================================================================
FAIL: test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) [header]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 125, in test_fmt_rewrites_the_file_and_prints_the_diff
    self.assert_formatted(name)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 111, in assert_formatted
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'cod[308 chars]",           _             -> String = "top"\n[107 chars]alse} != {'cod[308 chars]",   _     -> String = "top"\nfn grade other, [75 chars]alse}
  {'code': 0,
   'error': False,
   'file': b'// EXPERIMENT 0004 slice 6b step 10: OWNER question Q6B-9 (notes.md '
           b'F4), the only case of a signature line above clauses.\n// DL-148 '
           b'(replaces the F4 reading of DL-114): the signature line (no `=`) is '
           b'a row of the table below it.\nfn grade score: String, bonus: Stri'
-          b'ng -> String\nfn grade "a",           _             -> String = "'
?                                          -------- --------

+          b'ng -> String\nfn grade "a",   _     -> String = "top"\nfn grade ot'
?                                                             +++++++++++++++++

-          b'top"\nfn grade other,         bonus         -> String = other\n',
+          b'her, bonus -> String = other\n',
   'renamed': True,
   'temp_left': False} : fmt contract for header; stderr: 

======================================================================
FAIL: test_fmt_rewrites_the_file_and_prints_the_diff (__main__.Slice6Fmt.test_fmt_rewrites_the_file_and_prints_the_diff) [layout]
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 125, in test_fmt_rewrites_the_file_and_prints_the_diff
    self.assert_formatted(name)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 111, in assert_formatted
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        {"code": 0, "file": want, "renamed": True, "temp_left": False, "error": False},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"code": run["code"], "file": run["after"], "renamed": not run["same_inode"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         "temp_left": not run["listing_same"], "error": "error" in run["stderr"]},
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "fmt contract for %s; stderr: %s" % (name, run["stderr"]))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'cod[115 chars]pty {}\ntype Note { text: String }\ntype Amoun[1583 chars]alse} != {'cod[115 chars]pty {  }\ntype Note {   text: String   }\ntype[1323 chars]alse}
  {'code': 0,
   'error': False,
   'file': b'// EXPERIMENT 0004 fmt layout (DL-148): TYPE and ENUM bodies, one cl'
-          b'ause table per block.\ntype Empty {}\ntype Note { text: String }\nt'
?                                                                          -----

+          b'ause table per block.\ntype Empty {  }\ntype Note {   text: String'
?                                               ++              ++

-          b'ype Amount {\n  value: String\n  currency: String\n}\ntype Order'
?                        ---              ---                 ^^

+          b'   }\ntype Amount { value: String currency: String }\ntype Order {'
?            +++++++                                           ^             ++

-          b' {\n  order_id: String\n  amount: Amount\n}\ntype One { id: String }'
?            --                                                            ------

+          b'\n  order_id: String\n    amount: Amount\n}\ntype One {\n  id: St'
?                                    ++                             +++

-          b'\ntype Pair {\n  a: String,\n  b: String\n}\ntype Commented {\n   '
+          b'ring\n}\ntype Pair { a: String, b: String }\ntype Commented {\n    a'
-          b' a: String // a comment inside a body keeps the body as written\n'
?            --

+          b': String // a comment inside a body keeps the body as written\n  '
?                                                                           ++

-          b'  b: String\n}\nenum Channel {\n  Web = "web"\n  App = "app"\n  U'
?            --                            ---            --             ^ ^^^

+          b'b: String\n}\nenum Channel { Web = "web"  App = "app"  Unknown(Str'
?                                                                 ^^^ ^^^^^^^^^

-          b'nknown(String)\n}\nenum Single { Only }\ntype BadAmount {}\ntype Sto'
?            ----------    ^^

+          b'ing) }\nenum Single { Only }\ntype BadAmount {}\ntype StoreError { '
?                ^                                                    ++++++++++

-          b'reError { reason: String }\n\n// One table: a signature line, cons'
?            ----------

+          b'reason: String }\n\n// One table: a signature line, constructor cl'
?                                                                    ++++++++++

-          b'tructor clauses, EFFECT lines, an ENTRY LINE and fn clauses.\nfn '
?            ----------

+          b'auses, EFFECT lines, an ENTRY LINE and fn clauses.\nfn Amount val'
?                                                                   ++++++++++

+          b'ue: String, currency: String -> Amount ! BadAmount\nfn Amount _, '
-          b'Amount             value: String, currency: String -> Amount ! BadAm'
-          b'ount\nfn Amount             _,             ""               -> Am'
-          b'ount ! BadAmount  = BadAmount {}\nfn Amount             value,   '
?                             -                          ------------    -----

+          b'    ""       -> Amount ! BadAmount = BadAmount {}\nfn Amount valu'
?            ++++++++++++++++++

-          b'      currency         -> Amount ! BadAmount  = Amount { value: valu'
?            ^^^^^          --------                      -

+          b'e, currency -> Amount ! BadAmount = Amount { value: value, currency:'
?            ^^                                                      ++++++++++++

+          b' currency }\neffect orders.save Order   -> Order ! StoreError = d'
+          b'b.put("records")\neffect payments.check Note -> Note ! StoreError'
-          b'e, currency: currency }\neffect orders.save    Order             '
-          b'              -> Order  ! StoreError = db.put("records")\neffect '
-          b'payments.check Note                            -> Note   ! StoreErro'
-          b'r = http.post("payments/check")\neffect ui.save        Order     '
?            ^                                               -------

+          b'  = http.post("payments/check")\neffect ui.save Order       -> Or'
?            ^                                                         +++++++

+          b'der ! StoreError = ui.event("save") |> save\nfn check_note n: Not'
-          b'                      -> Order  ! StoreError = ui.event("save") |> s'
-          b'ave\nfn check_note         n: Note                         -> Not'
-          b'e   ! StoreError = n |> payments.check\nfn label              c: '
?              ^                                              -------------

+          b'e -> Note ! StoreError = n |> payments.check\nfn label c: Channel'
?              ^^^^^^^                                                 +++++++

+          b' -> String = "a -> b = c"\n// A comment line ends the block:   x '
+          b' ->   y\nfn save o: Order -> Order ! StoreError = o |> orders.sav'
+          b'e\nfn keep n: Note -> Note = n\nfn tidy Only -> String =\n  "a"\nfn '
-          b'Channel                      -> String              = "a -> b = '
-          b'c"\n// A comment line ends the block:   x  ->   y\nfn save o: Orde'
-          b'r -> Order ! StoreError = o |> orders.save\nfn keep n: Note  -> N'
-          b'ote               = n\nfn tidy Only -> String =\n  "a"\nfn tidy_one'
-          b' x: String -> String = x\n',
+          b'tidy_one x: String -> String = x\n',
?            ++++++++

   'renamed': True,
   'temp_left': False} : fmt contract for layout; stderr: 

======================================================================
FAIL: test_lone_clause_is_a_group_of_one (__main__.Slice6Fmt.test_lone_clause_is_a_group_of_one)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 185, in test_lone_clause_is_a_group_of_one
    self.assertEqual(b"fn lone x: String -> String = x", line(after, 36))
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: b'fn lone x: String -> String = x' != b''

======================================================================
FAIL: test_mark_kept_beside_a_chain_above_v1_and_chain_from_v1_unchanged (__main__.Slice6Fmt.test_mark_kept_beside_a_chain_above_v1_and_chain_from_v1_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 226, in test_mark_kept_beside_a_chain_above_v1_and_chain_from_v1_unchanged
    self.assertIn(b"\ntype Kept v5 {\n  id: String\n  note: String\n}\n", after)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: b'\ntype Kept v5 {\n  id: String\n  note: String\n}\n' not found in b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` VERSION MARK form (b) by DL-104 (D6B-43).\n// Chain from v1 that ends at the mark: the chain implies v3, so the mark goes.\ntype Chained { id: String state: String channel: String }\nmigrate Chained v1 -> v2 { rename status -> state }\nmigrate Chained v2 -> v3 { add channel: String = "web" }\n\n// Mark without a chain (a SQUASH): the mark is the only source of v3, so it stays.\ntype Squashed v3 { id: String }\n\n// Chain that starts above v1, no mark: the mark v5 is written after the name.\ntype Shortened v5 { id: String note: String }\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chain that starts above v1, with its mark: the mark stays.\ntype Kept v5 { id: String note: String }\nmigrate Kept v4 -> v5 { add note: String = "" }\n\n// Chain from v1, no mark: nothing changes.\ntype Plain { id: String state: String }\nmigrate Plain v1 -> v2 { rename status -> state }\n\n// v1 without a chain, as the EFFECT output: the mark selects the versioned decode, so it stays (O3).\ntype Order { order_id: String }\ntype Payment v1 { order_id: String state: String }\ntype PaymentError { reason: String }\neffect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n\nfn place order: Order -> Payment ! PaymentError =\n  order\n  |> payments.authorize\n'

======================================================================
FAIL: test_mark_removed_when_a_chain_from_v1_implies_it (__main__.Slice6Fmt.test_mark_removed_when_a_chain_from_v1_implies_it)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 209, in test_mark_removed_when_a_chain_from_v1_implies_it
    self.assertIn(b"\ntype Chained {\n  id: String\n  state: String\n  channel: String\n}\n", after)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: b'\ntype Chained {\n  id: String\n  state: String\n  channel: String\n}\n' not found in b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` VERSION MARK form (b) by DL-104 (D6B-43).\n// Chain from v1 that ends at the mark: the chain implies v3, so the mark goes.\ntype Chained { id: String state: String channel: String }\nmigrate Chained v1 -> v2 { rename status -> state }\nmigrate Chained v2 -> v3 { add channel: String = "web" }\n\n// Mark without a chain (a SQUASH): the mark is the only source of v3, so it stays.\ntype Squashed v3 { id: String }\n\n// Chain that starts above v1, no mark: the mark v5 is written after the name.\ntype Shortened v5 { id: String note: String }\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chain that starts above v1, with its mark: the mark stays.\ntype Kept v5 { id: String note: String }\nmigrate Kept v4 -> v5 { add note: String = "" }\n\n// Chain from v1, no mark: nothing changes.\ntype Plain { id: String state: String }\nmigrate Plain v1 -> v2 { rename status -> state }\n\n// v1 without a chain, as the EFFECT output: the mark selects the versioned decode, so it stays (O3).\ntype Order { order_id: String }\ntype Payment v1 { order_id: String state: String }\ntype PaymentError { reason: String }\neffect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n\nfn place order: Order -> Payment ! PaymentError =\n  order\n  |> payments.authorize\n'

======================================================================
FAIL: test_mark_written_when_the_chain_starts_above_v1 (__main__.Slice6Fmt.test_mark_written_when_the_chain_starts_above_v1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 222, in test_mark_written_when_the_chain_starts_above_v1
    self.assertIn(b"\ntype Shortened v5 {\n  id: String\n  note: String\n}\n", after)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: b'\ntype Shortened v5 {\n  id: String\n  note: String\n}\n' not found in b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` VERSION MARK form (b) by DL-104 (D6B-43).\n// Chain from v1 that ends at the mark: the chain implies v3, so the mark goes.\ntype Chained { id: String state: String channel: String }\nmigrate Chained v1 -> v2 { rename status -> state }\nmigrate Chained v2 -> v3 { add channel: String = "web" }\n\n// Mark without a chain (a SQUASH): the mark is the only source of v3, so it stays.\ntype Squashed v3 { id: String }\n\n// Chain that starts above v1, no mark: the mark v5 is written after the name.\ntype Shortened v5 { id: String note: String }\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chain that starts above v1, with its mark: the mark stays.\ntype Kept v5 { id: String note: String }\nmigrate Kept v4 -> v5 { add note: String = "" }\n\n// Chain from v1, no mark: nothing changes.\ntype Plain { id: String state: String }\nmigrate Plain v1 -> v2 { rename status -> state }\n\n// v1 without a chain, as the EFFECT output: the mark selects the versioned decode, so it stays (O3).\ntype Order { order_id: String }\ntype Payment v1 { order_id: String state: String }\ntype PaymentError { reason: String }\neffect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n\nfn place order: Order -> Payment ! PaymentError =\n  order\n  |> payments.authorize\n'

======================================================================
FAIL: test_multi_line_clause_breaks_a_group (__main__.Slice6Fmt.test_multi_line_clause_breaks_a_group)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 178, in test_multi_line_clause_breaks_a_group
    self.assertEqual([line(source("clauses"), n) for n in (24, 25, 26)]
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     + [b"fn label Unknown(text) -> String = text",
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        b'fn label Declined(r)   -> String = "declined"'],
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     [line(after, n) for n in range(29, 34)])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [b'fn label Authorized -> String = "ok" // k[156 chars]ed"'] != [b'', b'// A lone single-line clause is a gr[85 chars]g }']

First differing element 0:
b'fn label Authorized -> String = "ok" // keep   this  -> text'
b''

- [b'fn label Authorized -> String = "ok" // keep   this  -> text',
-  b'fn label Pending -> String =',
-  b'  "a//b"',
-  b'fn label Unknown(text) -> String = text',
-  b'fn label Declined(r)   -> String = "declined"']
+ [b'',
+  b'// A lone single-line clause is a group of one.',
+  b'fn lone x: String -> String = x',
+  b'',
+  b'type Order { order_id: String }']

======================================================================
FAIL: test_signature_line_is_a_table_row (__main__.Slice6Fmt.test_signature_line_is_a_table_row)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 145, in test_signature_line_is_a_table_row
    self.assertEqual(expected("header"), self.formatted("header"))
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: b'// [288 chars]",           _             -> String = "top"\n[53 chars]er\n' != b'// [288 chars]",   _     -> String = "top"\nfn grade other, [21 chars]er\n'

======================================================================
FAIL: test_type_body_one_line_up_to_one_field_else_one_field_per_line (__main__.Slice6Fmt.test_type_body_one_line_up_to_one_field_else_one_field_per_line)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 233, in test_type_body_one_line_up_to_one_field_else_one_field_per_line
    self.assertEqual([b"type Empty {}", b"type Note { text: String }", b"type Amount {", b"  value: String",
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      b"  currency: String", b"}", b"type Order {", b"  order_id: String", b"  amount: Amount",
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      b"}", b"type One { id: String }", b"type Pair {", b"  a: String,", b"  b: String", b"}"],
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     [line(after, n) for n in range(2, 17)], "a one-line body expands, a lone field collapses")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [b'type Empty {}', b'type Note { text: String }', b'type[205 chars]b'}'] != [b'type Empty {  }', b'type Note {   text: String   }', [305 chars]b'}']

First differing element 0:
b'type Empty {}'
b'type Empty {  }'

- [b'type Empty {}',
+ [b'type Empty {  }',
?                ++

-  b'type Note { text: String }',
+  b'type Note {   text: String   }',
?               ++              ++

+  b'type Amount { value: String currency: String }',
-  b'type Amount {',
-  b'  value: String',
-  b'  currency: String',
-  b'}',
   b'type Order {',
   b'  order_id: String',
-  b'  amount: Amount',
+  b'    amount: Amount',
?    ++

   b'}',
-  b'type One { id: String }',
-  b'type Pair {',
?         ^^^^

+  b'type One {',
?         ^^^

-  b'  a: String,',
?      ^        -

+  b'  id: String',
?      ^^

+  b'}',
+  b'type Pair { a: String, b: String }',
+  b'type Commented {',
+  b'    a: String // a comment inside a body keeps the body as written',
   b'  b: String',
   b'}'] : a one-line body expands, a lone field collapses

======================================================================
FAIL: test_type_body_with_a_comment_stays_as_written (__main__.Slice6Fmt.test_type_body_with_a_comment_stays_as_written)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 240, in test_type_body_with_a_comment_stays_as_written
    self.assertEqual([line(source("layout"), n) for n in range(13, 17)], [line(after, n) for n in range(17, 21)])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [b'type Commented {', b'    a: String // a c[65 chars]b'}'] != [b'enum Channel { Web = "web"  App = "app"  [100 chars]g }']

First differing element 0:
b'type Commented {'
b'enum Channel { Web = "web"  App = "app"  Unknown(String) }'

- [b'type Commented {',
-  b'    a: String // a comment inside a body keeps the body as written',
-  b'  b: String',
-  b'}']
+ [b'enum Channel { Web = "web"  App = "app"  Unknown(String) }',
+  b'enum Single { Only }',
+  b'type BadAmount {}',
+  b'type StoreError { reason: String }']

======================================================================
FAIL: test_v1_mark_without_chain_is_kept (__main__.Slice6Fmt.test_v1_mark_without_chain_is_kept)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/lennart/Projects/beaml/experiments/0004-generated-replay/tests/slice6_fmt_test.py", line 218, in test_v1_mark_without_chain_is_kept
    self.assertIn(b"\ntype Payment v1 {\n  order_id: String\n  state: String\n}\n", after)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: b'\ntype Payment v1 {\n  order_id: String\n  state: String\n}\n' not found in b'// EXPERIMENT 0004 slice 6b step 10: `beaml fmt` VERSION MARK form (b) by DL-104 (D6B-43).\n// Chain from v1 that ends at the mark: the chain implies v3, so the mark goes.\ntype Chained { id: String state: String channel: String }\nmigrate Chained v1 -> v2 { rename status -> state }\nmigrate Chained v2 -> v3 { add channel: String = "web" }\n\n// Mark without a chain (a SQUASH): the mark is the only source of v3, so it stays.\ntype Squashed v3 { id: String }\n\n// Chain that starts above v1, no mark: the mark v5 is written after the name.\ntype Shortened v5 { id: String note: String }\nmigrate Shortened v4 -> v5 { add note: String = "" }\n\n// Chain that starts above v1, with its mark: the mark stays.\ntype Kept v5 { id: String note: String }\nmigrate Kept v4 -> v5 { add note: String = "" }\n\n// Chain from v1, no mark: nothing changes.\ntype Plain { id: String state: String }\nmigrate Plain v1 -> v2 { rename status -> state }\n\n// v1 without a chain, as the EFFECT output: the mark selects the versioned decode, so it stays (O3).\ntype Order { order_id: String }\ntype Payment v1 { order_id: String state: String }\ntype PaymentError { reason: String }\neffect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")\n\nfn place order: Order -> Payment ! PaymentError =\n  order\n  |> payments.authorize\n'

----------------------------------------------------------------------
Ran 30 tests in 1.066s

FAILED (failures=35, errors=4)
```
