const PREC = { pipe: 1, concat: 2 };

module.exports = grammar({
  name: "beaml",

  // Match the compiler's Unicode White_Space set.
  extras: ($) => [/[\t-\r \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/, $.comment],
  word: ($) => $.identifier,

  rules: {
    source_file: ($) =>
      repeat(
        choice(
          $.type_declaration,
          $.enum_declaration,
          $.effect_declaration,
          $.migrate_declaration,
          $.retire_declaration,
          $.function_clause,
        ),
      ),

    // `type Payment v3 { ... }` (DL-061, DL-070, DL-071, DL-072). `interface` is no record keyword (DL-074).
    type_declaration: ($) => seq("type", field("name", $.type), optional(field("version", $.version)), $._field_block),

    _field_block: ($) => seq("{", repeat(seq($.field_declaration, optional(","))), "}"),

    field_declaration: ($) => seq($.property, ":", $._field_type),

    // `redacted` marks PII before the field TYPE (DL-059).
    _field_type: ($) => seq(optional($.redacted), $.type),
    redacted: () => "redacted",

    enum_declaration: ($) =>
      seq("enum", field("name", $.type), "{", repeat(seq($.variant_declaration, optional(","))), "}"),

    variant_declaration: ($) =>
      seq($.constructor, optional(seq(token.immediate("("), optional(commaList($.type)), ")"))),

    // `effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")` (DL-013, DL-015).
    effect_declaration: ($) =>
      seq(
        "effect",
        field("name", $._name),
        field("input", $.type),
        "->",
        field("return_type", $.type),
        optional($.failures),
        "=",
        field("body", $._expression),
      ),

    // MIGRATE CHAIN step: `migrate Payment v1 -> v2 { ... }` (DL-022, DL-072). A plain number is no VERSION (DL-074).
    migrate_declaration: ($) =>
      seq(
        "migrate",
        field("name", $.type),
        field("from", $.version),
        "->",
        field("to", $.version),
        "{",
        repeat(seq($._migrate_operation, optional(","))),
        "}",
      ),

    _migrate_operation: ($) => choice($.rename_operation, $.add_operation, $.drop_operation),

    rename_operation: ($) => seq("rename", field("from", $.property), "->", field("to", $.property)),

    add_operation: ($) => seq("add", $.property, ":", $._field_type, "=", field("value", $._expression)),

    // `drop` names the TYPE (DL-023).
    drop_operation: ($) => seq("drop", $.property, ":", $._field_type),

    // `retire payments.authorize keep 30 days` (DL-055, DL-057).
    retire_declaration: ($) => seq("retire", field("name", $._name), "keep", field("duration", $.integer), "days"),

    function_clause: ($) =>
      seq(
        "fn",
        field("name", $.identifier),
        optional(commaList($.parameter)),
        "->",
        field("return_type", $.type),
        optional($.failures),
        "=",
        field("body", $._expression),
      ),

    // `! A | B` failure TYPES (DL-015).
    failures: ($) => seq("!", $.type, repeat(seq("|", $.type))),

    parameter: ($) => seq($._expression, optional(seq(":", $.type))),

    _name: ($) => choice($.identifier, $.qualified_name),

    qualified_name: ($) => seq($.identifier, repeat1(seq(token.immediate("."), $.identifier))),

    _expression: ($) =>
      choice($.identifier, $.qualified_name, $.string, $.call, $.record, $.concatenation, $.pipe, $.with_expression),

    call: ($) =>
      seq(field("name", $._name), token.immediate("("), optional(commaList($._expression)), ")"),

    record: ($) =>
      seq($.type, "{", optional(seq(commaList($.record_field), optional(","))), "}"),

    record_field: ($) => seq($.property, optional(seq(":", $._expression))),

    concatenation: ($) => prec.right(PREC.concat, seq($._expression, "+", $._expression)),

    // `x |> f |> ns.g` (DL-014).
    pipe: ($) => prec.left(PREC.pipe, seq(field("left", $._expression), "|>", field("right", $._expression))),

    // `with ... do ... else ... end` (DL-014). Only the keywords are decided; the clause shapes are tolerant.
    with_expression: ($) =>
      seq(
        "with",
        commaList($.with_clause),
        "do",
        field("body", $._expression),
        optional(seq("else", repeat($.else_arm))),
        "end",
      ),

    with_clause: ($) => seq(optional(seq(field("pattern", $._expression), "<-")), field("value", $._expression)),

    else_arm: ($) => seq(field("pattern", $._expression), "->", field("body", $._expression)),

    string: ($) => seq('"', repeat(choice($._string_content, $.escape)), token.immediate('"')),
    // Give string contents priority over a line comment inside quotes.
    _string_content: () => token.immediate(prec(1, /[^"\\\x00-\x1f\x7f-\x9f]+/)),
    escape: () => token.immediate(/\\[nrt"\\]/),
    comment: () => token(seq("//", /[^\n]*/)),

    // A TYPE VERSION: `v3` (DL-072); no `v0`, no leading zero. The u32 range is a compiler check.
    version: () => /v[1-9][0-9]*/,
    integer: () => /[0-9]+/,

    identifier: () => /[A-Za-z_][A-Za-z0-9_]*/,
    type: ($) => $.identifier,
    constructor: ($) => $.identifier,
    property: ($) => $.identifier,
  },
});

function commaList(rule) {
  return seq(rule, repeat(seq(",", rule)));
}
