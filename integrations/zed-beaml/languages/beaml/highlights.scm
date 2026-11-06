[
  "type" "enum" "fn" "effect"
  "migrate" "rename" "add" "drop"
  "retire" "keep" "days"
  "with" "do" "else" "end"
] @keyword
(redacted) @keyword
["->" "=" ":" "+" "|>" "!" "|" "<-"] @operator
["{" "}" "(" ")"] @punctuation.bracket
"," @punctuation.delimiter

(comment) @comment
(string) @string
(escape) @string.escape
(version) @number
(integer) @number
(type) @type
(constructor) @constructor
(property) @property
(function_clause name: (identifier) @function)
(effect_declaration name: (_) @function)
(retire_declaration name: (_) @function)
(pipe right: (identifier) @function)
(pipe right: (qualified_name) @function)
((call name: (identifier) @constructor)
 (#match? @constructor "^[A-Z]"))
((call name: (identifier) @function)
 (#not-match? @function "^[A-Z]"))
(call name: (qualified_name) @function)
