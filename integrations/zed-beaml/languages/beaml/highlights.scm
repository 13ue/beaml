[
  "type" "enum" "fn" "effect"
  "migrate" "rename" "add" "drop"
  "quarantine" "map" "redact"
  "retire" "keep" "days"
  "with" "do" "else" "end"
] @keyword
(redacted) @keyword
["->" "=" ":" "+" "|>" "!" "|" "<-"] @operator
["{" "}" "(" ")" "[" "]"] @punctuation.bracket
"," @punctuation.delimiter

(comment) @comment
(string) @string
(escape) @string.escape
(version) @number
(integer) @number
(type) @type
(constructor) @constructor
(property) @property
((function_clause name: (identifier) @function)
 (#not-match? @function "^[A-Z]"))
(effect_declaration name: (_) @function)
(retire_declaration name: (_) @function)
((pipe right: (identifier) @function)
 (#not-match? @function "^[A-Z]"))
(pipe right: (qualified_name) @function)
((call name: (identifier) @function)
 (#not-match? @function "^[A-Z]"))
(call name: (qualified_name) @function)
; Uppercase identifiers in name and expression positions are constructors and variants (DL-082, DL-086).
([
  (function_clause (identifier) @constructor)
  (effect_declaration body: (identifier) @constructor)
  (add_operation value: (identifier) @constructor)
  (pipe (identifier) @constructor)
  (call (identifier) @constructor)
  (record_field (identifier) @constructor)
  (parameter (identifier) @constructor)
  (concatenation (identifier) @constructor)
  (with_expression body: (identifier) @constructor)
  (with_clause (identifier) @constructor)
  (else_arm (identifier) @constructor)
 ]
 (#match? @constructor "^[A-Z]"))
