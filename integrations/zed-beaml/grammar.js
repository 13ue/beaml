module.exports = grammar({
  name: "beaml",

  // Match the compiler's Unicode White_Space set.
  extras: ($) => [/[\t-\r \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/, $.comment],
  word: ($) => $.identifier,

  rules: {
    source_file: ($) => repeat(choice($.interface_declaration, $.enum_declaration, $.function_clause)),

    interface_declaration: ($) =>
      seq("interface", field("name", $.type), "{", repeat(seq($.field_declaration, optional(","))), "}"),

    field_declaration: ($) => seq($.property, ":", $.type),

    enum_declaration: ($) =>
      seq("enum", field("name", $.type), "{", repeat(seq($.variant_declaration, optional(","))), "}"),

    variant_declaration: ($) => seq($.constructor, "(", optional(commaList($.type)), ")"),

    function_clause: ($) =>
      seq(
        "fn",
        field("name", $.identifier),
        optional(commaList($.parameter)),
        "->",
        field("return_type", $.type),
        "=",
        field("body", $._expression),
      ),

    parameter: ($) => seq($._expression, optional(seq(":", $.type))),

    _expression: ($) => choice($.identifier, $.string, $.call, $.record, $.concatenation),

    call: ($) =>
      seq(field("name", $.identifier), token.immediate("("), optional(commaList($._expression)), ")"),

    record: ($) =>
      seq($.type, "{", optional(seq(commaList($.record_field), optional(","))), "}"),

    record_field: ($) => seq($.property, optional(seq(":", $._expression))),

    concatenation: ($) => prec.right(seq($._expression, "+", $._expression)),

    string: ($) => seq('"', repeat(choice($._string_content, $.escape)), token.immediate('"')),
    // Give string contents priority over a line comment inside quotes.
    _string_content: () => token.immediate(prec(1, /[^"\\\x00-\x1f\x7f-\x9f]+/)),
    escape: () => token.immediate(/\\[nrt"\\]/),
    comment: () => token(seq("//", /[^\n]*/)),

    identifier: () => /[A-Za-z_][A-Za-z0-9_]*/,
    type: ($) => $.identifier,
    constructor: ($) => $.identifier,
    property: ($) => $.identifier,
  },
});

function commaList(rule) {
  return seq(rule, repeat(seq(",", rule)));
}
