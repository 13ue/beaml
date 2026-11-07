use std::collections::{BTreeMap, BTreeSet};
use std::io::Write;
use std::ops::Range;

type Checked<T> = Result<T, String>;
// TYPE VERSIONS per TYPE name: index 0 is the chain start version (1 without a shortened chain).
type Versions = BTreeMap<String, Vec<Vec<(String, String)>>>;

#[derive(Clone, Debug, PartialEq)]
enum Token {
    Word(String),
    Text(String),
    // A version number of a MIGRATE CHAIN step (slice 2).
    Number(u32),
    Symbol(char),
    Arrow,
    Pipe,
    End,
}

fn lex(source: &str) -> Checked<Vec<(Token, Range<usize>)>> {
    if source.len() > 262_144 {
        return Err("source exceeds spike limit (256 KiB)".into());
    }
    let mut chars = source.char_indices().peekable();
    let mut tokens = Vec::new();
    while let Some((pos, ch)) = chars.next() {
        let token = match ch {
            c if c.is_whitespace() => continue,
            '/' if chars.peek().is_some_and(|(_, c)| *c == '/') => {
                for (_, c) in chars.by_ref() {
                    if c == '\n' {
                        break;
                    }
                }
                continue;
            }
            c if c.is_ascii_alphabetic() || c == '_' => {
                let mut word = c.to_string();
                loop {
                    while chars
                        .peek()
                        .is_some_and(|(_, c)| c.is_ascii_alphanumeric() || *c == '_')
                    {
                        word.push(chars.next().unwrap().1);
                    }
                    // A dotted name (`payments.authorize`, `http.post`): '.' directly between two segments.
                    let mut ahead = chars.clone();
                    if ahead.next().is_some_and(|(_, c)| c == '.')
                        && ahead
                            .peek()
                            .is_some_and(|(_, c)| c.is_ascii_alphabetic() || *c == '_')
                    {
                        word.push(chars.next().unwrap().1);
                    } else {
                        break;
                    }
                }
                Token::Word(word)
            }
            c if c.is_ascii_digit() => {
                let mut digits = c.to_string();
                while chars.peek().is_some_and(|(_, c)| c.is_ascii_digit()) {
                    digits.push(chars.next().unwrap().1);
                }
                Token::Number(
                    digits
                        .parse()
                        .map_err(|_| format!("number too large at byte {pos}"))?,
                )
            }
            '"' => {
                let mut text = String::new();
                let mut closed = false;
                while let Some((_, c)) = chars.next() {
                    match c {
                        '"' => {
                            closed = true;
                            break;
                        }
                        '\\' => text.push(match chars.next().map(|(_, c)| c) {
                            Some('n') => '\n',
                            Some('r') => '\r',
                            Some('t') => '\t',
                            Some('"') => '"',
                            Some('\\') => '\\',
                            _ => return Err(format!("unsupported string escape at byte {pos}")),
                        }),
                        c if c.is_control() => {
                            return Err(format!("control character in string at byte {pos}"));
                        }
                        c => text.push(c),
                    }
                }
                if !closed {
                    return Err(format!("unclosed string at byte {pos}"));
                }
                Token::Text(text)
            }
            '-' if chars.peek().is_some_and(|(_, c)| *c == '>') => {
                chars.next();
                Token::Arrow
            }
            '|' if chars.peek().is_some_and(|(_, c)| *c == '>') => {
                chars.next();
                Token::Pipe
            }
            '{' | '}' | '(' | ')' | ':' | ',' | '=' | '+' | '!' | '|' => Token::Symbol(ch),
            _ => return Err(format!("unsupported token at byte {pos}")),
        };
        let end = chars.peek().map_or(source.len(), |&(next, _)| next);
        tokens.push((token, pos..end));
        if tokens.len() > 8192 {
            return Err("token limit exceeded".into());
        }
    }
    tokens.push((Token::End, source.len()..source.len()));
    Ok(tokens)
}

#[derive(Clone, Debug)]
enum Node {
    Text(String),
    // An integer literal (slice 6b, D6B-02). No negative literal, no arithmetic (D6B-03).
    Int(u32),
    Name(String),
    Call(String, Vec<Node>),
    Record(String, Vec<(String, Node)>),
    Plus(Box<Node>, Box<Node>),
    Annotated(Box<Node>, String),
    // `head |> step |> step`: a clause body, a call argument or a record field value (DL-086).
    Pipe(Box<Node>, Vec<String>),
}

#[derive(Clone, Debug)]
enum Definition {
    Record(Vec<(String, String)>),
    Enum(Vec<(String, Vec<String>)>),
}
#[derive(Clone, Debug)]
struct Clause {
    name: String,
    // The signature this clause belongs to: the fn name, or `T#k` for signature k of a constructor `fn T` (D6B-13).
    key: String,
    args: Vec<Node>,
    output: String,
    failures: Vec<String>,
    body: Node,
    source_range: Range<usize>,
}
// `fn NAME p: T, ... -> OUT ! ERR` without `=` (slice 6b, D6B-12): the clauses below take its TYPES by position.
#[derive(Clone, Debug)]
struct SignatureLine {
    name: String,
    key: String,
    args: Vec<Node>,
    output: String,
    failures: Vec<String>,
    start: usize,
}
// `effect NAME IN -> OUT ! ERR = KIND("path")`: an operation that leaves the module.
#[derive(Clone, Debug)]
struct Effect {
    name: String,
    input: String,
    output: String,
    failures: Vec<String>,
    kind: String,
    path: String,
    source_range: Range<usize>,
}
// `migrate T va -> vb { change, change }`: one MIGRATE STEP of the MIGRATE CHAIN of the TYPE T.
// The `type` is the newest TYPE VERSION; older versions are derived backwards.
#[derive(Clone, Debug)]
struct Migration {
    type_name: String,
    from: u32,
    to: u32,
    changes: Vec<Change>,
    // From the `migrate` keyword to the closing `}` (slice 4: the removal of a DEAD LINE).
    source_range: Range<usize>,
}
// `retire <operation> keep <n> days` (slice 4): the operation has left the source on purpose. Its stored
// RESPONSE RECORDS are RETIRED RECORDS: not path-checked, not replayable, kept `keep_days` days (metadata only).
#[derive(Clone, Debug)]
struct Retire {
    operation: String,
    keep_days: u32,
    // From the `retire` keyword to `days`.
    source_range: Range<usize>,
}
// One MIGRATE CHANGE (slice 3): `rename old -> new`, `add f: T = "c"` or `drop f: T`.
#[derive(Clone, Debug)]
enum Change {
    Rename(String, String),
    // The constant is `Ok(text)` for a string literal, `Err(token text)` for any other token (K3).
    Add(String, String, Result<String, String>),
    Drop(String, String),
}
#[derive(Default)]
struct Program {
    types: BTreeMap<String, Definition>,
    clauses: Vec<Clause>,
    signature_lines: Vec<SignatureLine>,
    effects: Vec<Effect>,
    migrations: Vec<Migration>,
    retires: Vec<Retire>,
    // Slice 5: the VERSION MARK `type T vN { ... }` per record TYPE that has one (DL-070, DL-071).
    marks: BTreeMap<String, u32>,
    // Slice 6b (DL-082): the ENUM LITERALS `V = "text"` per enum, in source order (D6B-21).
    literals: BTreeMap<String, Vec<(String, String)>>,
    // Slice 5: the byte end of the TYPE name in each `type` declaration (where `--remove-dead` writes a mark).
    name_ends: BTreeMap<String, usize>,
}

// Slice 5 (DL-072, DL-075): a VERSION is a Word `v` DIGITS, no leading zero, from v1 to v4294967295.
fn version_word(word: &str) -> Result<u32, String> {
    let digits = word.strip_prefix('v').unwrap_or("");
    if digits.is_empty() || !digits.bytes().all(|b| b.is_ascii_digit()) {
        return Err(format!(
            "{word} is not a VERSION; write a version as v<number>, for example v3"
        ));
    }
    let trimmed = digits.trim_start_matches('0');
    if trimmed.is_empty() {
        return Err(format!("{word}: versions start at v1"));
    }
    if trimmed.len() != digits.len() {
        return Err(format!(
            "{word}: a VERSION has no leading zero; write v{trimmed}"
        ));
    }
    digits.parse::<u32>().map_err(|_| {
        format!(
            "{word}: version number too large; the largest is v{}",
            u32::MAX
        )
    })
}

struct Parser {
    tokens: Vec<(Token, Range<usize>)>,
    at: usize,
}
impl Parser {
    fn peek(&self) -> &Token {
        &self.tokens[self.at].0
    }
    fn error(&self, message: &str) -> String {
        format!("{message} at byte {}", self.tokens[self.at].1.start)
    }
    fn eat(&mut self, ch: char) -> bool {
        if self.peek() == &Token::Symbol(ch) {
            self.at += 1;
            true
        } else {
            false
        }
    }
    fn expect(&mut self, ch: char) -> Checked<()> {
        if self.eat(ch) {
            Ok(())
        } else {
            Err(self.error(&format!("expected '{ch}'")))
        }
    }
    fn word(&mut self) -> Checked<String> {
        match self.peek().clone() {
            Token::Word(word) if !word.contains('.') => {
                self.at += 1;
                Ok(word)
            }
            _ => Err(self.error("expected identifier")),
        }
    }
    // A plain or dotted name: EFFECT names, EFFECT kinds and pipe steps only.
    fn dotted(&mut self) -> Checked<String> {
        if let Token::Word(word) = self.peek().clone() {
            self.at += 1;
            Ok(word)
        } else {
            Err(self.error("expected name"))
        }
    }
    // One VERSION of a `migrate` line (slice 5): `Ok(n)` for `v<n>`, `Err(n)` for a plain number (an error
    // with a `help` line, reported by the caller once both numbers are read).
    fn version(&mut self, context: &str) -> Checked<Result<u32, u32>> {
        match self.peek().clone() {
            Token::Word(word) => {
                let version =
                    version_word(&word).map_err(|e| self.error(&format!("{context} {e}")))?;
                self.at += 1;
                Ok(Ok(version))
            }
            Token::Number(number) => {
                self.at += 1;
                Ok(Err(number))
            }
            _ => Err(self.error(&format!("{context}: expected a VERSION v<number>"))),
        }
    }
    fn arrow(&mut self) -> Checked<()> {
        if self.peek() != &Token::Arrow {
            return Err(self.error("expected '->'"));
        }
        self.at += 1;
        Ok(())
    }
    // One MIGRATE CHANGE: `rename old -> new`, `add f: T = <constant>` or `drop f: T`.
    fn change(&mut self) -> Checked<Change> {
        let kind = match self.peek().clone() {
            Token::Word(word) => word,
            _ => return Err(self.error("expected rename, add or drop")),
        };
        match kind.as_str() {
            "rename" => {
                self.at += 1;
                let old = self.word()?;
                self.arrow()?;
                Ok(Change::Rename(old, self.word()?))
            }
            "add" => {
                self.at += 1;
                let field = self.word()?;
                self.expect(':')?;
                let ty = self.word()?;
                self.expect('=')?;
                let constant = match self.peek().clone() {
                    Token::Text(text) => Ok(text),
                    Token::Word(word) => Err(word),
                    Token::Number(number) => Err(number.to_string()),
                    _ => return Err(self.error("expected a constant after '='")),
                };
                self.at += 1;
                Ok(Change::Add(field, ty, constant))
            }
            "drop" => {
                self.at += 1;
                let field = self.word()?;
                self.expect(':')?;
                Ok(Change::Drop(field, self.word()?))
            }
            other => Err(self.error(&format!(
                "unsupported migrate step: {other}; a MIGRATE CHANGE is rename, add or drop"
            ))),
        }
    }
    // Optional `! Error | Error`.
    fn failures(&mut self) -> Checked<Vec<String>> {
        let mut failures = Vec::new();
        if self.eat('!') {
            loop {
                failures.push(self.word()?);
                if !self.eat('|') {
                    break;
                }
            }
        }
        Ok(failures)
    }
    fn node(&mut self, depth: usize) -> Checked<Node> {
        if depth > 64 {
            return Err(self.error("nesting limit exceeded"));
        }
        let mut node = match self.peek().clone() {
            Token::Text(s) => {
                self.at += 1;
                Node::Text(s)
            }
            Token::Number(n) => {
                self.at += 1;
                Node::Int(n)
            }
            Token::Word(_) => {
                let name = self.word()?;
                if self.peek() == &Token::Symbol('(')
                    && self.tokens[self.at].1.start != self.tokens[self.at - 1].1.end
                {
                    return Err(self.error("no whitespace before call or constructor parentheses"));
                }
                if self.eat('(') {
                    let mut args = Vec::new();
                    if !self.eat(')') {
                        loop {
                            args.push(self.piped(depth + 1)?);
                            if self.eat(')') {
                                break;
                            }
                            self.expect(',')?;
                        }
                    }
                    Node::Call(name, args)
                } else if self.eat('{') {
                    let mut fields = Vec::new();
                    if !self.eat('}') {
                        loop {
                            let field = self.word()?;
                            let value = if self.eat(':') {
                                self.piped(depth + 1)?
                            } else {
                                Node::Name(field.clone())
                            };
                            fields.push((field, value));
                            if self.eat('}') {
                                break;
                            }
                            self.expect(',')?;
                            if self.eat('}') {
                                break;
                            }
                        }
                    }
                    Node::Record(name, fields)
                } else if upper(&name) {
                    // D6B-20: a bare uppercase name is a variant `A()`, never a variable.
                    Node::Call(name, Vec::new())
                } else {
                    Node::Name(name)
                }
            }
            _ => return Err(self.error("expected expression or pattern")),
        };
        while self.eat('+') {
            node = Node::Plus(Box::new(node), Box::new(self.node(depth + 1)?));
        }
        Ok(node)
    }
    // D6B-25: `|>` binds weaker than `+`; a pipe ends at `,`, `)` and `}`. Steps are bare names.
    fn piped(&mut self, depth: usize) -> Checked<Node> {
        let node = self.node(depth)?;
        if self.peek() != &Token::Pipe {
            return Ok(node);
        }
        let mut steps = Vec::new();
        while self.peek() == &Token::Pipe {
            self.at += 1;
            steps.push(self.dotted()?);
        }
        Ok(Node::Pipe(Box::new(node), steps))
    }
    fn program(mut self) -> Checked<Program> {
        let mut program = Program::default();
        let mut keys: BTreeMap<String, String> = BTreeMap::new();
        while self.peek() != &Token::End {
            let start = self.tokens[self.at].1.start;
            match self.word()?.as_str() {
                // DL-061, DL-074: `interface` stays free for behaviour contracts; a record is a `type`.
                "interface" => {
                    let name = match self.peek() {
                        Token::Word(word) if upper(word) => word.clone(),
                        _ => "<Name>".into(),
                    };
                    return Err(format!(
                        "error: interface does not declare a record; records use type\n  at byte {start}\n  help: declare: type {name} {{ ... }}\n  note: the word interface is kept for behaviour contracts"
                    ));
                }
                "type" => {
                    let name = self.word()?;
                    let name_end = self.tokens[self.at - 1].1.end;
                    // The optional VERSION MARK `type T vN {` (slice 5).
                    match self.peek().clone() {
                        Token::Symbol('{') => {}
                        Token::Word(word) => {
                            let mark = version_word(&word)
                                .map_err(|e| self.error(&format!("type {name} {e}")))?;
                            self.at += 1;
                            program.marks.insert(name.clone(), mark);
                        }
                        Token::Number(number) => {
                            return Err(format!(
                                "{}\n  help: write: type {name} v{number}",
                                self.error(&format!(
                                    "type {name} {number}: expected '{{' or a VERSION MARK v<number>"
                                ))
                            ));
                        }
                        _ => {
                            return Err(self.error(&format!(
                                "type {name}: expected '{{' or a VERSION MARK v<number>"
                            )));
                        }
                    }
                    if program.name_ends.insert(name.clone(), name_end).is_some() {
                        return Err(self.error("duplicate type"));
                    }
                    self.expect('{')?;
                    let mut fields = Vec::new();
                    while !self.eat('}') {
                        let field = self.word()?;
                        self.expect(':')?;
                        fields.push((field, self.word()?));
                        self.eat(',');
                    }
                    if program
                        .types
                        .insert(name, Definition::Record(fields))
                        .is_some()
                    {
                        return Err(self.error("duplicate type"));
                    }
                }
                "enum" => {
                    let name = self.word()?;
                    self.expect('{')?;
                    let mut variants = Vec::new();
                    let mut literals = Vec::new();
                    while !self.eat('}') {
                        let variant = self.word()?;
                        // D6B-20: a bare variant `A` is `A()`.
                        let mut args = Vec::new();
                        if self.eat('(') && !self.eat(')') {
                            loop {
                                args.push(self.word()?);
                                if self.eat(')') {
                                    break;
                                }
                                self.expect(',')?;
                            }
                        }
                        if self.eat('=') {
                            let Token::Text(literal) = self.peek().clone() else {
                                return Err(self.error("expected a string literal after '='"));
                            };
                            self.at += 1;
                            literals.push((variant.clone(), literal));
                        }
                        variants.push((variant, args));
                        self.eat(',');
                    }
                    if !literals.is_empty() {
                        program.literals.insert(name.clone(), literals);
                    }
                    if program
                        .types
                        .insert(name, Definition::Enum(variants))
                        .is_some()
                    {
                        return Err(self.error("duplicate type"));
                    }
                }
                "fn" => {
                    let name = self.word()?;
                    // D6B-13, D6B-15: signature k of a constructor `fn T` is `T#k`; its clauses follow it.
                    let key = if !upper(&name) {
                        name.clone()
                    } else {
                        keys.get(&name).cloned().unwrap_or(format!("{name}#1"))
                    };
                    let mut args = Vec::new();
                    if self.peek() != &Token::Arrow {
                        loop {
                            let mut arg = self.node(0)?;
                            if self.eat(':') {
                                arg = Node::Annotated(Box::new(arg), self.word()?);
                            }
                            args.push(arg);
                            if !self.eat(',') {
                                break;
                            }
                        }
                    }
                    self.arrow()?;
                    let output = self.word()?;
                    let failures = self.failures()?;
                    if !self.eat('=') {
                        // A signature line has `name: TYPE` parameters only (D6B-12).
                        let typed = |arg: &Node| matches!(arg, Node::Annotated(inner, _) if matches!(inner.as_ref(), Node::Name(n) if lower(n)));
                        if !args.iter().all(typed) {
                            return Err(format!(
                                "error: fn {name}: a signature line has name: TYPE parameters only"
                            ));
                        }
                        let key = if upper(&name) {
                            let k = program
                                .signature_lines
                                .iter()
                                .filter(|l| l.name == name)
                                .count();
                            format!("{name}#{}", k + 1)
                        } else {
                            key
                        };
                        keys.insert(name.clone(), key.clone());
                        program.signature_lines.push(SignatureLine {
                            name,
                            key,
                            args,
                            output,
                            failures,
                            start,
                        });
                        continue;
                    }
                    let body = self.piped(0)?;
                    program.clauses.push(Clause {
                        name,
                        key,
                        args,
                        output,
                        failures,
                        body,
                        source_range: start..self.tokens[self.at - 1].1.end,
                    });
                }
                "effect" => {
                    let name = self.dotted()?;
                    let input = self.word()?;
                    self.arrow()?;
                    let output = self.word()?;
                    let failures = self.failures()?;
                    self.expect('=')?;
                    let kind = self.dotted()?;
                    if self.tokens[self.at].1.start != self.tokens[self.at - 1].1.end {
                        return Err(
                            self.error("no whitespace before call or constructor parentheses")
                        );
                    }
                    self.expect('(')?;
                    let path = match self.peek().clone() {
                        Token::Text(path) => {
                            self.at += 1;
                            path
                        }
                        _ => return Err(self.error("expected effect target string")),
                    };
                    self.expect(')')?;
                    program.effects.push(Effect {
                        name,
                        input,
                        output,
                        failures,
                        kind,
                        path,
                        source_range: start..self.tokens[self.at - 1].1.end,
                    });
                }
                "migrate" => {
                    let type_name = self.word()?;
                    // DL-072, DL-074: every version number has a `v`; a plain number is an error with help.
                    let context = format!("migrate {type_name}");
                    let first = self.at;
                    let from = self.version(&context)?;
                    let plain = |v: Result<u32, u32>| v.unwrap_or_else(|n| n);
                    if let Err(number) = from {
                        let to = (self.peek() == &Token::Arrow)
                            .then(|| self.tokens.get(self.at + 1).map(|t| t.0.clone()))
                            .flatten()
                            .and_then(|t| match t {
                                Token::Number(n) => Some(n.to_string()),
                                Token::Word(w) => version_word(&w).ok().map(|v| v.to_string()),
                                _ => None,
                            })
                            .unwrap_or_else(|| "<number>".into());
                        return Err(format!(
                            "error: migrate {type_name} {number}: a version number needs v\n  at byte {}\n  help: write: migrate {type_name} v{number} -> v{to}",
                            self.tokens[first].1.start
                        ));
                    }
                    self.arrow()?;
                    let second = self.at;
                    let to = self.version(&format!("{context} v{} ->", plain(from)))?;
                    if let Err(number) = to {
                        return Err(format!(
                            "error: migrate {type_name} v{} -> {number}: a version number needs v\n  at byte {}\n  help: write: migrate {type_name} v{} -> v{number}",
                            plain(from),
                            self.tokens[second].1.start,
                            plain(from)
                        ));
                    }
                    let (from, to) = (plain(from), plain(to));
                    self.expect('{')?;
                    // MIGRATE CHANGES separated by commas; no trailing comma (K9, K10).
                    let mut changes = Vec::new();
                    if !self.eat('}') {
                        loop {
                            changes.push(self.change()?);
                            if self.eat('}') {
                                break;
                            }
                            if !self.eat(',') {
                                return Err(self.error(
                                    "expected ',' between two MIGRATE CHANGES or '}' after the last one",
                                ));
                            }
                        }
                    }
                    program.migrations.push(Migration {
                        type_name,
                        from,
                        to,
                        changes,
                        source_range: start..self.tokens[self.at - 1].1.end,
                    });
                }
                "retire" => {
                    // T3-T7: `retire OPERATION keep NUMBER days`. The lexer rejects `-1`, `1.5` and a
                    // number above the u32 range before the parser.
                    let operation = match self.peek().clone() {
                        Token::Word(word) => {
                            self.at += 1;
                            word
                        }
                        _ => return Err(self.error("retire: expected an operation name")),
                    };
                    if !operation_name(&operation) {
                        return Err(format!(
                            "retire {operation}: invalid operation name (expected namespace.operation, two lowercase segments) at byte {}",
                            self.tokens[self.at - 1].1.start
                        ));
                    }
                    if !matches!(self.peek(), Token::Word(word) if word == "keep") {
                        return Err(
                            self.error(&format!("retire {operation}: expected keep <n> days"))
                        );
                    }
                    self.at += 1;
                    let keep_days = match self.peek().clone() {
                        Token::Number(number) => {
                            self.at += 1;
                            number
                        }
                        _ => {
                            return Err(self.error(&format!(
                                "retire {operation} keep: expected number of days"
                            )));
                        }
                    };
                    let unit = match self.peek().clone() {
                        Token::Word(word) if word == "days" => {
                            self.at += 1;
                            None
                        }
                        Token::Word(word) => Some(word),
                        Token::End => Some("the end of the source".into()),
                        _ => Some("another token".into()),
                    };
                    if let Some(unit) = unit {
                        return Err(self.error(&format!(
                            "retire {operation} keep {keep_days}: keep supports days only, not {unit}"
                        )));
                    }
                    program.retires.push(Retire {
                        operation,
                        keep_days,
                        source_range: start..self.tokens[self.at - 1].1.end,
                    });
                }
                _ => return Err(self.error("expected type, enum, effect, migrate, retire or fn")),
            }
        }
        Ok(program)
    }
}

struct Checker<'a> {
    program: &'a Program,
    variants: BTreeMap<String, (String, Vec<String>)>,
    signatures: BTreeMap<String, (Vec<String>, String)>,
    // The `!` list of each function; empty for a function that cannot fail.
    failures: BTreeMap<String, Vec<String>>,
    // TYPE VERSIONS of each TYPE with a MIGRATE CHAIN: index 0 is the chain start, the last is the interface.
    versions: Versions,
    // TYPES with a constructor `fn T` (DL-092): nominal TYPES (D6B-17).
    constructors: BTreeSet<String>,
}
// The Elixir name of a signature key: signature k of a constructor `fn T` (`T#k`) is `new_T_k` (D6B-15).
fn elixir_name(key: &str) -> String {
    match key.split_once('#') {
        Some((name, k)) => format!("new_{name}_{k}"),
        None => key.to_string(),
    }
}
// The BEAML fn name of a signature key.
fn display(key: &str) -> &str {
    key.split('#').next().unwrap_or(key)
}

// The MIGRATE CHAIN check: MIGRATE STEPS `1 -> 2 -> ...` without gaps per TYPE. Old TYPE VERSIONS are
// derived backwards from the `interface`, from the newest MIGRATE STEP to the oldest (slice 3):
// `rename old -> new` names the field `new` of version b `old` in version a; `add f` removes `f`;
// `drop f: String` adds `f: String`. The consistency checks K1-K8 run here, before the EFFECT checks
// (DL-050). In one MIGRATE STEP, K7 and K8 run before the checks of the single MIGRATE CHANGES.
fn derive_versions(program: &Program) -> Checked<Versions> {
    let mut chains: BTreeMap<&str, Vec<&Migration>> = BTreeMap::new();
    for step in &program.migrations {
        chains.entry(&step.type_name).or_default().push(step);
    }
    let mut versions = BTreeMap::new();
    for (name, steps) in chains {
        let Some(Definition::Record(newest)) = program.types.get(name) else {
            return Err(format!("migrate {name}: unknown type: {name}"));
        };
        // Slice 4: a MIGRATE CHAIN starts at any version k >= 1 (its first MIGRATE STEP `k -> k+1`).
        let start = u64::from(steps[0].from);
        for (index, step) in steps.iter().enumerate() {
            let from = start + index as u64;
            if from == 0 {
                return Err(format!(
                    "migrate {name} v0 -> v{}: a MIGRATE CHAIN starts at v1 or higher",
                    step.to
                ));
            }
            if u64::from(step.from) != from || u64::from(step.to) != from + 1 {
                return Err(format!(
                    "migrate {name} v{} -> v{}: the MIGRATE CHAIN of {name} must count without gaps from its first MIGRATE STEP, expected v{from} -> v{}",
                    step.from,
                    step.to,
                    from + 1
                ));
            }
        }
        let end = steps.last().unwrap().to;
        let mark = program.marks.get(name).copied();
        mark_form_allowed(name, mark, Some((steps[0].from, end)))?;
        if let Some(mark) = mark {
            mark_agrees(name, mark, end)?;
        }
        let mut chain = vec![newest.clone()];
        for step in steps.iter().rev() {
            let current = chain.last().unwrap();
            let (a, b) = (step.from, step.to);
            let label = format!("migrate {name} v{a} -> v{b}");
            // K8: an empty MIGRATE STEP.
            if step.changes.is_empty() {
                return Err(format!(
                    "{label}: a MIGRATE STEP needs at least one rename, add or drop"
                ));
            }
            // K7: one field name at most once per MIGRATE STEP (both names of a `rename`).
            let mut seen = BTreeSet::new();
            for change in &step.changes {
                let names: Vec<&String> = match change {
                    Change::Rename(old, new) => vec![old, new],
                    Change::Add(field, _, _) | Change::Drop(field, _) => vec![field],
                };
                for field in names {
                    if !seen.insert(field.clone()) {
                        return Err(format!(
                            "{label}: field {field} is named two times in one MIGRATE STEP; a field that leaves and comes back needs two MIGRATE STEPS"
                        ));
                    }
                }
            }
            let type_of = |field: &str| {
                current
                    .iter()
                    .find(|(f, _)| f == field)
                    .map(|(_, t)| t.clone())
            };
            let mut previous = current.clone();
            for change in &step.changes {
                match change {
                    Change::Rename(old, new) => {
                        if !lower(old) {
                            return Err(format!(
                                "{label}: field names must start lowercase: {old}"
                            ));
                        }
                        if type_of(new).is_none() {
                            return Err(format!(
                                "{label}: rename {old} -> {new}: field {new} is not in {name} v{b}"
                            ));
                        }
                        if type_of(old).is_some() {
                            return Err(format!(
                                "{label}: rename {old} -> {new}: field {old} is still in {name} v{b}"
                            ));
                        }
                        for field in previous.iter_mut() {
                            if &field.0 == new {
                                field.0 = old.clone();
                            }
                        }
                    }
                    Change::Add(field, ty, constant) => {
                        // K1, K2, K4, K3.
                        let Some(actual) = type_of(field) else {
                            return Err(format!(
                                "{label}: add {field}: field {field} is not in {name} v{b}"
                            ));
                        };
                        if &actual != ty {
                            return Err(format!(
                                "{label}: add {field}: {ty}: field {field} has the TYPE {actual} in {name} v{b}"
                            ));
                        }
                        if ty != "String" {
                            return Err(format!(
                                "{label}: add {field}: {ty}: add supports String fields only"
                            ));
                        }
                        if let Err(token) = constant {
                            return Err(format!(
                                "{label}: add {field}: String = {token}: the constant must be a String literal"
                            ));
                        }
                        previous.retain(|(f, _)| f != field);
                    }
                    Change::Drop(field, ty) => {
                        // K6, K5.
                        if ty != "String" {
                            return Err(format!(
                                "{label}: drop {field}: {ty}: drop supports String fields only"
                            ));
                        }
                        if !lower(field) {
                            return Err(format!(
                                "{label}: field names must start lowercase: {field}"
                            ));
                        }
                        if type_of(field).is_some() {
                            return Err(format!(
                                "{label}: drop {field}: field {field} is still in {name} v{b}"
                            ));
                        }
                        previous.push((field.clone(), ty.clone()));
                    }
                }
            }
            chain.push(previous);
        }
        chain.reverse();
        versions.insert(name.to_string(), chain);
    }
    for (name, &mark) in &program.marks {
        if !versions.contains_key(name) {
            mark_form_allowed(name, Some(mark), None)?;
        }
    }
    Ok(versions)
}

// O7 answered (DL-080, option (a)): which VERSION MARK forms are legal. `chain` is (first `from`, last `to`) of the
// MIGRATE CHAIN of `name`, if it has one. Every mark that agrees with the chain is legal (the agreement is error M1,
// `mark_agrees`), a mark without a chain is legal, and a chain without a mark is legal, also when it starts above
// v1. Option (b) (a mark only after a SQUASH) is the default form; `beaml fmt` writes it, with no compiler warning
// (DL-081, not built), so this function rejects nothing.
fn mark_form_allowed(_name: &str, _mark: Option<u32>, _chain: Option<(u32, u32)>) -> Checked<()> {
    Ok(())
}

// Error M1 (slice 5, DL-071): a VERSION MARK and a MIGRATE CHAIN must agree. A source check, before `--stored`.
fn mark_agrees(name: &str, mark: u32, end: u32) -> Checked<()> {
    if mark == end {
        return Ok(());
    }
    let help = if mark < end {
        format!("write: type {name} v{end}")
    } else if u64::from(mark) == u64::from(end) + 1 {
        format!(
            "add migrate {name} v{end} -> v{mark} {{ ... }}, or write type {name} v{end} if no record of v{mark} exists"
        )
    } else {
        format!(
            "add migrate {name} v{end} -> v{} {{ ... }} and the next MIGRATE STEPS to v{mark}, or write type {name} v{end} if no record newer than v{end} exists",
            end + 1
        )
    };
    Err(format!(
        "error: type {name} v{mark} disagrees with its MIGRATE CHAIN: the last MIGRATE STEP is migrate {name} v{} -> v{end}\n  help: the VERSION MARK and the MIGRATE CHAIN must agree; {help}",
        end - 1
    ))
}

// An EFFECT name or a RETIRE LINE operation: `namespace.operation`, two segments that start lowercase.
fn operation_name(name: &str) -> bool {
    let segments: Vec<&str> = name.split('.').collect();
    segments.len() == 2 && segments.iter().all(|s| lower(s))
}
fn upper(name: &str) -> bool {
    name.as_bytes().first().is_some_and(u8::is_ascii_uppercase)
}
fn lower(name: &str) -> bool {
    name.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
}
fn unique(names: impl Iterator<Item = String>) -> Checked<()> {
    let mut seen = BTreeSet::new();
    for name in names {
        if !seen.insert(name.clone()) {
            return Err(format!("duplicate name: {name}"));
        }
    }
    Ok(())
}
impl<'a> Checker<'a> {
    fn new(program: &'a Program) -> Checked<Self> {
        let mut checker = Self {
            program,
            variants: BTreeMap::new(),
            signatures: BTreeMap::new(),
            failures: BTreeMap::new(),
            versions: BTreeMap::new(),
            constructors: program
                .clauses
                .iter()
                .map(|c| &c.name)
                .chain(program.signature_lines.iter().map(|s| &s.name))
                .filter(|n| upper(n))
                .cloned()
                .collect(),
        };
        for (name, def) in &program.types {
            if !upper(name) || name == "String" || name == "Int" {
                return Err(format!("invalid type name: {name}"));
            }
            match def {
                Definition::Record(fields) => {
                    unique(fields.iter().map(|(n, _)| n.clone()))?;
                    for (field, _) in fields {
                        if !lower(field) {
                            return Err("field names must start lowercase".into());
                        }
                    }
                }
                Definition::Enum(variants) => {
                    if variants.is_empty() {
                        return Err("empty enums are outside this spike".into());
                    }
                    for (variant, args) in variants {
                        if !upper(variant)
                            || program.types.contains_key(variant)
                            || checker
                                .variants
                                .insert(variant.clone(), (name.clone(), args.clone()))
                                .is_some()
                        {
                            return Err(format!("invalid or duplicate constructor: {variant}"));
                        }
                    }
                    if let Some(literals) = program.literals.get(name) {
                        checker.literal_rules(name, variants, literals)?;
                    }
                }
            }
        }
        for name in program.types.keys() {
            checker.check_type(name, &mut Vec::new())?;
        }
        checker.versions = derive_versions(program)?;
        if program.clauses.is_empty() {
            return Err("expected at least one function".into());
        }
        // D6B-12, D6B-14: a signature line gives the parameter TYPES. A constructor has one signature per line.
        let mut lines: BTreeMap<&str, usize> = BTreeMap::new();
        for (index, line) in program.signature_lines.iter().enumerate() {
            checker.fn_name(&line.name, &line.output)?;
            checker.check_type(&line.output, &mut Vec::new())?;
            let mut vars = BTreeMap::new();
            let mut args = Vec::new();
            for pattern in &line.args {
                args.push(checker.pattern(pattern, None, &mut vars)?);
            }
            let owner = format!("fn {}", line.name);
            checker.failure_types(&owner, &line.failures)?;
            checker.overlap(&owner, &line.output, &line.failures, true)?;
            let signature = (args, line.output.clone());
            let unreachable = |help: &str| {
                format!(
                    "unreachable signature: {0}\n  help: an earlier signature line of fn {0} {help}; remove this one",
                    line.name
                )
            };
            lines.entry(&line.name).or_insert(line.start);
            if upper(&line.name) {
                // D6B-23: unreachable when every (name, TYPE) of an earlier signature line is also in this one.
                let pairs = |l: &SignatureLine| -> Vec<(String, String)> {
                    l.args
                        .iter()
                        .filter_map(|a| match a {
                            Node::Annotated(inner, ty) => match inner.as_ref() {
                                Node::Name(n) => Some((n.clone(), ty.clone())),
                                _ => None,
                            },
                            _ => None,
                        })
                        .collect()
                };
                let mine = pairs(line);
                for earlier in program.signature_lines[..index]
                    .iter()
                    .filter(|l| l.name == line.name)
                {
                    let theirs = pairs(earlier);
                    if theirs.iter().all(|p| mine.contains(p)) {
                        return Err(unreachable(if theirs.len() == mine.len() {
                            "has the same parameters"
                        } else {
                            "has a part of these parameters and matches first"
                        }));
                    }
                }
            } else if checker.signatures.contains_key(&line.key) {
                // D6B-14: a lowercase fn has one signature line.
                if checker.signatures.get(&line.key) == Some(&signature)
                    && checker.failures.get(&line.key) == Some(&line.failures)
                {
                    return Err(unreachable("has the same parameters"));
                }
                return Err(format!("inconsistent function signature: {}", line.name));
            }
            checker.signatures.insert(line.key.clone(), signature);
            checker
                .failures
                .insert(line.key.clone(), line.failures.clone());
        }
        for clause in &program.clauses {
            checker.fn_name(&clause.name, &clause.output)?;
            // D6B-13: with a signature line, no clause stands before it.
            let line = lines.get(clause.name.as_str());
            if line.is_some_and(|start| clause.source_range.start < *start) {
                return Err(format!(
                    "error: fn {}: a clause stands before the signature line\n  help: move the signature line above the first clause",
                    clause.name
                ));
            }
            checker.check_type(&clause.output, &mut Vec::new())?;
            let mut vars = BTreeMap::new();
            let mut args = Vec::new();
            let given = line.map(|_| checker.signatures[&clause.key].0.clone());
            for (index, pattern) in clause.args.iter().enumerate() {
                let expected = given.as_ref().and_then(|types| types.get(index));
                args.push(checker.pattern(pattern, expected.map(String::as_str), &mut vars)?);
            }
            let owner = format!("fn {}", clause.name);
            checker.failure_types(&owner, &clause.failures)?;
            checker.overlap(&owner, &clause.output, &clause.failures, true)?;
            // An Int column against an earlier clause is a type mismatch (slice 6b). Sources without Int
            // keep "inconsistent function signature".
            if let Some((previous, _)) = checker.signatures.get(&clause.key) {
                for (ty, expected) in args.iter().zip(previous) {
                    if ty == "Int" || expected == "Int" {
                        checker.require_type(ty, expected)?;
                    }
                }
            }
            let signature = (args, clause.output.clone());
            if let Some(previous) = checker
                .signatures
                .insert(clause.key.clone(), signature.clone())
                && previous != signature
            {
                return Err(format!("inconsistent function signature: {}", clause.name));
            }
            if let Some(previous) = checker
                .failures
                .insert(clause.key.clone(), clause.failures.clone())
                && previous != clause.failures
            {
                return Err(format!("inconsistent function signature: {}", clause.name));
            }
        }
        for clause in &program.clauses {
            // D6B-28: the one-clause rule stays for a whole-body pipe with an EFFECT step.
            let effect_step = matches!(&clause.body, Node::Pipe(_, steps) if steps.iter().any(|s| checker.effect(s).is_some()));
            if effect_step
                && program
                    .clauses
                    .iter()
                    .filter(|c| c.name == clause.name)
                    .count()
                    != 1
            {
                return Err(format!(
                    "a function with a pipe body has one clause in slice 1: {}",
                    clause.name
                ));
            }
        }
        checker.effects()?;
        checker.retires()?;
        Ok(checker)
    }
    // A lowercase fn name, or a constructor `fn T` of a `type T` or an `enum T` that returns T (D6B-11).
    fn fn_name(&self, name: &str, output: &str) -> Checked<()> {
        if upper(name) {
            if !self.program.types.contains_key(name) {
                return Err(format!(
                    "error: fn {name}: a constructor needs a type {name}\n  help: declare type {name} {{ ... }}, or write the fn name in lowercase"
                ));
            }
            if output != name {
                return Err(format!(
                    "error: fn {name}: a constructor returns its own TYPE {name}, not {output}"
                ));
            }
            return Ok(());
        }
        let reserved = [
            "fn",
            "def",
            "defp",
            "end",
            "do",
            "when",
            "case",
            "cond",
            "if",
            "unless",
            "try",
            "catch",
            "rescue",
            "after",
            "else",
            "true",
            "false",
            "nil",
            "and",
            "or",
            "not",
            "in",
            "receive",
            "for",
            "with",
            "quote",
            "unquote",
            "super",
            "import",
            "alias",
            "require",
            "use",
            "raise",
            "throw",
            "exit",
            "is_binary",
            "is_integer",
            "is_map",
            "map_size",
        ];
        if !lower(name) || reserved.contains(&name) {
            return Err(format!("invalid function name: {name}"));
        }
        // `new_T_k` is the Elixir name of signature k of the constructor `fn T`.
        let program = self.program;
        let mut keys = (program.clauses.iter().map(|c| &c.key))
            .chain(program.signature_lines.iter().map(|l| &l.key));
        if keys.any(|k| k.contains('#') && elixir_name(k) == name) {
            return Err(format!("duplicate name: {name}"));
        }
        Ok(())
    }
    // D6B-21, D6B-22, D6B-23: an enum with literals has no constructor; every variant has its own literal and
    // no payload, except one keep-value variant X(String) without a literal (found by its shape).
    fn literal_rules(
        &self,
        name: &str,
        variants: &[(String, Vec<String>)],
        literals: &[(String, String)],
    ) -> Checked<()> {
        if self.constructors.contains(name) {
            return Err(format!(
                "error: enum {name} has literals and a constructor\n  help: keep the literals for a 1:1 mapping or the constructor fn {name}, not both"
            ));
        }
        let mut keep: Option<&str> = None;
        for (index, (variant, args)) in variants.iter().enumerate() {
            let literal = literals.iter().find(|(v, _)| v == variant).map(|(_, l)| l);
            match literal {
                Some(_) if !args.is_empty() => {
                    return Err(format!(
                        "error: enum {name}: the variant {variant} has a payload and a literal\n  help: a variant has a payload or a literal, not both"
                    ));
                }
                Some(literal) => {
                    let first = variants[..index]
                        .iter()
                        .find(|(v, _)| literals.iter().any(|(w, l)| w == v && l == literal));
                    if let Some((first, _)) = first {
                        return Err(format!(
                            "error: enum {name}: the literal {} of {variant} is unreachable, {first} has it first\n  help: give each variant a literal of its own",
                            json_string(literal)
                        ));
                    }
                }
                None if args.as_slice() == ["String"] => {
                    if let Some(keep) = keep {
                        return Err(format!(
                            "error: enum {name}: the variant {variant} has no literal, {keep} keeps the value already\n  help: an enum with literals has at most one keep-value variant X(String)"
                        ));
                    }
                    keep = Some(variant);
                }
                // ponytail: text not fixed by a test (step 4 notes, open Undo point).
                None => {
                    return Err(format!(
                        "error: enum {name}: the variant {variant} has no literal\n  help: give {variant} a literal, or make it the one keep-value variant X(String)"
                    ));
                }
            }
        }
        Ok(())
    }
    // The keep-value variant X(String) of a literal enum: the variant without a literal (D6B-21).
    fn keep_variant(&self, name: &str) -> Option<&str> {
        let literals = self.program.literals.get(name)?;
        match self.program.types.get(name)? {
            Definition::Enum(variants) => variants
                .iter()
                .find(|(v, args)| {
                    args.as_slice() == ["String"] && !literals.iter().any(|(w, _)| w == v)
                })
                .map(|(v, _)| v.as_str()),
            Definition::Record(_) => None,
        }
    }
    // The literal enum fields of an EFFECT output TYPE, sorted by field name: (field, enum).
    fn literal_fields(&self, output: &str) -> Vec<(String, String)> {
        let mut fields: Vec<(String, String)> = self
            .record(output)
            .cloned()
            .unwrap_or_default()
            .into_iter()
            .filter(|(_, t)| self.program.literals.contains_key(t))
            .collect();
        fields.sort();
        fields
    }
    // D6B-04: any TYPE after `!`. RED repair R3: two failure TYPES with equal fields are the same TYPE.
    fn failure_types(&self, owner: &str, failures: &[String]) -> Checked<()> {
        unique(failures.iter().cloned())?;
        for (index, failure) in failures.iter().enumerate() {
            // Each record failure TYPE becomes a nested struct module next to `Replay` and `Http`.
            if failure == "Replay" || failure == "Http" {
                return Err(format!("reserved failure type name: {failure}"));
            }
            // D6B-10: a variant is no TYPE; the help line names its enum.
            if let (Err(error), Some((owner, _))) = (
                self.check_type(failure, &mut Vec::new()),
                self.variants.get(failure),
            ) {
                return Err(format!(
                    "{error}\n  help: {failure} is a variant of the enum {owner}, not a TYPE; write {owner}"
                ));
            }
            self.check_type(failure, &mut Vec::new())?;
            if let Some(same) = failures[..index]
                .iter()
                .find(|f| self.same_type(f, failure))
            {
                return Err(format!(
                    "error: {owner}: the failure TYPE {same} is also a failure TYPE: {failure} has the same fields\n  help: remove {failure} after !"
                ));
            }
        }
        Ok(())
    }
    // DL-093 (E1), D6B-06, D6B-08: the success TYPE is never a failure TYPE, also structurally.
    fn overlap(
        &self,
        owner: &str,
        success: &str,
        failures: &[String],
        removable: bool,
    ) -> Checked<()> {
        let Some(failure) = failures.iter().find(|f| self.same_type(success, f)) else {
            return Ok(());
        };
        let mut error =
            format!("error: {owner}: the success TYPE {success} is also a failure TYPE");
        if failure != success {
            error.push_str(&format!(": {failure} has the same fields"));
        }
        error.push_str("\n  help: give the failure a TYPE of its own (for example type FError { reason: String })");
        // An EFFECT needs one failure TYPE, so removing it is no fix.
        if removable {
            error.push_str(&format!(", or remove {failure} after !"));
        }
        Err(error)
    }
    // T1, T2 (slice 4): one RETIRE LINE per operation, and none for an operation with an `effect`.
    fn retires(&self) -> Checked<()> {
        for retire in &self.program.retires {
            let op = &retire.operation;
            if self
                .program
                .retires
                .iter()
                .filter(|r| &r.operation == op)
                .count()
                != 1
            {
                return Err(format!(
                    "retire {op}: the operation is retired two times; declare one RETIRE LINE per operation"
                ));
            }
            if self.effect(op).is_some() {
                return Err(format!(
                    "retire {op}: the source still declares effect {op}; remove the effect or the RETIRE LINE"
                ));
            }
        }
        Ok(())
    }
    fn retire(&self, operation: &str) -> Option<&Retire> {
        self.program
            .retires
            .iter()
            .find(|r| r.operation == operation)
    }
    fn effect(&self, name: &str) -> Option<&Effect> {
        self.program.effects.iter().find(|e| e.name == name)
    }
    fn effects(&self) -> Checked<()> {
        let effects = &self.program.effects;
        for effect in effects {
            let name = &effect.name;
            if effect.kind != "http.post" {
                return Err(format!(
                    "unsupported effect kind: {} in effect {name} (slice 1 supports http.post)",
                    effect.kind
                ));
            }
            if !operation_name(name) {
                return Err(format!(
                    "invalid effect name: {name} (expected namespace.operation)"
                ));
            }
            let elixir = name.replace('.', "_");
            if self.signatures.contains_key(&elixir)
                || effects.iter().filter(|e| &e.name == name).count() != 1
            {
                return Err(format!("duplicate name: {elixir}"));
            }
            if effect.path.is_empty()
                || effect.path.starts_with('/')
                || !effect
                    .path
                    .bytes()
                    .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b"/_-".contains(&b))
            {
                return Err(format!("unsupported http path in effect {name}"));
            }
            // D6B-19, interim for Q6B-3 (DL-101 replaces it with the decode through the constructor).
            let positions = [("input", &effect.input), ("output", &effect.output)]
                .into_iter()
                .chain(effect.failures.iter().map(|f| ("failure", f)));
            for (position, ty) in positions {
                if let Some((nominal, field)) = self.constructor_inside(ty) {
                    return Err(format!(
                        "error: effect {name}: the TYPE {nominal} has a constructor and cannot stand in an EFFECT {position}{field} (interim D6B-19, Q6B-3)\n  help: use a TYPE without a constructor at the EFFECT, then pipe it into fn {nominal}"
                    ));
                }
            }
            self.check_type(&effect.input, &mut Vec::new())?;
            // D6B-03: no Int in an EFFECT input, also not in a nested TYPE.
            if let Some(place) = self.int_inside(&effect.input) {
                return Err(format!(
                    "effect {name}: slice 6b sends String fields only, not {place}"
                ));
            }
            for (field, ty) in self.record(&effect.output)? {
                let output = &effect.output;
                // Slice 6b step 7: an enum with ENUM LITERALS decodes by its mapping (D6B-35).
                if self.program.literals.contains_key(ty) {
                    if self.versioned(output) {
                        return Err(format!(
                            "error: effect {name}: the enum field {output}.{field} cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)\n  help: remove the MIGRATE CHAIN and the VERSION MARK of {output}, or make {field} a String field"
                        ));
                    }
                    if self.keep_variant(ty).is_none() {
                        return Err(format!(
                            "error: effect {name}: the enum {ty} of {output}.{field} has no keep-value variant (DL-065)\n  help: add the variant Unknown(String) to enum {ty}"
                        ));
                    }
                } else if ty != "String" {
                    return Err(format!(
                        "effect {name}: slice 1 decodes String fields only, not {}.{field}",
                        effect.output
                    ));
                }
            }
            let owner = format!("effect {name}");
            self.failure_types(&owner, &effect.failures)?;
            self.overlap(&owner, &effect.output, &effect.failures, false)?;
            // The failure struct gets only `reason`, so an Int field would stay nil (D6B-03).
            if let Some(place) = effect.failures.iter().find_map(|f| self.int_inside(f)) {
                return Err(format!(
                    "effect {name}: slice 6b fails with String fields only, not {place}"
                ));
            }
            match effect.failures.as_slice() {
                [failure]
                    if self.record(failure).is_ok_and(|fields| {
                        fields.iter().any(|(f, t)| f == "reason" && t == "String")
                    }) => {}
                _ => {
                    return Err(format!(
                        "effect {name} needs one failure type with the field reason: String"
                    ));
                }
            }
        }
        if effects.len() > 1 {
            return Err("slice 1 supports one effect".into());
        }
        Ok(())
    }
    // The first TYPE with a constructor in `ty`: itself (`""`) or the place ` field Owner.field` that holds it.
    fn constructor_inside(&self, ty: &str) -> Option<(String, String)> {
        if self.constructors.contains(ty) {
            return Some((ty.into(), String::new()));
        }
        let refs: Vec<(String, &String)> = match self.program.types.get(ty)? {
            Definition::Record(fields) => fields
                .iter()
                .map(|(f, t)| (format!("{ty}.{f}"), t))
                .collect(),
            Definition::Enum(variants) => variants
                .iter()
                .flat_map(|(v, args)| args.iter().map(move |t| (format!("{ty}.{v}"), t)))
                .collect(),
        };
        refs.into_iter().find_map(|(place, t)| {
            self.constructor_inside(t).map(|(nominal, inner)| {
                (
                    nominal,
                    if inner.is_empty() {
                        format!(" field {place}")
                    } else {
                        inner
                    },
                )
            })
        })
    }
    // D6B-18: a record literal of a TYPE T with a constructor stands only in the clauses of `fn T`, at any depth.
    fn literals(&self, node: &Node, owner: &str) -> Checked<()> {
        let children: Vec<&Node> = match node {
            Node::Record(ty, fields) => {
                if self.constructors.contains(ty) && ty != owner {
                    let how = if self.failures[&format!("{ty}#1")].is_empty() {
                        format!("as a call {ty}(...)")
                    } else {
                        "as a pipe step, because it can fail".into()
                    };
                    return Err(format!(
                        "error: fn {owner}: the record literal {ty} {{ ... }} is legal only in the clauses of the constructor fn {ty}\n  help: call the constructor fn {ty} ({how})"
                    ));
                }
                fields.iter().map(|(_, v)| v).collect()
            }
            Node::Call(_, args) => args.iter().collect(),
            Node::Plus(a, b) => vec![a, b],
            Node::Pipe(head, _) | Node::Annotated(head, _) => vec![head],
            Node::Text(_) | Node::Int(_) | Node::Name(_) => vec![],
        };
        children
            .into_iter()
            .try_for_each(|n| self.literals(n, owner))
    }
    // The first place with the TYPE Int inside `ty`: `Owner.field`, `Owner.Variant` or `Int` itself.
    fn int_inside(&self, ty: &str) -> Option<String> {
        if ty == "Int" {
            return Some(ty.into());
        }
        let here = |place: &str, t: &String| {
            if t == "Int" {
                Some(format!("{ty}.{place}"))
            } else {
                self.int_inside(t)
            }
        };
        match self.program.types.get(ty)? {
            Definition::Record(fields) => fields.iter().find_map(|(f, t)| here(f, t)),
            Definition::Enum(variants) => variants
                .iter()
                .find_map(|(v, args)| args.iter().find_map(|t| here(v, t))),
        }
    }
    fn check_type(&self, name: &str, path: &mut Vec<String>) -> Checked<()> {
        if name == "String" || name == "Int" {
            return Ok(());
        }
        if path.iter().any(|n| n == name) || path.len() > 32 {
            return Err("recursive or deeply nested types are outside this spike".into());
        }
        path.push(name.to_string());
        let refs: Vec<&String> = match self
            .program
            .types
            .get(name)
            .ok_or(format!("unknown type: {name}"))?
        {
            Definition::Record(fields) => fields.iter().map(|(_, ty)| ty).collect(),
            Definition::Enum(variants) => variants.iter().flat_map(|(_, args)| args).collect(),
        };
        for ty in refs {
            self.check_type(ty, path)?;
        }
        path.pop();
        Ok(())
    }
    fn record(&self, name: &str) -> Checked<&Vec<(String, String)>> {
        match self.program.types.get(name) {
            Some(Definition::Record(fields)) => Ok(fields),
            _ => Err(format!("unknown type: {name}")),
        }
    }
    fn same_type(&self, left: &str, right: &str) -> bool {
        if left == right {
            return true;
        }
        // D6B-17: a TYPE with a constructor is nominal, at every gate.
        if self.constructors.contains(left) || self.constructors.contains(right) {
            return false;
        }
        match (self.program.types.get(left), self.program.types.get(right)) {
            (Some(Definition::Record(a)), Some(Definition::Record(b))) => {
                a.len() == b.len()
                    && a.iter()
                        .all(|(n, t)| b.iter().any(|(m, u)| n == m && self.same_type(t, u)))
            }
            _ => false,
        }
    }
    fn require_type(&self, actual: &str, expected: &str) -> Checked<()> {
        if self.same_type(actual, expected) {
            Ok(())
        } else {
            Err(format!("type mismatch: expected {expected}, got {actual}"))
        }
    }
    fn pattern(
        &self,
        node: &Node,
        expected: Option<&str>,
        vars: &mut BTreeMap<String, String>,
    ) -> Checked<String> {
        let ty = match node {
            Node::Annotated(inner, ty) => {
                self.check_type(ty, &mut Vec::new())?;
                self.pattern(inner, Some(ty), vars)?;
                ty.clone()
            }
            Node::Text(_) => "String".into(),
            Node::Int(_) => "Int".into(),
            Node::Name(name) => {
                let ty = expected
                    .ok_or("a variable or wildcard parameter needs a type annotation")?
                    .to_string();
                if name != "_" {
                    if !lower(name) {
                        return Err(format!("invalid variable: {name}"));
                    }
                    if vars.insert(name.clone(), ty.clone()).is_some() {
                        return Err(format!("duplicate pattern binding: {name}"));
                    }
                }
                ty
            }
            Node::Record(name, fields) => {
                let declared = self.record(name)?;
                unique(fields.iter().map(|(n, _)| n.clone()))?;
                for (field, value) in fields {
                    let ty = &declared
                        .iter()
                        .find(|(n, _)| n == field)
                        .ok_or(format!("unknown field: {name}.{field}"))?
                        .1;
                    self.pattern(value, Some(ty), vars)?;
                }
                name.clone()
            }
            Node::Call(name, args) => {
                let (ty, types) = self
                    .variants
                    .get(name)
                    .ok_or(format!("not a constructor pattern: {name}"))?;
                if types.len() != args.len() {
                    return Err(format!("constructor arity mismatch: {name}"));
                }
                for (arg, ty) in args.iter().zip(types) {
                    self.pattern(arg, Some(ty), vars)?;
                }
                ty.clone()
            }
            Node::Plus(_, _) | Node::Pipe(_, _) => {
                return Err("expressions are not patterns".into());
            }
        };
        if let Some(expected) = expected {
            self.require_type(&ty, expected)?;
        }
        Ok(ty)
    }
    fn expression(&self, node: &Node, vars: &BTreeMap<String, String>) -> Checked<String> {
        match node {
            Node::Text(_) => Ok("String".into()),
            Node::Int(_) => Ok("Int".into()),
            Node::Name(name) => vars
                .get(name)
                .cloned()
                .ok_or(format!("unknown variable: {name}")),
            Node::Plus(a, b) => {
                self.require_type(&self.expression(a, vars)?, "String")?;
                self.require_type(&self.expression(b, vars)?, "String")?;
                Ok("String".into())
            }
            Node::Record(name, fields) => {
                let declared = self.record(name)?;
                unique(fields.iter().map(|(n, _)| n.clone()))?;
                for (field, value) in fields {
                    let ty = &declared
                        .iter()
                        .find(|(n, _)| n == field)
                        .ok_or(format!("unknown field: {name}.{field}"))?
                        .1;
                    self.require_type(&self.expression(value, vars)?, ty)?;
                }
                if fields.len() != declared.len() {
                    return Err(format!("missing required field in {name}"));
                }
                Ok(name.clone())
            }
            Node::Call(name, args) => {
                let (types, output) = if let Some((owner, args)) = self.variants.get(name) {
                    (args, owner)
                } else {
                    let key = if upper(name) {
                        let given = args
                            .iter()
                            .map(|a| self.expression(a, vars))
                            .collect::<Checked<Vec<_>>>()?;
                        self.pick(name, &given)
                    } else {
                        name.clone()
                    };
                    let (args, output) = self
                        .signatures
                        .get(&key)
                        .ok_or(format!("unknown function: {name}"))?;
                    if !self.failures[&key].is_empty() {
                        return Err(format!("{name} can fail: call it as a pipe step"));
                    }
                    (args, output)
                };
                if args.len() != types.len() {
                    return Err(format!("call arity mismatch: {name}"));
                }
                for (arg, ty) in args.iter().zip(types) {
                    self.require_type(&self.expression(arg, vars)?, ty)?;
                }
                Ok(output.clone())
            }
            Node::Annotated(_, _) => {
                Err("type annotations are only supported on parameters".into())
            }
            Node::Pipe(head, steps) => Ok(self.steps(self.expression(head, vars)?, steps, None)?.0),
        }
    }
    // The signature key a call `name(args)` takes: for a constructor `fn T`, the first signature whose arity
    // and TYPES fit, else signature 1 (its checks then give the error); for a lowercase fn, the name (D6B-16).
    fn pick(&self, name: &str, given: &[String]) -> String {
        if !upper(name) {
            return name.into();
        }
        (1..)
            .map(|k| format!("{name}#{k}"))
            .take_while(|key| self.signatures.contains_key(key))
            .find(|key| {
                let types = &self.signatures[key].0;
                types.len() == given.len()
                    && types.iter().zip(given).all(|(t, g)| self.same_type(g, t))
            })
            .unwrap_or(format!("{name}#1"))
    }
    // Pipe check: each step is a known one-argument fn, a constructor, a variant with one payload or an
    // EFFECT; its input TYPE is the previous output TYPE, and each of its failure TYPES is in the `!` list
    // of the enclosing fn. Also gives the step targets: the signature key, variant or EFFECT name.
    fn body(
        &self,
        clause: &Clause,
        vars: &BTreeMap<String, String>,
    ) -> Checked<(String, Vec<String>)> {
        // D6B-27: `expression` knows no fn name; the clause adds it to a nested pipe error.
        let named = |e: String| {
            if e.starts_with("a nested pipe has the ") {
                format!(
                    "error: fn {}: {e}\n  help: make the pipe the whole body",
                    clause.name
                )
            } else {
                e
            }
        };
        let Node::Pipe(head, steps) = &clause.body else {
            return Ok((
                self.expression(&clause.body, vars).map_err(named)?,
                Vec::new(),
            ));
        };
        let ty = self.expression(head, vars).map_err(named)?;
        self.steps(ty, steps, Some(clause))
    }
    // The steps from the head TYPE `ty`. `clause` is the fn of a whole-body pipe (the `!` rule); a nested pipe
    // (None) has no EFFECT step and no failing step (D6B-27).
    fn steps(
        &self,
        mut ty: String,
        steps: &[String],
        clause: Option<&Clause>,
    ) -> Checked<(String, Vec<String>)> {
        let mut targets = Vec::new();
        let none = Vec::new();
        for step in steps {
            let key = self.pick(step, std::slice::from_ref(&ty));
            let (input, output, failures) = if let Some(effect) = self.effect(step) {
                (&effect.input, &effect.output, &effect.failures)
            } else if let Some((owner, args)) = self.variants.get(step) {
                // D6B-26: a variant with exactly one payload.
                if args.len() != 1 {
                    return Err(format!("pipe step {step} must take one argument"));
                }
                (&args[0], owner, &none)
            } else if let Some((args, output)) = self.signatures.get(&key) {
                if args.len() != 1 {
                    return Err(format!("pipe step {step} must take one argument"));
                }
                (&args[0], output, &self.failures[&key])
            } else {
                return Err(format!("unknown pipe step: {step}"));
            };
            if clause.is_none() && self.effect(step).is_some() {
                return Err(format!("a nested pipe has the EFFECT step {step}"));
            }
            if clause.is_none() && !failures.is_empty() {
                return Err(format!("a nested pipe has the failing step {step}"));
            }
            targets.push(
                if self.variants.contains_key(step) || self.effect(step).is_some() {
                    step.clone()
                } else {
                    key
                },
            );
            if !self.same_type(&ty, input) {
                return Err(format!(
                    "type mismatch in pipe step {step}: expected {input}, got {ty}"
                ));
            }
            if let Some(clause) = clause
                && let Some(failure) = failures.iter().find(|f| !clause.failures.contains(f))
            {
                return Err(format!(
                    "pipe step {step} can fail with {failure}, which is not in the ! list of {}",
                    clause.name
                ));
            }
            ty = output.clone();
        }
        Ok((ty, targets))
    }
}

// Pattern coverage specializes one typed column at a time, including omitted record fields.
#[derive(Clone, Debug)]
enum Pattern {
    Any,
    Constructor(String, Vec<Pattern>),
}
impl Checker<'_> {
    fn normalized(&self, node: &Node, ty: &str) -> Pattern {
        match node {
            Node::Annotated(inner, _) => self.normalized(inner, ty),
            Node::Text(s) => Pattern::Constructor(format!("text:{s}"), vec![]),
            Node::Int(n) => Pattern::Constructor(format!("int:{n}"), vec![]),
            Node::Call(name, args) => Pattern::Constructor(
                name.clone(),
                args.iter()
                    .zip(&self.variants[name].1)
                    .map(|(n, t)| self.normalized(n, t))
                    .collect(),
            ),
            Node::Record(_, fields) => {
                let declared = self.record(ty).unwrap();
                Pattern::Constructor(
                    "record".into(),
                    declared
                        .iter()
                        .map(|(name, ty)| {
                            fields
                                .iter()
                                .find(|(n, _)| n == name)
                                .map_or(Pattern::Any, |(_, n)| self.normalized(n, ty))
                        })
                        .collect(),
                )
            }
            _ => Pattern::Any,
        }
    }
    fn useful(
        &self,
        rows: &[Vec<Pattern>],
        query: &[Pattern],
        types: &[String],
        budget: &mut usize,
    ) -> Checked<bool> {
        if *budget == 0 {
            return Err("pattern coverage exceeds spike work limit".into());
        }
        *budget -= 1;
        if query.is_empty() {
            return Ok(rows.is_empty());
        }
        let options: Vec<(String, Vec<String>)> = match &query[0] {
            Pattern::Constructor(tag, _) if types[0] == "String" || types[0] == "Int" => {
                vec![(tag.clone(), vec![])]
            }
            _ if types[0] == "String" || types[0] == "Int" => {
                let mut tags = BTreeSet::new();
                for row in rows {
                    if let Pattern::Constructor(tag, _) = &row[0] {
                        tags.insert(tag.clone());
                    }
                }
                // The sentinel is outside the text: and int: prefixes used for all literals.
                tags.insert(
                    if types[0] == "Int" {
                        "other-int"
                    } else {
                        "other-string"
                    }
                    .into(),
                );
                tags.into_iter().map(|tag| (tag, vec![])).collect()
            }
            _ => match &self.program.types[&types[0]] {
                Definition::Record(fields) => vec![(
                    "record".into(),
                    fields.iter().map(|(_, t)| t.clone()).collect(),
                )],
                Definition::Enum(variants) => variants.clone(),
            },
        };
        for (tag, arguments) in options {
            let specialize = |patterns: &[Pattern]| -> Option<Vec<Pattern>> {
                let mut head = match &patterns[0] {
                    Pattern::Any => vec![Pattern::Any; arguments.len()],
                    Pattern::Constructor(name, args) if name == &tag => args.clone(),
                    _ => return None,
                };
                head.extend_from_slice(&patterns[1..]);
                Some(head)
            };
            if let Some(next) = specialize(query) {
                let next_rows: Vec<_> = rows.iter().filter_map(|row| specialize(row)).collect();
                let mut next_types = arguments;
                next_types.extend_from_slice(&types[1..]);
                if self.useful(&next_rows, &next, &next_types, budget)? {
                    return Ok(true);
                }
            }
        }
        Ok(false)
    }
    fn validate(&self) -> Checked<()> {
        for (key, (types, _)) in &self.signatures {
            let name = display(key);
            let mut rows = Vec::new();
            let mut budget = 20_000;
            for clause in self.program.clauses.iter().filter(|c| &c.key == key) {
                let mut vars = BTreeMap::new();
                for (arg, ty) in clause.args.iter().zip(types) {
                    self.pattern(arg, Some(ty), &mut vars)?;
                }
                self.literals(&clause.body, name)?;
                let (ty, _) = self.body(clause, &vars)?;
                // D6B-05: a body of a fn with `!` has the output TYPE or one failure TYPE.
                if clause.failures.is_empty() {
                    self.require_type(&ty, &clause.output)?;
                } else if self.failure_of(clause, &ty).is_none()
                    && !self.same_type(&ty, &clause.output)
                {
                    return Err(format!(
                        "type mismatch: expected {} ! {}, got {ty}",
                        clause.output,
                        clause.failures.join(" | ")
                    ));
                }
                let query: Vec<_> = clause
                    .args
                    .iter()
                    .zip(types)
                    .map(|(n, t)| self.normalized(n, t))
                    .collect();
                if !self.useful(&rows, &query, types, &mut budget)? {
                    return Err(format!("unreachable clause: {name}"));
                }
                rows.push(query);
            }
            if self.useful(&rows, &vec![Pattern::Any; types.len()], types, &mut budget)? {
                return Err(format!("non-exhaustive function: {name}"));
            }
        }
        // After the pipe checks, so that a pipe error names its step first.
        for effect in &self.program.effects {
            self.flow(effect)?;
        }
        Ok(())
    }
}

fn binary(s: &str) -> String {
    // Byte literals prevent source strings from becoming Elixir interpolation or code.
    format!(
        "<<{}>>",
        s.bytes()
            .map(|b| b.to_string())
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn referenced_names(node: &Node, names: &mut BTreeSet<String>) {
    match node {
        Node::Name(name) => {
            names.insert(name.clone());
        }
        Node::Call(_, args) => {
            for arg in args {
                referenced_names(arg, names);
            }
        }
        Node::Record(_, fields) => {
            for (_, value) in fields {
                referenced_names(value, names);
            }
        }
        Node::Plus(a, b) => {
            referenced_names(a, names);
            referenced_names(b, names);
        }
        Node::Pipe(head, _) => referenced_names(head, names),
        _ => (),
    }
}

fn omit_unused(node: &Node, used: &BTreeSet<String>) -> Node {
    match node {
        Node::Name(name) if !used.contains(name) => Node::Name("_".into()),
        Node::Call(name, args) => Node::Call(
            name.clone(),
            args.iter().map(|n| omit_unused(n, used)).collect(),
        ),
        Node::Record(name, fields) => Node::Record(
            name.clone(),
            fields
                .iter()
                .map(|(f, n)| (f.clone(), omit_unused(n, used)))
                .collect(),
        ),
        Node::Annotated(n, ty) => Node::Annotated(Box::new(omit_unused(n, used)), ty.clone()),
        _ => node.clone(),
    }
}
impl Checker<'_> {
    // `vars` types the arguments of a constructor call, which picks the signature (D6B-16).
    fn emit_node(&self, node: &Node, vars: &BTreeMap<String, String>) -> String {
        match node {
            Node::Text(s) => binary(s),
            Node::Int(n) => n.to_string(),
            Node::Name(name) if name == "_" => "_".into(),
            Node::Name(name) => format!("v_{name}"),
            Node::Annotated(n, _) => self.emit_node(n, vars),
            Node::Plus(a, b) => format!(
                "({} <> {})",
                self.emit_node(a, vars),
                self.emit_node(b, vars)
            ),
            // D6B-28: a nested pipe is plain nested calls; validate rejected EFFECT and failing steps.
            Node::Pipe(head, steps) => {
                let ty = self.expression(head, vars).expect("checked head");
                let (_, targets) = self.steps(ty, steps, None).expect("checked pipe");
                targets
                    .iter()
                    .fold(self.emit_node(head, vars), |value, step| {
                        match self.variants.get(step) {
                            Some((owner, _)) => {
                                format!("{{{}, {}, [{value}]}}", binary(owner), binary(step))
                            }
                            None => format!("__MODULE__.{}({value})", elixir_name(step)),
                        }
                    })
            }
            Node::Record(_, fields) => format!(
                "%{{{}}}",
                fields
                    .iter()
                    .map(|(n, v)| format!("{} => {}", binary(n), self.emit_node(v, vars)))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Node::Call(name, nodes) => {
                let args = nodes
                    .iter()
                    .map(|n| self.emit_node(n, vars))
                    .collect::<Vec<_>>()
                    .join(", ");
                if let Some((owner, _)) = self.variants.get(name) {
                    format!("{{{}, {}, [{}]}}", binary(owner), binary(name), args)
                } else {
                    let given: Vec<String> = nodes
                        .iter()
                        .map(|n| self.expression(n, vars).expect("checked call"))
                        .collect();
                    format!(
                        "__MODULE__.{}({args})",
                        elixir_name(&self.pick(name, &given))
                    )
                }
            }
        }
    }
    fn emit(&self, service: &str) -> String {
        // Nested modules (failure structs, Http, Replay) need `defmodule`; payments.beaml output stays unchanged.
        let nested = if self.structs().is_empty()
            && self.program.effects.is_empty()
            && self.program.retires.is_empty()
        {
            ""
        } else {
            ", defmodule: 2"
        };
        // `Int` adds `is_integer` only where it is used, so that a String-only output stays byte-equal.
        let int = self.program.types.values().any(|def| match def {
            Definition::Record(fields) => fields.iter().any(|(_, t)| t == "Int"),
            Definition::Enum(variants) => variants.iter().flat_map(|(_, a)| a).any(|t| t == "Int"),
        }) || self
            .signatures
            .values()
            .any(|(args, output)| output == "Int" || args.iter().any(|t| t == "Int"));
        let is_integer = if int { " is_integer: 1," } else { "" };
        let mut out = format!(
            "# Generated by experiment 0001. Not a stable ABI.\ndefmodule BeamlSpike do\n  import Kernel, only: [and: 2, is_binary: 1,{is_integer} is_map: 1, map_size: 1, ==: 2, <>: 2, if: 2, raise: 2, def: 2, defp: 2{nested}]\n",
        );
        // D6B-07: the failure structs that no EFFECT names come first, so that clause bodies can build them.
        // ponytail: an EFFECT failure struct stays after the clauses (byte guard); a pure clause that builds one needs it first.
        out.push_str(&self.emit_structs(|f| !self.effect_failure(f)));
        out.push_str("  defp __beaml_valid__(v, <<83,116,114,105,110,103>>), do: is_binary(v) and String.valid?(v)\n");
        if int {
            out.push_str("  defp __beaml_valid__(v, <<73,110,116>>), do: is_integer(v)\n");
        }
        for (name, def) in &self.program.types {
            match def {
                Definition::Record(fields) => {
                    let checks = fields
                        .iter()
                        .map(|(n, t)| {
                            format!("__beaml_valid__(Map.get(v, {}), {})", binary(n), binary(t))
                        })
                        .collect::<Vec<_>>();
                    out.push_str(&format!("  defp __beaml_valid__(v, {}) when is_map(v) and map_size(v) == {}, do: {}\n", binary(name), fields.len(), if checks.is_empty() { "true".into() } else { checks.join(" and ") }));
                }
                Definition::Enum(variants) => {
                    for (variant, args) in variants {
                        let vars: Vec<_> = (0..args.len()).map(|i| format!("v{i}")).collect();
                        let checks = vars
                            .iter()
                            .zip(args)
                            .map(|(v, t)| format!("__beaml_valid__({v}, {})", binary(t)))
                            .collect::<Vec<_>>();
                        out.push_str(&format!(
                            "  defp __beaml_valid__({{{}, {}, [{}]}}, {}), do: {}\n",
                            binary(name),
                            binary(variant),
                            vars.join(", "),
                            binary(name),
                            if checks.is_empty() {
                                "true".into()
                            } else {
                                checks.join(" and ")
                            }
                        ));
                    }
                }
            }
        }
        out.push_str("  defp __beaml_valid__(_, _), do: false\n");
        for (key, (types, output)) in &self.signatures {
            let fun = elixir_name(key);
            let name = display(key);
            let args: Vec<_> = (0..types.len()).map(|i| format!("a{i}")).collect();
            let checks: Vec<_> = args
                .iter()
                .zip(types)
                .map(|(a, t)| format!("__beaml_valid__({a}, {})", binary(t)))
                .collect();
            let fails = !self.failures[key].is_empty();
            if fails {
                // `name/n` of a function that can fail: `{:ok, value}` or `{:error, error}`.
                out.push_str(&format!("  def {fun}({}) do\n    if {} do\n      case __beaml_{fun}({}) do\n        {{:ok, result}} ->\n          if __beaml_valid__(result, {}), do: {{:ok, result}}, else: raise(ArgumentError, \"invalid BEAML output\")\n\n        {{:error, error}} ->\n          {{:error, error}}\n      end\n    else\n      raise ArgumentError, \"invalid BEAML input\"\n    end\n  end\n", args.join(", "), if checks.is_empty() { "true".into() } else { checks.join(" and ") }, args.join(", "), binary(output)));
            } else {
                out.push_str(&format!("  def {fun}({}) do\n    if {} do\n      result = __beaml_{fun}({})\n      if __beaml_valid__(result, {}), do: result, else: raise(ArgumentError, \"invalid BEAML output\")\n    else\n      raise ArgumentError, \"invalid BEAML input\"\n    end\n  end\n", args.join(", "), if checks.is_empty() { "true".into() } else { checks.join(" and ") }, args.join(", "), binary(output)));
            }
            for clause in self.program.clauses.iter().filter(|c| &c.key == key) {
                out.push_str(&format!(
                    "  # beaml-declaration-v1 {name} {} {}\n",
                    clause.source_range.start, clause.source_range.end
                ));
                let mut used = BTreeSet::new();
                referenced_names(&clause.body, &mut used);
                let params = clause
                    .args
                    .iter()
                    .map(|n| self.emit_node(&omit_unused(n, &used), &BTreeMap::new()))
                    .collect::<Vec<_>>()
                    .join(", ");
                let vars = self.vars(clause);
                if let Node::Pipe(head, _) = &clause.body {
                    out.push_str(&format!(
                        "  defp __beaml_{fun}({params}) do\n    p0 = {}\n{}  end\n",
                        self.emit_node(head, &vars),
                        self.emit_chain(
                            &self.body_type(clause).1,
                            fails.then_some(clause),
                            service,
                            "    ",
                            Step::Live
                        )
                    ));
                } else if fails {
                    out.push_str(&format!(
                        "  defp __beaml_{fun}({params}), do: {}\n",
                        self.result(clause, &self.emit_node(&clause.body, &vars), "__MODULE__")
                    ));
                } else {
                    out.push_str(&format!(
                        "  defp __beaml_{fun}({params}), do: {}\n",
                        self.emit_node(&clause.body, &vars)
                    ));
                }
            }
        }
        for effect in &self.program.effects {
            out.push_str(&self.emit_effect(effect, service));
        }
        if self.program.effects.is_empty() && !self.program.retires.is_empty() {
            // Slice 4: a RETIRE LINE without an `effect`. A REPLAY RUN gives the `Retired` reject for a
            // RETIRED RECORD, `missing_response` for no record and `operation_mismatch` otherwise.
            out.push_str(&format!(
                "  defmodule Replay do\n    import Kernel\n{}\n    def run(_a0, trace_id, records) do\n      with {{:ok, record}} <- select(records, trace_id),\n           :ok <- not_retired(record[\"operation\"]) do\n        {{:error, :operation_mismatch}}\n      end\n    end\n{SELECT}  end\n",
                self.emit_retired()
            ));
        }
        out.push_str("end\n");
        out
    }
}

// How a pipe step is emitted: in the live flow (spans, the prepared event, the EFFECT call)
// or in `Replay.run/3` (plain calls through the parent module, the EFFECT replaced by record checks).
#[derive(Clone, Copy, PartialEq)]
enum Step {
    Live,
    Replay,
}

fn decode_name(output: &str) -> String {
    format!("__beaml_decode_{}", output.to_ascii_lowercase())
}

impl Checker<'_> {
    // TYPE VERSIONS of a TYPE, oldest first; the last one is the `type`.
    fn type_versions(&self, name: &str) -> Vec<Vec<(String, String)>> {
        match self.versions.get(name) {
            Some(chain) => chain.clone(),
            None => vec![self.record(name).cloned().unwrap_or_default()],
        }
    }
    // The version number of index 0 of `type_versions`: the `from` of the first MIGRATE STEP, else the VERSION
    // MARK, else 1 (slice 5 version table).
    fn chain_start(&self, name: &str) -> u32 {
        self.migrations(name)
            .first()
            .map(|m| m.from)
            .or_else(|| self.mark(name))
            .unwrap_or(1)
    }
    // The newest version number of a TYPE: the VERSION MARK, else the `to` of its last MIGRATE STEP, else 1. M1
    // has checked that a mark and a chain agree.
    fn newest_version(&self, name: &str) -> u32 {
        self.mark(name)
            .or_else(|| self.migrations(name).last().map(|m| m.to))
            .unwrap_or(1)
    }
    fn mark(&self, name: &str) -> Option<u32> {
        self.program.marks.get(name).copied()
    }
    // The decode reads the TYPE VERSION of a RESPONSE RECORD when the TYPE has a MIGRATE CHAIN or a VERSION
    // MARK (a mark without a chain knows one version). Otherwise the decode stays the slice 1 form.
    fn versioned(&self, name: &str) -> bool {
        !self.migrations(name).is_empty() || self.mark(name).is_some()
    }
    // The steps of the MIGRATE CHAIN of a TYPE, in chain order (the chain start first).
    fn migrations(&self, name: &str) -> Vec<&Migration> {
        let mut steps: Vec<&Migration> = self
            .program
            .migrations
            .iter()
            .filter(|m| m.type_name == name)
            .collect();
        steps.sort_by_key(|m| m.from);
        steps
    }
    // The `type` key of a RESPONSE RECORD: the newest TYPE VERSION of the build.
    fn emit_type_version(&self, name: &str) -> String {
        let versions = self.type_versions(name);
        let fields = sorted_fields(versions.last().unwrap());
        format!(
            "%{{name: {}, version: {}, fields: [{}], fingerprint: {}}}",
            binary(name),
            self.newest_version(name),
            fields
                .iter()
                .map(|(f, t)| format!("[{}, {}]", binary(f), binary(t)))
                .collect::<Vec<_>>()
                .join(", "),
            binary(&fingerprint(&fields))
        )
    }
    // Record failure TYPES named in any `!` list; each becomes a nested struct module (D6B-04, D6B-07).
    fn structs(&self) -> BTreeSet<String> {
        let clauses = self.program.clauses.iter().map(|c| &c.failures);
        let effects = self.program.effects.iter().map(|e| &e.failures);
        clauses
            .chain(effects)
            .flatten()
            .filter(|f| self.record(f).is_ok())
            .cloned()
            .collect()
    }
    fn effect_failure(&self, failure: &str) -> bool {
        self.program
            .effects
            .iter()
            .any(|e| e.failures.iter().any(|f| f == failure))
    }
    fn emit_structs(&self, keep: impl Fn(&str) -> bool) -> String {
        let mut out = String::new();
        for failure in self.structs().into_iter().filter(|f| keep(f)) {
            let fields: Vec<String> = self
                .record(&failure)
                .expect("checked failure")
                .iter()
                .map(|(field, _)| format!(":{field}"))
                .collect();
            out.push_str(&format!(
                "  defmodule {failure} do\n    import Kernel, only: [defstruct: 1]\n    defstruct [{}]\n  end\n",
                fields.join(", ")
            ));
        }
        out
    }
    // The failure TYPE of the `!` list that `ty` is (R3 makes it unique).
    fn failure_of<'c>(&self, clause: &'c Clause, ty: &str) -> Option<&'c String> {
        clause.failures.iter().find(|f| self.same_type(ty, f))
    }
    // The parameter TYPES of a clause; validate checked them.
    fn vars(&self, clause: &Clause) -> BTreeMap<String, String> {
        let mut vars = BTreeMap::new();
        for (arg, ty) in clause.args.iter().zip(&self.signatures[&clause.key].0) {
            self.pattern(arg, Some(ty), &mut vars)
                .expect("checked pattern");
        }
        vars
    }
    // The static TYPE of a clause body and its pipe step targets; validate checked it.
    fn body_type(&self, clause: &Clause) -> (String, Vec<String>) {
        self.body(clause, &self.vars(clause)).expect("checked body")
    }
    // D6B-05, D6B-07: `{:ok, v}` for the output TYPE, `{:error, v}` for a failure TYPE. A record failure is the
    // failure struct with atom keys: from the literal fields, else from the map `value`.
    fn result(&self, clause: &Clause, value: &str, owner: &str) -> String {
        let (ty, _) = self.body_type(clause);
        let Some(failure) = self.failure_of(clause, &ty) else {
            return format!("{{:ok, {value}}}");
        };
        let Ok(fields) = self.record(failure) else {
            return format!("{{:error, {value}}}");
        };
        let literal = match &clause.body {
            Node::Record(_, given) => Some(given),
            _ => None,
        };
        // ponytail: a non-literal, non-variable value is evaluated once per field; bind it first if a body gets costly.
        let fields: Vec<String> = fields
            .iter()
            .map(|(field, _)| match literal {
                Some(given) => {
                    let node = &given
                        .iter()
                        .find(|(n, _)| n == field)
                        .expect("checked field")
                        .1;
                    format!("{field}: {}", self.emit_node(node, &self.vars(clause)))
                }
                None => format!("{field}: Map.get({value}, {})", binary(field)),
            })
            .collect();
        format!("{{:error, %{owner}.{failure}{{{}}}}}", fields.join(", "))
    }
    // The one flow that calls the EFFECT: a one-clause fn whose pipe starts with its only parameter.
    fn flow(&self, effect: &Effect) -> Checked<&Clause> {
        let flows: Vec<&Clause> = self
            .program
            .clauses
            .iter()
            .filter(|c| matches!(&c.body, Node::Pipe(_, steps) if steps.contains(&effect.name)))
            .collect();
        let [flow] = flows.as_slice() else {
            return Err(format!(
                "slice 1 needs exactly one pipe that calls the effect {}",
                effect.name
            ));
        };
        let Node::Pipe(head, steps) = &flow.body else {
            unreachable!()
        };
        let parameter = match flow.args.as_slice() {
            [Node::Annotated(inner, _)] => match inner.as_ref() {
                Node::Name(name) => Some(name),
                _ => None,
            },
            _ => None,
        };
        let starts = matches!((parameter, head.as_ref()), (Some(p), Node::Name(h)) if p == h);
        if !starts || steps.iter().filter(|s| *s == &effect.name).count() != 1 {
            return Err(format!(
                "slice 1 replays a flow with one parameter that starts its pipe and calls {} once: {}",
                effect.name, flow.name
            ));
        }
        Ok(flow)
    }
    // The pipe after `p0 = head`: one `with` clause per step; a failed step stops the pipe.
    fn emit_chain(
        &self,
        steps: &[String],
        fails: Option<&Clause>,
        service: &str,
        indent: &str,
        mode: Step,
    ) -> String {
        let owner = if mode == Step::Live {
            "__MODULE__"
        } else {
            "@parent"
        };
        // D6B-28: only a pipe with an EFFECT step has spans; every other pipe is plain calls.
        let spans = steps.iter().any(|s| self.effect(s).is_some());
        let mut clauses = Vec::new();
        let mut matched = false;
        for (index, step) in steps.iter().enumerate() {
            let (input, output) = (format!("p{index}"), format!("p{}", index + 1));
            if let Some(effect) = self.effect(step) {
                if mode == Step::Live {
                    clauses.push(format!(
                        "{{:ok, {output}}} <- __MODULE__.{}({input})",
                        step.replace('.', "_")
                    ));
                } else {
                    clauses.push("{:ok, record} <- select(records, trace_id)".into());
                    // Slice 4: a RETIRED RECORD stops the REPLAY RUN before the operation check.
                    if !self.program.retires.is_empty() {
                        clauses.push(":ok <- not_retired(record[\"operation\"])".into());
                    }
                    clauses.push(format!(
                        ":ok <- expect(record[\"operation\"], {}, :operation_mismatch)",
                        binary(step)
                    ));
                    clauses.push(":ok <- expect(record[\"attempt\"], 1, :attempt_mismatch)".into());
                    clauses.push(format!(
                        ":ok <- expect(record[\"request\"], {input}, :request_mismatch)"
                    ));
                    clauses.push(":ok <- expect(record[\"status\"], 200, :status_mismatch)".into());
                    clauses.push("{:ok, bytes} <- body(record)".into());
                    // With a MIGRATE CHAIN, the decode reads the body as the TYPE VERSION of the record.
                    let version = if !self.versioned(&effect.output) {
                        ""
                    } else {
                        ", record[\"type\"]"
                    };
                    clauses.push(format!(
                        "{{:ok, {output}}} <- @parent.__beaml_attempt__(fn -> ProbeSupport.span({}, :internal, p0, nil, fn -> @parent.__beaml_result_{}(bytes{version}) end) end)",
                        binary(&format!("{service}.{step}")),
                        effect.name.replace('.', "_")
                    ));
                }
                matched = true;
                continue;
            }
            let failing = self.failures.get(step).is_some_and(|f| !f.is_empty());
            let call = match self.variants.get(step) {
                // D6B-26: a variant step builds the variant from its one payload.
                Some((enum_name, _)) => {
                    format!("{{{}, {}, [{input}]}}", binary(enum_name), binary(step))
                }
                None => format!("{owner}.{}({input})", elixir_name(step)),
            };
            let step = display(step);
            let expression = match (mode, steps.get(index + 1).and_then(|s| self.effect(s))) {
                (Step::Replay, _) => call,
                (Step::Live, _) if !spans => call,
                (Step::Live, next) => {
                    // The Orders log: inside the span of the pure step directly before an EFFECT.
                    let inner = match next {
                        Some(effect) if !failing => format!(
                            "result = {call}; ProbeSupport.event({}, {}); result",
                            binary(&format!(
                                "{}_request_prepared",
                                effect.output.to_ascii_lowercase()
                            )),
                            binary(step)
                        ),
                        _ => call,
                    };
                    format!(
                        "ProbeSupport.span({}, :internal, p0, {}, fn -> {inner} end)",
                        binary(&format!("{service}.{step}")),
                        binary(step)
                    )
                }
            };
            if failing {
                clauses.push(format!("{{:ok, {output}}} <- {expression}"));
                matched = true;
            } else {
                clauses.push(format!("{output} = {expression}"));
            }
        }
        let last = format!("p{}", steps.len());
        let result = match fails {
            Some(clause) => self.result(clause, &last, owner),
            None => last,
        };
        if matched {
            format!(
                "{indent}with {} do\n{indent}  {result}\n{indent}end\n",
                clauses.join(&format!(",\n{indent}     "))
            )
        } else {
            clauses
                .iter()
                .map(|c| format!("{indent}{c}\n"))
                .chain([format!("{indent}{result}\n")])
                .collect()
        }
    }
    // The HTTP EFFECT, its decode, the failure structs, the transport and the REPLAY RUN runner.
    fn emit_effect(&self, effect: &Effect, service: &str) -> String {
        let name = &effect.name;
        let elixir = name.replace('.', "_");
        let namespace = name.split('.').next().unwrap();
        let decode = decode_name(&effect.output);
        let flow = self.flow(effect).expect("checked flow");
        let mut out = format!(
            "  # beaml-declaration-v1 {name} {} {}\n",
            effect.source_range.start, effect.source_range.end
        );
        // A failed EFFECT raises inside its span (outcome "error", attribute `reason`) and returns
        // `{:error, %Failure{reason: r}}` outside it. Transport, status and decode never raise to the caller.
        let failure = &effect.failures[0];
        out.push_str(&format!(
            "  def {elixir}(a0) do\n    if __beaml_valid__(a0, {input}) do\n      __beaml_attempt__(fn ->\n        ProbeSupport.span({span}, :client, a0, nil, fn ->\n          carrier = if ProbeSupport.config(:drop_context), do: [], else: :otel_propagator_text_map.inject([])\n\n          case __MODULE__.Http.post(:{namespace}_port, {path}, a0, carrier) do\n            {{:ok, status, bytes}} ->\n              __MODULE__.Replay.record(a0, status, bytes)\n              if status == 200, do: __beaml_result_{elixir}(bytes), else: __beaml_fail_{elixir}({status_reason})\n\n            :error ->\n              __beaml_fail_{elixir}({transport_reason})\n          end\n        end)\n      end)\n    else\n      raise ArgumentError, \"invalid BEAML input\"\n    end\n  end\n",
            input = binary(&effect.input),
            span = binary(&format!("{service}.{name}")),
            path = binary(&effect.path),
            status_reason = binary("status"),
            transport_reason = binary("transport"),
        ));
        // Tolerant typed decode: every declared field present with its TYPE, extra keys are a hint.
        let declared: Vec<String> = self
            .record(&effect.output)
            .expect("checked output")
            .iter()
            .map(|(field, _)| binary(field))
            .collect();
        // MIGRATE CHAIN: the decode reads a body as the TYPE VERSION of its RESPONSE RECORD (DL-043). The
        // version number picks the MIGRATE STEPS; the fingerprint only validates the version. A body of
        // version n gets the MIGRATE CHANGES of the steps n -> n+1 -> ... -> newest in chain order; a live
        // body is the newest version and gets none. Before any step the body is typed by its own TYPE
        // VERSION (DL-054): every field of that version must hold its TYPE, every other key goes to
        // `unknown_keys` (sorted). The steps then work on typed data only: `rename old -> new` moves the
        // value, `add f = c` puts `c`, `drop f` removes the (already typed) field.
        // A record `type` with another TYPE name, an unknown version or another fingerprint is a typed
        // decode error. No `type` key: the newest version. Without a chain the decode stays the slice 1 form.
        let migrations = self.migrations(&effect.output);
        let versions = self.type_versions(&effect.output);
        let start = self.chain_start(&effect.output) as usize;
        let newest = self.newest_version(&effect.output);
        let list = |last: usize| {
            (start..=last)
                .map(|v| v.to_string())
                .collect::<Vec<_>>()
                .join(", ")
        };
        // Slice 6b step 7 (D6B-35, D6B-37): a literal enum field maps its wire String by `__beaml_literal_E`:
        // a literal gives its variant, another String the keep-value variant, any other value `:error` (the
        // typed reject `decode`). Only with literal fields; other outputs keep their bytes.
        let literal_fields = self.literal_fields(&effect.output);
        let unknown_fields = format!(
            "__beaml_unknown_fields_{}",
            effect.output.to_ascii_lowercase()
        );
        let mut literal_map = String::new();
        if !literal_fields.is_empty() {
            let enums: BTreeSet<&String> = literal_fields.iter().map(|(_, e)| e).collect();
            for enum_name in enums {
                for (variant, literal) in &self.program.literals[enum_name] {
                    out.push_str(&format!(
                        "  defp __beaml_literal_{enum_name}({}), do: {{{}, {}, []}}\n",
                        binary(literal),
                        binary(enum_name),
                        binary(variant)
                    ));
                }
                out.push_str(&format!(
                    "  defp __beaml_literal_{enum_name}(v) when is_binary(v), do: {{{}, {}, [v]}}\n  defp __beaml_literal_{enum_name}(_), do: :error\n",
                    binary(enum_name),
                    binary(self.keep_variant(enum_name).expect("checked keep-value variant"))
                ));
            }
            // D6B-37: the field names whose value went to the keep-value variant, sorted, no values.
            let keeps: Vec<String> = literal_fields
                .iter()
                .map(|(f, e)| {
                    format!(
                        "{{{}, {}, {}}}",
                        binary(f),
                        binary(e),
                        binary(self.keep_variant(e).expect("checked keep-value variant"))
                    )
                })
                .collect();
            out.push_str(&format!(
                "  def {unknown_fields}(value) do\n    Enum.flat_map([{}], fn {{field, owner, keep}} ->\n      case Map.get(value, field) do\n        {{^owner, ^keep, _}} -> [field]\n        _ -> []\n      end\n    end)\n  end\n",
                keeps.join(", ")
            ));
            for (field, enum_name) in &literal_fields {
                literal_map.push_str(&format!(
                    "    shape =\n      if is_map(shape) and Map.has_key?(shape, {field}),\n        do: Map.update!(shape, {field}, &__beaml_literal_{enum_name}/1),\n        else: shape\n\n",
                    field = binary(field)
                ));
            }
        }
        if !self.versioned(&effect.output) {
            out.push_str(&format!(
                "  def {decode}(a0) do\n    declared = [{}]\n\n    value =\n      try do\n        :json.decode(a0)\n      rescue\n        _ -> nil\n      end\n\n    shape = if is_map(value), do: Map.take(value, declared), else: nil\n\n{literal_map}    if __beaml_valid__(shape, {output}),\n      do: {{:ok, shape, Enum.sort(Map.keys(Map.drop(value, declared)))}},\n      else: :error\n  end\n",
                declared.join(", "),
                output = binary(&effect.output),
            ));
        } else {
            let known: Vec<String> = versions
                .iter()
                .enumerate()
                .map(|(index, fields)| {
                    format!("{{{}, {}}}", index + start, binary(&fingerprint(fields)))
                })
                .collect();
            // Per TYPE VERSION: its fields with their TYPES (DL-054).
            let by_version: String = versions
                .iter()
                .enumerate()
                .map(|(index, fields)| {
                    let pairs: Vec<String> = sorted_fields(fields)
                        .iter()
                        .map(|(f, t)| format!("{{{}, {}}}", binary(f), binary(t)))
                        .collect();
                    format!(
                        "        {} -> {{:ok, [{}]}}\n",
                        index + start,
                        pairs.join(", ")
                    )
                })
                .collect();
            let mut changes = String::new();
            for step in &migrations {
                let guard = format!(
                    "Enum.member?([{}], version) and is_map(value)",
                    list(step.from as usize)
                );
                for change in &step.changes {
                    changes.push_str(&match change {
                        Change::Rename(old, new) => format!(
                            "    value =\n      if {guard},\n        do: Map.delete(Map.put(value, {new}, Map.get(value, {old})), {old}),\n        else: value\n\n",
                            old = binary(old),
                            new = binary(new)
                        ),
                        Change::Add(field, _, constant) => format!(
                            "    value = if {guard}, do: Map.put(value, {field}, {constant}), else: value\n\n",
                            field = binary(field),
                            constant = binary(constant.as_ref().expect("checked constant"))
                        ),
                        Change::Drop(field, _) => format!(
                            "    value = if {guard}, do: Map.delete(value, {field}), else: value\n\n",
                            field = binary(field)
                        ),
                    });
                }
            }
            out.push_str(&format!(
                "  def {decode}(a0), do: {decode}(a0, nil)\n  def {decode}(a0, type_version) do\n    declared = [{declared}]\n\n    version =\n      case type_version do\n        nil ->\n          {newest}\n\n        %{{{name_key} => {name}, {version_key} => v, {fingerprint_key} => f}} ->\n          if Enum.member?([{known}], {{v, f}}), do: v, else: 0\n\n        _ ->\n          0\n      end\n\n    body =\n      try do\n        :json.decode(a0)\n      rescue\n        _ -> nil\n      end\n\n    fields =\n      case version do\n{by_version}        _ -> :none\n      end\n\n    {{value, unread}} =\n      case {{fields, body}} do\n        {{{{:ok, fields}}, %{{}}}} ->\n          names = Enum.map(fields, fn {{field, _}} -> field end)\n\n          if Enum.all?(fields, fn {{field, type}} -> __beaml_valid__(Map.get(body, field), type) end),\n            do: {{Map.take(body, names), Enum.sort(Map.keys(Map.drop(body, names)))}},\n            else: {{nil, []}}\n\n        _ ->\n          {{nil, []}}\n      end\n\n{changes}    shape = if is_map(value), do: Map.take(value, declared), else: nil\n\n    if __beaml_valid__(shape, {output}) do\n      {{:ok, shape, unread}}\n    else\n      :error\n    end\n  end\n",
                declared = declared.join(", "),
                name_key = binary("name"),
                name = binary(&effect.output),
                version_key = binary("version"),
                fingerprint_key = binary("fingerprint"),
                known = known.join(", "),
                by_version = by_version,
                output = binary(&effect.output),
            ));
        }
        let (result_head, arity) = if !self.versioned(&effect.output) {
            (format!("  def __beaml_result_{elixir}(a0) do\n"), "")
        } else {
            (
                format!(
                    "  def __beaml_result_{elixir}(a0), do: __beaml_result_{elixir}(a0, nil)\n  def __beaml_result_{elixir}(a0, type_version) do\n"
                ),
                ", type_version",
            )
        };
        let mark = if literal_fields.is_empty() {
            String::new()
        } else {
            format!(
                "fields = {unknown_fields}(value)\n        if fields == [], do: :ok, else: :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :unknown_fields, fields)\n        "
            )
        };
        out.push_str(&format!(
            "{result_head}    case {decode}(a0{arity}) do\n      {{:ok, value, []}} ->\n        {mark}{{:ok, value}}\n\n      {{:ok, value, keys}} ->\n        :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :unknown_keys, keys)\n        {mark}{{:ok, value}}\n\n      :error ->\n        __beaml_fail_{elixir}({decode_reason})\n    end\n  end\n  def __beaml_fail_{elixir}(a0) do\n    :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :reason, a0)\n    raise(__MODULE__.BeamlFailure, error: Kernel.struct!(__MODULE__.{failure}, reason: a0))\n  end\n  def __beaml_attempt__(a0) do\n    try do\n      a0.()\n    rescue\n      failure in __MODULE__.BeamlFailure -> {{:error, failure.error}}\n    end\n  end\n",
            decode_reason = binary("decode"),
        ));
        out.push_str(&self.emit_structs(|f| self.effect_failure(f)));
        out.push_str("  defmodule BeamlFailure do\n    import Kernel\n    defexception [:error]\n\n    @impl true\n    def message(_), do: \"BEAML failure\"\n  end\n");
        out.push_str(HTTP);
        out.push_str(&format!(
            "  defmodule Replay do\n    import Kernel\n    @parent __MODULE__ |> Module.split() |> Enum.drop(-1) |> Module.concat()\n{retired}\n    def record(request, status, bytes) do\n      ctx = OpenTelemetry.Tracer.current_span_ctx()\n\n{unknown}\n      ProbeSupport.Capture.write(\"responses\", %{{\n        version: 1,\n        trace_id: OpenTelemetry.Span.hex_trace_id(ctx),\n        client_span_id: OpenTelemetry.Span.hex_span_id(ctx),\n        artifact_id: ProbeSupport.beam_hash(@parent),\n        operation: {operation},\n        attempt: 1,\n        request: request,\n        status: status,\n        body_base64: Base.encode64(bytes),\n        body_length: byte_size(bytes),\n        body_sha256: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower),\n        unknown_keys: unknown_keys,\n{fields_key}        type: {type_version}\n      }})\n    end\n\n    def run(a0, trace_id, records) do\n      p0 = a0\n{chain}    end\n{REPLAY_HELPERS}  end\n",
            operation = binary(name),
            // Step 7 (notes.md S4): the RESPONSE RECORD key `unknown_fields` holds field names only.
            unknown = if literal_fields.is_empty() {
                format!("      unknown_keys =\n        case @parent.{decode}(bytes) do\n          {{:ok, _, keys}} -> keys\n          _ -> []\n        end\n")
            } else {
                format!("      {{unknown_keys, unknown_fields}} =\n        case @parent.{decode}(bytes) do\n          {{:ok, value, keys}} -> {{keys, @parent.{unknown_fields}(value)}}\n          _ -> {{[], []}}\n        end\n")
            },
            fields_key = if literal_fields.is_empty() { "" } else { "        unknown_fields: unknown_fields,\n" },
            retired = self.emit_retired(),
            type_version = self.emit_type_version(&effect.output),
            chain = self.emit_chain(&self.body_type(flow).1, Some(flow), service, "      ", Step::Replay),
        ));
        out
    }
}

impl Checker<'_> {
    // Slice 4, inside `Replay`: the `Retired` struct, `retired/0` (the generated metadata, sorted by operation)
    // and `not_retired/1`. Empty without a RETIRE LINE, so that other sources keep their output.
    fn emit_retired(&self) -> String {
        if self.program.retires.is_empty() {
            return String::new();
        }
        let mut retires: Vec<&Retire> = self.program.retires.iter().collect();
        retires.sort_by(|a, b| a.operation.cmp(&b.operation));
        let entries: Vec<String> = retires
            .iter()
            .map(|r| {
                format!(
                    "%{{operation: {}, keep_days: {}}}",
                    binary(&r.operation),
                    r.keep_days
                )
            })
            .collect();
        let mut out = format!(
            "\n    defmodule Retired do\n      defstruct [:operation, :keep_days]\n    end\n\n    def retired, do: [{}]\n\n",
            entries.join(", ")
        );
        for r in &retires {
            out.push_str(&format!(
                "    defp not_retired({op}), do: {{:error, %__MODULE__.Retired{{operation: {op}, keep_days: {}}}}}\n",
                r.keep_days,
                op = binary(&r.operation)
            ));
        }
        out.push_str("    defp not_retired(_operation), do: :ok\n");
        out
    }
}

// The record selection of a REPLAY RUN (the first helper of REPLAY_HELPERS).
const SELECT: &str = r#"
    defp select(records, trace_id) do
      case Enum.filter(records, &(&1["trace_id"] == trace_id)) do
        [record] -> {:ok, record}
        _ -> {:error, :missing_response}
      end
    end
"#;

// Transport of an http.post EFFECT: 0002 framing on :gen_tcp, Content-Length bodies only.
const HTTP: &str = r#"  defmodule Http do
    import Kernel

    def post(port_key, path, request, carrier) do
      port = ProbeSupport.config(port_key)
      body = ProbeSupport.json(request)
      headers = Enum.map(carrier, fn {key, value} -> [key, ": ", value, "\r\n"] end)
      ProbeSupport.increment()

      # Any connect, send, framing or read failure is the typed transport failure, never a raise.
      case :gen_tcp.connect(
             {127, 0, 0, 1},
             port,
             [:binary, active: false, packet: :http_bin, packet_size: 8192, send_timeout: 1000],
             1000
           ) do
        {:ok, socket} ->
          try do
            exchange(socket, port, path, body, headers)
          catch
            _, _ -> :error
          after
            :gen_tcp.close(socket)
          end

        {:error, _} ->
          :error
      end
    end

    defp exchange(socket, port, path, body, headers) do
      :ok =
        :gen_tcp.send(socket, [
          "POST /", path, " HTTP/1.1\r\n",
          "Host: 127.0.0.1:#{port}\r\n",
          "Connection: close\r\n",
          "Content-Type: application/json\r\n",
          "Content-Length: #{byte_size(body)}\r\n",
          headers,
          "\r\n",
          body
        ])

      deadline = System.monotonic_time(:millisecond) + 2000
      {:ok, {:http_response, {1, minor}, status, _}} = recv(socket, 0, deadline)
      true = minor in [0, 1]
      :ok = :inet.setopts(socket, packet: :httph_bin)
      length = content_length(socket, deadline, 32, nil)
      :ok = :inet.setopts(socket, packet: :raw)
      {:ok, bytes} = recv(socket, length, deadline)
      {:ok, status, bytes}
    end

    defp content_length(socket, deadline, remaining, length) when remaining >= 0 do
      case recv(socket, 0, deadline) do
        {:ok, :http_eoh} when is_integer(length) ->
          length

        {:ok, {:http_header, _, :"Content-Length", _, <<first, _::binary>> = value}}
        when is_nil(length) and first in ?0..?9 ->
          {size, ""} = Integer.parse(value)
          true = size in 1..1024
          content_length(socket, deadline, remaining - 1, size)

        {:ok, {:http_header, _, name, _, _}}
        when name not in [:"Content-Length", :"Transfer-Encoding"] ->
          content_length(socket, deadline, remaining - 1, length)

        _ ->
          raise ArgumentError
      end
    end

    defp recv(socket, length, deadline) do
      timeout = deadline - System.monotonic_time(:millisecond)
      true = timeout > 0
      :gen_tcp.recv(socket, length, timeout)
    end
  end
"#;

// RESPONSE RECORD checks of the REPLAY RUN (0003 format version 1, six reasons).
const REPLAY_HELPERS: &str = r#"
    defp select(records, trace_id) do
      case Enum.filter(records, &(&1["trace_id"] == trace_id)) do
        [record] -> {:ok, record}
        _ -> {:error, :missing_response}
      end
    end

    defp expect(value, value, _reason), do: :ok
    defp expect(_value, _expected, reason), do: {:error, reason}

    defp body(%{"body_base64" => text, "body_length" => length, "body_sha256" => sha256})
         when is_binary(text) do
      with {:ok, bytes} <- Base.decode64(text),
           true <- byte_size(bytes) === length,
           true <- Base.encode16(:crypto.hash(:sha256, bytes), case: :lower) === sha256 do
        {:ok, bytes}
      else
        _ -> {:error, :body_digest_mismatch}
      end
    end

    defp body(_record), do: {:error, :body_digest_mismatch}
"#;

// Fields of a TYPE VERSION sorted by field name (the order of the RESPONSE RECORD `type` key).
fn sorted_fields(fields: &[(String, String)]) -> Vec<(String, String)> {
    let mut sorted = fields.to_vec();
    sorted.sort();
    sorted
}

// Fingerprint of a TYPE VERSION: lower-case hex SHA-256 of the compact JSON of the sorted field list,
// for example `[["order_id","String"],["status","String"]]`. The TYPE name is not part of it.
fn fingerprint(fields: &[(String, String)]) -> String {
    let text = format!(
        "[{}]",
        sorted_fields(fields)
            .iter()
            .map(|(f, t)| format!("[{},{}]", json_string(f), json_string(t)))
            .collect::<Vec<_>>()
            .join(",")
    );
    sha256(text.as_bytes())
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

fn json_string(text: &str) -> String {
    let mut out = String::from("\"");
    for c in text.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

// FIPS 180-4 SHA-256. The compiler has no dependencies.
fn sha256(data: &[u8]) -> [u8; 32] {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut h: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    let mut message = data.to_vec();
    message.push(0x80);
    while message.len() % 64 != 56 {
        message.push(0);
    }
    message.extend_from_slice(&((data.len() as u64) * 8).to_be_bytes());
    for block in message.chunks(64) {
        let mut w = [0u32; 64];
        for (i, word) in block.chunks(4).enumerate() {
            w[i] = u32::from_be_bytes([word[0], word[1], word[2], word[3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh] = h;
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ (!e & g);
            let t1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let t2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        for (state, value) in h.iter_mut().zip([a, b, c, d, e, f, g, hh]) {
            *state = state.wrapping_add(value);
        }
    }
    let mut out = [0u8; 32];
    for (i, word) in h.iter().enumerate() {
        out[i * 4..i * 4 + 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

// A small JSON reader for RECORD SNAPSHOT lines. Numbers keep their text.
#[derive(Clone, Debug, PartialEq)]
enum Json {
    Null,
    Bool(bool),
    Number(String),
    Text(String),
    List(Vec<Json>),
    Object(Vec<(String, Json)>),
}
impl Json {
    fn get(&self, key: &str) -> Option<&Json> {
        match self {
            Json::Object(pairs) => pairs.iter().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }
    fn text(&self) -> Option<&str> {
        match self {
            Json::Text(text) => Some(text),
            _ => None,
        }
    }
}

fn parse_json(text: &str) -> Option<Json> {
    let bytes = text.as_bytes();
    let mut at = 0;
    let value = json_value(bytes, &mut at, 0)?;
    json_space(bytes, &mut at);
    (at == bytes.len()).then_some(value)
}
fn json_space(bytes: &[u8], at: &mut usize) {
    while *at < bytes.len() && b" \t\r\n".contains(&bytes[*at]) {
        *at += 1;
    }
}
fn json_value(bytes: &[u8], at: &mut usize, depth: usize) -> Option<Json> {
    if depth > 64 {
        return None;
    }
    json_space(bytes, at);
    match *bytes.get(*at)? {
        b'{' => {
            *at += 1;
            let mut pairs = Vec::new();
            json_space(bytes, at);
            if bytes.get(*at) == Some(&b'}') {
                *at += 1;
                return Some(Json::Object(pairs));
            }
            loop {
                json_space(bytes, at);
                let Json::Text(key) = json_value(bytes, at, depth + 1)? else {
                    return None;
                };
                json_space(bytes, at);
                if bytes.get(*at) != Some(&b':') {
                    return None;
                }
                *at += 1;
                pairs.push((key, json_value(bytes, at, depth + 1)?));
                json_space(bytes, at);
                match bytes.get(*at)? {
                    b',' => *at += 1,
                    b'}' => {
                        *at += 1;
                        return Some(Json::Object(pairs));
                    }
                    _ => return None,
                }
            }
        }
        b'[' => {
            *at += 1;
            let mut items = Vec::new();
            json_space(bytes, at);
            if bytes.get(*at) == Some(&b']') {
                *at += 1;
                return Some(Json::List(items));
            }
            loop {
                items.push(json_value(bytes, at, depth + 1)?);
                json_space(bytes, at);
                match bytes.get(*at)? {
                    b',' => *at += 1,
                    b']' => {
                        *at += 1;
                        return Some(Json::List(items));
                    }
                    _ => return None,
                }
            }
        }
        b'"' => {
            *at += 1;
            let mut text = String::new();
            loop {
                match *bytes.get(*at)? {
                    b'"' => {
                        *at += 1;
                        return Some(Json::Text(text));
                    }
                    b'\\' => {
                        let escape = *bytes.get(*at + 1)?;
                        *at += 2;
                        text.push(match escape {
                            b'"' => '"',
                            b'\\' => '\\',
                            b'/' => '/',
                            b'b' => '\u{8}',
                            b'f' => '\u{c}',
                            b'n' => '\n',
                            b'r' => '\r',
                            b't' => '\t',
                            b'u' => {
                                let high = json_hex(bytes, at)?;
                                if (0xd800..0xdc00).contains(&high) {
                                    if bytes.get(*at..*at + 2)? != b"\\u" {
                                        return None;
                                    }
                                    *at += 2;
                                    let low = json_hex(bytes, at)?;
                                    if !(0xdc00..0xe000).contains(&low) {
                                        return None;
                                    }
                                    char::from_u32(
                                        0x10000 + ((high - 0xd800) << 10) + (low - 0xdc00),
                                    )?
                                } else {
                                    char::from_u32(high)?
                                }
                            }
                            _ => return None,
                        });
                    }
                    byte if byte < 0x20 => return None,
                    _ => {
                        let start = *at;
                        while *at < bytes.len()
                            && bytes[*at] != b'"'
                            && bytes[*at] != b'\\'
                            && bytes[*at] >= 0x20
                        {
                            *at += 1;
                        }
                        text.push_str(std::str::from_utf8(&bytes[start..*at]).ok()?);
                    }
                }
            }
        }
        b't' if bytes[*at..].starts_with(b"true") => {
            *at += 4;
            Some(Json::Bool(true))
        }
        b'f' if bytes[*at..].starts_with(b"false") => {
            *at += 5;
            Some(Json::Bool(false))
        }
        b'n' if bytes[*at..].starts_with(b"null") => {
            *at += 4;
            Some(Json::Null)
        }
        b'-' | b'0'..=b'9' => {
            let start = *at;
            while *at < bytes.len() && b"+-.eE0123456789".contains(&bytes[*at]) {
                *at += 1;
            }
            let number = std::str::from_utf8(&bytes[start..*at]).ok()?;
            number.parse::<f64>().ok()?;
            Some(Json::Number(number.to_string()))
        }
        _ => None,
    }
}
fn json_hex(bytes: &[u8], at: &mut usize) -> Option<u32> {
    let hex = std::str::from_utf8(bytes.get(*at..*at + 4)?).ok()?;
    *at += 4;
    u32::from_str_radix(hex, 16).ok()
}

// What the DEAD LINE rules read from a RECORD SNAPSHOT (slice 4).
#[derive(Default)]
struct Snapshot {
    // Every operation with at least one record (W1).
    operations: BTreeSet<String>,
    // The oldest stored version per EFFECT output TYPE, from records of operations with an `effect` (W2).
    oldest: BTreeMap<String, u32>,
    // DL-103: the `note:` lines of stored values that a literal maps now (counts, never values).
    notes: Vec<String>,
}

// (TYPE, operation, field, enum) of a literal enum field in the `--stored` check.
type FieldKey = (String, String, String, String);

// Standard base64 (with padding) of a RESPONSE RECORD body; None for any other text.
fn base64(text: &str) -> Option<Vec<u8>> {
    let digit = |c: u8| match c {
        b'A'..=b'Z' => Some(c - b'A'),
        b'a'..=b'z' => Some(c - b'a' + 26),
        b'0'..=b'9' => Some(c - b'0' + 52),
        b'+' => Some(62),
        b'/' => Some(63),
        _ => None,
    };
    let bytes = text.as_bytes();
    if !bytes.len().is_multiple_of(4) {
        return None;
    }
    let mut out = Vec::new();
    for chunk in bytes.chunks(4) {
        let pad = chunk.iter().rev().take_while(|c| **c == b'=').count();
        if pad > 2 {
            return None;
        }
        let mut n = 0u32;
        for c in &chunk[..4 - pad] {
            n = n << 6 | u32::from(digit(*c)?);
        }
        n <<= 6 * pad as u32;
        out.extend_from_slice(&n.to_be_bytes()[1..4 - pad]);
    }
    Some(out)
}

// A DEAD LINE: its byte range in the source, its form (`retire ...` or `migrate T a -> b`) and why it is dead.
#[derive(Clone, Debug)]
struct Dead {
    range: Range<usize>,
    form: String,
    reason: String,
}

// One stored TYPE VERSION as a RESPONSE RECORD names it in its `type` key.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
struct StoredVersion {
    operation: String,
    name: String,
    version: u32,
    fingerprint: String,
    fields: Vec<(String, String)>,
}

fn show_fields(fields: &[(String, String)]) -> String {
    if fields.is_empty() {
        return "{ }".into();
    }
    format!(
        "{{ {} }}",
        fields
            .iter()
            .map(|(f, t)| format!("{f}: {t}"))
            .collect::<Vec<_>>()
            .join(" ")
    )
}

// Read the TYPE VERSION of one RECORD SNAPSHOT line. The body bytes are not read.
fn stored_version(record: &Json) -> Result<StoredVersion, &'static str> {
    let operation = record
        .get("operation")
        .and_then(Json::text)
        .ok_or("stored RESPONSE RECORD has no operation")?;
    let tv = record
        .get("type")
        .filter(|t| **t != Json::Null)
        .ok_or("stored RESPONSE RECORD has no TYPE VERSION")?;
    let malformed = "stored RESPONSE RECORD has a malformed TYPE VERSION";
    let name = tv.get("name").and_then(Json::text).ok_or(malformed)?;
    let version = match tv.get("version") {
        Some(Json::Number(n)) => n.parse::<u32>().ok().filter(|v| *v >= 1).ok_or(malformed)?,
        _ => return Err(malformed),
    };
    let fingerprint = tv
        .get("fingerprint")
        .and_then(Json::text)
        .ok_or(malformed)?;
    if fingerprint.len() != 64
        || !fingerprint
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err(malformed);
    }
    let Some(Json::List(items)) = tv.get("fields") else {
        return Err(malformed);
    };
    let mut fields = Vec::new();
    for item in items {
        match item {
            Json::List(pair) => match pair.as_slice() {
                [Json::Text(f), Json::Text(t)] => fields.push((f.clone(), t.clone())),
                _ => return Err(malformed),
            },
            _ => return Err(malformed),
        }
    }
    Ok(StoredVersion {
        operation: operation.to_string(),
        name: name.to_string(),
        version,
        fingerprint: fingerprint.to_string(),
        fields,
    })
}

impl Checker<'_> {
    // Path check (README slice 2): each stored TYPE VERSION of an `operation` must equal the derived
    // TYPE VERSION with the same number of the EFFECT output TYPE. Equal means the same name and the same
    // fingerprint; the stored field list is read for the message only. Every line is checked.
    // Slice 4 (DL-055): a record of an operation with a RETIRE LINE is a RETIRED RECORD. It must parse with its
    // `type` key (C7), but the path check does not run for it. A record of an operation with neither an
    // `effect` nor a RETIRE LINE is error R1, one message per operation with the count of its records.
    fn check_stored(&self, source: &str, text: &str) -> Checked<Snapshot> {
        let mut groups: BTreeMap<StoredVersion, (usize, usize)> = BTreeMap::new();
        let mut snapshot = Snapshot::default();
        // Operation -> (record count, first line) of records with no `effect` and no RETIRE LINE.
        let mut orphans: BTreeMap<String, (usize, usize)> = BTreeMap::new();
        // DL-102, DL-103: per (TYPE, operation, field, enum) of a literal enum field: (failed records, first
        // failed line, resolved records). The body is mapped by the current literals (one file, one environment).
        let mut mapped: BTreeMap<FieldKey, (usize, usize, usize)> = BTreeMap::new();
        for (index, line) in text.lines().enumerate() {
            let number = index + 1;
            if line.trim().is_empty() {
                continue;
            }
            let at = format!("record source: {source}:{number} (line {number})");
            let record = parse_json(line)
                .ok_or_else(|| format!("error: stored RESPONSE RECORD is not JSON\n  {at}"))?;
            let stored = stored_version(&record).map_err(|e| format!("error: {e}\n  {at}"))?;
            snapshot.operations.insert(stored.operation.clone());
            if let Some(effect) = self.effect(&stored.operation) {
                let oldest = snapshot
                    .oldest
                    .entry(effect.output.clone())
                    .or_insert(stored.version);
                *oldest = (*oldest).min(stored.version);
                let literal_fields = self.literal_fields(&effect.output);
                if stored.name == effect.output && !literal_fields.is_empty() {
                    let body = record
                        .get("body_base64")
                        .and_then(Json::text)
                        .and_then(base64)
                        .and_then(|bytes| String::from_utf8(bytes).ok())
                        .and_then(|text| parse_json(&text));
                    // A record without the key `unknown_fields` (written before step 7) kept nothing.
                    let kept = |field: &str| match record.get("unknown_fields") {
                        Some(Json::List(names)) => names.iter().any(|n| n.text() == Some(field)),
                        _ => false,
                    };
                    for (field, enum_name) in literal_fields {
                        let value = body.as_ref().and_then(|b| b.get(&field));
                        let literal = value.and_then(Json::text).is_some_and(|text| {
                            self.program.literals[&enum_name]
                                .iter()
                                .any(|(_, l)| l == text)
                        });
                        let resolved = literal && kept(&field);
                        let entry = mapped
                            .entry((
                                effect.output.clone(),
                                stored.operation.clone(),
                                field,
                                enum_name,
                            ))
                            .or_insert((0, 0, 0));
                        // A String always has a variant (D6B-36); any other value has none.
                        if value.and_then(Json::text).is_none() {
                            entry.0 += 1;
                            if entry.1 == 0 {
                                entry.1 = number;
                            }
                        }
                        entry.2 += usize::from(resolved);
                    }
                }
                groups.entry(stored).or_insert((0, number)).0 += 1;
            } else if self.retire(&stored.operation).is_none() {
                orphans.entry(stored.operation).or_insert((0, number)).0 += 1;
            }
        }
        if !orphans.is_empty() {
            return Err(orphans
                .iter()
                .map(|(op, (count, line))| {
                    format!(
                        "error: stored RESPONSE RECORD of operation {op} has no effect in the source\n  record source: {source}:{line} (line {line})\n  stored RESPONSE RECORDS of operation {op}: {count}\n  help: if the effect is deleted on purpose, declare: retire {op} keep <n> days"
                    )
                })
                .collect::<Vec<_>>()
                .join("\n"));
        }
        let mut errors: Vec<String> = groups
            .iter()
            .filter_map(|(stored, (count, line))| self.no_path(source, stored, *count, *line))
            .collect();
        if errors.is_empty() {
            let plural = |n: usize| if n == 1 { "" } else { "S" };
            for ((ty, op, field, enum_name), (failed, line, resolved)) in &mapped {
                if *failed > 0 {
                    errors.push(format!(
                        "error: TYPE {ty}: {failed} stored RESPONSE RECORD{} of operation {op} {} no variant of {enum_name} for field {field}\n  record source: {source}:{line} (line {line})\n  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of {ty} (DL-102)",
                        plural(*failed),
                        if *failed == 1 { "has" } else { "have" }
                    ));
                } else if *resolved > 0 {
                    snapshot.notes.push(format!(
                        "note: TYPE {ty}: {resolved} stored RESPONSE RECORD{} of operation {op} kept a value of field {field} that a literal of {enum_name} maps now (DL-103)",
                        plural(*resolved)
                    ));
                }
            }
        }
        if errors.is_empty() {
            Ok(snapshot)
        } else {
            Err(errors.join("\n"))
        }
    }
    // DEAD LINES (slice 4, DL-056), in source order. W1: a RETIRE LINE whose operation has no record in the
    // RECORD SNAPSHOT. W2: a MIGRATE STEP `T a -> b` when no record of an operation whose `effect` outputs T
    // has a version <= a; RETIRED RECORDS do not count. DL-070 supersedes DL-058: the last MIGRATE STEP can be dead
    // too, because `--remove-dead` keeps the newest version as a VERSION MARK on the type line.
    fn dead_lines(&self, snapshot: &Snapshot) -> Vec<Dead> {
        let mut dead = Vec::new();
        for retire in &self.program.retires {
            let op = &retire.operation;
            if !snapshot.operations.contains(op) {
                dead.push(Dead {
                    range: retire.source_range.clone(),
                    form: format!("retire {op} keep {} days", retire.keep_days),
                    reason: format!("no stored RESPONSE RECORD of operation {op}"),
                });
            }
        }
        for step in &self.program.migrations {
            let name = &step.type_name;
            let needed = snapshot.oldest.get(name).is_some_and(|v| *v <= step.from);
            if !needed {
                dead.push(Dead {
                    range: step.source_range.clone(),
                    form: format!("migrate {name} v{} -> v{}", step.from, step.to),
                    reason: format!(
                        "no stored RESPONSE RECORD of TYPE {name} has v{} or older",
                        step.from
                    ),
                });
            }
        }
        dead.sort_by_key(|d| d.range.start);
        dead
    }
    // The completeness rule (README slice 4, removal contract step 2a, DL-069): the refusal message per DEAD
    // LINE without evidence, keyed by its start byte. A dead MIGRATE STEP of T needs a record of an operation
    // whose `effect` outputs T (the records W2 counts). A dead RETIRE LINE needs a non-empty snapshot.
    fn refusals(&self, snapshot: &Snapshot, stored: &str) -> BTreeMap<usize, String> {
        let help = "an empty or partial RECORD SNAPSHOT makes needed lines look dead\n  help: if the --stored file holds every stored RESPONSE RECORD, run again with --assume-complete";
        let mut out = BTreeMap::new();
        for dead in self.dead_lines(snapshot) {
            let why = if let Some(retire) = self
                .program
                .retires
                .iter()
                .find(|r| r.source_range == dead.range)
            {
                snapshot.operations.is_empty().then(|| {
                    format!(
                        "no stored RESPONSE RECORD of any operation (operation {})",
                        retire.operation
                    )
                })
            } else {
                self.program
                    .migrations
                    .iter()
                    .find(|m| m.source_range == dead.range)
                    .filter(|m| !snapshot.oldest.contains_key(&m.type_name))
                    .map(|m| format!("no stored RESPONSE RECORD of TYPE {}", m.type_name))
            };
            if let Some(why) = why {
                out.insert(
                    dead.range.start,
                    format!(
                        "error: removal refused: {}\n  record source: {stored}: {why}; {help}",
                        dead.form
                    ),
                );
            }
        }
        out
    }
    // The message for a stored TYPE VERSION without a path to the newest TYPE VERSION, or None.
    fn no_path(
        &self,
        source: &str,
        stored: &StoredVersion,
        count: usize,
        line: usize,
    ) -> Option<String> {
        let type_name = &self.effect(&stored.operation)?.output;
        let versions = self.type_versions(type_name);
        let start = self.chain_start(type_name);
        let newest = self.newest_version(type_name);
        let derived = stored
            .version
            .checked_sub(start)
            .and_then(|index| versions.get(index as usize));
        // Slice 4: a stored version below the chain start (a removed DEAD LINE needed again, E17).
        let below_start = stored.version < start && &stored.name == type_name;
        if &stored.name == type_name
            && derived.is_some_and(|d| fingerprint(d) == stored.fingerprint)
        {
            return None;
        }
        let newest_fields = versions.last().unwrap();
        let plural = if count == 1 { "" } else { "S" };
        let mut m = vec![
            format!(
                "error: TYPE {type_name} cannot read {count} stored RESPONSE RECORD{plural} of operation {}",
                stored.operation
            ),
            format!(
                "  stored TYPE VERSION: {} v{} {} (fingerprint {})",
                stored.name,
                stored.version,
                show_fields(&stored.fields),
                &stored.fingerprint[..12]
            ),
            format!(
                "  newest TYPE VERSION: {type_name} v{newest} {}",
                show_fields(newest_fields)
            ),
        ];
        // N1 (slice 5, DL-070): version numbers only grow. A stored version newer than the newest version of the
        // source means a reset (a lowered mark, removed MIGRATE STEPS); no MIGRATE STEP can count backwards.
        // Slice 5 final review (medium 1): the version check comes before the name check. A stored TYPE of another
        // name with a newer version also gets N1, never a help line that counts backwards.
        if stored.version > newest {
            if &stored.name != type_name {
                m.push(format!(
                    "  the stored TYPE name {} is not {type_name}",
                    stored.name
                ));
            }
            m.push(format!("  record source: {source} (first at line {line})"));
            m.push(format!(
                "  the stored TYPE VERSION v{} is newer than the newest TYPE VERSION v{newest}; version numbers only grow",
                stored.version
            ));
            m.push(format!(
                "  help: the source must declare v{} or newer; restore the type line and the MIGRATE STEPS from version control",
                stored.version
            ));
            return Some(m.join("\n"));
        }
        // A stored version older than the newest one is compared with its derived version.
        let target = derived.filter(|_| stored.version < newest);
        if let Some(d) = target {
            m.push(format!(
                "  derived TYPE VERSION: {type_name} v{} {} (fingerprint {}), from the MIGRATE CHAIN",
                stored.version,
                show_fields(d),
                &fingerprint(d)[..12]
            ));
        }
        if &stored.name != type_name {
            m.push(format!(
                "  the stored TYPE name {} is not {type_name}",
                stored.name
            ));
        }
        let own = fingerprint(&stored.fields);
        if own != stored.fingerprint {
            m.push(format!(
                "  the stored fingerprint {} is not the fingerprint of the stored fields ({})",
                &stored.fingerprint[..12],
                &own[..12]
            ));
        }
        m.push(format!("  record source: {source} (first at line {line})"));
        m.push("  no path from the stored TYPE VERSION to the newest TYPE VERSION".into());
        let (compare, label) = match target {
            Some(d) => (d, format!("derived TYPE VERSION v{}", stored.version)),
            None => (newest_fields, "newest TYPE VERSION".to_string()),
        };
        let gone: Vec<&(String, String)> = stored
            .fields
            .iter()
            .filter(|f| !compare.contains(f))
            .collect();
        let added: Vec<&(String, String)> = compare
            .iter()
            .filter(|f| !stored.fields.contains(f))
            .collect();
        for (f, t) in &gone {
            m.push(format!(
                "  field {f}: {t} is in the stored TYPE VERSION, not in the {label}"
            ));
        }
        for (f, t) in &added {
            m.push(format!(
                "  field {f}: {t} is in the {label}, not in the stored TYPE VERSION"
            ));
        }
        // Help lines (README slice 3, "Path errors and help lines"). `<constant>` stays a placeholder.
        if target.is_some() {
            m.push(format!(
                "  help: the MIGRATE CHAIN of {type_name} must derive v{} with the fields of the stored TYPE VERSION; check its rename, add and drop steps",
                stored.version
            ));
        } else if below_start {
            // Slice 5: name every missing MIGRATE STEP (with a mark and no chain, the start is the mark).
            let step = |i: u32| format!("migrate {type_name} v{i} -> v{}", i + 1);
            let missing: Vec<String> = if start - stored.version <= 10 {
                (stored.version..start).map(step).collect()
            } else {
                vec![
                    step(stored.version),
                    step(stored.version + 1),
                    format!("... ({} MIGRATE STEPS in all)", start - stored.version),
                    step(start - 1),
                ]
            };
            m.push(format!(
                "  help: the MIGRATE CHAIN of {type_name} starts at v{start}; the stored TYPE VERSION v{} is older. Restore from version control: {}",
                stored.version,
                missing.join(", ")
            ));
        } else if !gone.iter().any(|(f, _)| added.iter().any(|(g, _)| f == g)) {
            // A changed field TYPE under the same name gets no help line (out of scope).
            let next = newest.checked_add(1);
            let migrate = format!(
                "migrate {type_name} v{} -> v{}",
                stored.version,
                next.unwrap_or(newest)
            );
            // Slice 5 (revision 9.1): a new step of a TYPE with a VERSION MARK also needs the new mark (M1).
            let mark = match (self.mark(type_name), next) {
                (Some(_), Some(next)) => format!("; write: type {type_name} v{next}"),
                _ => String::new(),
            };
            if next.is_none() {
                m.push(format!(
                    "  help: no newer version: v{newest} is the largest version number"
                ));
            } else if let ([(old, old_type)], [(new, new_type)]) =
                (gone.as_slice(), added.as_slice())
                && old_type == new_type
            {
                m.push(format!(
                    "  help: if {new} is {old} renamed, declare: {migrate} {{ rename {old} -> {new} }}{mark}"
                ));
            }
            let other: Vec<String> = gone
                .iter()
                .chain(added.iter())
                .filter(|(_, t)| t != "String")
                .map(|(f, t)| format!("{f}: {t}"))
                .collect();
            if next.is_none() {
                // The largest version: only the help line above.
            } else if !other.is_empty() {
                m.push(format!(
                    "  help: no MIGRATE CHANGE for {}: drop supports String fields only, add supports String fields only",
                    other.join(", ")
                ));
            } else if !gone.is_empty() || !added.is_empty() {
                let mut drops: Vec<&String> = gone.iter().map(|(f, _)| f).collect();
                let mut adds: Vec<&String> = added.iter().map(|(f, _)| f).collect();
                drops.sort();
                adds.sort();
                let changes: Vec<String> = drops
                    .iter()
                    .map(|f| format!("drop {f}: String"))
                    .chain(adds.iter().map(|f| format!("add {f}: String = <constant>")))
                    .collect();
                let names = |fields: &[&String]| {
                    fields
                        .iter()
                        .map(|f| f.as_str())
                        .collect::<Vec<_>>()
                        .join(", ")
                };
                let reason = match (drops.is_empty(), adds.is_empty()) {
                    (false, true) => format!("if {} is removed", names(&drops)),
                    (true, false) => format!("if {} is new", names(&adds)),
                    _ => format!(
                        "if {} is removed and {} is new",
                        names(&drops),
                        names(&adds)
                    ),
                };
                m.push(format!(
                    "  help: {reason}, declare: {migrate} {{ {} }}{mark}",
                    changes.join(", ")
                ));
            }
        }
        Some(m.join("\n"))
    }
}

pub fn compile(source: &str) -> Checked<String> {
    compile_service(source, None)
}

// `service` is the source file stem (`orders`). Pipes and EFFECTS name their spans `<service>.<step>`.
pub fn compile_service(source: &str, service: Option<&str>) -> Checked<String> {
    compile_stored(source, service, None)
}

// `stored` is the `--stored` RECORD SNAPSHOT (slice 2). It is read after the parse and TYPE checks (C16).
pub fn compile_stored(
    source: &str,
    service: Option<&str>,
    stored: Option<&std::path::Path>,
) -> Checked<String> {
    build(source, service, stored).map(|built| built.code)
}

// A successful build: the Elixir source and the DEAD LINES of the source against the RECORD SNAPSHOT.
struct Build {
    code: String,
    dead: Vec<Dead>,
    // DL-103 `note:` lines for stderr.
    notes: Vec<String>,
}

fn build(source: &str, service: Option<&str>, stored: Option<&std::path::Path>) -> Checked<Build> {
    build_with_refusals(source, service, stored).map(|(built, _, _)| built)
}

// What the removal command reads about the record TYPES of a build (slice 5): the newest version per TYPE, the
// TYPES with a VERSION MARK, and the byte end of each TYPE name in its `type` declaration.
#[derive(Clone, Debug, Default, PartialEq)]
struct Types {
    newest: BTreeMap<String, u32>,
    marked: BTreeSet<String>,
    name_ends: BTreeMap<String, usize>,
}

thread_local! {
    // The `Types` of the last successful build on this thread. The removal recheck (contract step 4) reads it
    // after its recheck: `Build` keeps its two fields, because the recheck seam of unit test U1 builds one.
    static LAST_TYPES: std::cell::RefCell<Option<Types>> = const { std::cell::RefCell::new(None) };
}

// The build and, per DEAD LINE (by its start byte), the refusal of the completeness rule (README slice 4,
// removal contract step 2a, revision 8.2).
fn build_with_refusals(
    source: &str,
    service: Option<&str>,
    stored: Option<&std::path::Path>,
) -> Checked<(Build, BTreeMap<usize, String>, Types)> {
    let program = Parser {
        tokens: lex(source)?,
        at: 0,
    }
    .program()?;
    let checker = Checker::new(&program)?;
    checker.validate()?;
    // D6B-28: only an EFFECT pipe names spans.
    let spans = !program.effects.is_empty();
    let service = match service {
        Some(name)
            if lower(name)
                && name
                    .bytes()
                    .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'_') =>
        {
            name
        }
        _ if spans => {
            return Err("a pipe or an effect needs a source file name that is a lowercase identifier (it names the spans)".into());
        }
        _ => "",
    };
    let (dead, refusals, notes) = match stored {
        Some(path) => {
            let text = std::fs::read_to_string(path)
                .map_err(|e| format!("cannot read --stored input: {}", e.kind()))?;
            let label = path.display().to_string();
            let snapshot = checker.check_stored(&label, &text)?;
            (
                checker.dead_lines(&snapshot),
                checker.refusals(&snapshot, &label),
                snapshot.notes,
            )
        }
        None if !program.effects.is_empty() || !program.retires.is_empty() => {
            return Err("error: stored TYPE VERSIONS unknown: a source with an effect or a RETIRE LINE needs --stored SNAPSHOT.jsonl (an unknown store is not an empty store)".into());
        }
        None => (Vec::new(), BTreeMap::new(), Vec::new()),
    };
    let types = Types {
        newest: program
            .types
            .iter()
            .filter(|(_, def)| matches!(def, Definition::Record(_)))
            .map(|(name, _)| (name.clone(), checker.newest_version(name)))
            .collect(),
        marked: program.marks.keys().cloned().collect(),
        name_ends: program.name_ends.clone(),
    };
    LAST_TYPES.with(|last| *last.borrow_mut() = Some(types.clone()));
    Ok((
        Build {
            code: checker.emit(service),
            dead,
            notes,
        },
        refusals,
        types,
    ))
}

// Python `str.splitlines(keepends=True)`: the line boundaries of the difflib reference (README slice 4).
fn split_lines(text: &str) -> Vec<&str> {
    let mut lines = Vec::new();
    let mut begin = 0;
    let mut chars = text.char_indices().peekable();
    while let Some((at, c)) = chars.next() {
        let end = match c {
            '\r' if chars.peek().is_some_and(|(_, n)| *n == '\n') => {
                chars.next();
                at + 2
            }
            '\n' | '\r' | '\u{b}' | '\u{c}' | '\u{1c}' | '\u{1d}' | '\u{1e}' | '\u{85}'
            | '\u{2028}' | '\u{2029}' => at + c.len_utf8(),
            _ => continue,
        };
        lines.push(&text[begin..end]);
        begin = end;
    }
    if begin < text.len() {
        lines.push(&text[begin..]);
    }
    lines
}

// The matching blocks of Python `difflib.SequenceMatcher(None, a, b)` (no junk; autojunk for 200+ lines).
fn matching_blocks(a: &[&str], b: &[&str]) -> Vec<(usize, usize, usize)> {
    let mut b2j: std::collections::HashMap<&str, Vec<usize>> = std::collections::HashMap::new();
    for (j, line) in b.iter().enumerate() {
        b2j.entry(line).or_default().push(j);
    }
    if b.len() >= 200 {
        let limit = b.len() / 100 + 1;
        b2j.retain(|_, places| places.len() <= limit);
    }
    let longest = |alo: usize, ahi: usize, blo: usize, bhi: usize| {
        let (mut besti, mut bestj, mut bestsize) = (alo, blo, 0);
        let mut j2len: std::collections::HashMap<usize, usize> = std::collections::HashMap::new();
        for (i, line) in a.iter().enumerate().take(ahi).skip(alo) {
            let mut next = std::collections::HashMap::new();
            for &j in b2j.get(line).map_or(&[][..], |v| v.as_slice()) {
                if j < blo {
                    continue;
                }
                if j >= bhi {
                    break;
                }
                let k = j
                    .checked_sub(1)
                    .and_then(|p| j2len.get(&p))
                    .copied()
                    .unwrap_or(0)
                    + 1;
                next.insert(j, k);
                if k > bestsize {
                    (besti, bestj, bestsize) = (i + 1 - k, j + 1 - k, k);
                }
            }
            j2len = next;
        }
        while besti > alo && bestj > blo && a[besti - 1] == b[bestj - 1] {
            (besti, bestj, bestsize) = (besti - 1, bestj - 1, bestsize + 1);
        }
        while besti + bestsize < ahi
            && bestj + bestsize < bhi
            && a[besti + bestsize] == b[bestj + bestsize]
        {
            bestsize += 1;
        }
        (besti, bestj, bestsize)
    };
    let mut queue = vec![(0, a.len(), 0, b.len())];
    let mut blocks = Vec::new();
    while let Some((alo, ahi, blo, bhi)) = queue.pop() {
        let (i, j, k) = longest(alo, ahi, blo, bhi);
        if k > 0 {
            blocks.push((i, j, k));
            if alo < i && blo < j {
                queue.push((alo, i, blo, j));
            }
            if i + k < ahi && j + k < bhi {
                queue.push((i + k, ahi, j + k, bhi));
            }
        }
    }
    blocks.sort();
    let mut merged = Vec::new();
    let (mut i1, mut j1, mut k1) = (0, 0, 0);
    for (i2, j2, k2) in blocks {
        if i1 + k1 == i2 && j1 + k1 == j2 {
            k1 += k2;
        } else {
            if k1 > 0 {
                merged.push((i1, j1, k1));
            }
            (i1, j1, k1) = (i2, j2, k2);
        }
    }
    if k1 > 0 {
        merged.push((i1, j1, k1));
    }
    merged.push((a.len(), b.len(), 0));
    merged
}

// Python `"".join(difflib.unified_diff(a, b, label, label, n=0))` over `splitlines(keepends=True)`.
fn unified_diff(old: &str, new: &str, label: &str) -> String {
    let (a, b) = (split_lines(old), split_lines(new));
    let mut codes = Vec::new();
    let (mut i, mut j) = (0, 0);
    for (ai, bj, size) in matching_blocks(&a, &b) {
        if i < ai || j < bj {
            codes.push((false, i, ai, j, bj));
        }
        (i, j) = (ai + size, bj + size);
        if size > 0 {
            codes.push((true, ai, i, bj, j));
        }
    }
    // With n = 0 every equal run ends a group; a group is the changes between two equal runs.
    let mut out = String::new();
    for (equal, i1, i2, j1, j2) in codes {
        if equal {
            continue;
        }
        if out.is_empty() {
            out.push_str(&format!("--- {label}\n+++ {label}\n"));
        }
        let range = |start: usize, stop: usize| match stop - start {
            1 => format!("{}", start + 1),
            0 => format!("{start},0"),
            length => format!("{},{length}", start + 1),
        };
        out.push_str(&format!("@@ -{} +{} @@\n", range(i1, i2), range(j1, j2)));
        for line in &a[i1..i2] {
            out.push('-');
            out.push_str(line);
        }
        for line in &b[j1..j2] {
            out.push('+');
            out.push_str(line);
        }
    }
    out
}

fn line_number(text: &str, at: usize) -> usize {
    text[..at].bytes().filter(|b| *b == b'\n').count() + 1
}

// The text without the DEAD LINES and with ` v<n>` inserted at each mark position (slice 5, contract step 3).
// `marks` is sorted by position; no position is inside a removed line (a DEAD LINE line holds only the DEAD LINE).
fn without_dead_marked(text: &str, dead: &[Dead], marks: &[(usize, &str, u32)]) -> Checked<String> {
    let mut marked = String::with_capacity(text.len() + 16 * marks.len());
    let mut kept = 0;
    for (at, _, version) in marks {
        marked.push_str(&text[kept..*at]);
        marked.push_str(&format!(" v{version}"));
        kept = *at;
    }
    marked.push_str(&text[kept..]);
    let shift = |at: usize| -> usize {
        at + marks
            .iter()
            .filter(|(m, _, _)| *m <= at)
            .map(|(_, _, v)| format!(" v{v}").len())
            .sum::<usize>()
    };
    let moved: Vec<Dead> = dead
        .iter()
        .map(|d| Dead {
            range: shift(d.range.start)..shift(d.range.end),
            ..d.clone()
        })
        .collect();
    without_dead(&marked, &moved)
}

// The text without the whole lines of each DEAD LINE (README slice 4, removal contract 2 and 3). A line of a
// DEAD LINE that holds other text than the DEAD LINE and white space stops the removal.
fn without_dead(text: &str, dead: &[Dead]) -> Checked<String> {
    let mut out = String::new();
    let mut kept = 0;
    for line in dead {
        let begin = text[..line.range.start].rfind('\n').map_or(0, |at| at + 1);
        let end = text[line.range.end..]
            .find('\n')
            .map_or(text.len(), |at| line.range.end + at + 1);
        let blank = |part: &str| part.chars().all(char::is_whitespace);
        let other = if !blank(&text[begin..line.range.start]) {
            Some(line.range.start)
        } else if !blank(&text[line.range.end..end]) {
            Some(line.range.end)
        } else {
            None
        };
        if let Some(at) = other {
            return Err(format!(
                "error: cannot remove {}: line {} holds other text",
                line.form,
                line_number(text, at)
            ));
        }
        out.push_str(&text[kept..begin]);
        kept = end;
    }
    out.push_str(&text[kept..]);
    Ok(out)
}

// Write through a temporary file in the same directory and a rename (README slice 4, removal contract 5).
// Revision 8.2 (DL-069): resolve SOURCE to the real file first, so that a symbolic link stays a link, and
// refuse a file that the process cannot open for writing.
fn write_atomic(source: &std::path::Path, text: &str) -> Checked<()> {
    let cannot =
        |e: std::io::Error| format!("error: cannot write {}: {}", source.display(), e.kind());
    let real = std::fs::canonicalize(source).map_err(cannot)?;
    if let Err(e) = std::fs::OpenOptions::new().write(true).open(&real) {
        return Err(match e.kind() {
            std::io::ErrorKind::PermissionDenied => format!(
                "error: cannot write {}: the file is not writable",
                source.display()
            ),
            _ => cannot(e),
        });
    }
    let path = real.as_path();
    let directory = match path.parent() {
        Some(parent) if !parent.as_os_str().is_empty() => parent,
        _ => std::path::Path::new("."),
    };
    let name = path
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default();
    let temporary = directory.join(format!(".{name}.remove-dead-{}.tmp", std::process::id()));
    let result = (|| -> std::io::Result<()> {
        let permissions = std::fs::metadata(path)?.permissions();
        let mut file = std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary)?;
        file.write_all(text.as_bytes())?;
        file.set_permissions(permissions)?;
        file.sync_all()?;
        std::fs::rename(&temporary, path)
    })();
    result.map_err(|e| {
        let _ = std::fs::remove_file(&temporary);
        cannot(e)
    })
}

// The removal command (README slice 4): build, find the DEAD LINES, remove them, rebuild, write atomically.
// Return the number of removed DEAD LINE declarations and the number of written VERSION MARKS (slice 5).
fn remove_dead(
    path: &std::path::Path,
    label: &str,
    stem: Option<&str>,
    stored: &std::path::Path,
    assume_complete: bool,
) -> Checked<(usize, usize)> {
    let recheck = |new: &str| build(new, stem, Some(stored));
    remove_dead_marked(path, label, stem, stored, assume_complete, &recheck)
}

// The removal command with its recheck (contract step 4) as a parameter: the seam of unit tests U1 and U2.
#[cfg_attr(not(test), allow(dead_code))]
fn remove_dead_with(
    path: &std::path::Path,
    label: &str,
    stem: Option<&str>,
    stored: &std::path::Path,
    assume_complete: bool,
    recheck: &dyn Fn(&str) -> Checked<Build>,
) -> Checked<usize> {
    remove_dead_marked(path, label, stem, stored, assume_complete, recheck).map(|(n, _)| n)
}

fn remove_dead_marked(
    path: &std::path::Path,
    label: &str,
    stem: Option<&str>,
    stored: &std::path::Path,
    assume_complete: bool,
    recheck: &dyn Fn(&str) -> Checked<Build>,
) -> Checked<(usize, usize)> {
    let old =
        std::fs::read_to_string(path).map_err(|e| format!("cannot read source: {}", e.kind()))?;
    let (built, refusals, types) = build_with_refusals(&old, stem, Some(stored))?;
    let dead = built.dead;
    if dead.is_empty() {
        eprintln!("no DEAD LINE in {label}");
        return Ok((0, 0));
    }
    if !assume_complete && !refusals.is_empty() {
        return Err(refusals.into_values().collect::<Vec<_>>().join("\n"));
    }
    // Slice 5, contract step 3 (DL-070, DL-071): each TYPE that loses a MIGRATE STEP and has no VERSION MARK gets
    // ` v<newest>` directly after its name. A TYPE with a mark keeps its line (M1 holds).
    let lost: BTreeSet<&str> = dead
        .iter()
        .filter_map(|d| d.form.strip_prefix("migrate "))
        .filter_map(|rest| rest.split(' ').next())
        .collect();
    let mut marks: Vec<(usize, &str, u32)> = lost
        .iter()
        .filter(|name| !types.marked.contains(**name))
        .map(|name| (types.name_ends[*name], *name, types.newest[*name]))
        .collect();
    marks.sort();
    let new = without_dead_marked(&old, &dead, &marks)?;
    LAST_TYPES.with(|last| *last.borrow_mut() = None);
    match recheck(&new) {
        Ok(rebuilt) if rebuilt.dead.is_empty() => (),
        Ok(rebuilt) => {
            return Err(format!(
                "error: removal check failed\n  the new text still has {} DEAD LINES",
                rebuilt.dead.len()
            ));
        }
        Err(error) => return Err(format!("error: removal check failed\n{error}")),
    }
    // Contract step 4 (slice 5): the newest version of every TYPE stays the same (a guard against a reset; U2).
    // A recheck that does not build (a forced test recheck) leaves no `Types` to compare.
    if let Some(after) = LAST_TYPES.with(|last| last.borrow_mut().take()) {
        for (name, before) in &types.newest {
            match after.newest.get(name) {
                Some(now) if now == before => (),
                now => {
                    return Err(format!(
                        "error: removal check failed\n  newest version of {name} changed from v{before} to {}",
                        now.map_or("no TYPE".to_string(), |n| format!("v{n}"))
                    ));
                }
            }
        }
    }
    let diff = unified_diff(&old, &new, label);
    write_atomic(path, &new)?;
    std::io::stdout()
        .write_all(diff.as_bytes())
        .map_err(|e| format!("cannot write output: {}", e.kind()))?;
    let plural = if dead.len() == 1 { "" } else { "S" };
    eprintln!("removed {} DEAD LINE{plural} from {label}", dead.len());
    for (_, name, version) in &marks {
        eprintln!("wrote VERSION MARK v{version} on type {name} in {label}");
    }
    Ok((dead.len(), marks.len()))
}

// The warning of one DEAD LINE (README slice 4, "Warning texts").
fn warning(source: &str, label: &str, stored: &str, dead: &Dead) -> String {
    format!(
        "warning: DEAD LINE: {}\n  at {label}:{}\n  record source: {stored}: {}\n  help: remove DEAD LINES with: beaml-spike {label} --stored {stored} --remove-dead",
        dead.form,
        line_number(source, dead.range.start),
        dead.reason
    )
}

fn action(action: &str, result: &str, counts: &[(&str, usize)]) {
    // Logging must never prevent compilation. Source text, line text and file paths are not recorded.
    let _ = (|| -> std::io::Result<()> {
        std::fs::create_dir_all(".beaml")?;
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(".beaml/actions.jsonl")?;
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs_f64();
        let count: String = counts
            .iter()
            .map(|(key, n)| format!(",\"{key}\":{n}"))
            .collect();
        writeln!(
            file,
            "{{\"ts\":{ts},\"source\":\"cli\",\"action\":\"{action}\",\"target\":\"experiment-0001\",\"result\":\"{result}\"{count}}}"
        )
    })();
}
fn main() {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    let remove = matches!(args.as_slice(), [_, flag, _, last, ..] if flag == "--stored" && last == "--remove-dead");
    let assume_complete =
        matches!(args.as_slice(), [_, _, _, _, last] if last == "--assume-complete");
    let result = (|| -> Checked<Vec<(&str, usize)>> {
        let stored = match args.as_slice() {
            [_] => None,
            [_, flag, path] if flag == "--stored" => Some(std::path::Path::new(path)),
            [_, flag, path, last] if flag == "--stored" && last == "--remove-dead" => {
                Some(std::path::Path::new(path))
            }
            [_, flag, path, last, assume]
                if flag == "--stored"
                    && last == "--remove-dead"
                    && assume == "--assume-complete" =>
            {
                Some(std::path::Path::new(path))
            }
            _ => {
                return Err("usage: beaml-spike SOURCE.beaml [--stored SNAPSHOT.jsonl [--remove-dead [--assume-complete]]] (Elixir source goes to stdout; --remove-dead removes the DEAD LINES from SOURCE and prints the diff; --assume-complete trusts an empty or partial SNAPSHOT)".into());
            }
        };
        let path = std::path::Path::new(&args[0]);
        let label = args[0].to_string_lossy();
        let stem = path.file_stem().and_then(|stem| stem.to_str());
        if remove {
            let (removed, marked) = remove_dead(
                path,
                &label,
                stem,
                stored.expect("checked arguments"),
                assume_complete,
            )?;
            return Ok(vec![("removed", removed), ("marked", marked)]);
        }
        let source = std::fs::read_to_string(path)
            .map_err(|e| format!("cannot read source: {}", e.kind()))?;
        let built = build(&source, stem, stored)?;
        std::io::stdout()
            .write_all(built.code.as_bytes())
            .map_err(|e| format!("cannot write output: {}", e.kind()))?;
        for note in &built.notes {
            eprintln!("{note}");
        }
        if let Some(stored) = stored {
            let stored = stored.display().to_string();
            for dead in &built.dead {
                eprintln!("{}", warning(&source, &label, &stored, dead));
            }
        }
        Ok(vec![("warnings", built.dead.len())])
    })();
    let name = if remove { "remove-dead" } else { "compile" };
    match &result {
        Ok(counts) => action(name, "ok", counts),
        Err(_) if remove => action(name, "error", &[("removed", 0), ("marked", 0)]),
        Err(_) => action(name, "error", &[]),
    }
    if let Err(error) = result {
        eprintln!("{error}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    const SOURCE: &str = include_str!("../example.beaml");
    #[test]
    fn accepts_nested_partial_patterns() {
        assert!(compile(SOURCE).is_ok());
    }
    #[test]
    fn rejects_wrong_return_type() {
        assert!(
            compile("type Box { text: String } fn bad text: String -> Box = text")
                .unwrap_err()
                .contains("type mismatch")
        );
    }
    #[test]
    fn checks_exact_construction_and_pattern_fields() {
        for (source, error) in [
            (
                "type Box { text: String } fn bad -> Box = Box {}",
                "missing required field",
            ),
            (
                "type Box { text: String } fn bad -> Box = Box { text: \"x\", extra: \"x\" }",
                "unknown field",
            ),
            (
                "type Box { text: String } fn bad Box { extra } -> String = extra",
                "unknown field",
            ),
            (
                "type Box { text: String } fn bad -> Box = Box { text: \"x\", text: \"y\" }",
                "duplicate name",
            ),
        ] {
            assert!(compile(source).unwrap_err().contains(error), "{source}");
        }
    }
    #[test]
    fn checks_coverage_and_clause_order() {
        let prefix = "type Box { text: String } enum R { Ok(Box) Error(String) } ";
        assert!(
            compile(&format!(
                "{prefix} fn show Ok(Box {{ text }}) -> String = text"
            ))
            .unwrap_err()
            .contains("non-exhaustive")
        );
        assert!(
            compile("fn show text: String -> String = text fn show \"x\" -> String = \"x\"")
                .unwrap_err()
                .contains("unreachable")
        );
        assert!(
            compile("fn show \"x\" -> String = \"x\"")
                .unwrap_err()
                .contains("non-exhaustive")
        );
        assert!(
            compile("fn show \"x\" -> String = \"x\" fn show text: String -> String = text")
                .is_ok()
        );
    }
    #[test]
    fn checks_calls_and_bindings() {
        for source in [
            "fn one text: String -> String = text fn bad -> String = one()",
            "fn bad -> String = missing()",
            "fn bad -> String = missing",
            "fn bad x: String, x: String -> String = x",
            "fn bad (x: String) -> String = x",
            "fn bad x: String -> String = bad x",
            "fn bad -> String = bad (\"x\")",
            "enum R { Ok(String) } fn bad Ok (x) -> String = x",
        ] {
            assert!(compile(source).is_err(), "{source}");
        }
    }
    #[test]
    fn rejects_unsupported_or_recursive_types() {
        for source in [
            "type A { a: A } fn test -> String = \"x\"",
            "enum R<T> { Ok(T) } fn test -> String = \"x\"",
            "fn test text: Missing -> String = \"x\"",
            "fn test -> String = 42",
            "fn test -> String = \"unclosed",
        ] {
            assert!(compile(source).is_err());
        }
    }
    #[test]
    fn interfaces_are_structural_and_exact() {
        assert!(
            compile("type A { text: String } type B { text: String } fn f a: A -> B = a").is_ok()
        );
        assert!(
            compile(
                "type A { text: String } type B { text: String, extra: String } fn f a: A -> B = a"
            )
            .is_err()
        );
    }
    #[test]
    fn coverage_handles_multiple_arguments_and_empty_shapes() {
        assert!(
            compile(
                "fn f \"a\", \"b\" -> String = \"pair\" fn f a: String, b: String -> String = a + b"
            )
            .is_ok()
        );
        assert!(compile("type Empty {} enum State { Waiting() Done(Empty) } fn f Waiting() -> String = \"wait\" fn f Done(Empty {}) -> String = \"done\"").is_ok());
        assert!(compile("type Box { text: String } fn f Box {} -> String = \"all\" fn f Box { text: \"a\" } -> String = \"late\"").unwrap_err().contains("unreachable"));
    }
    #[test]
    fn coverage_agrees_with_a_four_value_truth_table() {
        let pairs = [("A", "A"), ("A", "B"), ("B", "A"), ("B", "B")];
        for subset in 0..16 {
            let mut source = String::from("enum Bit { A() B() } ");
            for (index, (left, right)) in pairs.iter().enumerate() {
                if subset & (1 << index) != 0 {
                    source.push_str(&format!(
                        "fn pair {left}(), {right}() -> String = \"covered\" "
                    ));
                }
            }
            assert_eq!(compile(&source).is_ok(), subset == 15, "subset {subset}");
        }
    }
    // U1 (EXPERIMENT 0004 README revision 8.2, contract step 4): a failed recheck writes nothing. The recheck
    // is unreachable by the prefix rule, so the test forces it through the recheck parameter (the seam).
    #[test]
    fn removal_writes_nothing_when_the_recheck_fails() {
        const RETIRED: &str = "type Order { order_id: String }\ntype Payment { order_id: String status: String }\ntype PaymentError { reason: String }\n\neffect payments.charge Order -> Payment ! PaymentError = http.post(\"payments/authorize\")\nretire payments.authorize keep 30 days\n\nfn prepare Order { order_id } -> Order = Order { order_id: order_id + \"\" }\nfn finish Payment { order_id, status } -> Payment = Payment { order_id: order_id + \"\", status: status }\n\nfn place order: Order -> Payment ! PaymentError =\n  order\n  |> prepare\n  |> payments.charge\n  |> finish\n";
        use std::os::unix::fs::MetadataExt;
        let directory = std::env::temp_dir().join(format!(
            "beaml-u1-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_nanos()
        ));
        std::fs::create_dir_all(&directory).unwrap();
        let source = directory.join("orders.beaml");
        let stored = directory.join("empty.jsonl");
        std::fs::write(&source, RETIRED).unwrap();
        std::fs::write(&stored, "").unwrap();
        let listing = |dir: &std::path::Path| {
            let mut names: Vec<_> = std::fs::read_dir(dir)
                .unwrap()
                .map(|e| e.unwrap().file_name())
                .collect();
            names.sort();
            names
        };
        // The forced failures: a build error, and a new text that still has a DEAD LINE.
        let failed = |_: &str| -> Checked<Build> { Err("error: forced recheck failure".into()) };
        let still_dead = |_: &str| -> Checked<Build> {
            Ok(Build {
                code: String::new(),
                notes: Vec::new(),
                dead: vec![Dead {
                    range: 0..1,
                    form: "retire forced.line keep 1 days".into(),
                    reason: "forced".into(),
                }],
            })
        };
        type Recheck<'a> = &'a dyn Fn(&str) -> Checked<Build>;
        let cases: [(Recheck, &str); 2] = [
            (&failed, "error: forced recheck failure"),
            (&still_dead, "still has 1 DEAD LINES"),
        ];
        for (recheck, expected) in cases {
            let (before, stat, names) = (
                std::fs::read(&source).unwrap(),
                std::fs::metadata(&source).unwrap(),
                listing(&directory),
            );
            let error = remove_dead_with(
                &source,
                "orders.beaml",
                Some("orders"),
                &stored,
                true,
                recheck,
            )
            .unwrap_err();
            let after = std::fs::metadata(&source).unwrap();
            assert!(error.starts_with("error: removal check failed"), "{error}");
            assert!(error.contains(expected), "{error}");
            assert_eq!(before, std::fs::read(&source).unwrap(), "same bytes");
            assert_eq!(
                (stat.ino(), stat.mtime(), stat.mtime_nsec()),
                (after.ino(), after.mtime(), after.mtime_nsec()),
                "same inode and modification time"
            );
            assert_eq!(names, listing(&directory), "no temporary file");
        }
        // Control: the normal recheck removes the RETIRE LINE (the setup has a DEAD LINE and passes step 2a).
        let normal = |new: &str| build(new, Some("orders"), Some(&stored));
        assert_eq!(
            Ok(1),
            remove_dead_with(
                &source,
                "orders.beaml",
                Some("orders"),
                &stored,
                true,
                &normal
            )
        );
        assert!(!std::fs::read_to_string(&source).unwrap().contains("retire"));
        let _ = std::fs::remove_dir_all(&directory);
    }

    // U2 (EXPERIMENT 0004 README revision 9.1, slice 5 contract step 4): a recheck whose newest version of a TYPE
    // differs from the old text writes nothing. The insertion rule makes this unreachable, so the test forces it
    // through the recheck seam of U1: the forced recheck builds a text without mark and chain (newest v1).
    #[test]
    fn removal_writes_nothing_when_the_newest_version_changes() {
        const HEAD: &str =
            "type Order { order_id: String }\ntype Payment { order_id: String state: String }\n";
        const CHAIN: &str = "migrate Payment v1 -> v2 { rename status -> state }\n";
        const TAIL: &str = "type PaymentError { reason: String }\n\neffect payments.authorize Order -> Payment ! PaymentError = http.post(\"payments/authorize\")\n\nfn prepare Order { order_id } -> Order = Order { order_id: order_id + \"\" }\nfn finish Payment { order_id, state } -> Payment = Payment { order_id: order_id + \"\", state: state }\n\nfn place order: Order -> Payment ! PaymentError =\n  order\n  |> prepare\n  |> payments.authorize\n  |> finish\n";
        use std::os::unix::fs::MetadataExt;
        let directory = std::env::temp_dir().join(format!(
            "beaml-u2-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_nanos()
        ));
        std::fs::create_dir_all(&directory).unwrap();
        let source = directory.join("orders.beaml");
        let stored = directory.join("empty.jsonl");
        std::fs::write(&source, format!("{HEAD}{CHAIN}{TAIL}")).unwrap();
        std::fs::write(&stored, "").unwrap();
        let listing = |dir: &std::path::Path| {
            let mut names: Vec<_> = std::fs::read_dir(dir)
                .unwrap()
                .map(|e| e.unwrap().file_name())
                .collect();
            names.sort();
            names
        };
        // The forced recheck: a valid build of a text whose newest version of Payment is v1, not v2.
        let reset_text = format!("{HEAD}{TAIL}");
        let reset = |_: &str| build(&reset_text, Some("orders"), Some(&stored));
        let (before, stat, names) = (
            std::fs::read(&source).unwrap(),
            std::fs::metadata(&source).unwrap(),
            listing(&directory),
        );
        let error = remove_dead_with(
            &source,
            "orders.beaml",
            Some("orders"),
            &stored,
            true,
            &reset,
        )
        .unwrap_err();
        let after = std::fs::metadata(&source).unwrap();
        assert!(error.starts_with("error: removal check failed"), "{error}");
        assert!(
            error.contains("newest version of Payment changed from v2 to v1"),
            "{error}"
        );
        assert_eq!(before, std::fs::read(&source).unwrap(), "same bytes");
        assert_eq!(
            (stat.ino(), stat.mtime(), stat.mtime_nsec()),
            (after.ino(), after.mtime(), after.mtime_nsec()),
            "same inode and modification time"
        );
        assert_eq!(names, listing(&directory), "no temporary file");
        // Control: the normal recheck removes the step and writes the VERSION MARK v2.
        let normal = |new: &str| build(new, Some("orders"), Some(&stored));
        assert_eq!(
            Ok(1),
            remove_dead_with(
                &source,
                "orders.beaml",
                Some("orders"),
                &stored,
                true,
                &normal
            )
        );
        let written = std::fs::read_to_string(&source).unwrap();
        assert!(
            written.contains("type Payment v2 { order_id: String state: String }")
                && !written.contains("migrate"),
            "{written}"
        );
        let _ = std::fs::remove_dir_all(&directory);
    }
    #[test]
    fn int_literals_and_patterns() {
        assert!(
            compile("fn f 0 -> String = \"zero\"\nfn f n: Int -> String = \"other\"\n").is_ok()
        );
        assert_eq!(
            compile("fn f 0 -> String = \"zero\"\n").unwrap_err(),
            "non-exhaustive function: f"
        );
        assert_eq!(
            compile("fn g -> Int = \"x\"\n").unwrap_err(),
            "type mismatch: expected Int, got String"
        );
    }
    #[test]
    fn effect_input_has_no_int_also_nested() {
        // red-review.md N1 (slice 6b step 1): a nested Int field and Int as the direct input TYPE.
        let tail = "effect payments.authorize I -> P ! O = http.post(\"payments/authorize\")\nfn g i: I -> P ! O = i |> payments.authorize\n";
        let head = "type O { reason: String }\ntype P { id: String }\n";
        assert_eq!(
            compile(&format!(
                "{head}type J {{ n: Int }}\ntype I {{ inner: J }}\n{tail}"
            ))
            .unwrap_err(),
            "effect payments.authorize: slice 6b sends String fields only, not J.n"
        );
        assert_eq!(
            compile(&format!("{head}{}", tail.replace(" I ", " Int "))).unwrap_err(),
            "effect payments.authorize: slice 6b sends String fields only, not Int"
        );
    }
    #[test]
    fn success_and_failure_types_never_overlap() {
        // Plan step 2 first RED, DL-093 (E1).
        for source in [
            "fn f x: String -> String ! String = x\n",
            "fn f x: String -> String ! Int | String = x\n",
        ] {
            let error = compile(source).unwrap_err();
            assert!(
                error.contains("success TYPE String") && error.contains("\n  help: "),
                "{error}"
            );
        }
        assert!(compile("fn f x: String -> String ! Int = 5\n").is_ok());
    }
    #[test]
    fn constructor_is_the_only_way_in() {
        // DL-092, D6B-17, D6B-18: the literal only in its own constructor; a structural twin is no NonZeroInt.
        let head = "type IsZero {}\ntype NonZeroInt { value: Int }\nfn NonZeroInt n: Int -> NonZeroInt ! IsZero\nfn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}\nfn NonZeroInt n -> NonZeroInt ! IsZero = NonZeroInt { value: n }\n";
        assert!(
            compile(&format!(
                "{head}fn wrap n: Int -> NonZeroInt ! IsZero = n |> NonZeroInt\n"
            ))
            .is_ok()
        );
        let error = compile(&format!(
            "{head}fn make n: Int -> NonZeroInt = NonZeroInt {{ value: n }}\n"
        ));
        assert!(
            error
                .unwrap_err()
                .contains("is legal only in the clauses of the constructor fn NonZeroInt")
        );
        assert_eq!(
            compile(&format!(
                "{head}type Plain {{ value: Int }}\nfn same p: Plain -> NonZeroInt = p\n"
            ))
            .unwrap_err(),
            "type mismatch: expected NonZeroInt, got Plain"
        );
    }
    #[test]
    fn enum_literals_and_constructor() {
        // DL-088, D6B-15, D6B-23: literals or a constructor; one Elixir function per signature.
        assert!(compile("enum S { A = \"a\"  K(String) }\nfn f -> S = A\n").is_ok());
        let head = "enum S { A  K(String) }\nfn S c: String -> S\nfn S \"a\" -> S = A\nfn S c -> S = K(c)\n";
        let out = compile(&format!("{head}fn S n: Int -> S\nfn S n -> S = A\n")).unwrap();
        assert!(out.contains("def new_S_1(a0) do") && out.contains("def new_S_2(a0) do"));
        assert!(
            compile(&format!(
                "{head}fn S c: String, d: String -> S\nfn S c, _ -> S = K(c)\n"
            ))
            .unwrap_err()
            .starts_with("unreachable signature: S")
        );
        assert!(
            compile("enum S { A = \"a\" }\nfn S c: String -> S\nfn S c -> S = A\n")
                .unwrap_err()
                .starts_with("error: enum S has literals and a constructor")
        );
    }

    #[test]
    fn pipe_in_any_expression() {
        // DL-086, D6B-25, D6B-27: a nested pipe is nested calls; `+` binds first; no failing nested step.
        let head = "fn f s: String -> String = s\nfn j a: String, b: String -> String = a\n";
        let out = compile(&format!(
            "{head}fn g a: String -> String = j(a + a |> f, a)\n"
        ))
        .unwrap();
        assert!(out.contains("__MODULE__.j(__MODULE__.f((v_a <> v_a)), v_a)"));
        let fail = "type Z {}\ntype N { v: String }\nfn N s: String -> N ! Z\nfn N s -> N ! Z = N { v: s }\n";
        assert!(
            compile(&format!(
                "{fail}type B {{ n: N }}\nfn w s: String -> B ! Z = B {{ n: s |> N }}\n"
            ))
            .unwrap_err()
            .starts_with("error: fn w: a nested pipe has the failing step N\n")
        );
    }
}
