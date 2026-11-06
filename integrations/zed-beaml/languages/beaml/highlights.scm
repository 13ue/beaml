["interface" "enum" "fn"] @keyword
["->" "=" ":" "+"] @operator
["{" "}" "(" ")"] @punctuation.bracket
"," @punctuation.delimiter

(comment) @comment
(string) @string
(escape) @string.escape
(type) @type
(constructor) @constructor
(property) @property
(function_clause name: (identifier) @function)
((call name: (identifier) @constructor)
 (#match? @constructor "^[A-Z]"))
((call name: (identifier) @function)
 (#not-match? @function "^[A-Z]"))
