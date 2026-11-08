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
            // `[` and `]` hold the TYPE of a LIST TYPE field (0005 Q5-3).
            '{' | '}' | '(' | ')' | '[' | ']' | ':' | ',' | '=' | '+' | '!' | '|' => {
                Token::Symbol(ch)
            }
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
    // DL-148: the byte end of the line, so `fmt` can make it a row of a clause table.
    end: usize,
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
    // Slice 6b step 6b (D6B-31): `with f1, f2` after the target names redacted input fields that go on the wire.
    with: Vec<String>,
    source_range: Range<usize>,
}
// `effect NAME IN -> OUT ! ERR = ui.event("e") |> f` (slice 6d, DL-130): an ENTRY LINE, an operation that enters the
// module. The head TYPES equal those of fn f (drift rule); the host calls `NAME_with_underscore(params)` (DL-131).
#[derive(Clone, Debug)]
struct Entry {
    name: String,
    input: String,
    output: String,
    failures: Vec<String>,
    kind: String,
    target: String,
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
    // fates-a1 (DL-125, DL-162): `quarantine f`, `quarantine "old"`, `quarantine f "old"`.
    Quarantine(Option<String>, Option<String>),
    // fates-a1 (DL-125, QF-7 ruled): `map "old" -> V` (enum step) or `map f "old" -> V` (owner TYPE step).
    Map(Option<String>, String, String),
    // PF-09: parsed, rejected by the checker until fates-b.
    Redact(String),
    Retire(String, u32),
}
impl Change {
    fn fate(&self) -> bool {
        !matches!(
            self,
            Change::Rename(..) | Change::Add(..) | Change::Drop(..)
        )
    }
}
// The source text of a fate line, for messages (DL-124: source text only).
fn fate_text(change: &Change) -> String {
    let lit = |l: &str| json_string(l);
    match change {
        Change::Quarantine(Some(f), None) => format!("quarantine {f}"),
        Change::Quarantine(None, Some(l)) => format!("quarantine {}", lit(l)),
        Change::Quarantine(Some(f), Some(l)) => format!("quarantine {f} {}", lit(l)),
        Change::Map(None, l, v) => format!("map {} -> {v}", lit(l)),
        Change::Map(Some(f), l, v) => format!("map {f} {} -> {v}", lit(l)),
        Change::Redact(f) => format!("redact {f}"),
        Change::Retire(f, n) => format!("retire {f} keep {n} days"),
        _ => String::new(),
    }
}
// A fate line that a stored value hits: (step label, line text, `quarantined` or `mapped`).
type Fate = (String, String, &'static str);
enum Literal {
    Fine,
    Lost,
    Moved(String, String),
    Fated(Fate),
}
fn variant_of<'t>(table: &'t [(String, String)], literal: &str) -> Option<&'t str> {
    table
        .iter()
        .find(|(_, l)| l == literal)
        .map(|(v, _)| v.as_str())
}
// An enum declaration: its variants and its ENUM LITERALS.
type EnumTable = (Vec<(String, Vec<String>)>, Vec<(String, String)>);
#[derive(Default)]
struct Program {
    types: BTreeMap<String, Definition>,
    clauses: Vec<Clause>,
    signature_lines: Vec<SignatureLine>,
    effects: Vec<Effect>,
    entries: Vec<Entry>,
    migrations: Vec<Migration>,
    retires: Vec<Retire>,
    // Slice 5: the VERSION MARK `type T vN { ... }` per record TYPE that has one (DL-070, DL-071).
    marks: BTreeMap<String, u32>,
    // Slice 6b (DL-082): the ENUM LITERALS `V = "text"` per enum, in source order (D6B-21).
    literals: BTreeMap<String, Vec<(String, String)>>,
    // fates-a1 (DL-155): the VERSION MARK `enum E vN { ... }`, and the older declarations `enum E vK` that stay in the
    // source while stored values of vK exist (ruling on DL-161: the previous literal table comes from them).
    enum_marks: BTreeMap<String, u32>,
    old_enums: BTreeMap<String, BTreeMap<u32, EnumTable>>,
    // Slice 6b step 6b (D6B-29): the (TYPE, field) pairs declared `name: redacted TYPE`.
    redacted: BTreeSet<(String, String)>,
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
    // A TYPE word outside a `type` field: `redacted` stands only there (D6B-29, D6B-64).
    fn type_word(&mut self) -> Checked<String> {
        if matches!(self.peek(), Token::Word(w) if w == "redacted")
            && matches!(self.tokens.get(self.at + 1), Some((Token::Word(_), _)))
        {
            return Err(format!(
                "error: redacted stands only before a field TYPE in a type (D6B-29)\n  at byte {}",
                self.tokens[self.at].1.start
            ));
        }
        self.word()
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
                let ty = self.type_word()?;
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
                Ok(Change::Drop(field, self.type_word()?))
            }
            "quarantine" => {
                self.at += 1;
                let field = match self.peek() {
                    Token::Word(_) => Some(self.word()?),
                    _ => None,
                };
                let literal = match self.peek().clone() {
                    Token::Text(text) => {
                        self.at += 1;
                        Some(text)
                    }
                    _ if field.is_some() => None,
                    _ => return Err(self.error("quarantine: expected a field or a string literal")),
                };
                Ok(Change::Quarantine(field, literal))
            }
            "map" => {
                self.at += 1;
                let field = match self.peek() {
                    Token::Word(_) => Some(self.word()?),
                    _ => None,
                };
                let Token::Text(old) = self.peek().clone() else {
                    return Err(self.error("map: expected the old ENUM LITERAL as a string literal"));
                };
                self.at += 1;
                self.arrow()?;
                let variant = self.word()?;
                if self.peek() == &Token::Symbol('(') {
                    return Err(self.error("a map target takes no payload (QF-6 A)"));
                }
                Ok(Change::Map(field, old, variant))
            }
            "redact" => {
                self.at += 1;
                Ok(Change::Redact(self.word()?))
            }
            "retire" => {
                self.at += 1;
                let field = self.word()?;
                if !matches!(self.peek(), Token::Word(w) if w == "keep") {
                    return Err(self.error(&format!("retire {field}: expected keep <n> days")));
                }
                self.at += 1;
                let Token::Number(days) = self.peek().clone() else {
                    return Err(self.error(&format!("retire {field} keep: expected number of days")));
                };
                self.at += 1;
                if !matches!(self.peek(), Token::Word(w) if w == "days") {
                    return Err(self.error(&format!("retire {field} keep {days}: keep supports days only")));
                }
                self.at += 1;
                Ok(Change::Retire(field, days))
            }
            other => Err(self.error(&format!(
                "unsupported migrate step: {other}; a MIGRATE CHANGE is rename, add or drop, a fate line is quarantine, map, redact or retire"
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
                        if matches!(self.peek(), Token::Word(w) if w == "redacted")
                            && matches!(self.tokens.get(self.at + 1), Some((Token::Word(_), _)))
                        {
                            self.at += 1;
                            program.redacted.insert((name.clone(), field.clone()));
                        }
                        // A LIST TYPE `[T]` keeps its text, also in the fingerprint (PDB-08).
                        let ty = if self.eat('[') {
                            let inner = self.word()?;
                            self.expect(']')?;
                            format!("[{inner}]")
                        } else {
                            self.word()?
                        };
                        fields.push((field, ty));
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
                    // fates-a1 (DL-155): the optional VERSION MARK `enum E vN {`, as on `type` (DL-072, DL-074).
                    let mark = match self.peek().clone() {
                        Token::Word(word) => {
                            let mark = version_word(&word)
                                .map_err(|e| self.error(&format!("enum {name} {e}")))?;
                            self.at += 1;
                            Some(mark)
                        }
                        _ => None,
                    };
                    self.expect('{')?;
                    let mut variants = Vec::new();
                    let mut literals = Vec::new();
                    while !self.eat('}') {
                        let variant = self.word()?;
                        // D6B-20: a bare variant `A` is `A()`.
                        let mut args = Vec::new();
                        if self.eat('(') && !self.eat(')') {
                            loop {
                                args.push(self.type_word()?);
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
                    // DL-155, ruling on DL-161: two marked declarations of one enum; the newest is the enum, the
                    // older ones keep their literal tables for the `--stored` swap check.
                    let newest = program.enum_marks.get(&name).copied();
                    if let (Some(m), Some(n)) = (mark, newest)
                        && m != n
                        && matches!(program.types.get(&name), Some(Definition::Enum(_)))
                    {
                        let mut table = (variants, literals);
                        if m > n {
                            let Some(Definition::Enum(v)) = program
                                .types
                                .insert(name.clone(), Definition::Enum(table.0))
                            else {
                                unreachable!()
                            };
                            let l = program.literals.remove(&name).unwrap_or_default();
                            if !table.1.is_empty() {
                                program.literals.insert(name.clone(), table.1);
                            }
                            program.enum_marks.insert(name.clone(), m);
                            table = (v, l);
                        }
                        let old = program.old_enums.entry(name).or_default();
                        if old.insert(m.min(n), table).is_some() {
                            return Err(self.error("duplicate type"));
                        }
                        continue;
                    }
                    if !literals.is_empty() {
                        program.literals.insert(name.clone(), literals);
                    }
                    if let Some(mark) = mark {
                        program.enum_marks.insert(name.clone(), mark);
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
                                arg = Node::Annotated(Box::new(arg), self.type_word()?);
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
                            end: self.tokens[self.at - 1].1.end,
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
                    // Slice 6d (DL-130): `|> f` after the call makes the line an ENTRY LINE; the event String is free text.
                    if self.peek() == &Token::Pipe {
                        self.at += 1;
                        let target = self.word()?;
                        program.entries.push(Entry {
                            name,
                            input,
                            output,
                            failures,
                            kind,
                            target,
                            source_range: start..self.tokens[self.at - 1].1.end,
                        });
                        continue;
                    }
                    let mut with = Vec::new();
                    if matches!(self.peek(), Token::Word(w) if w == "with") {
                        self.at += 1;
                        loop {
                            with.push(self.word()?);
                            if !self.eat(',') {
                                break;
                            }
                        }
                    }
                    program.effects.push(Effect {
                        name,
                        input,
                        output,
                        failures,
                        kind,
                        path,
                        with,
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
    // DL-108, D6B-84: the EFFECTS that each signature key reaches through call edges, transitively. Set by `validate`.
    reach: BTreeMap<String, BTreeSet<String>>,
    // Q6E-1 C: the generated module name, from the stem for an ENTRY LINE source. Set by `build_with_refusals`.
    module: String,
}
// The Elixir name of a signature key: signature k of a constructor `fn T` (`T#k`) is `new_T_k` (D6B-15).
fn elixir_name(key: &str) -> String {
    match key.split_once('#') {
        Some((name, k)) => format!("new_{name}_{k}"),
        None => key.to_string(),
    }
}
// The signature number k of a key `T#k`.
fn display_k(key: &str) -> &str {
    key.split_once('#').map_or("1", |(_, k)| k)
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
        let newest = match program.types.get(name) {
            Some(Definition::Record(newest)) => newest,
            // fates-a1 (DL-155, PF-06): an enum chain holds bare map and quarantine lines; no TYPE VERSIONS derive.
            Some(Definition::Enum(_)) => {
                enum_chain(program, name, &steps)?;
                continue;
            }
            None => return Err(format!("migrate {name}: unknown type: {name}")),
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
            mark_agrees("type", name, mark, end)?;
        }
        let mut chain = vec![newest.clone()];
        for step in steps.iter().rev() {
            let current = chain.last().unwrap();
            let (a, b) = (step.from, step.to);
            let label = format!("migrate {name} v{a} -> v{b}");
            // K8: an empty MIGRATE STEP (PF-05: a fate line counts).
            if step.changes.is_empty() {
                return Err(empty_step(&label));
            }
            // K7: one field name at most once per MIGRATE STEP (both names of a `rename`). Fate lines: `Checker::fates`.
            let mut seen = BTreeSet::new();
            for change in &step.changes {
                let names: Vec<&String> = match change {
                    Change::Rename(old, new) => vec![old, new],
                    Change::Add(field, _, _) | Change::Drop(field, _) => vec![field],
                    _ => vec![],
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
                    // A fate line keeps the fields (DL-125); its checks run in `Checker::fates`.
                    _ => {}
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

fn empty_step(label: &str) -> String {
    format!("{label}: a MIGRATE STEP needs at least one rename, add, drop or fate line")
}

// fates-a1 (DL-155, PF-06, ruling on DL-161): the chain of an enum. No gaps, the mark agrees, the steps hold bare
// `map` and `quarantine "old"` lines only, and every `from` version keeps its declaration in the source.
fn enum_chain(program: &Program, name: &str, steps: &[&Migration]) -> Checked<()> {
    let start = steps[0].from;
    for (index, step) in steps.iter().enumerate() {
        let from = u64::from(start) + index as u64;
        if u64::from(step.from) != from || u64::from(step.to) != from + 1 {
            return Err(format!(
                "migrate {name} v{} -> v{}: the MIGRATE CHAIN of {name} must count without gaps from its first MIGRATE STEP, expected v{from} -> v{}",
                step.from,
                step.to,
                from + 1
            ));
        }
        let label = format!("migrate {name} v{} -> v{}", step.from, step.to);
        if step.changes.is_empty() {
            return Err(empty_step(&label));
        }
        let bare = |c: &Change| {
            matches!(
                c,
                Change::Map(None, _, _) | Change::Quarantine(None, Some(_))
            )
        };
        if !step.changes.iter().all(bare) {
            return Err(format!(
                "{label}: an enum MIGRATE STEP holds bare map and quarantine lines only (PF-06, DL-162)"
            ));
        }
    }
    let end = steps.last().unwrap().to;
    if let Some(&mark) = program.enum_marks.get(name) {
        mark_agrees("enum", name, mark, end)?;
    }
    Ok(())
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
fn mark_agrees(kind: &str, name: &str, mark: u32, end: u32) -> Checked<()> {
    if mark == end {
        return Ok(());
    }
    let help = if mark < end {
        format!("write: {kind} {name} v{end}")
    } else if u64::from(mark) == u64::from(end) + 1 {
        format!(
            "add migrate {name} v{end} -> v{mark} {{ ... }}, or write {kind} {name} v{end} if no record of v{mark} exists"
        )
    } else {
        format!(
            "add migrate {name} v{end} -> v{} {{ ... }} and the next MIGRATE STEPS to v{mark}, or write {kind} {name} v{end} if no record newer than v{end} exists",
            end + 1
        )
    };
    Err(format!(
        "error: {kind} {name} v{mark} disagrees with its MIGRATE CHAIN: the last MIGRATE STEP is migrate {name} v{} -> v{end}\n  help: the VERSION MARK and the MIGRATE CHAIN must agree; {help}",
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
// The element TYPE of a LIST TYPE `[T]` (0005 Q5-3).
fn list_inner(ty: &str) -> Option<&str> {
    ty.strip_prefix('[')?.strip_suffix(']')
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
            reach: BTreeMap::new(),
            module: "BeamlSpike".into(),
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
        // Q5-3: a LIST TYPE holds a record TYPE and stands only as the one field of a db.list output TYPE.
        for (owner, def) in &program.types {
            let Definition::Record(fields) = def else {
                continue;
            };
            for (field, ty) in fields {
                let Some(inner) = list_inner(ty) else {
                    continue;
                };
                if !matches!(program.types.get(inner), Some(Definition::Record(_))) {
                    return Err(format!(
                        "error: the LIST TYPE {ty} needs a record TYPE inside the brackets"
                    ));
                }
                let output = program
                    .effects
                    .iter()
                    .any(|e| e.kind == "db.list" && &e.output == owner);
                if !output || fields.len() != 1 {
                    return Err(format!(
                        "error: the LIST TYPE {ty} of {owner}.{field} stands only as the field of a db.list output TYPE (Q5-3)"
                    ));
                }
            }
        }
        for name in program.types.keys() {
            checker.check_type(name, &mut Vec::new())?;
        }
        checker.versions = derive_versions(program)?;
        checker.fates()?;
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
    // fates-a1 (PF-07 to PF-11, RF-02 to RF-06, DL-161, DL-162): the checks of the fate lines and of the older enum
    // declarations. One compile error per wrong form.
    fn fates(&self) -> Checked<()> {
        let program = self.program;
        for step in &program.migrations {
            let name = &step.type_name;
            let label = format!("migrate {name} v{} -> v{}", step.from, step.to);
            if !step.changes.iter().any(Change::fate) {
                continue;
            }
            let is_enum = matches!(program.types.get(name), Some(Definition::Enum(_)));
            if self.migrations(name).last().map(|m| m.from) != Some(step.from) {
                let newest = if is_enum {
                    self.enum_newest(name)
                } else {
                    self.newest_version(name)
                };
                return Err(format!(
                    "{label}: a fate line stands only in the last MIGRATE STEP of {name} (v{newest})"
                ));
            }
            let field_type = |f: &str| {
                self.record(name)
                    .ok()
                    .and_then(|fields| fields.iter().find(|(g, _)| g == f))
                    .map(|(_, t)| t.clone())
            };
            let mut quarantined: Vec<&String> = Vec::new();
            let mut lines: BTreeMap<(Option<&String>, &String), bool> = BTreeMap::new();
            for change in step.changes.iter().filter(|c| c.fate()) {
                let text = fate_text(change);
                match change {
                    Change::Redact(f) => {
                        return Err(format!(
                            "{label}: redact {f}: the meaning for stored values is not built yet (fates-b, QF-9)"
                        ));
                    }
                    Change::Retire(f, n) => {
                        return Err(format!(
                            "{label}: retire {f} keep {n} days: the meaning for stored values waits on M5 (QF-4)"
                        ));
                    }
                    Change::Quarantine(Some(f), None) => {
                        let Some(ty) = field_type(f) else {
                            return Err(format!(
                                "{label}: quarantine {f} names no field of {name}"
                            ));
                        };
                        if quarantined.contains(&f) {
                            return Err(format!("{label}: two fate lines name the field {f}"));
                        }
                        if self.constructors.contains(name) {
                            // DL-172: a constructor TYPE takes one quarantine line per parameter.
                        } else if self.constructors.contains(&ty) {
                            let n = self.newest_version(&ty);
                            return Err(format!(
                                "{label}: quarantine {f}: write the quarantine line in the MIGRATE STEP of the constructor TYPE: type {ty} v{} and migrate {ty} v{n} -> v{} {{ quarantine <parameter> }} (QF-3 A)",
                                n + 1,
                                n + 1
                            ));
                        } else if program.literals.contains_key(&ty) {
                            return Err(format!(
                                "{label}: quarantine {f}: a quarantine line on an enum field names the literal: quarantine {f} \"<old literal>\" (DL-162)"
                            ));
                        } else {
                            return Err(format!(
                                "{label}: quarantine {f}: the field {f} has no rule to fail (no constructor, no ENUM LITERAL)"
                            ));
                        }
                        quarantined.push(f);
                    }
                    Change::Quarantine(None, Some(l)) | Change::Map(None, l, _) => {
                        if !is_enum {
                            let rest = match change {
                                Change::Map(_, _, v) => {
                                    format!("map <field> {} -> {v}", json_string(l))
                                }
                                _ => format!("quarantine <field> {}", json_string(l)),
                            };
                            let word = if matches!(change, Change::Map(..)) {
                                "map"
                            } else {
                                "quarantine"
                            };
                            return Err(format!(
                                "{label}: a bare {word} stands only in the MIGRATE STEP of an enum; write {rest}"
                            ));
                        }
                        self.fate_literal(&label, &text, name, change)?;
                        self.fate_once(&label, &mut lines, None, l, change)?;
                    }
                    Change::Quarantine(Some(f), Some(l)) | Change::Map(Some(f), l, _) => {
                        let word = if matches!(change, Change::Map(..)) {
                            "map"
                        } else {
                            "quarantine"
                        };
                        let Some(ty) = field_type(f) else {
                            return Err(format!("{label}: {word} {f} names no field of {name}"));
                        };
                        if !program.literals.contains_key(&ty) {
                            if matches!(program.types.get(&ty), Some(Definition::Enum(_)))
                                && self.constructors.contains(&ty)
                            {
                                self.fate_literal(&label, &text, &ty, change)?;
                            }
                            return Err(format!(
                                "{label}: {word} {f}: the field {f} is no literal enum field"
                            ));
                        }
                        self.fate_literal(&label, &text, &ty, change)?;
                        self.fate_once(&label, &mut lines, Some(f), l, change)?;
                        // RF-05: one literal has one fate line, in the enum step or in the owner step.
                        let bare = |c: &Change| matches!(c, Change::Map(None, m, _) | Change::Quarantine(None, Some(m)) if m == l);
                        if let Some(other) = self.migrations(&ty).last()
                            && let Some(c) = other.changes.iter().find(|c| bare(c))
                        {
                            let word = if matches!(c, Change::Map(..)) {
                                "map"
                            } else {
                                "quarantine"
                            };
                            return Err(format!(
                                "{label}: {text}: {} has a {word} line in migrate {ty} v{} -> v{} too; keep one",
                                json_string(l),
                                other.from,
                                other.to
                            ));
                        }
                    }
                    _ => {}
                }
            }
        }
        // Ruling on DL-161 (DL-155): an enum chain keeps the declaration of every older version; an older
        // declaration needs its step.
        for (name, olds) in &program.old_enums {
            for (version, (variants, literals)) in olds {
                if !literals.is_empty() {
                    self.literal_rules(name, variants, literals)?;
                }
                if !self.migrations(name).iter().any(|m| m.from == *version) {
                    return Err(format!(
                        "error: enum {name} v{version} has no MIGRATE STEP to v{}; add migrate {name} v{version} -> v{} {{ ... }} or remove enum {name} v{version} (DL-155)",
                        version + 1,
                        version + 1
                    ));
                }
            }
        }
        for step in &program.migrations {
            let name = &step.type_name;
            if matches!(program.types.get(name), Some(Definition::Enum(_)))
                && !program
                    .old_enums
                    .get(name)
                    .is_some_and(|o| o.contains_key(&step.from))
            {
                let v = step.from;
                return Err(format!(
                    "error: enum {name} v{v} is not declared; keep the previous declaration while v{v} values exist (DL-155)"
                ));
            }
        }
        Ok(())
    }
    // The checks of one `map "old" -> V` or `quarantine "old"` line on the enum `e`.
    fn fate_literal(&self, label: &str, text: &str, e: &str, change: &Change) -> Checked<()> {
        let word = if matches!(change, Change::Map(..)) {
            "map"
        } else {
            "quarantine"
        };
        if self.constructors.contains(e) {
            return Err(format!(
                "{label}: {word}: {e} has an ENUM CONSTRUCTOR; map works on ENUM LITERALS only (D041 open)"
            ));
        }
        let (Change::Map(_, l, _) | Change::Quarantine(_, Some(l))) = change else {
            return Ok(());
        };
        if let Change::Map(_, _, v) = change {
            let Some(Definition::Enum(variants)) = self.program.types.get(e) else {
                return Ok(());
            };
            match variants.iter().find(|(w, _)| w == v) {
                None => return Err(format!("{label}: {text}: {v} is no variant of {e}")),
                Some((_, args)) if !args.is_empty() => {
                    return Err(format!(
                        "{label}: {text}: {v} carries a payload; map to a variant without payload (QF-6 A)"
                    ));
                }
                _ => {}
            }
        }
        let now = variant_of(&self.program.literals[e], l);
        let before = self.prev_table(e).and_then(|t| variant_of(t, l));
        if now.is_some() && (before.is_none() || before == now) {
            return Err(format!(
                "{label}: {text}: {} is a current ENUM LITERAL of {e} that keeps its variant; a fate line names a literal that left or moved (DL-161)",
                json_string(l)
            ));
        }
        Ok(())
    }
    // RF-04, DL-162: one fate line per (field, literal) in a step.
    fn fate_once<'c>(
        &self,
        label: &str,
        lines: &mut BTreeMap<(Option<&'c String>, &'c String), bool>,
        field: Option<&'c String>,
        literal: &'c String,
        change: &Change,
    ) -> Checked<()> {
        let map = matches!(change, Change::Map(..));
        let of = field.map_or(String::new(), |f| format!(" of field {f}"));
        let l = json_string(literal);
        match lines.insert((field, literal), map) {
            Some(before) if before == map => Err(format!(
                "{label}: two {} lines name {l}{of}",
                if map { "map" } else { "quarantine" }
            )),
            Some(_) => Err(format!(
                "{label}: {l}{of} has a map line and a quarantine line; keep one (DL-162)"
            )),
            None => Ok(()),
        }
    }
    // fates-a1 (DL-155): the newest version of an enum: its mark, else the `to` of its last step, else 1.
    fn enum_newest(&self, name: &str) -> u32 {
        (self.program.enum_marks.get(name).copied())
            .or_else(|| self.migrations(name).last().map(|m| m.to))
            .unwrap_or(1)
    }
    // Ruling on DL-161: the literal table of the version before the newest, from its declaration in the source.
    fn prev_table(&self, e: &str) -> Option<&Vec<(String, String)>> {
        let step = *self.migrations(e).last()?;
        self.program.old_enums.get(e)?.get(&step.from).map(|t| &t.1)
    }
    // The fate line in the last MIGRATE STEP of `name` that `pick` selects: (step label, line text, verb).
    fn fate_in(&self, name: &str, pick: impl Fn(&Change) -> bool) -> Option<Fate> {
        let step = *self.migrations(name).last()?;
        let change = step.changes.iter().find(|c| pick(c))?;
        let verb = if matches!(change, Change::Map(..)) {
            "mapped"
        } else {
            "quarantined"
        };
        Some((
            format!("migrate {name} v{} -> v{}", step.from, step.to),
            fate_text(change),
            verb,
        ))
    }
    // The fate line that names a stored literal of `owner.field` (enum `e`): bare in the enum step, else qualified in
    // the owner step.
    fn literal_fate(&self, owner: &str, field: &str, e: &str, literal: &str) -> Option<Fate> {
        self.fate_in(e, |c| matches!(c, Change::Map(None, l, _) | Change::Quarantine(None, Some(l)) if l == literal))
            .or_else(|| {
                self.fate_in(owner, |c| matches!(c, Change::Map(Some(f), l, _) | Change::Quarantine(Some(f), Some(l)) if f == field && l == literal))
            })
    }
    // DL-102, DL-140, DL-161: what a stored String of a literal enum field means now.
    fn literal_verdict(
        &self,
        owner: &str,
        field: &str,
        e: &str,
        text: Option<&str>,
        kept: bool,
    ) -> Literal {
        let Some(text) = text.filter(|_| !kept) else {
            return Literal::Fine;
        };
        let moved = match variant_of(&self.program.literals[e], text) {
            None => None,
            Some(now) => match self.prev_table(e).and_then(|t| variant_of(t, text)) {
                Some(before) if before != now => Some((before.to_string(), now.to_string())),
                _ => return Literal::Fine,
            },
        };
        match (self.literal_fate(owner, field, e, text), moved) {
            (Some(fate), _) => Literal::Fated(fate),
            (None, Some((before, now))) => Literal::Moved(before, now),
            (None, None) => Literal::Lost,
        }
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
            if self.effect(op).is_some() || self.program.entries.iter().any(|e| &e.name == op) {
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
            if !["http.post", "db.put", "db.get", "db.list"].contains(&effect.kind.as_str()) {
                return Err(format!(
                    "unsupported effect kind: {} in effect {name} (supported: http.post, db.put, db.get, db.list)\n  help: write http.post(\"path\"), db.put(\"records\"), db.get(\"records\") or db.list(\"records\")",
                    effect.kind
                ));
            }
            let db = effect.kind != "http.post";
            // DL-127: one table.
            if db && effect.path != "records" {
                return Err(format!(
                    "error: effect {name}: {} uses the table \"records\" only (DL-127)",
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
            // A DB TRANSPORT has its own rules, not the http wire rules (D6B-40, D6B-19, D6B-03).
            if db {
                self.effect_failures(effect)?;
                self.db_effect(effect)?;
                continue;
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
            // D6B-40: no enum in an EFFECT input, also not nested (the tuple form has no JSON encoding).
            if let Some((place, enum_name)) = self.enum_inside(&effect.input) {
                return Err(format!(
                    "error: effect {name}: the enum field {place} cannot stand in an EFFECT input in slice 6b (D6B-40)\n  help: send a String field, then map it to the enum {enum_name} after the EFFECT"
                ));
            }
            // D6B-19, interim for Q6B-3. Step 8 (DL-101, S3) lifts it for the fields of the output TYPE only.
            let positions = [("input", &effect.input), ("output", &effect.output)]
                .into_iter()
                .chain(effect.failures.iter().map(|f| ("failure", f)));
            for (position, ty) in positions {
                let found = if position == "output" {
                    self.constructors
                        .contains(ty)
                        .then(|| (ty.clone(), String::new()))
                } else {
                    self.constructor_inside(ty)
                };
                if let Some((nominal, field)) = found {
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
            // D6B-65: each `with` name is a top-level redacted field of the input TYPE, named once.
            let input = &effect.input;
            let mut named = BTreeSet::new();
            for field in &effect.with {
                if !self.record(input)?.iter().any(|(f, _)| f == field) {
                    return Err(format!(
                        "error: with names {field}, which is not a field of {input}"
                    ));
                }
                if !self.is_redacted(input, field) {
                    return Err(format!(
                        "error: with names {field}, which is not a redacted field of {input}"
                    ));
                }
                if !named.insert(field) {
                    return Err(format!("error: with names {field} twice"));
                }
            }
            // DL-116 interim (D6B-154, D6B-157): a redacted output field at any depth is a String or Int field of a
            // TYPE without a constructor. Before the slice 1 decode limit. D6B-184: also not below an enum payload
            // or a TYPE with a constructor, because D6B-106 stores the constructor inputs in `value`.
            let mut todo = vec![(effect.output.clone(), false)];
            let mut seen = BTreeSet::new();
            while let Some((ty, below)) = todo.pop() {
                if !seen.insert((ty.clone(), below)) {
                    continue;
                }
                let fields = match self.program.types.get(&ty) {
                    Some(Definition::Record(fields)) => fields,
                    Some(Definition::Enum(variants)) => {
                        todo.extend(
                            variants
                                .iter()
                                .flat_map(|(_, p)| p)
                                .map(|t| (t.clone(), true)),
                        );
                        continue;
                    }
                    None => continue,
                };
                let below = below || self.constructors.contains(&ty);
                for (field, t) in fields {
                    if !self.is_redacted(&ty, field) {
                        todo.push((t.clone(), below));
                    } else if !["String", "Int"].contains(&t.as_str()) || below {
                        return Err(format!(
                            "error: effect {name}: the redacted field {ty}.{field} must be a String or Int field of a TYPE without a constructor in slice 6b (DL-116)\n  help: remove redacted from {ty}.{field}; the limit holds until a rule over an absent value exists (DL-116)"
                        ));
                    } else if ty == effect.output && self.versioned(&ty) {
                        // ponytail: the versioned decode does not mark a field; lift with a `redact` form (DL-125).
                        return Err(format!(
                            "error: effect {name}: the redacted field {ty}.{field} cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)\n  help: remove the MIGRATE CHAIN and the VERSION MARK of {ty}"
                        ));
                    }
                }
            }
            self.output_fields(name, &effect.output)?;
            self.effect_failures(effect)?;
        }
        Ok(())
    }
    // The fields of an EFFECT output TYPE or a ROW TYPE that the decode reads (steps 7 and 8). M4 step 1 (DL-152):
    // a versioned TYPE may hold enum and constructor fields; DL-166: a `rename` onto one builds too.
    fn output_fields(&self, name: &str, output: &str) -> Checked<()> {
        for (field, ty) in self.record(output)? {
            // Slice 6b step 7: an enum with ENUM LITERALS decodes by its mapping (D6B-35).
            if self.program.literals.contains_key(ty) {
                if self.keep_variant(ty).is_none() {
                    return Err(format!(
                        "error: effect {name}: the enum {ty} of {output}.{field} has no keep-value variant (DL-065)\n  help: add the variant Unknown(String) to enum {ty}"
                    ));
                }
            } else if self.constructors.contains(ty) && self.ctor_signatures(ty).is_some() {
                // Step 8 (DL-101): the decode calls the constructor with String parameters (S4).
                self.ctor_keeps(name, output, field, ty)?;
            } else if ty != "String" {
                return Err(format!(
                    "effect {name}: slice 1 decodes String fields only, not {}.{field}",
                    output
                ));
            }
        }
        Ok(())
    }
    // D6B-04, D6B-03: the one failure TYPE of an EFFECT with the field reason: String.
    fn effect_failures(&self, effect: &Effect) -> Checked<()> {
        let name = &effect.name;
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
        Ok(())
    }
    // 0005 P4 (DL-127, DL-129): the transport shape of a db EFFECT, then the ROW TYPE rules (PDB-05 to PDB-07).
    fn db_effect(&self, effect: &Effect) -> Checked<()> {
        let (name, input, output) = (&effect.name, &effect.input, &effect.output);
        let error = |text: String| Err(format!("error: effect {name}: {text}"));
        if !effect.with.is_empty() {
            return error("with stands only after http.post (D6B-31)".into());
        }
        match effect.kind.as_str() {
            "db.put" if output != input => {
                return error(format!(
                    "db.put returns its input TYPE; write {input} -> {input}"
                ));
            }
            "db.get" => {
                let [(key, t)] = self.record(input)?.as_slice() else {
                    return error("db.get takes a key TYPE with one String field (QDB-1)".into());
                };
                if t != "String" {
                    return error("db.get takes a key TYPE with one String field (QDB-1)".into());
                }
                if !self
                    .record(output)?
                    .iter()
                    .any(|(f, t)| f == key && t == "String")
                {
                    return error(format!(
                        "the key field {key} of {input} is not a String field of {output} (QDB-1)"
                    ));
                }
            }
            "db.list" => {
                if !self.record(input)?.is_empty() {
                    return error("db.list takes a query TYPE with no fields (Q5-2)".into());
                }
                if !matches!(self.record(output)?.as_slice(), [(_, t)] if list_inner(t).is_some()) {
                    return error("db.list returns a TYPE with one field of a LIST TYPE, for example type OrderList { items: [Order] } (Q5-3)".into());
                }
            }
            _ => {}
        }
        let row = self.row_type(effect);
        if self.constructors.contains(&row) {
            return error(format!(
                "the ROW TYPE {row} has a constructor; a row holds a plain record (PDB-06)"
            ));
        }
        let fields = self.record(&row)?;
        if let Some((f, _)) = fields.iter().find(|(f, _)| self.is_redacted(&row, f)) {
            return error(format!(
                "the ROW TYPE {row} has the redacted field {f}; rows hold no redacted field yet (M3, DL-116)"
            ));
        }
        for (f, t) in fields {
            if matches!(self.program.types.get(t), Some(Definition::Enum(_)))
                && !self.program.literals.contains_key(t)
            {
                return error(format!(
                    "the enum {t} of {row}.{f} has no ENUM LITERALS; a row stores an enum by its literal (PDB-07)"
                ));
            }
        }
        self.output_fields(name, &row)?;
        // PDB-13: the encode writes a constructor value by its String fields; the decode reads them back through
        // the first signature, so that signature takes exactly those fields.
        for (f, t) in fields.iter().filter(|(_, t)| self.ctor_record(t)) {
            let own = self.record(t)?;
            let first = &self.ctor_signatures(t).expect("checked signatures")[0].1;
            let same = own.len() == first.len()
                && own.iter().all(|(g, u)| u == "String" && first.contains(g));
            if !same {
                return error(format!(
                    "the constructor {t} of {row}.{f} needs a first signature that takes the String fields of {t}; a row stores the field values (PDB-13)"
                ));
            }
        }
        Ok(())
    }
    // The ROW TYPE of a db EFFECT: the input of db.put, the output of db.get, the element of the db.list output.
    fn row_type(&self, effect: &Effect) -> String {
        match effect.kind.as_str() {
            "db.put" => effect.input.clone(),
            "db.list" => self
                .record(&effect.output)
                .ok()
                .and_then(|f| f.first())
                .and_then(|(_, t)| list_inner(t))
                .unwrap_or_default()
                .to_string(),
            _ => effect.output.clone(),
        }
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
    // D6B-40: the first enum inside `ty` as (`Owner.field` or `Owner.Variant`, enum).
    fn enum_inside(&self, ty: &str) -> Option<(String, String)> {
        let here = |place: String, t: &String| match self.program.types.get(t) {
            Some(Definition::Enum(_)) => Some((place, t.clone())),
            _ => self.enum_inside(t),
        };
        match self.program.types.get(ty)? {
            Definition::Record(fields) => fields
                .iter()
                .find_map(|(f, t)| here(format!("{ty}.{f}"), t)),
            Definition::Enum(variants) => variants
                .iter()
                .find_map(|(v, args)| args.iter().find_map(|t| here(format!("{ty}.{v}"), t))),
        }
    }
    // DL-084 K1: the signatures `T#k` of the constructor `fn T` in source order with their parameter names (the
    // keys). None when a parameter is not `name: String` (S4: the decode reads String parameters only).
    fn ctor_signatures(&self, ty: &str) -> Option<Vec<(String, Vec<String>)>> {
        (1..)
            .map(|k| format!("{ty}#{k}"))
            .take_while(|key| self.signatures.contains_key(key))
            .map(|key| {
                let names = self
                    .ctor_args(&key)?
                    .iter()
                    .map(|a| match a {
                        Node::Annotated(inner, t) if t == "String" => match inner.as_ref() {
                            Node::Name(n) if n != "_" => Some(n.clone()),
                            _ => None,
                        },
                        _ => None,
                    })
                    .collect::<Option<Vec<_>>>()?;
                (!names.is_empty()).then_some((key, names))
            })
            .collect::<Option<Vec<_>>>()
            .filter(|s| !s.is_empty())
    }
    // The parameters of signature `key`: its signature line, else its first clause.
    fn ctor_args(&self, key: &str) -> Option<&Vec<Node>> {
        self.program
            .signature_lines
            .iter()
            .find(|l| l.key == key)
            .map(|l| &l.args)
            .or_else(|| {
                self.program
                    .clauses
                    .iter()
                    .find(|c| c.key == key)
                    .map(|c| &c.args)
            })
    }
    // DL-106: a record TYPE with a constructor `fn T` is a struct at the host. Enum constructors stay tuples (D6B-79).
    fn ctor_record(&self, ty: &str) -> bool {
        self.constructors.contains(ty) && self.record(ty).is_ok()
    }
    // D6B-50 (DL-065): for an enum constructor in an EFFECT decode, the last clause of each signature binds every
    // input and puts one String input into a keep-value variant X(String). Gives those variants, one per signature.
    fn ctor_keeps(
        &self,
        effect: &str,
        output: &str,
        field: &str,
        ty: &str,
    ) -> Checked<Vec<String>> {
        let Some(Definition::Enum(variants)) = self.program.types.get(ty) else {
            return Ok(Vec::new());
        };
        let keeps: Vec<&String> = variants
            .iter()
            .filter(|(_, args)| args.as_slice() == ["String"])
            .map(|(v, _)| v)
            .collect();
        let Some(first) = keeps.first() else {
            return Err(format!(
                "error: effect {effect}: the enum {ty} of {output}.{field} has no keep-value variant (DL-065)\n  help: add the variant Unknown(String) to enum {ty}"
            ));
        };
        let mut found = Vec::new();
        for (key, names) in self.ctor_signatures(ty).expect("checked signatures") {
            let last = self.program.clauses.iter().rfind(|c| c.key == key);
            let bound = |arg: &Node| -> Option<String> {
                match arg {
                    Node::Name(n) => Some(n.clone()),
                    Node::Annotated(inner, _) => match inner.as_ref() {
                        Node::Name(n) => Some(n.clone()),
                        _ => None,
                    },
                    _ => None,
                }
            };
            let kept = last.and_then(|clause| {
                let vars = clause.args.iter().map(bound).collect::<Option<Vec<_>>>()?;
                let (variant, input) = match &clause.body {
                    Node::Call(v, args) => match args.as_slice() {
                        [Node::Name(x)] => (v, x),
                        _ => return None,
                    },
                    Node::Pipe(head, steps) => match (head.as_ref(), steps.as_slice()) {
                        (Node::Name(x), [v]) => (v, x),
                        _ => return None,
                    },
                    _ => return None,
                };
                (input != "_" && vars.contains(input) && keeps.contains(&variant))
                    .then(|| variant.clone())
            });
            let Some(variant) = kept else {
                let k = display_k(&key);
                let rest = ", _".repeat(names.len() - 1);
                return Err(format!(
                    "error: effect {effect}: the last clause of signature {k} of constructor {ty} (field {output}.{field}) keeps no String input in the keep-value variant {first} (DL-065, D6B-50)\n  help: bind every input in the last clause and put one String input into {first}, for example fn {ty} other{rest} -> {ty} = {first}(other)"
                ));
            };
            if !found.contains(&variant) {
                found.push(variant);
            }
        }
        Ok(found)
    }
    // The constructor fields of an EFFECT output TYPE, sorted by field name: (field, TYPE).
    fn ctor_fields(&self, output: &str) -> Vec<(String, String)> {
        let mut fields: Vec<(String, String)> = self
            .record(output)
            .cloned()
            .unwrap_or_default()
            .into_iter()
            .filter(|(_, t)| self.constructors.contains(t))
            .collect();
        fields.sort();
        fields
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
        if let Some(inner) = list_inner(name) {
            return self.check_type(inner, path);
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

// A variable bound to a redacted field: the field and its declaring TYPE (D6B-177).
type Redacted = BTreeMap<String, (String, String)>;
// A direct redacted value (D6B-174, D6B-182): the field, its declaring TYPE, and whether the one hop is used.
type Direct = Option<((String, String), bool)>;
// D6B-67 (b), (c), D6B-175, D6B-176: a variant payload or a whole clause body.
fn hold_error(clause: &Clause, field: &str, owner: &str, ty: &str, failure: bool) -> String {
    let (kind, dl) = if failure {
        ("failure TYPE", "DL-105")
    } else {
        ("TYPE", "DL-112")
    };
    format!(
        "error: fn {} copies the redacted field {field} of {owner} into the {kind} {ty}, which cannot hold a redacted value\n  help: do not copy the value ({dl})",
        clause.name
    )
}
impl Checker<'_> {
    // DL-112, D6B-67: no direct copy of a redacted value into a place that is not redacted. A build check after
    // `validate`; `fmt` does not check it.
    fn redacted_copies(&self) -> Checked<()> {
        for clause in &self.program.clauses {
            let mut rv = BTreeMap::new();
            for arg in &clause.args {
                self.bound(arg, &mut rv);
            }
            self.copies(clause, &clause.body, &rv, None)?;
            let ty = self.body_type(clause).0;
            if let (Some(((field, owner), _)), Some(failure)) =
                (self.direct(&clause.body, &rv), self.failure_of(clause, &ty))
            {
                return Err(hold_error(clause, &field, &owner, failure, true));
            }
        }
        Ok(())
    }
    // The pattern variables bound to a redacted field, at any depth and under any name (D6B-174).
    fn bound(&self, node: &Node, rv: &mut Redacted) {
        match node {
            Node::Annotated(inner, _) => self.bound(inner, rv),
            Node::Record(ty, fields) => {
                for (field, value) in fields {
                    match value {
                        Node::Name(v) if v != "_" && self.is_redacted(ty, field) => {
                            rv.insert(v.clone(), (field.clone(), ty.clone()));
                        }
                        _ => self.bound(value, rv),
                    }
                }
            }
            Node::Call(_, args) => args.iter().for_each(|a| self.bound(a, rv)),
            _ => {}
        }
    }
    fn direct(&self, node: &Node, rv: &Redacted) -> Direct {
        match node {
            Node::Name(v) => rv.get(v).map(|hit| (hit.clone(), false)),
            Node::Call(f, args) if args.len() == 1 => self.hop(f, self.direct(&args[0], rv)),
            Node::Pipe(head, steps) => steps
                .iter()
                .fold(self.direct(head, rv), |cur, step| self.hop(step, cur)),
            _ => None,
        }
    }
    // One call or pipe step into the BEAML fn `f` with one parameter: an identity fn keeps a direct value, an
    // accessor makes one (D6B-174, D6B-182). Every clause must qualify (D6B-183). One hop only.
    fn hop(&self, f: &str, cur: Direct) -> Direct {
        let clauses: Vec<&Clause> = self.program.clauses.iter().filter(|c| c.key == f).collect();
        if clauses.is_empty() || clauses.iter().any(|c| c.args.len() != 1) {
            return None;
        }
        let identity = clauses.iter().all(|c| {
            let param = match &c.args[0] {
                Node::Annotated(inner, _) => inner.as_ref(),
                arg => arg,
            };
            matches!((param, &c.body), (Node::Name(p), Node::Name(b)) if p == b)
        });
        if identity {
            return cur.filter(|(_, used)| !used).map(|(hit, _)| (hit, true));
        }
        let mut hits = clauses.iter().map(|c| {
            let mut rv = BTreeMap::new();
            self.bound(&c.args[0], &mut rv);
            match &c.body {
                Node::Name(v) => rv.get(v).cloned(),
                _ => None,
            }
        });
        let first = hits.next().flatten()?;
        hits.all(|h| h.is_some()).then_some((first, true))
    }
    // DL-105, DL-112: a direct value in a record field that is not redacted, or in a variant payload. `outer` is
    // the outer record literal TYPE and the dotted target of a record literal nested in a field (D6B-177).
    fn copies(
        &self,
        clause: &Clause,
        node: &Node,
        rv: &Redacted,
        outer: Option<(&str, &str)>,
    ) -> Checked<()> {
        let payload = |variant: &str, value: Direct| match (self.variants.get(variant), value) {
            (Some((ty, _)), Some(((field, owner), _))) => Err(hold_error(
                clause,
                &field,
                &owner,
                ty,
                self.failure_of(clause, ty).is_some(),
            )),
            _ => Ok(()),
        };
        match node {
            Node::Record(ty, fields) => {
                for (field, value) in fields {
                    let (top, target) = match outer {
                        Some((top, path)) => (top, format!("{path}.{field}")),
                        None => (ty.as_str(), field.clone()),
                    };
                    if let Some(((source, owner), _)) = self.direct(value, rv)
                        && !self.is_redacted(ty, field)
                    {
                        let (kind, dl) = if self.failure_of(clause, top).is_some() {
                            ("failure TYPE", "DL-105")
                        } else {
                            ("TYPE", "DL-112")
                        };
                        return Err(format!(
                            "error: fn {} copies the redacted field {source} of {owner} into {target} of the {kind} {top}, which is not redacted\n  help: mark {field} as redacted in {ty}, or do not copy the value ({dl})",
                            clause.name
                        ));
                    }
                    self.copies(clause, value, rv, Some((top, &target)))?;
                }
                Ok(())
            }
            Node::Call(name, args) => {
                for arg in args {
                    payload(name, self.direct(arg, rv))?;
                    self.copies(clause, arg, rv, None)?;
                }
                Ok(())
            }
            Node::Pipe(head, steps) => {
                self.copies(clause, head, rv, None)?;
                let mut cur = self.direct(head, rv);
                for step in steps {
                    payload(step, cur.clone())?;
                    cur = self.hop(step, cur);
                }
                Ok(())
            }
            Node::Plus(a, b) => {
                self.copies(clause, a, rv, None)?;
                self.copies(clause, b, rv, None)
            }
            Node::Annotated(inner, _) => self.copies(clause, inner, rv, None),
            _ => Ok(()),
        }
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
    fn validate(&mut self) -> Checked<()> {
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
        let mut flows: BTreeMap<&str, &str> = BTreeMap::new();
        for effect in &self.program.effects {
            let flow = &self.flow(effect)?.name;
            // Q6E-4 A: a flow calls one EFFECT, so a REPLAY RUN selects one RESPONSE RECORD per trace.
            if let Some(first) = flows.insert(flow, &effect.name) {
                return Err(format!(
                    "error: fn {flow} calls the effects {first} and {}; slice 6e replays a flow with one effect",
                    effect.name
                ));
            }
        }
        self.reach = self.reach_map();
        self.pure_constructors()?;
        self.entries()
    }
    // Slice 6d: the ENTRY LINE checks in the order of R6D-03, so that each text is reachable: line form, target kind,
    // parameter count, drift rule (DL-130), input TYPE (D6B-130), flow (D6B-129), names (D6B-138).
    fn entries(&self) -> Checked<()> {
        for entry in &self.program.entries {
            let (op, target, input) = (&entry.name, &entry.target, &entry.input);
            let error = |text: String| Err(format!("error: effect {op}: {text}"));
            if !operation_name(op) {
                return Err(format!(
                    "invalid effect name: {op} (expected namespace.operation)"
                ));
            }
            if entry.kind != "ui.event" {
                return error(
                    "slice 6d supports the inbound transport ui.event only (HTTP route entries come later)"
                        .into(),
                );
            }
            if upper(target) {
                return error(format!(
                    "{target} is a constructor; an ENTRY LINE calls a fn (DL-120)"
                ));
            }
            let Some((params, output)) = self.signatures.get(target) else {
                return error(format!("fn {target} is not declared"));
            };
            let [param] = params.as_slice() else {
                return error(format!("fn {target} must take one parameter"));
            };
            let none = |f: &[String]| {
                if f.is_empty() {
                    "none".to_string()
                } else {
                    f.join(" | ")
                }
            };
            let roles = [
                ("input", input.clone(), param.clone()),
                ("output", entry.output.clone(), output.clone()),
                (
                    "failure",
                    none(&entry.failures),
                    none(&self.failures[target]),
                ),
            ];
            for (role, head, fun) in roles {
                if head != fun {
                    return Err(format!(
                        "error: effect {op}: the {role} TYPE is {head} in the head but {fun} in fn {target} (DL-130)\n  help: write the input, output and failure TYPE of fn {target} in the head of effect {op}"
                    ));
                }
            }
            if self.constructors.contains(input) {
                return error(format!(
                    "{input} has a constructor; slice 6d decodes a plain record (D6B-130)"
                ));
            }
            if self.versioned(input) {
                return error(format!(
                    "{input} has a MIGRATE CHAIN or a VERSION MARK; slice 6d decodes the newest TYPE only (D6B-130)"
                ));
            }
            for (field, ty) in self.record(input)? {
                if self.program.literals.contains_key(ty) && self.keep_variant(ty).is_none() {
                    return error(format!(
                        "the enum {ty} of {input}.{field} has no keep-value variant (DL-065)\n  help: add the variant Unknown(String) to enum {ty}"
                    ));
                }
                if self.constructors.contains(ty) {
                    if self.ctor_signatures(ty).is_none() {
                        return error(format!(
                            "the constructor {ty} of {input}.{field} takes a parameter that is not name: String (S4)"
                        ));
                    }
                    self.ctor_keeps(op, input, field, ty)?;
                }
            }
            // TEST O1 (DL-144): the decode maps an enum or constructor field at the top level only, so a deeper one
            // is a build error, not a reject of every event. check_type has already rejected recursive TYPES.
            let mut nested: Vec<&String> = self.record(input)?.iter().map(|(_, t)| t).collect();
            nested.retain(|t| !self.constructors.contains(*t));
            let mut next = 0;
            while let Some(ty) = nested.get(next).copied() {
                next += 1;
                let Some(Definition::Record(fields)) = self.program.types.get(ty) else {
                    continue;
                };
                for (field, t) in fields {
                    let kind = match self.program.types.get(t) {
                        _ if self.constructors.contains(t) => "constructor",
                        Some(Definition::Enum(_)) => "enum",
                        _ => {
                            nested.push(t);
                            continue;
                        }
                    };
                    return error(format!(
                        "the {kind} field {ty}.{field} below the top level of {input} is a slice 6d limit (DL-144)\n  help: move {ty}.{field} to the top level of {input}; slice 6d decodes enum and constructor fields at the top level only"
                    ));
                }
            }
            for reached in &self.reach[target] {
                let effect = self.effect(reached).expect("reached effect");
                if &self.flow(effect)?.name != target {
                    return error(format!(
                        "fn {target} reaches {reached} but is not its flow; slice 6d replays the flow only"
                    ));
                }
            }
            let elixir = op.replace('.', "_");
            if self.signatures.contains_key(&elixir)
                || self
                    .program
                    .effects
                    .iter()
                    .any(|e| e.name.replace('.', "_") == elixir)
                // D6B-201: two ENTRY LINES with one operation collide on the generated name.
                || self.program.entries.iter().filter(|e| &e.name == op).count() > 1
            {
                return Err(format!("duplicate name: {elixir}"));
            }
            if self.program.types.contains_key("Rejected") {
                return error(
                    "the TYPE name Rejected is reserved next to an ENTRY LINE (DL-133)".into(),
                );
            }
        }
        Ok(())
    }
    // The call edges of each signature key, in source order (clause order, then step order): signature keys,
    // variant names and EFFECT names (D6B-85: call forms, nested pipes and whole-body pipe steps).
    fn edges(&self) -> BTreeMap<String, Vec<String>> {
        let mut edges: BTreeMap<String, Vec<String>> = BTreeMap::new();
        for clause in &self.program.clauses {
            let vars = self.vars(clause);
            let targets = edges.entry(clause.key.clone()).or_default();
            if let Node::Pipe(head, _) = &clause.body {
                self.callees(head, &vars, targets);
                targets.extend(self.body_type(clause).1);
            } else {
                self.callees(&clause.body, &vars, targets);
            }
        }
        edges
    }
    fn callees(&self, node: &Node, vars: &BTreeMap<String, String>, out: &mut Vec<String>) {
        match node {
            Node::Call(name, args) => {
                if self.variants.contains_key(name) {
                    out.push(name.clone());
                } else {
                    let given: Vec<_> = args
                        .iter()
                        .map(|a| self.expression(a, vars).expect("checked call"))
                        .collect();
                    out.push(self.pick(name, &given));
                }
                for arg in args {
                    self.callees(arg, vars, out);
                }
            }
            Node::Record(_, fields) => {
                for (_, value) in fields {
                    self.callees(value, vars, out);
                }
            }
            Node::Plus(a, b) => {
                self.callees(a, vars, out);
                self.callees(b, vars, out);
            }
            Node::Pipe(head, steps) => {
                self.callees(head, vars, out);
                let ty = self.expression(head, vars).expect("checked pipe head");
                out.extend(self.steps(ty, steps, None).expect("checked pipe").1);
            }
            _ => (),
        }
    }
    // D6B-84: a fixpoint, so a cycle gives the same set in every order (E4, E5).
    // ponytail: O(n x e) per compile; Tarjan SCC if a source grows large.
    fn reach_map(&self) -> BTreeMap<String, BTreeSet<String>> {
        let edges = self.edges();
        let mut reach: BTreeMap<String, BTreeSet<String>> = self
            .signatures
            .keys()
            .map(|k| (k.clone(), BTreeSet::new()))
            .collect();
        loop {
            let mut changed = false;
            for (key, targets) in &edges {
                let mut found = reach[key].clone();
                for target in targets {
                    if self.effect(target).is_some() {
                        found.insert(target.clone());
                    } else if let Some(more) = reach.get(target) {
                        found.extend(more.iter().cloned());
                    }
                }
                if found != reach[key] {
                    reach.insert(key.clone(), found);
                    changed = true;
                }
            }
            if !changed {
                return reach;
            }
        }
    }
    fn reaches(&self, key: &str) -> bool {
        self.reach.get(key).is_some_and(|r| !r.is_empty())
    }
    // DL-120: a constructor is pure. D6B-112 text; D6B-113 path: the shortest, ties to the first edge in source
    // order (a breadth-first search over the edges in source order).
    fn pure_constructors(&self) -> Checked<()> {
        let edges = self.edges();
        for clause in &self.program.clauses {
            if !upper(&clause.name) || !self.reaches(&clause.key) {
                continue;
            }
            let mut before: BTreeMap<&str, &str> = BTreeMap::new();
            let mut queue = std::collections::VecDeque::from([clause.key.as_str()]);
            let mut end = None;
            while let Some(node) = queue.pop_front() {
                if self.effect(node).is_some() {
                    end = Some(node);
                    break;
                }
                for target in edges.get(node).into_iter().flatten() {
                    if target != &clause.key && !before.contains_key(target.as_str()) {
                        before.insert(target, node);
                        queue.push_back(target);
                    }
                }
            }
            let mut path = vec![end.expect("a reaching constructor has a path")];
            while let Some(node) = before.get(path.last().unwrap()) {
                path.push(node);
            }
            let path: Vec<_> = path.iter().rev().map(|k| display(k)).collect();
            let name = &clause.name;
            return Err(format!(
                "error: fn {name}: a constructor cannot reach an EFFECT: {} (DL-120)\n  help: call the EFFECT in a lowercase fn, then pipe its result into fn {name}",
                path.join(" -> ")
            ));
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
            Node::Record(ty, fields) if self.ctor_record(ty) => format!(
                "%__MODULE__.{ty}{{{}}}",
                fields
                    .iter()
                    .map(|(n, v)| format!("{n}: {}", self.emit_node(v, vars)))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
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
        let ctor = self.program.types.keys().any(|t| self.ctor_record(t));
        let nested = if self.structs().is_empty()
            && !ctor
            && self.program.effects.is_empty()
            && self.program.retires.is_empty()
            && self.program.entries.is_empty()
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
        let is_struct = if ctor { " is_struct: 2," } else { "" };
        let mut out = format!(
            "# Generated by experiment 0001. Not a stable ABI.\ndefmodule {} do\n  import Kernel, only: [and: 2, is_binary: 1,{is_integer} is_map: 1,{is_struct} map_size: 1, ==: 2, <>: 2, if: 2, raise: 2, def: 2, defp: 2{nested}]\n",
            self.module
        );
        // D6B-07: the failure structs that no EFFECT names, or that a clause body builds, come first.
        out.push_str(
            &self.emit_structs(|f| self.ctor_record(f) || !self.effect_failure(f) || self.built(f)),
        );
        if !self.program.entries.is_empty() {
            // DL-133: the decode reject of an ENTRY LINE, apart from the failure TYPES of the fn.
            out.push_str("  defmodule Rejected do\n    import Kernel, only: [defstruct: 1]\n    defstruct [:reason]\n  end\n");
        }
        out.push_str("  defp __beaml_valid__(v, <<83,116,114,105,110,103>>), do: is_binary(v) and String.valid?(v)\n");
        if int {
            out.push_str("  defp __beaml_valid__(v, <<73,110,116>>), do: is_integer(v)\n");
        }
        // Q5-3: a LIST TYPE value is a list of values of its record TYPE.
        let lists: BTreeSet<&String> = self
            .program
            .types
            .values()
            .flat_map(|def| match def {
                Definition::Record(fields) => fields.iter().map(|(_, t)| t).collect(),
                Definition::Enum(_) => Vec::new(),
            })
            .filter(|t| list_inner(t).is_some())
            .collect();
        for ty in lists {
            out.push_str(&format!(
                "  defp __beaml_valid__(v, {}), do: :erlang.is_list(v) and Enum.all?(v, fn x -> __beaml_valid__(x, {}) end)\n",
                binary(ty),
                binary(list_inner(ty).expect("a LIST TYPE"))
            ));
        }
        // DL-115 (Q6B-14 A): a marked EFFECT output field holds a value of its TYPE or the atom `:redacted`.
        let marked: BTreeSet<String> = self
            .program
            .types
            .keys()
            .flat_map(|t| self.output_marks(t))
            .map(|(_, t)| t)
            .collect();
        for ty in marked {
            let tag = binary(&format!("redacted {ty}"));
            out.push_str(&format!(
                "  defp __beaml_valid__(:redacted, {tag}), do: true\n  defp __beaml_valid__(v, {tag}), do: __beaml_valid__(v, {})\n",
                binary(&ty)
            ));
        }
        for (name, def) in &self.program.types {
            match def {
                Definition::Record(fields) if self.ctor_record(name) => {
                    let checks = fields
                        .iter()
                        .map(|(n, t)| format!("__beaml_valid__(Map.get(v, :{n}), {})", binary(t)))
                        .collect::<Vec<_>>();
                    out.push_str(&format!("  defp __beaml_valid__(v, {}) when is_struct(v, __MODULE__.{name}), do: {}\n", binary(name), if checks.is_empty() { "true".into() } else { checks.join(" and ") }));
                }
                Definition::Record(fields) => {
                    let marks = self.output_marks(name);
                    let checks = fields
                        .iter()
                        .map(|(n, t)| {
                            let t = if marks.iter().any(|(f, _)| f == n) {
                                format!("redacted {t}")
                            } else {
                                t.clone()
                            };
                            format!("__beaml_valid__(Map.get(v, {}), {})", binary(n), binary(&t))
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
                    // D6B-88: a plain record head is the span input; any other head gives `nil`.
                    let ty = self.expression(head, &vars).expect("checked pipe head");
                    let plain = self.record(&ty).is_ok() && !self.ctor_record(&ty);
                    out.push_str(&format!(
                        "  defp __beaml_{fun}({params}) do\n    p0 = {}\n{}  end\n",
                        self.emit_node(head, &vars),
                        self.emit_chain(
                            &self.body_type(clause).1,
                            fails.then_some(clause),
                            service,
                            "    ",
                            Step::Live,
                            &if plain {
                                self.redact("p0", &ty, &[], "")
                            } else {
                                "nil".into()
                            }
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
            out.push_str(&if effect.kind == "http.post" {
                self.emit_effect(effect, service)
            } else {
                self.emit_db_effect(effect, service)
            });
        }
        if !self.program.effects.is_empty() {
            out.push_str(&self.emit_replay(service));
        }
        for entry in &self.program.entries {
            out.push_str(&self.emit_entry(entry, service));
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
        written_once(&out)
    }
}

// D6B-198: a module-level item (a def clause, a nested module, a comment) that stands two times in the same text is
// written once, at its first place. Several EFFECTS and ENTRY LINES share `Http`, `BeamlFailure`, the failure structs
// and the decode helpers of a shared TYPE. A one-EFFECT source repeats no item, so its bytes stay (N13).
// ponytail: keyed by text, not by name; a def with one name and other text still reaches elixirc (N2 catches it).
fn written_once(code: &str) -> String {
    let (mut seen, mut out, mut item) = (BTreeSet::new(), String::new(), String::new());
    for line in code.split_inclusive('\n').chain([""]) {
        let starts = line.is_empty()
            || (line != "  end\n"
                && !line.starts_with("   ")
                && line != "\n"
                && !line.starts_with("  end "));
        if starts {
            if !item.starts_with("  ") || seen.insert(item.clone()) {
                out.push_str(&item);
            }
            item.clear();
        }
        item.push_str(line);
    }
    out
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
    // D6B-148 (DL-111 1A): the newest version writes a redacted field TYPE as `redacted T` (`type` key, fingerprint).
    fn type_versions(&self, name: &str) -> Vec<Vec<(String, String)>> {
        let mut chain = match self.versions.get(name) {
            Some(chain) => chain.clone(),
            None => vec![self.record(name).cloned().unwrap_or_default()],
        };
        for (field, ty) in chain.last_mut().into_iter().flatten() {
            if self.is_redacted(name, field) {
                *ty = format!("redacted {ty}");
            }
        }
        chain
    }
    fn is_redacted(&self, ty: &str, field: &str) -> bool {
        self.program
            .redacted
            .contains(&(ty.to_string(), field.to_string()))
    }
    // Slice 6b step 6b (DL-089, D6B-72): the paths of the redacted fields of a TYPE, at any depth.
    fn redacted_paths(&self, ty: &str) -> Vec<Vec<String>> {
        let Some(Definition::Record(fields)) = self.program.types.get(ty) else {
            return Vec::new();
        };
        let mut paths = Vec::new();
        for (field, t) in fields {
            if self.is_redacted(ty, field) {
                paths.push(vec![field.clone()]);
            } else {
                for mut path in self.redacted_paths(t) {
                    path.insert(0, field.clone());
                    paths.push(path);
                }
            }
        }
        paths
    }
    // D6B-32, D6B-33: `expr` of TYPE `ty` without its redacted fields at any depth, except the top-level `keep` names
    // (the `with` names on the wire). Unchanged without redacted fields, so other sources keep their output.
    fn redact(&self, expr: &str, ty: &str, keep: &[String], owner: &str) -> String {
        let paths: Vec<String> = self
            .redacted_paths(ty)
            .into_iter()
            .filter(|p| !(p.len() == 1 && keep.contains(&p[0])))
            .map(|p| {
                let keys: Vec<String> = p.iter().map(|k| binary(k)).collect();
                format!("[{}]", keys.join(", "))
            })
            .collect();
        if paths.is_empty() {
            expr.to_string()
        } else {
            format!("{owner}__beaml_redact__({expr}, [{}])", paths.join(", "))
        }
    }
    // DL-115, D6B-55: the redacted (field, TYPE) pairs of an EFFECT output TYPE; DL-116 keeps them top-level.
    fn output_marks(&self, ty: &str) -> Vec<(String, String)> {
        if !self.program.effects.iter().any(|e| e.output == ty) {
            return Vec::new();
        }
        self.record(ty)
            .map(|fields| {
                fields
                    .iter()
                    .filter(|(f, _)| self.is_redacted(ty, f))
                    .cloned()
                    .collect()
            })
            .unwrap_or_default()
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
    // The `type` key of an ENTRY RECORD, a ROW CORE and a db call record: the newest TYPE VERSION, fields in source
    // order (DL-141, R6D-05, R6D-13); the fingerprint sorts.
    fn emit_type_key(&self, ty: &str) -> String {
        let versions = self.type_versions(ty);
        let type_fields = versions.last().expect("one TYPE VERSION");
        format!(
            "%{{name: {}, version: {}, fields: [{}], fingerprint: {}}}",
            binary(ty),
            self.newest_version(ty),
            type_fields
                .iter()
                .map(|(f, t)| format!("[{}, {}]", binary(f), binary(t)))
                .collect::<Vec<_>>()
                .join(", "),
            binary(&fingerprint(type_fields))
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
    // A clause whose body has the failure TYPE builds its struct in `result` (struct-order P2).
    fn built(&self, failure: &str) -> bool {
        self.program.clauses.iter().any(|c| {
            self.failure_of(c, &self.body_type(c).0)
                .is_some_and(|f| f == failure)
        })
    }
    fn emit_structs(&self, keep: impl Fn(&str) -> bool) -> String {
        let mut out = String::new();
        let ctors = self.program.types.keys().filter(|t| self.ctor_record(t));
        let all: BTreeSet<String> = self.structs().into_iter().chain(ctors.cloned()).collect();
        for failure in all.into_iter().filter(|f| keep(f)) {
            let fields: Vec<String> = self
                .record(&failure)
                .expect("checked failure")
                .iter()
                .map(|(field, _)| format!(":{field}"))
                .collect();
            if self.ctor_record(&failure) {
                out.push_str(&self.emit_new(&failure, &fields));
                continue;
            }
            out.push_str(&format!(
                "  defmodule {failure} do\n    import Kernel, only: [defstruct: 1]\n    defstruct [{}]\n  end\n",
                fields.join(", ")
            ));
        }
        out
    }
    // DL-117: `T.new/1` takes one map with atom keys. The first signature whose parameter names equal the key set
    // runs (D6B-99, D6B-101). No match: `{:error, {:no_signature, text}}` (D6B-97), with the help line for a non-atom
    // key (D6B-98). A non-map raises (D6B-100). The result is always `{:ok, _}` or `{:error, _}` (D6B-74).
    fn emit_new(&self, ty: &str, fields: &[String]) -> String {
        let mut clauses = String::new();
        for key in (1..)
            .map(|k| format!("{ty}#{k}"))
            .take_while(|key| self.signatures.contains_key(key))
        {
            let args = self.ctor_args(&key).expect("checked signature");
            // ponytail: an unnamed parameter gets the key `aI`; DL-117 assumes named parameters.
            let names: Vec<String> = args
                .iter()
                .enumerate()
                .map(|(i, a)| match a {
                    Node::Annotated(inner, _) => match inner.as_ref() {
                        Node::Name(n) if n != "_" => n.clone(),
                        _ => format!("a{i}"),
                    },
                    _ => format!("a{i}"),
                })
                .collect();
            let vars: Vec<String> = (0..names.len()).map(|i| format!("a{i}")).collect();
            let pattern: Vec<String> = names
                .iter()
                .zip(&vars)
                .map(|(n, v)| format!("{n}: {v}"))
                .collect();
            let call = format!("@parent.{}({})", elixir_name(&key), vars.join(", "));
            let body = if self.failures[&key].is_empty() {
                format!("{{:ok, {call}}}")
            } else {
                call
            };
            clauses.push_str(&format!(
                "    def new(%{{{}}} = m) when map_size(m) == {}, do: {body}\n",
                pattern.join(", "),
                names.len()
            ));
        }
        format!(
            "  defmodule {ty} do\n    import Kernel\n    @parent __MODULE__ |> Module.split() |> Enum.drop(-1) |> Module.concat()\n    defstruct [{}]\n\n{clauses}\n    def new(m) when is_map(m) do\n      text = \"{ty}.new/1: no signature takes these keys\"\n      help = \"\\n  help: keys must be atoms; decode outside data through the EFFECT\"\n      {{:error, {{:no_signature, if(Enum.all?(Map.keys(m), &is_atom/1), do: text, else: text <> help)}}}}\n    end\n\n    def new(_), do: raise(ArgumentError, \"invalid BEAML input\")\n  end\n",
            fields.join(", ")
        )
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
        if self.ctor_record(failure) {
            return format!("{{:error, {value}}}");
        }
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
    // The pipe after `p0 = head`: one `with` clause per step; a failed step stops the pipe. `head` is the span
    // input of a reaching step (D6B-88).
    fn emit_chain(
        &self,
        steps: &[String],
        fails: Option<&Clause>,
        service: &str,
        indent: &str,
        mode: Step,
        head: &str,
    ) -> String {
        let owner = if mode == Step::Live {
            "__MODULE__"
        } else {
            "@parent"
        };
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
                    // 0005 P4 (PDB-19): a db step checks the request projection and the digest, then decodes the
                    // recorded `value` in `replay_<elixir>`; BeamlDb is never called.
                    if effect.kind != "http.post" {
                        let request = if effect.kind == "db.put" {
                            format!(
                                "@parent.__beaml_encode_{}({input})",
                                effect.input.to_ascii_lowercase()
                            )
                        } else {
                            input.clone()
                        };
                        clauses.push(format!(
                            ":ok <- expect(record[\"request\"], {request}, :request_mismatch)"
                        ));
                        clauses.push("{:ok, bytes, _keys} <- body(record)".into());
                        clauses.push(format!(
                            "{{:ok, {output}}} <- @parent.__beaml_attempt__(fn -> ProbeSupport.span({}, :internal, {head}, nil, fn -> replay_{}(record[\"outcome\"], record[\"reason\"], bytes) end) end)",
                            binary(&format!("{service}.{step}")),
                            effect.name.replace('.', "_"),
                        ));
                        matched = true;
                        continue;
                    }
                    clauses.push(format!(
                        ":ok <- expect(record[\"request\"], {}, :request_mismatch)",
                        self.redact(&input, &effect.input, &[], "@parent.")
                    ));
                    clauses.push(":ok <- expect(record[\"status\"], 200, :status_mismatch)".into());
                    // Slice 6b step 6a (D6B-58, D6B-60): the digest check of the projection gives the re-encoded `value`.
                    clauses.push("{:ok, bytes, keys} <- body(record)".into());
                    // With a MIGRATE CHAIN, the decode reads the body as the TYPE VERSION of the record.
                    let version = if !self.versioned(&effect.output) {
                        ""
                    } else {
                        ", record[\"type\"]"
                    };
                    clauses.push(format!(
                        "{{:ok, {output}}} <- @parent.__beaml_attempt__(fn -> ProbeSupport.span({}, :internal, {head}, nil, fn -> @parent.__beaml_result_{}(bytes{version}, keys{marked}) end) end)",
                        binary(&format!("{service}.{step}")),
                        effect.name.replace('.', "_"),
                        marked = if self.output_marks(&effect.output).is_empty() {
                            ""
                        } else {
                            ", record[\"redacted\"]"
                        }
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
            let reaches = self.reaches(step);
            let step = display(step);
            // DL-119 S: only a step that reaches an EFFECT through a fn has a span; a pure step is a plain call.
            let expression = if mode == Step::Live && reaches {
                format!(
                    "ProbeSupport.span({}, :internal, {head}, {}, fn -> {call} end)",
                    binary(&format!("{service}.{step}")),
                    binary(step)
                )
            } else {
                call
            };
            if failing {
                clauses.push(format!("{{:ok, {output}}} <- {expression}"));
                matched = true;
            } else {
                clauses.push(format!("{output} = {expression}"));
            }
            // D6B-89, D6B-114: the Orders log is the next `with` clause after the step before a direct EFFECT.
            if let (Step::Live, Some(effect), false) = (
                mode,
                steps.get(index + 1).and_then(|s| self.effect(s)),
                failing,
            ) {
                clauses.push(format!(
                    "_ = ProbeSupport.event({}, {})",
                    binary(&format!(
                        "{}_request_prepared",
                        effect.output.to_ascii_lowercase()
                    )),
                    binary(step)
                ));
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
        let mut out = format!(
            "  # beaml-declaration-v1 {name} {} {}\n",
            effect.source_range.start, effect.source_range.end
        );
        // A failed EFFECT raises inside its span (outcome "error", attribute `reason`) and returns
        // `{:error, %Failure{reason: r}}` outside it. Transport, status and decode never raise to the caller.
        let failure = &effect.failures[0];
        out.push_str(&format!(
            "  def {elixir}(a0) do\n    if __beaml_valid__(a0, {input}) do\n      __beaml_attempt__(fn ->\n        ProbeSupport.span({span}, :client, {record}, nil, fn ->\n          carrier = if ProbeSupport.config(:drop_context), do: [], else: :otel_propagator_text_map.inject([])\n\n          case __MODULE__.Http.post(:{namespace}_port, {path}, {wire}, carrier) do\n            {{:ok, status, bytes}} ->\n              __MODULE__.Replay.record({op}{record}, status, bytes)\n              if status == 200, do: __beaml_result_{elixir}(bytes), else: __beaml_fail_{elixir}({status_reason})\n\n            :error ->\n              __beaml_fail_{elixir}({transport_reason})\n          end\n        end)\n      end)\n    else\n      raise ArgumentError, \"invalid BEAML input\"\n    end\n  end\n",
            input = binary(&effect.input),
            op = self.replay_op(name),
            span = binary(&format!("{service}.{name}")),
            path = binary(&effect.path),
            status_reason = binary("status"),
            transport_reason = binary("transport"),
            record = self.redact("a0", &effect.input, &[], ""),
            wire = self.redact("a0", &effect.input, &effect.with, ""),
        ));
        if !self.program.redacted.is_empty() {
            // D6B-71: the redaction works on the plain map form; one path list per call.
            out.push_str("  def __beaml_redact__(v, paths) when is_map(v) do\n    Enum.reduce(paths, v, fn\n      [key], acc -> Map.delete(acc, key)\n      [key | rest], acc -> if Map.has_key?(acc, key), do: Map.put(acc, key, __beaml_redact__(Map.get(acc, key), [rest])), else: acc\n    end)\n  end\n\n  def __beaml_redact__(v, _paths), do: v\n");
        }
        // DL-115, D6B-55: the marked output fields (top-level String or Int fields, DL-116).
        let marks = self.output_marks(&effect.output);
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
        // M4 step 1 (DL-152): enum and constructor fields pass the steps raw; the DL-101 tail types them after.
        // A record `type` with another TYPE name, an unknown version or another fingerprint is a typed
        // decode error. No `type` key: the newest version. Without a chain the decode stays the slice 1 form.
        let parts = self.decode_parts(name, &effect.output);
        out.push_str(&parts.0);
        let (_, literal_map, tail, keeps, ctor_fields, inner) = parts;
        let unknown_fields = format!(
            "__beaml_unknown_fields_{}",
            effect.output.to_ascii_lowercase()
        );
        if !self.versioned(&effect.output) {
            out.push_str(&self.plain_decode(
                &effect.output,
                &marks,
                &declared,
                &literal_map,
                &tail,
            ));
        } else {
            out.push_str(&self.versioned_decode(&effect.output, &declared, &literal_map, &tail));
        }
        // Slice 6b step 6a (DL-105, D6B-54, D6B-56, D6B-57): the projection of a body for the RESPONSE RECORD.
        // `value`: the wire values under the declared keys of the newest TYPE VERSION, nested by DL-099 and D6B-49,
        // not validated; `:null` when the body is not a JSON object. `unknown_keys`: the other key names, dotted.
        // D6B-56 amendment: a dotted name per level, also below an undeclared key. D6B-55: a marked field leaves
        // `value`; `redacted` lists it when it was present and valid.
        if !marks.is_empty() {
            let pairs: Vec<String> = marks
                .iter()
                .map(|(f, t)| format!("{{{}, {}}}", binary(f), binary(t)))
                .collect();
            out.push_str(&format!(
                "  def __beaml_marked_{elixir}(body) do\n    Enum.sort(Enum.flat_map([{}], fn {{field, type}} -> if __beaml_valid__(Map.get(body, field), type), do: [field], else: [] end))\n  end\n",
                pairs.join(", ")
            ));
        }
        // D6B-56 amendment, D6B-172: a dotted name per level for every EFFECT source (one record shape).
        out.push_str(&keys_fn());
        out.push_str(&self.emit_project(&elixir, &effect.output, &marks, &declared, &inner));
        // D6B-60: a REPLAY RUN passes the record `unknown_keys` as `extra`; the span gets the sorted union.
        let (result_head, arity) = if !marks.is_empty() {
            (
                format!(
                    "  def __beaml_result_{elixir}(a0), do: __beaml_result_{elixir}(a0, [], [])\n  def __beaml_result_{elixir}(a0, extra, marked) do\n"
                ),
                ", marked",
            )
        } else if !self.versioned(&effect.output) {
            (
                format!(
                    "  def __beaml_result_{elixir}(a0), do: __beaml_result_{elixir}(a0, [])\n  def __beaml_result_{elixir}(a0, extra) do\n"
                ),
                "",
            )
        } else {
            (
                format!(
                    "  def __beaml_result_{elixir}(a0), do: __beaml_result_{elixir}(a0, nil, [])\n  def __beaml_result_{elixir}(a0, type_version, extra) do\n"
                ),
                ", type_version",
            )
        };
        let mark = if keeps.is_empty() {
            String::new()
        } else {
            format!(
                "fields = {unknown_fields}(value)\n        if fields == [], do: :ok, else: :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :unknown_fields, fields)\n        "
            )
        };
        out.push_str(&format!(
            "{result_head}    case {decode}(a0{arity}) do\n      {{:ok, value, keys}} ->\n        keys = Enum.sort(Enum.uniq(Enum.concat(extra, keys)))\n        if keys == [], do: :ok, else: :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :unknown_keys, keys)\n        {mark}{{:ok, value}}\n\n      :error ->\n        __beaml_fail_{elixir}({decode_reason})\n{reject}    end\n  end\n  def __beaml_fail_{elixir}(a0) do\n    :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :reason, a0)\n    raise(__MODULE__.BeamlFailure, error: Kernel.struct!(__MODULE__.{failure}, reason: a0))\n  end\n  def __beaml_attempt__(a0) do\n    try do\n      a0.()\n    rescue\n      failure in __MODULE__.BeamlFailure -> {{:error, failure.error}}\n    end\n  end\n",
            decode_reason = binary("decode"),
            reject = if ctor_fields.is_empty() {
                String::new()
            } else {
                format!("\n      {{:error, reason}} ->\n        __beaml_fail_{elixir}(reason)\n")
            },
        ));
        out.push_str(
            &self
                .emit_structs(|f| !self.ctor_record(f) && self.effect_failure(f) && !self.built(f)),
        );
        out.push_str("  defmodule BeamlFailure do\n    import Kernel\n    defexception [:error]\n\n    @impl true\n    def message(_), do: \"BEAML failure\"\n  end\n");
        out.push_str(HTTP);
        out
    }
    // D6B-199: the `Replay` clauses of one EFFECT: `record` and `run`, with the operation first from two EFFECTS on.
    fn emit_replay_clauses(&self, effect: &Effect, service: &str) -> (String, String) {
        let name = &effect.name;
        let elixir = name.replace('.', "_");
        let decode = decode_name(&effect.output);
        let flow = self.flow(effect).expect("checked flow");
        let op = self.replay_op(name);
        let run = format!(
            "    def run({op}a0, trace_id, records) do\n      p0 = a0\n{chain}    end\n",
            chain = self.emit_chain(
                &self.body_type(flow).1,
                Some(flow),
                service,
                "      ",
                Step::Replay,
                &self.redact("p0", &self.signatures[&flow.key].0[0], &[], "@parent."),
            ),
        );
        if effect.kind != "http.post" {
            return (self.emit_db_replay(effect), run);
        }
        let marks = self.output_marks(&effect.output);
        let (_, _, _, keeps, ctor_fields, _) = self.decode_parts(name, &effect.output);
        let unknown_fields = format!(
            "__beaml_unknown_fields_{}",
            effect.output.to_ascii_lowercase()
        );
        let record = format!(
            "    def record({op}request, status, bytes) do\n      ctx = OpenTelemetry.Tracer.current_span_ctx()\n      {{value, unknown_keys{marked}}} = @parent.__beaml_project_{elixir}(bytes)\n\n      {{unknown_fields, outcome, reason}} =\n        case @parent.{decode}(bytes) do\n          {fields}\n          :error -> {{[], \"rejected\", \"decode\"}}{ctor_capture}\n        end\n\n      {{outcome, reason}} = if status == 200, do: {{outcome, reason}}, else: {{\"rejected\", \"status\"}}\n\n      ProbeSupport.Capture.write(\"responses\", %{{\n        version: 3,\n        trace_id: OpenTelemetry.Span.hex_trace_id(ctx),\n        span_id: OpenTelemetry.Span.hex_span_id(ctx),\n        artifact_id: ProbeSupport.beam_hash(@parent),\n        operation: {operation},\n        attempt: 1,\n        request: request,\n        status: status,\n        value: value,\n        redacted: {redacted},\n        unknown_keys: unknown_keys,\n        value_sha256: digest(value, unknown_keys, {redacted}),\n        unknown_fields: unknown_fields,\n        type: {type_version},\n        outcome: outcome,\n        reason: reason\n      }})\n    end\n",
            operation = binary(name),
            marked = if marks.is_empty() { "" } else { ", redacted" },
            redacted = if marks.is_empty() { "[]" } else { "redacted" },
            // Step 7 (notes.md S4): `unknown_fields` holds field names only. DL-143 (QV3-4 A): `outcome` and
            // `reason` from the status, then the decode, then the constructor; `unknown_fields` always.
            fields = if keeps.is_empty() {
                "{:ok, _, _} -> {[], \"accepted\", :null}".to_string()
            } else {
                format!(
                    "{{:ok, decoded, _}} -> {{@parent.{unknown_fields}(decoded), \"accepted\", :null}}"
                )
            },
            ctor_capture = if ctor_fields.is_empty() {
                ""
            } else {
                "\n          {:error, reason} -> {[], \"rejected\", reason}"
            },
            type_version = self.emit_type_version(&effect.output),
        );
        (record, run)
    }
    // 0005 P4: a db EFFECT in the parent module. The call runs in `Replay` (the ROW CORE, the db call record and the
    // row decode need its `digest/3` and `body/1`); the parent keeps the input check, the client span, the failure
    // and the decode and encode of the ROW TYPE.
    fn emit_db_effect(&self, effect: &Effect, service: &str) -> String {
        let name = &effect.name;
        let elixir = name.replace('.', "_");
        let row = self.row_type(effect);
        let kind = &effect.kind[3..];
        let mut out = format!(
            "  # beaml-declaration-v1 {name} {} {}\n  def {elixir}(a0) do\n    if __beaml_valid__(a0, {}) do\n      __beaml_attempt__(fn ->\n        ProbeSupport.span({}, :client, a0, nil, fn -> __MODULE__.Replay.{kind}_{elixir}(a0) end)\n      end)\n    else\n      raise ArgumentError, \"invalid BEAML input\"\n    end\n  end\n  def __beaml_fail_{elixir}(a0) do\n    :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :reason, a0)\n    raise(__MODULE__.BeamlFailure, error: Kernel.struct!(__MODULE__.{}, reason: a0))\n  end\n",
            effect.source_range.start,
            effect.source_range.end,
            binary(&effect.input),
            binary(&format!("{service}.{name}")),
            effect.failures[0],
        );
        let declared: Vec<String> = self
            .record(&row)
            .expect("checked ROW TYPE")
            .iter()
            .map(|(f, _)| binary(f))
            .collect();
        let (defs, literal_map, tail, _, _, _) = self.decode_parts(name, &row);
        out.push_str(&defs);
        out.push_str(&if self.versioned(&row) {
            self.versioned_decode(&row, &declared, &literal_map, &tail)
        } else {
            self.plain_decode(&row, &[], &declared, &literal_map, &tail)
        });
        out.push_str(&self.emit_encode(&row));
        // The ENTRY LINE projection uses it too (D6B-172).
        out.push_str(&keys_fn());
        out.push_str(
            &self
                .emit_structs(|f| !self.ctor_record(f) && self.effect_failure(f) && !self.built(f)),
        );
        out.push_str(ATTEMPT_FAILURE);
        out
    }
    // PDB-13: `__beaml_encode_<t>/1`, a typed value as its wire map (the inverse of the decode): a constructor
    // struct gives its String fields, a literal enum its ENUM LITERAL, the keep-value variant its String.
    fn emit_encode(&self, ty: &str) -> String {
        let fun = |t: &str| format!("__beaml_encode_{}", t.to_ascii_lowercase());
        let mut out = String::new();
        let mut todo = vec![ty.to_string()];
        while let Some(ty) = todo.pop() {
            match self.program.types.get(&ty) {
                Some(Definition::Record(fields)) => {
                    let key = |f: &str| {
                        if self.ctor_record(&ty) {
                            format!(":{f}")
                        } else {
                            binary(f)
                        }
                    };
                    let pairs: Vec<String> = fields
                        .iter()
                        .map(|(f, t)| {
                            let get = format!("Map.get(v, {})", key(f));
                            if self.ctor_record(t) || self.program.literals.contains_key(t) {
                                todo.push(t.clone());
                                format!("{} => {}({get})", binary(f), fun(t))
                            } else {
                                format!("{} => {get}", binary(f))
                            }
                        })
                        .collect();
                    out.push_str(&format!(
                        "  def {}(v), do: %{{{}}}\n",
                        fun(&ty),
                        pairs.join(", ")
                    ));
                }
                Some(Definition::Enum(_)) => {
                    for (variant, literal) in &self.program.literals[&ty] {
                        out.push_str(&format!(
                            "  def {}({{{}, {}, []}}), do: {}\n",
                            fun(&ty),
                            binary(&ty),
                            binary(variant),
                            binary(literal)
                        ));
                    }
                    out.push_str(&format!(
                        "  def {}({{{}, {}, [v]}}), do: v\n",
                        fun(&ty),
                        binary(&ty),
                        binary(self.keep_variant(&ty).expect("checked keep-value variant"))
                    ));
                }
                None => {}
            }
        }
        out
    }
    // Inside `Replay`: the live call of a db EFFECT (`put_`, `get_` or `list_` + its Elixir name) and its REPLAY RUN
    // step `replay_<elixir>`. Every host error, other shape, raise and exit is the reason transport (PDB-12).
    fn emit_db_replay(&self, effect: &Effect) -> String {
        let name = &effect.name;
        let elixir = name.replace('.', "_");
        let row = self.row_type(effect);
        let low = row.to_ascii_lowercase();
        let op = binary(name);
        let ty = binary(&row);
        let fail = format!("@parent.__beaml_fail_{elixir}");
        let type_key = self.emit_type_key(&effect.output);
        let failed = |request: &str, reason: &str| {
            format!("{fail}(db_failed({op}, {request}, {type_key}, {reason}))")
        };
        let keeps = !self.literal_fields(&row).is_empty();
        let fields = |v: &str| {
            if keeps {
                format!("@parent.__beaml_unknown_fields_{low}({v})")
            } else {
                "[]".to_string()
            }
        };
        let write = |value: &str, fields: &str, request: &str| {
            format!(
                "ProbeSupport.Capture.write(\"responses\", Map.put(db_core({op}, {value}, {fields}, {type_key}), :request, {request}))"
            )
        };
        let transport = failed("a0", "\"transport\"");
        let call = match effect.kind.as_str() {
            "db.put" => format!(
                "    def put_{elixir}(a0) do\n      value = @parent.__beaml_encode_{low}(a0)\n      core = db_core({op}, value, {}, {type_key})\n\n      case db_call(fn -> BeamlDb.put(\"records\", {{{ty}, {}}}, IO.iodata_to_binary(:json.encode(core))) end) do\n        {{:ok, id}} when is_integer(id) ->\n          ProbeSupport.Capture.write(\"responses\", Map.put(core, :request, value))\n          {{:ok, a0}}\n\n        _ ->\n          {}\n      end\n    end\n",
                fields("a0"),
                self.newest_version(&row),
                failed("value", "\"transport\""),
            ),
            "db.get" => format!(
                "    def get_{elixir}(a0) do\n      case db_call(fn -> BeamlDb.get(\"records\", {ty}, a0) end) do\n        {{:ok, nil}} ->\n          {}\n\n        {{:ok, %{{\"value\" => json}}}} ->\n          case row_{low}(json) do\n            {{:ok, v}} ->\n              {}\n              {{:ok, v}}\n\n            {{:error, reason}} ->\n              {}\n          end\n\n        _ ->\n          {transport}\n      end\n    end\n",
                failed("a0", "\"not_found\""),
                write(
                    &format!("@parent.__beaml_encode_{low}(v)"),
                    &fields("v"),
                    "a0"
                ),
                failed("a0", "reason"),
            ),
            _ => {
                let items = binary(&self.record(&effect.output).expect("checked output")[0].0);
                let listed = if keeps {
                    format!(
                        "items |> Enum.with_index() |> Enum.flat_map(fn {{v, i}} -> Enum.map({}, &({items} <> \".#{{i}}.\" <> &1)) end)",
                        fields("v")
                    )
                } else {
                    "[]".to_string()
                };
                format!(
                    "    def list_{elixir}(a0) do\n      case db_call(fn -> BeamlDb.list(\"records\", {ty}, a0) end) do\n        {{:ok, rows}} when is_list(rows) ->\n          case rows_{low}(rows) do\n            {{:ok, items}} ->\n              fields = {listed}\n              value = %{{{items} => Enum.map(items, fn v -> @parent.__beaml_encode_{low}(v) end)}}\n              {}\n              {{:ok, %{{{items} => items}}}}\n\n            {{:error, reason}} ->\n              {}\n          end\n\n        _ ->\n          {transport}\n      end\n    end\n",
                    write("value", "fields", "a0"),
                    failed("a0", "reason"),
                )
            }
        };
        // PDB-19: the REPLAY RUN decodes the recorded `value`; a rejected record replays its reason.
        let decode = decode_name(&row);
        let replay = if effect.kind == "db.list" {
            let items = binary(&self.record(&effect.output).expect("checked output")[0].0);
            format!(
                "    defp replay_{elixir}(_outcome, _reason, bytes) do\n      decoded =\n        case :json.decode(bytes) do\n          %{{{items} => items}} when is_list(items) -> Enum.map(items, fn item -> @parent.{decode}(IO.iodata_to_binary(:json.encode(item))) end)\n          _ -> [:error]\n        end\n\n      if Enum.all?(decoded, &match?({{:ok, _, _}}, &1)),\n        do: {{:ok, %{{{items} => Enum.map(decoded, fn {{:ok, v, _}} -> v end)}}}},\n        else: {fail}(\"decode\")\n    end\n"
            )
        } else {
            format!(
                "    defp replay_{elixir}(_outcome, _reason, bytes) do\n      case @parent.{decode}(bytes) do\n        {{:ok, value, _}} -> {{:ok, value}}\n        _ -> {fail}(\"decode\")\n      end\n    end\n"
            )
        };
        format!(
            "{call}\n    defp replay_{elixir}(\"rejected\", reason, _bytes) when is_binary(reason), do: {fail}(reason)\n\n{replay}"
        )
    }
    // Inside `Replay`, once per source with a db EFFECT: the ROW CORE (DL-143 core, PDB-14), the rejected db call
    // record (QDB-6b), the transport guard and, per ROW TYPE, the row decode (PDB-15: TYPE name, digest, TYPE
    // VERSION, MIGRATE CHAIN, DL-101 tail) and the list decode (QDB-4 A: the first bad row fails the list).
    fn emit_db_rows(&self) -> String {
        let rows: BTreeSet<String> = self
            .program
            .effects
            .iter()
            .filter(|e| e.kind != "http.post")
            .map(|e| self.row_type(e))
            .collect();
        if rows.is_empty() {
            return String::new();
        }
        let mut out = String::from(DB_HELPERS);
        for row in rows {
            let low = row.to_ascii_lowercase();
            let versions = self.type_versions(&row);
            let start = self.chain_start(&row) as usize;
            let known: Vec<String> = versions
                .iter()
                .enumerate()
                .map(|(i, fields)| format!("{{{}, {}}}", i + start, binary(&fingerprint(fields))))
                .collect();
            let (type_bind, type_arg) = if self.versioned(&row) {
                (" = type", ", type")
            } else {
                ("", "")
            };
            let reject = if self.ctor_fields(&row).is_empty() {
                ""
            } else {
                "\n          {:error, reason} -> {:error, reason}"
            };
            out.push_str(&format!(
                "\n    defp row_{low}(json) do\n      core =\n        try do\n          if is_binary(json), do: :json.decode(json)\n        rescue\n          _ -> nil\n        end\n\n      with %{{\"type\" => %{{\"name\" => {name}, \"version\" => v, \"fingerprint\" => f}}{type_bind}}} <- core,\n           {{:ok, bytes, _keys}} <- body(core),\n           true <- Enum.member?([{known}], {{v, f}}) do\n        case @parent.{decode}(bytes{type_arg}) do\n          {{:ok, value, _}} -> {{:ok, value}}{reject}\n          :error -> {{:error, \"decode\"}}\n        end\n      else\n        _ -> {{:error, \"decode\"}}\n      end\n    end\n\n    defp rows_{low}(rows) do\n      Enum.reduce_while(rows, {{:ok, []}}, fn row, {{:ok, items}} ->\n        case row_{low}(if is_map(row), do: Map.get(row, \"value\")) do\n          {{:ok, v}} -> {{:cont, {{:ok, items ++ [v]}}}}\n          error -> {{:halt, error}}\n        end\n      end)\n    end\n",
                name = binary(&row),
                known = known.join(", "),
                decode = decode_name(&row),
            ));
        }
        out
    }
    // Q6E-3 A: the operation argument of `Replay.record` and `Replay.run`, only with two or more EFFECTS.
    fn replay_op(&self, name: &str) -> String {
        if self.program.effects.len() > 1 {
            format!("{}, ", binary(name))
        } else {
            String::new()
        }
    }
    // One `Replay` module after the EFFECT loop (D6B-199). With one EFFECT the slice 6 shape stays byte-equal.
    // ponytail: two shapes (with and without the operation argument); join them when the four pins move anyway.
    fn emit_replay(&self, service: &str) -> String {
        let (records, mut runs): (Vec<String>, Vec<String>) = self
            .program
            .effects
            .iter()
            .map(|e| self.emit_replay_clauses(e, service))
            .unzip();
        if runs.len() > 1 {
            runs.push("    def run(_operation, _a0, _trace_id, _records), do: {:error, :operation_mismatch}\n".into());
        }
        format!(
            "  defmodule Replay do\n    import Kernel\n    @parent __MODULE__ |> Module.split() |> Enum.drop(-1) |> Module.concat()\n{}\n{}{}\n{}{}{REPLAY_HELPERS}  end\n",
            self.emit_retired(),
            records.join("\n"),
            self.emit_db_rows(),
            runs.join("\n"),
            self.emit_replay_entry(),
        )
    }
}

impl Checker<'_> {
    // The decode helpers of a record TYPE `ty` (steps 7 and 8): the defs (literal maps, `unknown_fields`, `__beaml_from_T`),
    // the literal map lines, the decode tail, the keep-value triples, the constructor fields and the inner key lists.
    // Slice 6d: the outbound decode of the EFFECT output TYPE and the ENTRY LINE decode of the input TYPE share it.
    #[allow(clippy::type_complexity)]
    fn decode_parts(
        &self,
        op: &str,
        ty: &str,
    ) -> (
        String,
        String,
        String,
        Vec<(String, String, String)>,
        Vec<(String, String)>,
        Vec<String>,
    ) {
        let mut defs = String::new();
        // Slice 6b step 7 (D6B-35, D6B-37): a literal enum field maps its wire String by `__beaml_literal_E`:
        // a literal gives its variant, another String the keep-value variant, any other value `:error` (the
        // typed reject `decode`). Only with literal fields; other outputs keep their bytes.
        let literal_fields = self.literal_fields(ty);
        let unknown_fields = format!("__beaml_unknown_fields_{}", ty.to_ascii_lowercase());
        // Step 8 (DL-101, S5): (field, enum, keep-value variant) of literal and constructor enum fields.
        let ctor_fields = self.ctor_fields(ty);
        let mut keeps: Vec<(String, String, String)> = literal_fields
            .iter()
            .map(|(f, e)| {
                let keep = self.keep_variant(e).expect("checked keep-value variant");
                (f.clone(), e.clone(), keep.to_string())
            })
            .collect();
        for (field, ty) in &ctor_fields {
            for variant in self
                .ctor_keeps(op, ty, field, ty)
                .expect("checked keep-value variants")
            {
                keeps.push((field.clone(), ty.clone(), variant));
            }
        }
        keeps.sort();
        let mut literal_map = String::new();
        if !literal_fields.is_empty() {
            let enums: BTreeSet<&String> = literal_fields.iter().map(|(_, e)| e).collect();
            for enum_name in enums {
                for (variant, literal) in &self.program.literals[enum_name] {
                    defs.push_str(&format!(
                        "  defp __beaml_literal_{enum_name}({}), do: {{{}, {}, []}}\n",
                        binary(literal),
                        binary(enum_name),
                        binary(variant)
                    ));
                }
                defs.push_str(&format!(
                    "  defp __beaml_literal_{enum_name}(v) when is_binary(v), do: {{{}, {}, [v]}}\n  defp __beaml_literal_{enum_name}(_), do: :error\n",
                    binary(enum_name),
                    binary(self.keep_variant(enum_name).expect("checked keep-value variant"))
                ));
            }
        }
        if !keeps.is_empty() {
            // D6B-37: the field names whose value went to the keep-value variant, sorted, no values.
            let listed: Vec<String> = keeps
                .iter()
                .map(|(f, e, v)| format!("{{{}, {}, {}}}", binary(f), binary(e), binary(v)))
                .collect();
            defs.push_str(&format!(
                "  def {unknown_fields}(value) do\n    Enum.flat_map([{}], fn {{field, owner, keep}} ->\n      case Map.get(value, field) do\n        {{^owner, ^keep, _}} -> [field]\n        _ -> []\n      end\n    end)\n  end\n",
                listed.join(", ")
            ));
        }
        if !literal_fields.is_empty() {
            for (field, enum_name) in &literal_fields {
                literal_map.push_str(&format!(
                    "    shape =\n      if is_map(shape) and Map.has_key?(shape, {field}),\n        do: Map.update!(shape, {field}, &__beaml_literal_{enum_name}/1),\n        else: shape\n\n",
                    field = binary(field)
                ));
            }
        }
        // Step 8 (DL-084, DL-085, DL-099, DL-101, D6B-48): `__beaml_from_T` tries the signatures of `fn T` top to
        // bottom. A signature matches when all its keys hold Strings (one parameter: the field value is the
        // String). A constructor failure is `:constructor` (the typed reject `constructor`), no match `:error`.
        let ctor_types: BTreeSet<&String> = ctor_fields.iter().map(|(_, t)| t).collect();
        let string = binary("String");
        for ty in ctor_types {
            let mut branches = String::new();
            for (key, names) in self.ctor_signatures(ty).expect("checked signatures") {
                let (test, args) = if let [_] = names.as_slice() {
                    (format!("__beaml_valid__(v, {string})"), "v".to_string())
                } else {
                    let gets: Vec<String> = names
                        .iter()
                        .map(|n| format!("Map.get(v, {})", binary(n)))
                        .collect();
                    let tests: Vec<String> = gets
                        .iter()
                        .map(|g| format!(" and __beaml_valid__({g}, {string})"))
                        .collect();
                    (format!("is_map(v){}", tests.concat()), gets.join(", "))
                };
                let call = format!("{}({args})", elixir_name(&key));
                let body = if self.failures[&key].is_empty() {
                    call
                } else {
                    format!(
                        "case {call} do\n          {{:ok, value}} -> value\n          {{:error, _}} -> :constructor\n        end"
                    )
                };
                branches.push_str(&format!("      {test} ->\n        {body}\n\n"));
            }
            defs.push_str(&format!(
                "  defp __beaml_from_{ty}(v) do\n    cond do\n{branches}      true ->\n        :error\n    end\n  end\n"
            ));
        }
        for (field, ty) in &ctor_fields {
            literal_map.push_str(&format!(
                "    shape =\n      if is_map(shape) and Map.has_key?(shape, {field}),\n        do: Map.update!(shape, {field}, &__beaml_from_{ty}/1),\n        else: shape\n\n",
                field = binary(field)
            ));
        }
        // D6B-49, S8: the declared keys inside a constructor field value: every parameter name of every signature.
        let inner: Vec<String> = ctor_fields
            .iter()
            .map(|(field, ty)| {
                let mut names: Vec<String> = Vec::new();
                for (_, list) in self.ctor_signatures(ty).expect("checked signatures") {
                    for n in list {
                        if !names.contains(&n) {
                            names.push(n);
                        }
                    }
                }
                let names: Vec<String> = names.iter().map(|n| binary(n)).collect();
                format!("{{{}, [{}]}}", binary(field), names.join(", "))
            })
            .collect();
        let tail = if ctor_fields.is_empty() {
            format!(
                "    if __beaml_valid__(shape, {output}),\n      do: {{:ok, shape, Enum.sort(Map.keys(Map.drop(value, declared)))}},\n      else: :error\n",
                output = binary(ty)
            )
        } else {
            // D6B-49, S8: a stray key inside a constructor field value is `FIELD.KEY`.
            format!(
                "    cond do\n      is_map(shape) and Enum.member?(Map.values(shape), :constructor) ->\n        {{:error, {constructor}}}\n\n      __beaml_valid__(shape, {output}) ->\n        nested =\n          Enum.flat_map([{inner}], fn {{field, names}} ->\n            case Map.get(value, field) do\n              inner when is_map(inner) -> Enum.map(Map.keys(Map.drop(inner, names)), &(field <> {dot} <> &1))\n              _ -> []\n            end\n          end)\n\n        {{:ok, shape, Enum.sort(Enum.concat(Map.keys(Map.drop(value, declared)), nested))}}\n\n      true ->\n        :error\n    end\n",
                constructor = binary("constructor"),
                output = binary(ty),
                inner = inner.join(", "),
                dot = binary("."),
            )
        };
        (defs, literal_map, tail, keeps, ctor_fields, inner)
    }
    // The decode of a TYPE with a MIGRATE CHAIN (DL-043, DL-054): `{decode}(bytes, type_version)`.
    // M4 step 1 (DL-152, PM4-06): with enum or constructor fields (`literal_map` not empty) the per-version check takes
    // those fields raw, the MIGRATE CHANGES run on the raw values, then the DL-101 tail of `decode_parts` runs on the
    // shape. Its key list is the per-version `unread` list plus the nested keys. Other TYPES keep their bytes.
    fn versioned_decode(
        &self,
        ty: &str,
        declared: &[String],
        literal_map: &str,
        tail: &str,
    ) -> String {
        let raw = !literal_map.is_empty();
        let decode = decode_name(ty);
        let migrations = self.migrations(ty);
        let versions = self.type_versions(ty);
        let start = self.chain_start(ty) as usize;
        let newest = self.newest_version(ty);
        let list = |last: usize| {
            (start..=last)
                .map(|v| v.to_string())
                .collect::<Vec<_>>()
                .join(", ")
        };
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
                    .map(|(f, t)| {
                        let raw_field = raw
                            && (self.program.literals.contains_key(t)
                                || self.constructors.contains(t));
                        let t = if raw_field {
                            ":raw".to_string()
                        } else {
                            binary(t)
                        };
                        format!("{{{}, {t}}}", binary(f))
                    })
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
                    // ponytail: fate lines emit nothing in a1; a hit fate line stops the build (DL-157). fates-a2.
                    _ => String::new(),
                });
            }
        }
        // `or` is not in the Kernel import of the module, so the raw fields leave the checked list.
        let checked = if raw {
            "Enum.reject(fields, fn {_, type} -> type == :raw end)"
        } else {
            "fields"
        };
        // The tail reads the keys from `value`; after the steps they are the per-version `unread` list.
        let end = if raw {
            format!(
                "{literal_map}{}",
                tail.replacen("Map.keys(Map.drop(value, declared))", "unread", 1)
            )
        } else {
            format!(
                "    if __beaml_valid__(shape, {}) do\n      {{:ok, shape, unread}}\n    else\n      :error\n    end\n",
                binary(ty)
            )
        };
        format!(
            "  def {decode}(a0), do: {decode}(a0, nil)\n  def {decode}(a0, type_version) do\n    declared = [{declared}]\n\n    version =\n      case type_version do\n        nil ->\n          {newest}\n\n        %{{{name_key} => {name}, {version_key} => v, {fingerprint_key} => f}} ->\n          if Enum.member?([{known}], {{v, f}}), do: v, else: 0\n\n        _ ->\n          0\n      end\n\n    body =\n      try do\n        :json.decode(a0)\n      rescue\n        _ -> nil\n      end\n\n    fields =\n      case version do\n{by_version}        _ -> :none\n      end\n\n    {{value, unread}} =\n      case {{fields, body}} do\n        {{{{:ok, fields}}, %{{}}}} ->\n          names = Enum.map(fields, fn {{field, _}} -> field end)\n\n          if Enum.all?({checked}, fn {{field, type}} -> __beaml_valid__(Map.get(body, field), type) end),\n            do: {{Map.take(body, names), Enum.sort(Map.keys(Map.drop(body, names)))}},\n            else: {{nil, []}}\n\n        _ ->\n          {{nil, []}}\n      end\n\n{changes}    shape = if is_map(value), do: Map.take(value, declared), else: nil\n\n{end}  end\n",
            declared = declared.join(", "),
            name_key = binary("name"),
            name = binary(ty),
            version_key = binary("version"),
            fingerprint_key = binary("fingerprint"),
            known = known.join(", "),
            by_version = by_version,
        )
    }
    // The decode of a TYPE without a MIGRATE CHAIN (slice 1 form, steps 7 and 8).
    fn plain_decode(
        &self,
        ty: &str,
        marks: &[(String, String)],
        declared: &[String],
        literal_map: &str,
        tail: &str,
    ) -> String {
        let decode = decode_name(ty);
        // DL-115 (Q6B-14 A): a REPLAY RUN puts `:redacted` into each marked field before the TYPE check.
        let (head, shape) = if marks.is_empty() {
            (format!("  def {decode}(a0) do\n"), "value")
        } else {
            (
                format!(
                    "  def {decode}(a0), do: {decode}(a0, [])\n  def {decode}(a0, marked) do\n"
                ),
                "Map.merge(value, Map.new(List.wrap(marked), &{&1, :redacted}))",
            )
        };
        format!(
            "{head}    declared = [{}]\n\n    value =\n      try do\n        :json.decode(a0)\n      rescue\n        _ -> nil\n      end\n\n    shape = if is_map(value), do: Map.take({shape}, declared), else: nil\n\n{literal_map}{tail}  end\n",
            declared.join(", "),
        )
    }
    // Slice 6b step 6a (DL-105, D6B-54, D6B-56, D6B-57): `__beaml_project_<elixir>`, the record projection of a body of TYPE `ty`.
    fn emit_project(
        &self,
        elixir: &str,
        ty: &str,
        marks: &[(String, String)],
        declared: &[String],
        inner: &[String],
    ) -> String {
        let dot = binary(".");
        let (marked, null) = if marks.is_empty() {
            (String::new(), "")
        } else {
            (format!(", __beaml_marked_{elixir}(body)"), ", []")
        };
        let inner_keys = format!("__beaml_keys__(Map.drop(v, names), field <> {dot})");
        let top_keys = format!("__beaml_keys__(Map.drop(body, declared), {})", binary(""));
        let kept: Vec<String> = self
            .record(ty)
            .expect("checked output")
            .iter()
            .filter(|(f, _)| !marks.iter().any(|(m, _)| m == f))
            .map(|(f, _)| binary(f))
            .collect();
        format!(
            "  def __beaml_project_{elixir}(a0) do\n    body =\n      try do\n        :json.decode(a0)\n      rescue\n        _ -> nil\n      end\n\n    if is_map(body) do\n      declared = [{declared}]\n\n      nested =\n        Enum.flat_map([{inner}], fn {{field, names}} ->\n          case Map.get(body, field) do\n            v when is_map(v) -> [{{field, Map.take(v, names), {inner_keys}}}]\n            _ -> []\n          end\n        end)\n\n      value = Enum.reduce(nested, Map.take(body, {kept}), fn {{field, v, _}}, acc -> Map.put(acc, field, v) end)\n      {{value, Enum.sort(Enum.concat({top_keys}, Enum.flat_map(nested, fn {{_, _, keys}} -> keys end))){marked}}}\n    else\n      {{:null, []{null}}}\n    end\n  end\n",
            declared = declared.join(", "),
            kept = if marks.is_empty() {
                "declared".to_string()
            } else {
                format!("[{}]", kept.join(", "))
            },
            inner = inner.join(", "),
            inner_keys = inner_keys,
            top_keys = top_keys,
        )
    }
}

impl Checker<'_> {
    // Slice 6d (DL-130, DL-131, DL-133, D6B-133, D6B-143): `def ui_<event>(params)`. The strict term check, the DL-101
    // decode of the input TYPE on the JSON of the params, the ENTRY RECORD (only for the flow of an EFFECT, D6B-136) and
    // the call of the target fn run inside the root span. A reject raises inside the span and returns
    // `{:error, %Rejected{reason: r}}` outside it; a domain failure of the fn passes unchanged.
    fn emit_entry(&self, entry: &Entry, service: &str) -> String {
        let op = &entry.name;
        let elixir = op.replace('.', "_");
        let input = &entry.input;
        let declared: Vec<String> = self
            .record(input)
            .expect("checked input")
            .iter()
            .map(|(f, _)| binary(f))
            .collect();
        let (defs, literal_map, tail, keeps, ctors, inner) = self.decode_parts(op, input);
        let mut out = format!(
            "  # beaml-declaration-v1 {op} {} {}\n{defs}",
            entry.source_range.start, entry.source_range.end
        );
        out.push_str(&self.plain_decode(input, &[], &declared, &literal_map, &tail));
        let capture = self.reaches(&entry.target);
        if capture {
            out.push_str(&self.emit_project(&elixir, input, &[], &declared, &inner));
        }
        let target = &entry.target;
        let call = if self.failures[target].is_empty() {
            format!("{{:ok, __MODULE__.{target}(value)}}")
        } else {
            format!("__MODULE__.{target}(value)")
        };
        let mark = if keeps.is_empty() {
            String::new()
        } else {
            format!(
                "    fields = __beaml_unknown_fields_{}(value)\n    if fields == [], do: :ok, else: :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :unknown_fields, fields)\n",
                input.to_ascii_lowercase()
            )
        };
        out.push_str(&format!(
            "  def {elixir}(a0) do\n    __beaml_attempt__(fn ->\n      ProbeSupport.span({span}, :server, nil, nil, fn ->\n        bytes = if __beaml_term__(a0), do: IO.iodata_to_binary(:json.encode(a0)), else: nil\n        decoded = if bytes == nil, do: :error, else: {decode}(bytes)\n{record}        __beaml_enter_{elixir}(decoded)\n      end)\n    end)\n  end\n  defp __beaml_enter_{elixir}({{:ok, value, keys}}) do\n    if keys == [], do: :ok, else: :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :unknown_keys, keys)\n{mark}    {call}\n  end\n{ctor}  defp __beaml_enter_{elixir}(:error), do: __beaml_reject__({decode_reason})\n  def __beaml_rejected__(a0), do: %__MODULE__.Rejected{{reason: a0}}\n  defp __beaml_reject__(a0) do\n    :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :reason, a0)\n    raise(__MODULE__.BeamlFailure, error: __beaml_rejected__(a0))\n  end\n  # D6B-143: maps with String keys, lists, Strings, numbers, true and false; any other term is the reject decode.\n  defp __beaml_term__(v) do\n    cond do\n      is_map(v) -> Enum.all?(Map.to_list(v), fn {{k, x}} -> is_binary(k) and String.valid?(k) and __beaml_term__(x) end)\n      :erlang.is_list(v) -> if List.improper?(v), do: false, else: Enum.all?(v, &__beaml_term__/1)\n      is_binary(v) -> String.valid?(v)\n      :erlang.is_number(v) -> true\n      true -> Enum.member?([true, false], v)\n    end\n  end\n",
            span = binary(&format!("{service}.{op}")),
            decode = decode_name(input),
            record = if capture {
                format!("        __MODULE__.Replay.entry_record({}, bytes, decoded)\n", binary(op))
            } else {
                String::new()
            },
            decode_reason = binary("decode"),
            // Only a constructor field gives the reject `constructor` (step 8).
            ctor = if ctors.is_empty() {
                String::new()
            } else {
                format!("  defp __beaml_enter_{elixir}({{:error, reason}}), do: __beaml_reject__(reason)\n")
            },
        ));
        if self.program.effects.is_empty() {
            // A pure source has no EFFECT that defines these two (D6B-136).
            out.push_str(ATTEMPT_FAILURE);
        }
        out
    }
    // Inside `Replay`, per ENTRY LINE that targets the flow of an EFFECT: the ENTRY RECORD writer (D6B-135, D6B-145,
    // DL-138) and an `entry/2` clause, the REPLAY RUN from an ENTRY RECORD (D6B-137). D6B-200: both dispatch on the
    // operation. Empty without such an ENTRY LINE, so other sources keep their bytes.
    fn emit_replay_entry(&self) -> String {
        let (records, mut entries): (Vec<String>, Vec<String>) = self
            .program
            .entries
            .iter()
            .filter(|e| self.reaches(&e.target))
            .map(|e| self.emit_replay_entry_clauses(e))
            .unzip();
        if entries.is_empty() {
            return String::new();
        }
        entries
            .push("    def entry(_record, _records), do: {:error, :operation_mismatch}\n".into());
        format!("\n{}\n{}", records.join("\n"), entries.join("\n"))
    }
    fn emit_replay_entry_clauses(&self, entry: &Entry) -> (String, String) {
        let op = &entry.name;
        let elixir = op.replace('.', "_");
        let input = &entry.input;
        let decode = decode_name(input);
        let (_, _, _, keeps, ctors, _) = self.decode_parts(op, input);
        let (ctor_capture, ctor_replay) = if ctors.is_empty() {
            ("", "")
        } else {
            (
                "\n          {:error, reason} -> {[], \"rejected\", reason}",
                "\n          {:error, reason} -> {:error, @parent.__beaml_rejected__(reason)}",
            )
        };
        let fields = if keeps.is_empty() {
            "{:ok, _, _} -> {[], \"accepted\", :null}".to_string()
        } else {
            format!(
                "{{:ok, value, _}} -> {{@parent.__beaml_unknown_fields_{}(value), \"accepted\", :null}}",
                input.to_ascii_lowercase()
            )
        };
        // DL-141, R6D-05, R6D-13: the field list in source order, as the fixtures hold it; the fingerprint sorts.
        let type_key = self.emit_type_key(input);
        let record = format!(
            "    def entry_record({operation}, bytes, decoded) do\n      ctx = OpenTelemetry.Tracer.current_span_ctx()\n      {{value, unknown_keys}} = if bytes == nil, do: {{:null, []}}, else: @parent.__beaml_project_{elixir}(bytes)\n\n      {{fields, outcome, reason}} =\n        case decoded do\n          {fields}\n          :error -> {{[], \"rejected\", \"decode\"}}{ctor_capture}\n        end\n\n      ProbeSupport.Capture.write(\"entries\", %{{\n        version: 3,\n        trace_id: OpenTelemetry.Span.hex_trace_id(ctx),\n        span_id: OpenTelemetry.Span.hex_span_id(ctx),\n        artifact_id: ProbeSupport.beam_hash(@parent),\n        operation: {operation},\n        attempt: 1,\n        value: value,\n        redacted: [],\n        unknown_keys: unknown_keys,\n        unknown_fields: fields,\n        value_sha256: digest(value, unknown_keys, []),\n        type: {type_key},\n        outcome: outcome,\n        reason: reason\n      }})\n    end\n",
            operation = binary(op),
        );
        // Q6E-3 A: with two or more EFFECTS the run names the EFFECT of the flow (one EFFECT per flow, Q6E-4 A).
        let effect = self.reach[&entry.target].first().expect("reached effect");
        let entry_clause = format!(
            "    def entry(%{{\"operation\" => {operation}}} = record, records) do\n      with {{:ok, bytes, _keys}} <- body(record) do\n        case @parent.{decode}(bytes) do\n          {{:ok, value, _}} -> run({run_op}value, record[\"trace_id\"], records)\n          :error -> {{:error, @parent.__beaml_rejected__({decode_reason})}}{ctor_replay}\n        end\n      end\n    end\n",
            operation = binary(op),
            run_op = self.replay_op(effect),
            decode_reason = binary("decode"),
        );
        (record, entry_clause)
    }
}

impl Checker<'_> {
    // Slice 6d (DL-134, DL-136, DL-138, R6D-14, R6D-15): the stored ENTRY RECORDS. Only accepted records of the ENTRY
    // LINE are checked: the DL-122 literals and the DL-102 constructors of the input TYPE over `value`. A record of an
    // operation with neither an ENTRY LINE nor a RETIRE LINE blocks as a removed EFFECT does (DL-040 text, every record
    // counts). Gives the DL-136 count line. Names, counts and lines only, never a value (DL-124).
    fn check_entries(
        &self,
        source: &str,
        text: &str,
        code: &str,
        snapshot: &mut Snapshot,
    ) -> Checked<String> {
        let (mut total, mut checked, mut rejected) = (0, 0, 0);
        let mut orphans: BTreeMap<String, (usize, usize)> = BTreeMap::new();
        // fates-a1: the literal and constructor checks of the rows and RESPONSE RECORDS (one help and fate rule).
        let mut checks = ValueChecks::default();
        let mut wrong: BTreeMap<(String, String), (usize, usize)> = BTreeMap::new();
        for (index, line) in text.lines().enumerate() {
            let number = index + 1;
            if line.trim().is_empty() {
                continue;
            }
            let at = format!("record source: {source}:{number} (line {number})");
            let record = parse_json(line)
                .ok_or_else(|| format!("error: stored ENTRY RECORD is not JSON\n  {at}"))?;
            // DL-143 (RV3-06): this build reads ENTRY RECORD version 3 only.
            let version = match record.get("version") {
                Some(Json::Number(n)) if n == "3" => None,
                Some(Json::Number(n)) => Some(n.as_str()),
                None => Some("none"),
                Some(_) => Some("malformed"),
            };
            if let Some(v) = version {
                return Err(format!(
                    "error: stored ENTRY RECORD has record version {v}; this build reads record version 3 only (DL-143)\n  {at}"
                ));
            }
            let op = record
                .get("operation")
                .and_then(Json::text)
                .ok_or_else(|| format!("error: stored ENTRY RECORD has no operation\n  {at}"))?
                .to_string();
            let accepted = match record.get("outcome").and_then(Json::text) {
                Some("accepted") => true,
                Some("rejected") => false,
                _ => {
                    return Err(format!(
                        "error: stored ENTRY RECORD has no capture outcome accepted or rejected (DL-138)\n  {at}"
                    ));
                }
            };
            total += 1;
            rejected += usize::from(!accepted);
            snapshot.operations.insert(op.clone());
            let Some(entry) = self.program.entries.iter().find(|e| e.name == op) else {
                if self.retire(&op).is_none() {
                    orphans.entry(op).or_insert((0, number)).0 += 1;
                }
                continue;
            };
            // P2b (DL-164, RED review objection 2): `Replay.entry/2` reads `body(record)` whatever the outcome.
            if !digest_holds(&record) {
                let key = (entry.input.clone(), format!("operation {op}"));
                wrong.entry(key).or_insert((0, number)).0 += 1;
            }
            if !accepted {
                continue;
            }
            checked += 1;
            let ty = &entry.input;
            let body = record.get("value");
            let kept = |field: &str| match record.get("unknown_fields") {
                Some(Json::List(names)) => names.iter().any(|n| n.text() == Some(field)),
                _ => false,
            };
            let place = format!("operation {op}");
            let version = self.newest_version(ty);
            for (field, enum_name) in self.literal_fields(ty) {
                let text = body.and_then(|b| b.get(&field)).and_then(Json::text);
                match self.literal_verdict(ty, &field, &enum_name, text, kept(&field)) {
                    Literal::Fine => {}
                    Literal::Lost => checks
                        .lost
                        .entry((ty.clone(), version, place.clone(), field, enum_name))
                        .or_default()
                        .push(number),
                    Literal::Moved(before, now) => {
                        let key = (ty.clone(), version, place.clone(), field, enum_name);
                        let key = (
                            key.0,
                            key.1,
                            key.2,
                            key.3,
                            key.4,
                            text.unwrap_or_default().into(),
                        );
                        checks
                            .moved
                            .entry(key)
                            .or_insert((before, now, Vec::new()))
                            .2
                            .push(number);
                    }
                    Literal::Fated((step, line, verb)) => {
                        let at = (place.clone(), step, line, verb);
                        checks.fated.entry(at).or_default().insert(number);
                    }
                }
            }
            for (field, ctor) in self.ctor_fields(ty) {
                let value = body.and_then(|b| b.get(&field));
                let key = (ty.clone(), place.clone(), field, ctor);
                match self.ctor_pick(&key.3, value) {
                    None => checks.faults.entry((key, None)).or_insert((0, number)).0 += 1,
                    Some((sig, inputs)) if !self.failures[&sig].is_empty() => {
                        checks.calls.push((key, number, sig, inputs))
                    }
                    Some(_) => {}
                }
            }
        }
        if let Some(e) = digest_errors(&wrong, source, "ENTRY RECORD") {
            return Err(e);
        }
        if !orphans.is_empty() {
            return Err(orphans
                .iter()
                .map(|(op, (count, line))| {
                    format!(
                        "error: stored ENTRY RECORD of operation {op} has no effect in the source\n  record source: {source}:{line} (line {line})\n  stored ENTRY RECORDS of operation {op}: {count}\n  help: if the effect is deleted on purpose, declare: retire {op} keep <n> days"
                    )
                })
                .collect::<Vec<_>>()
                .join("\n"));
        }
        let errors =
            self.value_errors(checks, source, code, "ENTRY RECORD", &mut snapshot.notes)?;
        if !errors.is_empty() {
            return Err(errors.join("\n"));
        }
        Ok(format!(
            "{total} entries, {checked} checked, {rejected} rejected at capture"
        ))
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

// D6B-56 amendment, D6B-172: the dotted key names of a projection, one per level.
fn keys_fn() -> String {
    let dot = binary(".");
    format!(
        "  def __beaml_keys__(v, prefix) when is_map(v), do: Enum.flat_map(Map.keys(v), fn k -> [prefix <> k | __beaml_keys__(Map.get(v, k), prefix <> k <> {dot})] end)\n  def __beaml_keys__(_, _), do: []\n"
    )
}

// `__beaml_attempt__` and `BeamlFailure`: a failure raises inside its span and returns `{:error, failure}` outside it.
const ATTEMPT_FAILURE: &str = "  def __beaml_attempt__(a0) do\n    try do\n      a0.()\n    rescue\n      failure in __MODULE__.BeamlFailure -> {:error, failure.error}\n    end\n  end\n  defmodule BeamlFailure do\n    import Kernel\n    defexception [:error]\n\n    @impl true\n    def message(_), do: \"BEAML failure\"\n  end\n";

// Inside `Replay` for a source with a db EFFECT (0005 P4): the ROW CORE and db call record (DL-143 core, PDB-14,
// QDB-6b: a failed call is a rejected record with value null) and the transport guard (PDB-12).
const DB_HELPERS: &str = r#"
    defp db_core(operation, value, unknown_fields, type) do
      ctx = OpenTelemetry.Tracer.current_span_ctx()

      %{
        version: 3,
        trace_id: OpenTelemetry.Span.hex_trace_id(ctx),
        span_id: OpenTelemetry.Span.hex_span_id(ctx),
        artifact_id: ProbeSupport.beam_hash(@parent),
        operation: operation,
        attempt: 1,
        type: type,
        value: value,
        value_sha256: digest(value, [], []),
        redacted: [],
        unknown_keys: [],
        unknown_fields: unknown_fields,
        outcome: "accepted",
        reason: :null
      }
    end

    defp db_failed(operation, request, type, reason) do
      core = db_core(operation, :null, [], type)
      ProbeSupport.Capture.write("responses", Map.merge(core, %{request: request, outcome: "rejected", reason: reason}))
      reason
    end

    defp db_call(call) do
      try do
        call.()
      catch
        _, _ -> :error
      end
    end
"#;

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

// RESPONSE RECORD checks of the REPLAY RUN (record version 2 since slice 6b step 6a, six reasons).
const REPLAY_HELPERS: &str = r#"
    defp select(records, trace_id) do
      case Enum.filter(records, &(&1["trace_id"] == trace_id)) do
        [record] -> {:ok, record}
        _ -> {:error, :missing_response}
      end
    end

    defp expect(value, value, _reason), do: :ok
    defp expect(_value, _expected, reason), do: {:error, reason}

    # Slice 6b step 6a (D6B-58, D6B-60): a version 2 record replays the re-encoded `value` when the digest of its
    # projection holds. A record without `value` (version 1) is `:body_digest_mismatch`.
    defp body(%{"value" => value, "redacted" => redacted, "unknown_keys" => keys, "value_sha256" => sha256})
         when is_list(keys) do
      if digest(value, keys, redacted) === sha256,
        do: {:ok, IO.iodata_to_binary(:json.encode(value)), keys},
        else: {:error, :body_digest_mismatch}
    end

    defp body(_record), do: {:error, :body_digest_mismatch}

    # D6B-58: lower-case hex SHA-256 of the compact JSON of the projection, keys sorted at every level, UTF-8.
    # ponytail: :json float text (for example 1.0e100) can differ from other encoders; the writer and the reader
    # share this function, so only a foreign digest of an exponent float would differ.
    defp digest(value, keys, redacted) do
      sorted = fn
        map, encode when is_map(map) -> :json.encode_key_value_list(Enum.sort(Map.to_list(map)), encode)
        other, encode -> :json.encode_value(other, encode)
      end

      text = :json.encode(%{"redacted" => redacted, "unknown_keys" => keys, "value" => value}, sorted)
      Base.encode16(:crypto.hash(:sha256, text), case: :lower)
    end
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

// D6B-58: the digest of a stored projection holds: the lower-case hex SHA-256 of the compact JSON of
// `{"redacted", "unknown_keys", "value"}`, keys sorted at every level, as `digest/3` in `Replay` writes it.
fn digest_holds(record: &Json) -> bool {
    let (Some(value), Some(keys), Some(redacted), Some(Json::Text(sha))) = (
        record.get("value"),
        record.get("unknown_keys"),
        record.get("redacted"),
        record.get("value_sha256"),
    ) else {
        return false;
    };
    let projection = Json::Object(vec![
        ("redacted".into(), redacted.clone()),
        ("unknown_keys".into(), keys.clone()),
        ("value".into(), value.clone()),
    ]);
    let mut text = String::new();
    canonical(&projection, &mut text);
    let hex: String = sha256(text.as_bytes())
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    &hex == sha
}
// P2b (DL-164): one block per (TYPE, place) of stored items whose digest does not hold, or None. Names, counts and
// lines only (DL-124).
fn digest_errors(
    wrong: &BTreeMap<(String, String), (usize, usize)>,
    source: &str,
    noun: &str,
) -> Option<String> {
    (!wrong.is_empty()).then(|| {
        wrong
            .iter()
            .map(|((ty, place), (count, line))| {
                let (plural, verb) = if *count == 1 { ("", "has") } else { ("S", "have") };
                format!(
                    "error: TYPE {ty}: {count} stored {noun}{plural} of {place} {verb} a wrong digest: value_sha256 does not match value, unknown_keys and redacted (DL-164)\n  record source: {source}:{line} (line {line})\n  help: the stored value changed without a new digest (a hand edit or corruption); restore or delete the {noun}, then build again"
                )
            })
            .collect::<Vec<_>>()
            .join("\n")
    })
}
// Compact JSON with sorted object keys; strings escaped as `:json.encode` writes them (Erlang: upper-case `\u` hex).
// ponytail: number text is kept as read; an exponent or float form from another encoder would not match.
fn canonical(json: &Json, out: &mut String) {
    match json {
        Json::Null => out.push_str("null"),
        Json::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Json::Number(n) => out.push_str(n),
        Json::Text(text) => {
            out.push('"');
            for c in text.chars() {
                match c {
                    '"' => out.push_str("\\\""),
                    '\\' => out.push_str("\\\\"),
                    '\n' => out.push_str("\\n"),
                    '\r' => out.push_str("\\r"),
                    '\t' => out.push_str("\\t"),
                    '\u{8}' => out.push_str("\\b"),
                    '\u{c}' => out.push_str("\\f"),
                    c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04X}", c as u32)),
                    c => out.push(c),
                }
            }
            out.push('"');
        }
        Json::List(items) => {
            out.push('[');
            for (i, item) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                canonical(item, out);
            }
            out.push(']');
        }
        Json::Object(pairs) => {
            let mut sorted: Vec<&(String, Json)> = pairs.iter().collect();
            sorted.sort_by(|a, b| a.0.cmp(&b.0));
            out.push('{');
            for (i, (key, value)) in sorted.into_iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                canonical(&Json::Text(key.clone()), out);
                out.push(':');
                canonical(value, out);
            }
            out.push('}');
        }
    }
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

// (TYPE, TYPE VERSION, place, field, enum, literal) of a moved ENUM LITERAL (DL-140, DL-161).
type MovedKey = (String, u32, String, String, String, String);

// The DL-102, DL-103 and DL-122 findings over stored values; keys hold the place (`operation <op>`, `table records`).
#[derive(Default)]
struct ValueChecks {
    // DL-102, DL-103: per (TYPE, operation, field, enum) of a literal enum field: (failed records, first
    // failed line, resolved records). The body is mapped by the current literals (one file, one environment).
    mapped: BTreeMap<FieldKey, (usize, usize, usize)>,
    // Step 8 (DL-102, S9): per (TYPE, operation, field, constructor, failure TYPE or None for no signature):
    // (failed records, first failed line).
    faults: BTreeMap<(FieldKey, Option<String>), (usize, usize)>,
    // DL-122, DL-124: per (TYPE, TYPE VERSION, operation, field, enum): the lines of records with a lost ENUM LITERAL.
    lost: BTreeMap<(String, u32, String, String, String), Vec<usize>>,
    // D6B-102: the constructor calls for the Elixir run: (field key, line, signature key, inputs).
    calls: Vec<(FieldKey, usize, String, Vec<String>)>,
    // 0005 P4c (DL-102, DL-124): per (TYPE, place, field) of a String field without a String value: (failed
    // records, first failed line, last counted line; a list record counts once, not per item).
    strings: BTreeMap<(String, String, String), (usize, usize, usize)>,
    // DL-140, DL-161: per (TYPE, TYPE VERSION, place, field, enum, literal) of a literal that moved to another variant
    // since the previous declaration: (variant before, variant now, record lines).
    moved: BTreeMap<MovedKey, (String, String, Vec<usize>)>,
    // fates-a1 (PF-13): per (place, step label, fate line, verb): the record lines that the fate line lifts.
    fated: BTreeMap<(String, String, String, &'static str), BTreeSet<usize>>,
    // PF-21: per (field key, failure TYPE) the parameter that the first failing clause tests by a pattern; None
    // when it tests none (DL-172 QB-2).
    params: BTreeMap<(FieldKey, String), Option<String>>,
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

fn record_lines(source: &str, lines: &[usize]) -> String {
    lines
        .iter()
        .map(|n| format!("  record source: {source}:{n} (line {n})"))
        .collect::<Vec<_>>()
        .join("\n")
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
    // Slice 6b step 13 (DL-121): `code` is the generated module. When the static pass is clean, one Elixir run calls
    // the constructors with a failure TYPE over the stored values (D6B-102 to D6B-105).
    fn check_stored(&self, source: &str, text: &str, code: &str) -> Checked<Snapshot> {
        let mut groups: BTreeMap<StoredVersion, (usize, usize)> = BTreeMap::new();
        let mut snapshot = Snapshot::default();
        // Operation -> (record count, first line) of records with no `effect` and no RETIRE LINE.
        let mut orphans: BTreeMap<String, (usize, usize)> = BTreeMap::new();
        let mut checks = ValueChecks::default();
        // D6B-72, D6B-163: per (TYPE, operation, dotted path, place): (records that hold a value there, first line).
        let mut held: BTreeMap<(String, String, String, &str), (usize, usize)> = BTreeMap::new();
        let mut wrong: BTreeMap<(String, String), (usize, usize)> = BTreeMap::new();
        // DL-143 (QV3-7 A, QV3-8 B): records, checked records, records rejected at capture.
        let (mut total, mut checked, mut rejected) = (0, 0, 0);
        for (index, line) in text.lines().enumerate() {
            let number = index + 1;
            if line.trim().is_empty() {
                continue;
            }
            let at = format!("record source: {source}:{number} (line {number})");
            let record = parse_json(line)
                .ok_or_else(|| format!("error: stored RESPONSE RECORD is not JSON\n  {at}"))?;
            // D6B-59, DL-143: this build reads RESPONSE RECORD version 3 only.
            let version = match record.get("version") {
                Some(Json::Number(n)) if n == "3" => None,
                Some(Json::Number(n)) => Some(n.as_str()),
                None => Some("none"),
                Some(_) => Some("malformed"),
            };
            if let Some(v) = version {
                return Err(format!(
                    "error: stored RESPONSE RECORD has record version {v}; this build reads record version 3 only (DL-143)\n  {at}"
                ));
            }
            let accepted = match record.get("outcome").and_then(Json::text) {
                Some("accepted") => true,
                Some("rejected") => false,
                _ => {
                    return Err(format!(
                        "error: stored RESPONSE RECORD has no capture outcome accepted or rejected (DL-138)\n  {at}"
                    ));
                }
            };
            total += 1;
            rejected += usize::from(!accepted);
            let stored = stored_version(&record).map_err(|e| format!("error: {e}\n  {at}"))?;
            snapshot.operations.insert(stored.operation.clone());
            if let Some(effect) = self.effect(&stored.operation) {
                // P2b (DL-164, RED review objection 2): every record that reaches `body(record)` at replay: each db
                // record, an http record with status 200 (a rejected one too).
                let replayed = effect.kind != "http.post"
                    || matches!(record.get("status"), Some(Json::Number(n)) if n == "200");
                if replayed && !digest_holds(&record) {
                    let key = (
                        effect.output.clone(),
                        format!("operation {}", stored.operation),
                    );
                    wrong.entry(key).or_insert((0, number)).0 += 1;
                }
                for (place, ty) in [("request", &effect.input), ("value", &effect.output)] {
                    for path in self.redacted_paths(ty) {
                        let mut at = record.get(place);
                        for key in &path {
                            at = at.and_then(|v| v.get(key));
                        }
                        if at.is_some() {
                            let key = (ty.clone(), stored.operation.clone(), path.join("."), place);
                            held.entry(key).or_insert((0, number)).0 += 1;
                        }
                    }
                }
                // QV3-8 B (DL-136): a record rejected at capture skips the value, path and W2 checks.
                if !accepted {
                    continue;
                }
                checked += 1;
                let oldest = snapshot
                    .oldest
                    .entry(effect.output.clone())
                    .or_insert(stored.version);
                *oldest = (*oldest).min(stored.version);
                // 0005 P4 (N25, N25b): a db.list record holds ROW TYPE items; each item is checked as the ROW TYPE.
                let list = (effect.kind == "db.list").then(|| self.row_type(effect));
                let ty = list.clone().unwrap_or_else(|| effect.output.clone());
                if stored.name == effect.output {
                    let place = format!("operation {}", stored.operation);
                    // A record without the key `unknown_fields` (written before step 7) kept nothing.
                    let kept = |field: &str| match record.get("unknown_fields") {
                        Some(Json::List(names)) => names.iter().any(|n| n.text() == Some(field)),
                        _ => false,
                    };
                    if list.is_none() {
                        // Slice 6b step 6a (DL-105): the DL-102 checks read the projection `value`.
                        let body = record.get("value");
                        self.value_checks(
                            &mut checks,
                            &ty,
                            &place,
                            stored.version,
                            number,
                            body,
                            &kept,
                        );
                    } else {
                        // PDB-18: a kept value of item i is named `<field>.<i>.<name>`.
                        let field = &self.record(&effect.output).expect("checked output")[0].0;
                        if let Some(Json::List(items)) =
                            record.get("value").and_then(|v| v.get(field))
                        {
                            for (i, item) in items.iter().enumerate() {
                                let kept = |f: &str| kept(&format!("{field}.{i}.{f}"));
                                let version = self.newest_version(&ty);
                                self.value_checks(
                                    &mut checks,
                                    &ty,
                                    &place,
                                    version,
                                    number,
                                    Some(item),
                                    &kept,
                                );
                            }
                        }
                    }
                }
                groups.entry(stored).or_insert((0, number)).0 += 1;
            } else if self.retire(&stored.operation).is_none() {
                orphans.entry(stored.operation).or_insert((0, number)).0 += 1;
            }
        }
        if let Some(e) = digest_errors(&wrong, source, "RESPONSE RECORD") {
            return Err(e);
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
            .filter_map(|(stored, (count, line))| {
                let output = &self.effect(&stored.operation)?.output;
                let place = format!("operation {}", stored.operation);
                self.no_path(
                    source,
                    stored,
                    *count,
                    *line,
                    output,
                    "RESPONSE RECORD",
                    &place,
                )
            })
            .collect();
        if errors.is_empty() {
            errors =
                self.value_errors(checks, source, code, "RESPONSE RECORD", &mut snapshot.notes)?;
        }
        // D6B-72, D6B-149, D6B-151, D6B-152: a stored value under a field that is now redacted blocks, also when
        // the path check fails. Names and counts only (DL-032).
        for ((ty, op, field, place), (count, line)) in &held {
            let (records, verb) = if *count == 1 {
                ("RECORD", "holds")
            } else {
                ("RECORDS", "hold")
            };
            errors.push(format!(
                "error: TYPE {ty}: {count} stored RESPONSE {records} of operation {op} {verb} a value of the redacted field {field} in {place}\n  record source: {source}:{line} (line {line})\n  help: declare the fate in a MIGRATE STEP: redact {field} (DL-111); slice 6b has no form for it yet (DL-125)"
            ));
        }
        if errors.is_empty() {
            if rejected > 0 {
                snapshot.notes.push(format!(
                    "{total} records, {checked} checked, {rejected} rejected at capture"
                ));
            }
            Ok(snapshot)
        } else {
            Err(errors.join("\n"))
        }
    }
    // DL-102, DL-103, DL-122 over one stored value of TYPE `ty`: the literal enum and constructor fields. `place` is
    // `operation <op>` for a RESPONSE RECORD or `table records` for a stored ROW (0005 P4b).
    #[allow(clippy::too_many_arguments)]
    fn value_checks(
        &self,
        checks: &mut ValueChecks,
        ty: &str,
        place: &str,
        version: u32,
        number: usize,
        body: Option<&Json>,
        kept: &dyn Fn(&str) -> bool,
    ) {
        // 0005 P4c: each String field of a ROW TYPE holds a String, by the fields of the stored TYPE VERSION (P4c
        // TEST O1; a version off the chain gets the path text). A redacted field is absent from the projection.
        // http records stay unchecked (O3, Migrate, default A, open).
        let row =
            (self.program.effects.iter()).any(|e| e.kind != "http.post" && self.row_type(e) == ty);
        let fields = (version.checked_sub(self.chain_start(ty)))
            .and_then(|i| self.type_versions(ty).get(i as usize).cloned());
        if row {
            for (field, t) in fields.unwrap_or_default() {
                if t == "String"
                    && !self.is_redacted(ty, &field)
                    && body
                        .and_then(|b| b.get(&field))
                        .and_then(Json::text)
                        .is_none()
                {
                    let key = (ty.to_string(), place.to_string(), field);
                    let entry = checks.strings.entry(key).or_insert((0, number, 0));
                    if entry.2 != number {
                        (entry.0, entry.2) = (entry.0 + 1, number);
                    }
                }
            }
        }
        for (field, enum_name) in self.literal_fields(ty) {
            // DL-166: a stored body of an older TYPE VERSION holds the field under its name before the renames.
            let at = self.stored_key(ty, version, &field);
            let value = body.and_then(|b| b.get(&at));
            let literal = value.and_then(Json::text).is_some_and(|text| {
                self.program.literals[&enum_name]
                    .iter()
                    .any(|(_, l)| l == text)
            });
            let resolved = literal && kept(&at);
            // DL-122: a String that is no current literal and was not kept was an ENUM LITERAL at capture. DL-140,
            // DL-161: a literal that moved to another variant since the previous declaration. A fate line lifts both.
            let text = value.and_then(Json::text);
            match self.literal_verdict(ty, &field, &enum_name, text, kept(&at)) {
                Literal::Fine => {}
                Literal::Lost => checks
                    .lost
                    .entry((
                        ty.to_string(),
                        version,
                        place.to_string(),
                        field.clone(),
                        enum_name.clone(),
                    ))
                    .or_default()
                    .push(number),
                Literal::Moved(before, now) => {
                    let key = (
                        ty.to_string(),
                        version,
                        place.to_string(),
                        field.clone(),
                        enum_name.clone(),
                        text.unwrap_or_default().to_string(),
                    );
                    checks
                        .moved
                        .entry(key)
                        .or_insert((before, now, Vec::new()))
                        .2
                        .push(number);
                }
                Literal::Fated((step, line, verb)) => {
                    checks
                        .fated
                        .entry((place.to_string(), step, line, verb))
                        .or_default()
                        .insert(number);
                }
            }
            let entry = checks
                .mapped
                .entry((ty.to_string(), place.to_string(), field, enum_name))
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
        for (field, ctor) in self.ctor_fields(ty) {
            let value = body.and_then(|b| b.get(&self.stored_key(ty, version, &field)));
            let key = (ty.to_string(), place.to_string(), field, ctor);
            match self.ctor_pick(&key.3, value) {
                None => checks.faults.entry((key, None)).or_insert((0, number)).0 += 1,
                // D6B-104: a constructor without a failure TYPE cannot reject; no call.
                Some((sig, inputs)) if !self.failures[&sig].is_empty() => {
                    checks.calls.push((key, number, sig, inputs))
                }
                Some(_) => {}
            }
        }
    }
    // The errors (and DL-103 notes) of the value checks; one Elixir run for the constructors with a failure TYPE.
    fn value_errors(
        &self,
        mut checks: ValueChecks,
        source: &str,
        code: &str,
        noun: &str,
        notes: &mut Vec<String>,
    ) -> Checked<Vec<String>> {
        let mut errors = Vec::new();
        let plural = |n: usize| if n == 1 { "" } else { "S" };
        for ((ty, op, field), (failed, line, _)) in &checks.strings {
            errors.push(format!(
                "error: TYPE {ty}: {failed} stored {noun}{} of {op} {} no String value for field {field}\n  record source: {source}:{line} (line {line})\n  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of {ty} (DL-102)",
                plural(*failed),
                if *failed == 1 { "has" } else { "have" }
            ));
        }
        for ((ty, op, field, enum_name), (failed, line, resolved)) in &checks.mapped {
            if *failed > 0 {
                errors.push(format!(
                    "error: TYPE {ty}: {failed} stored {noun}{} of {op} {} no variant of {enum_name} for field {field}\n  record source: {source}:{line} (line {line})\n  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of {ty} (DL-102)",
                    plural(*failed),
                    if *failed == 1 { "has" } else { "have" }
                ));
            } else if *resolved > 0 {
                notes.push(format!(
                    "note: TYPE {ty}: {resolved} stored {noun}{} of {op} kept a value of field {field} that a literal of {enum_name} maps now (DL-103)",
                    plural(*resolved)
                ));
            }
        }
        for ((ty, version, op, field, enum_name), lines) in &checks.lost {
            let one = lines.len() == 1;
            errors.push(format!(
                "error: TYPE {ty} v{version}: {} stored {noun}{} of {op} {} of field {field} that {} no ENUM LITERAL of {enum_name} now (DL-122)\n{}\n{}",
                lines.len(),
                plural(lines.len()),
                if one { "has a value" } else { "have values" },
                if one { "is" } else { "are" },
                record_lines(source, lines),
                self.help_literal(enum_name)
            ));
        }
        for ((ty, version, op, field, enum_name, literal), (before, now, lines)) in &checks.moved {
            let one = lines.len() == 1;
            let step = self
                .migrations(enum_name)
                .last()
                .map(|m| (m.from, m.to))
                .unwrap_or((1, 2));
            let l = json_string(literal);
            errors.push(format!(
                "error: TYPE {ty} v{version}: {} stored {noun}{} of {op} {} the ENUM LITERAL {l} of field {field}, which was {before} in enum {enum_name} v{} and is {now} now (DL-140)\n{}\n  help: declare the fate of {l} in migrate {enum_name} v{} -> v{} (DL-161): map {l} -> <Variant> or quarantine {l}",
                lines.len(),
                plural(lines.len()),
                if one { "has" } else { "have" },
                step.0,
                record_lines(source, lines),
                step.0,
                step.1
            ));
        }
        // D6B-105: Elixir starts only when the static pass gives no error.
        if errors.is_empty()
            && !checks.faults.keys().any(|(_, r)| r.is_none())
            && !checks.calls.is_empty()
        {
            let failures: Vec<&[String]> = checks
                .calls
                .iter()
                .map(|c| self.failures[&c.2].as_slice())
                .collect();
            let stdin = format!(
                "{{\"module\":{},\"name\":{},\"calls\":[{}]}}",
                json_string(code),
                json_string(&self.module),
                checks
                    .calls
                    .iter()
                    .map(|(key, _, sig, inputs)| format!(
                        "[{},{},[{}]]",
                        json_string(&elixir_name(sig)),
                        json_string(&key.3),
                        inputs
                            .iter()
                            .map(|i| json_string(i))
                            .collect::<Vec<_>>()
                            .join(",")
                    ))
                    .collect::<Vec<_>>()
                    .join(",")
            );
            for ((key, number, sig, inputs), verdict) in
                checks.calls.iter().zip(run_elixir(&stdin, &failures)?)
            {
                let Some(failure) = verdict else {
                    continue;
                };
                // DL-102, DL-155, PF-12, DL-172: a `quarantine p` line of the constructor TYPE lifts the failed rule
                // only when its clause tests p with a literal. The same clause gives the help (PB-04).
                let tested = self.tested_params(&key.3, sig, inputs);
                if let Some((step, line, verb)) = self.ctor_fate(&key.3, &tested) {
                    let at = (key.1.clone(), step, line, verb);
                    checks.fated.entry(at).or_default().insert(*number);
                    continue;
                }
                let param = tested.into_iter().next();
                checks
                    .params
                    .entry((key.clone(), failure.clone()))
                    .or_insert(param);
                checks
                    .faults
                    .entry((key.clone(), Some(failure)))
                    .or_insert((0, *number))
                    .0 += 1;
            }
        }
        for ((key, reason), (failed, line)) in &checks.faults {
            let (ty, op, field, ctor) = key;
            let one = *failed == 1;
            let what = match reason {
                Some(failure) => format!(
                    "{} the constructor of {ctor} for field {field} with {failure}",
                    if one { "fails" } else { "fail" }
                ),
                None => format!(
                    "{} no signature of {ctor} for field {field}",
                    if one { "matches" } else { "match" }
                ),
            };
            // Plan repair 5, RF-09: the DL-155 help only where a fates-a line lifts the block.
            let enum_ctor = matches!(self.program.types.get(ctor), Some(Definition::Enum(_)));
            let help = match (reason, enum_ctor) {
                (Some(_), true) => format!(
                    "  help: no fate line covers an ENUM CONSTRUCTOR yet (D041 open); restore the constructor rule of fn {ctor} that reads these records"
                ),
                (None, true) => format!(
                    "  help: no fate line covers an ENUM CONSTRUCTOR yet (D041 open); restore a signature of fn {ctor} that reads these records"
                ),
                (None, false) => format!(
                    "  help: no fate line covers a value that matches no signature of {ctor} (a decode fault); restore a signature of fn {ctor} that reads these records"
                ),
                (Some(failure), false) => {
                    let n = self.newest_version(ctor);
                    // DL-172 QB-2 (open, built default): a failed rule that tests no parameter with a literal has
                    // no fate line.
                    match &checks.params[&(key.clone(), failure.clone())] {
                        None => format!(
                            "  help: no fate line covers a failed rule that tests no parameter with a literal (QB-2 open); restore the rule of fn {ctor} that reads these records"
                        ),
                        Some(param) => format!(
                            "  help: declare the next TYPE VERSION and a fate (DL-155): type {ctor} v{} and migrate {ctor} v{n} -> v{} {{ quarantine {param} }}",
                            n + 1,
                            n + 1
                        ),
                    }
                }
            };
            errors.push(format!(
                "error: TYPE {ty}: {failed} stored {noun}{} of {op} {what}\n  record source: {source}:{line} (line {line})\n{help}",
                plural(*failed)
            ));
        }
        // PF-13: one `fate:` line per (place, step, line), counted by record; beside a block, or before the count line.
        let fates: Vec<String> = checks
            .fated
            .iter()
            .map(|((op, step, line, verb), records)| {
                format!(
                    "fate: {} stored {noun}{} of {op} {verb} by {step} ({line})",
                    records.len(),
                    plural(records.len())
                )
            })
            .collect();
        if errors.is_empty() {
            notes.extend(fates);
        } else {
            errors.splice(0..0, fates);
        }
        Ok(errors)
    }
    // DL-155 help for a lost ENUM LITERAL; the old String is a stored value and stays a placeholder (DL-124).
    fn help_literal(&self, e: &str) -> String {
        let n = self.enum_newest(e);
        format!(
            "  help: declare the next TYPE VERSION and a fate (DL-155): enum {e} v{} and migrate {e} v{n} -> v{} {{ map \"<old literal>\" -> <Variant> }}",
            n + 1,
            n + 1
        )
    }
    // The `quarantine p` line in the last MIGRATE STEP of the constructor TYPE `ctor` for a parameter `p` in
    // `tested` (form A, QF-3 ruled; DL-172).
    fn ctor_fate(&self, ctor: &str, tested: &[String]) -> Option<Fate> {
        self.record(ctor).ok()?;
        self.fate_in(
            ctor,
            |c| matches!(c, Change::Quarantine(Some(f), None) if tested.contains(f)),
        )
    }
    // PF-21, DL-172: the parameters with a literal pattern in the first clause of `sig` that matches `inputs`, in
    // parameter order. Empty: the clause tests no parameter with a literal (QB-2), or no clause matches.
    // ponytail: a Rust mirror of the clause order; it decides the help and the quarantine lift (DL-172). A new
    // pattern kind (guards, Int compares) must change this mirror and the Elixir `cond` together.
    fn tested_params(&self, ctor: &str, sig: &str, inputs: &[String]) -> Vec<String> {
        let names = (self.ctor_signatures(ctor).unwrap_or_default())
            .into_iter()
            .find(|(k, _)| k == sig)
            .map(|(_, n)| n)
            .unwrap_or_default();
        let fits = |arg: &Node, input: &String| match arg {
            Node::Text(t) => t == input,
            Node::Int(n) => n.to_string() == *input,
            _ => true,
        };
        let clause = (self.program.clauses.iter())
            .filter(|c| c.key == sig)
            .find(|c| c.args.iter().zip(inputs).all(|(a, i)| fits(a, i)));
        let Some(clause) = clause else {
            return Vec::new();
        };
        (clause.args.iter().zip(names))
            .filter(|(a, _)| matches!(a, Node::Text(_) | Node::Int(_)))
            .map(|(_, n)| n)
            .collect()
    }
    // DL-166: the key of `field` (newest TYPE VERSION of `ty`) in a stored body of TYPE VERSION `version`: undo the
    // renames of each MIGRATE STEP from `version` on, the newest step first, the changes of a step in reverse order.
    fn stored_key(&self, ty: &str, version: u32, field: &str) -> String {
        let mut name = field.to_string();
        for step in self
            .migrations(ty)
            .iter()
            .rev()
            .filter(|m| m.from >= version)
        {
            for change in step.changes.iter().rev() {
                if let Change::Rename(old, new) = change
                    && *new == name
                {
                    name = old.clone();
                }
            }
        }
        name
    }
    // Step 8 (D6B-48, DL-101): the first signature of `fn T` whose keys all hold Strings (one parameter: the field
    // value is the String), with its inputs. None: no signature matches.
    // ponytail: a Rust mirror of the `cond` in `__beaml_from_T` (D6B-103); a new signature rule must change both
    // (guard E9). Upgrade path: emit a public `__beaml_from_T` and call it in the Elixir run.
    fn ctor_pick(&self, ty: &str, value: Option<&Json>) -> Option<(String, Vec<String>)> {
        self.ctor_signatures(ty)
            .expect("checked signatures")
            .into_iter()
            .find_map(|(key, names)| {
                let inputs: Option<Vec<String>> = match names.as_slice() {
                    [_] => value.and_then(Json::text).map(|t| vec![t.to_string()]),
                    _ => names
                        .iter()
                        .map(|n| {
                            value
                                .and_then(|v| v.get(n))
                                .and_then(Json::text)
                                .map(str::to_string)
                        })
                        .collect(),
                };
                inputs.map(|i| (key, i))
            })
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
            // Ruling on O1: a step with a fate line is never a DEAD LINE (its rows may be nested or parked).
            let needed = step.changes.iter().any(Change::fate)
                || snapshot.oldest.get(name).is_some_and(|v| *v <= step.from);
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
    // 0005 P4b (Q5-4 B, PDB-21 to PDB-26): the ROW SNAPSHOT `rows.jsonl`. A row is decodable when it is accepted, its
    // `type.name` is a ROW TYPE that a db.get or db.list reads (DL-137) and its digest holds (D6B-58); every other row
    // is counted, not checked (DL-136, QV3-8 B). A decodable row gets the path check of its TYPE (an off-chain TYPE
    // VERSION blocks), then the DL-102 and DL-122 checks. A row of an operation with no EFFECT and no RETIRE LINE
    // whose TYPE has no reader blocks as DL-040. Names, counts and lines only, never a value (DL-124).
    fn check_rows(
        &self,
        source: &str,
        text: &str,
        meta: Option<&str>,
        code: &str,
        snapshot: &mut Snapshot,
    ) -> Checked<String> {
        let lines = text.lines().filter(|l| !l.trim().is_empty()).count();
        // PDB-22: the compiler reads `row_count` only.
        if let Some(meta) = meta {
            let count = parse_json(meta)
                .and_then(|m| m.get("row_count").cloned())
                .and_then(|n| match n {
                    Json::Number(n) => n.parse::<usize>().ok(),
                    _ => None,
                })
                .ok_or("error: snapshot-meta.json has no row_count (P5-19)")?;
            if count != lines {
                return Err(format!(
                    "error: rows.jsonl holds {lines} rows but snapshot-meta.json counts {count}; the ROW SNAPSHOT is partial"
                ));
            }
        }
        let readers: BTreeSet<String> = self
            .program
            .effects
            .iter()
            .filter(|e| e.kind == "db.get" || e.kind == "db.list")
            .map(|e| self.row_type(e))
            .collect();
        let (mut total, mut checked) = (0, 0);
        let mut orphans: BTreeMap<String, (usize, usize)> = BTreeMap::new();
        let mut groups: BTreeMap<StoredVersion, (usize, usize)> = BTreeMap::new();
        let mut checks = ValueChecks::default();
        let mut wrong: BTreeMap<(String, String), (usize, usize)> = BTreeMap::new();
        let place = "table records";
        for (index, line) in text.lines().enumerate() {
            let number = index + 1;
            if line.trim().is_empty() {
                continue;
            }
            let at = format!("record source: {source}:{number} (line {number})");
            let row =
                parse_json(line).ok_or_else(|| format!("error: stored ROW is not JSON\n  {at}"))?;
            if row.get("source").and_then(Json::text) != Some("db") {
                return Err(format!("error: stored ROW has no source \"db\"\n  {at}"));
            }
            let version = match row.get("version") {
                Some(Json::Number(n)) if n == "3" => None,
                Some(Json::Number(n)) => Some(n.as_str()),
                None => Some("none"),
                Some(_) => Some("malformed"),
            };
            if let Some(v) = version {
                return Err(format!(
                    "error: stored ROW has record version {v}; this build reads record version 3 only (DL-143)\n  {at}"
                ));
            }
            total += 1;
            let name = row
                .get("type")
                .and_then(|t| t.get("name"))
                .and_then(Json::text);
            let read = name.is_some_and(|n| readers.contains(n));
            if let Some(op) = row.get("operation").and_then(Json::text) {
                snapshot.operations.insert(op.to_string());
                if !read && self.effect(op).is_none() && self.retire(op).is_none() {
                    orphans.entry(op.to_string()).or_insert((0, number)).0 += 1;
                    continue;
                }
            }
            // P2b (DL-164, PDB-15 read order: name, digest, version): a row of a read TYPE reaches `body(core)` in
            // `row_<type>/1` whatever its outcome (Repairs O3).
            if let Some(name) = name.filter(|_| read && !digest_holds(&row)) {
                let key = (name.to_string(), place.to_string());
                wrong.entry(key).or_insert((0, number)).0 += 1;
                continue;
            }
            let accepted = row.get("outcome").and_then(Json::text) == Some("accepted");
            let Ok(stored) = stored_version(&row) else {
                continue;
            };
            if !accepted || !read {
                continue;
            }
            checked += 1;
            let oldest = snapshot
                .oldest
                .entry(stored.name.clone())
                .or_insert(stored.version);
            *oldest = (*oldest).min(stored.version);
            let kept = |field: &str| match row.get("unknown_fields") {
                Some(Json::List(names)) => names.iter().any(|n| n.text() == Some(field)),
                _ => false,
            };
            let ty = stored.name.clone();
            self.value_checks(
                &mut checks,
                &ty,
                place,
                stored.version,
                number,
                row.get("value"),
                &kept,
            );
            groups.entry(stored).or_insert((0, number)).0 += 1;
        }
        if let Some(e) = digest_errors(&wrong, source, "ROW") {
            return Err(e);
        }
        if !orphans.is_empty() {
            return Err(orphans
                .iter()
                .map(|(op, (count, line))| {
                    format!(
                        "error: stored ROW of operation {op} has no effect in the source\n  record source: {source}:{line} (line {line})\n  stored ROWS of operation {op}: {count}\n  help: if the effect is deleted on purpose, declare: retire {op} keep <n> days"
                    )
                })
                .collect::<Vec<_>>()
                .join("\n"));
        }
        let mut errors: Vec<String> = groups
            .iter()
            .filter_map(|(stored, (count, line))| {
                self.no_path(source, stored, *count, *line, &stored.name, "ROW", place)
            })
            .collect();
        if errors.is_empty() {
            errors = self.value_errors(checks, source, code, "ROW", &mut snapshot.notes)?;
        }
        if !errors.is_empty() {
            return Err(errors.join("\n"));
        }
        Ok(format!(
            "rows: {total} rows, {checked} checked, {} not decodable",
            total - checked
        ))
    }
    // The message for a stored TYPE VERSION without a path to the newest TYPE VERSION of `type_name`, or None.
    // `noun` and `place` name the stored item: `RESPONSE RECORD` of `operation <op>`, or `ROW` of `table records`.
    #[allow(clippy::too_many_arguments)]
    fn no_path(
        &self,
        source: &str,
        stored: &StoredVersion,
        count: usize,
        line: usize,
        type_name: &str,
        noun: &str,
        place: &str,
    ) -> Option<String> {
        let versions = self.type_versions(type_name);
        let start = self.chain_start(type_name);
        let newest = self.newest_version(type_name);
        let derived = stored
            .version
            .checked_sub(start)
            .and_then(|index| versions.get(index as usize));
        // Slice 4: a stored version below the chain start (a removed DEAD LINE needed again, E17).
        let below_start = stored.version < start && stored.name == type_name;
        if stored.name == type_name && derived.is_some_and(|d| fingerprint(d) == stored.fingerprint)
        {
            return None;
        }
        let newest_fields = versions.last().unwrap();
        let plural = if count == 1 { "" } else { "S" };
        let mut m = vec![
            format!("error: TYPE {type_name} cannot read {count} stored {noun}{plural} of {place}"),
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
            if stored.name != type_name {
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
        if stored.name != type_name {
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

// Q6E-1: one capital per `_` segment (`order_flow` -> `OrderFlow`).
fn module_name_from_stem(stem: &str) -> String {
    stem.split('_')
        .map(|part| {
            let mut chars = part.chars();
            chars.next().map_or(String::new(), |c| {
                c.to_ascii_uppercase().to_string() + chars.as_str()
            })
        })
        .collect()
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
    let mut checker = Checker::new(&program)?;
    checker.validate()?;
    checker.redacted_copies()?;
    // D6B-28: only an EFFECT pipe names spans. Slice 6d: an ENTRY LINE names its root span.
    let spans = !program.effects.is_empty() || !program.entries.is_empty();
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
    // Q6E-1 C: a host-called (ENTRY LINE) source takes its module name from the stem; any other keeps BeamlSpike.
    if !program.entries.is_empty() {
        checker.module = module_name_from_stem(service);
        // D6B-203: a module that the generated code calls cannot be redefined.
        const CALLED: [&str; 15] = [
            "Kernel",
            "String",
            "Enum",
            "Map",
            "List",
            "IO",
            "Base",
            "Module",
            "Code",
            "Integer",
            "OpenTelemetry",
            "ProbeSupport",
            "ArgumentError",
            // TEST v3/multi O1: System is called too; 0005 P4: the generated code calls the host BeamlDb.
            "System",
            "BeamlDb",
        ];
        if CALLED.contains(&checker.module.as_str()) {
            return Err(format!(
                "error: the source file name {service} gives the module {}, which the generated code calls; rename the file",
                checker.module
            ));
        }
    }
    // Step 13 (contract 8): the same module goes to the --stored check and to the build output.
    let code = checker.emit(service);
    let (dead, refusals, notes) = match stored {
        Some(path) => {
            let text = std::fs::read_to_string(path)
                .map_err(|e| format!("cannot read --stored input: {}", e.kind()))?;
            let label = path.display().to_string();
            let mut snapshot = checker.check_stored(&label, &text, &code)?;
            // DL-134, R6D-04: the ENTRY RECORDS in `entries.jsonl` beside the --stored file; no file, no ENTRY RECORD.
            let entries = path
                .parent()
                .unwrap_or(std::path::Path::new(""))
                .join("entries.jsonl");
            if entries.is_file() {
                let text = std::fs::read_to_string(&entries).map_err(|e| {
                    format!("cannot read entries.jsonl beside --stored: {}", e.kind())
                })?;
                let line = checker.check_entries(
                    &entries.display().to_string(),
                    &text,
                    &code,
                    &mut snapshot,
                )?;
                snapshot.notes.push(line);
            }
            // 0005 P4b (PDB-21 to PDB-23): the ROW SNAPSHOT `rows.jsonl` beside the --stored file.
            let dir = path.parent().unwrap_or(std::path::Path::new(""));
            let rows = dir.join("rows.jsonl");
            if rows.is_file() {
                let text = std::fs::read_to_string(&rows)
                    .map_err(|e| format!("cannot read rows.jsonl beside --stored: {}", e.kind()))?;
                let meta = std::fs::read_to_string(dir.join("snapshot-meta.json")).ok();
                let line = checker.check_rows(
                    &rows.display().to_string(),
                    &text,
                    meta.as_deref(),
                    &code,
                    &mut snapshot,
                )?;
                snapshot.notes.push(line);
            } else if program
                .effects
                .iter()
                .any(|e| e.kind == "db.get" || e.kind == "db.list")
            {
                return Err("error: stored ROWS unknown: a source with db.get or db.list needs rows.jsonl beside --stored (an unknown store is not an empty store)".into());
            }
            // Ruling on O2 (RF-01): a1 lifts the block and counts, then stops until fates-a2 builds the run-time side.
            let hit = |verb: &str| {
                (snapshot.notes.iter()).any(|n| n.starts_with("fate: ") && n.contains(verb))
            };
            let mut stop = Vec::new();
            if hit(" quarantined by ") {
                stop.push("error: a quarantine line is hit, but quarantine at run time is not built yet (fates-a2, DL-157)");
            }
            if hit(" mapped by ") {
                stop.push(
                    "error: a map line is hit, but map at run time is not built yet (fates-a2)",
                );
            }
            if !stop.is_empty() {
                let mut lines = snapshot.notes.clone();
                lines.extend(stop.into_iter().map(String::from));
                return Err(lines.join("\n"));
            }
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
    Ok((Build { code, dead, notes }, refusals, types))
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

// `beaml-spike fmt SOURCE` (slice 6b step 10, D6B-41 to D6B-46): check the source without `--stored`, edit the
// VERSION MARKS and the column gaps by token ranges, write atomically only on a change, print the diff. Return the
// number of changed lines.
fn fmt_file(path: &std::path::Path, label: &str) -> Checked<usize> {
    let old =
        std::fs::read_to_string(path).map_err(|e| format!("cannot read source: {}", e.kind()))?;
    let new = formatted(&old)?;
    if new == old {
        return Ok(0);
    }
    // fmt-layout F2 (DL-148 adds lines): the old lines that the diff removes or replaces.
    let (a, b) = (split_lines(&old), split_lines(&new));
    let changed = a.len()
        - matching_blocks(&a, &b)
            .iter()
            .map(|block| block.2)
            .sum::<usize>();
    let diff = unified_diff(&old, &new, label);
    write_atomic(path, &new)?;
    std::io::stdout()
        .write_all(diff.as_bytes())
        .map_err(|e| format!("cannot write output: {}", e.kind()))?;
    Ok(changed)
}

// DL-104 form (b) (D6B-43): the VERSION MARK that `fmt` writes. `chain` is (first `from`, last `to`). A mark that a
// chain from v1 implies goes; a chain above v1 without a mark gets its end; every other mark stays (O3).
fn fmt_mark(mark: Option<u32>, chain: Option<(u32, u32)>) -> Option<u32> {
    match (mark, chain) {
        (Some(m), Some((1, end))) if m == end => None,
        (None, Some((from, end))) if from > 1 => Some(end),
        _ => mark,
    }
}

fn formatted(source: &str) -> Checked<String> {
    let tokens = lex(source)?;
    let program = Parser {
        tokens: tokens.clone(),
        at: 0,
    }
    .program()?;
    let mut checker = Checker::new(&program)?;
    checker.validate()?;
    let mut edits: Vec<(Range<usize>, String)> = Vec::new();
    for (name, &end) in &program.name_ends {
        let steps = checker.migrations(name);
        let chain = steps.first().zip(steps.last()).map(|(a, b)| (a.from, b.to));
        let mark = program.marks.get(name).copied();
        match (mark, fmt_mark(mark, chain)) {
            (Some(_), None) => {
                let token = &tokens.iter().find(|(_, r)| r.start >= end).unwrap().1;
                let start = end + source[end..token.start].trim_end_matches([' ', '\t']).len();
                edits.push((start..token.end, String::new()));
            }
            (None, Some(version)) => edits.push((end..end, format!(" v{version}"))),
            _ => {}
        }
    }
    edits.extend(aligned(source, &tokens, &program));
    edits.extend(bodies(source, &tokens, &program));
    edits.sort_by_key(|(range, _)| range.start);
    let mut text = source.to_string();
    for (range, with) in edits.into_iter().rev() {
        text.replace_range(range, &with);
    }
    Ok(text)
}

// DL-148 (1, 2): a TYPE or ENUM body with two or more members takes one member per line (two-space indent, `}` on
// its own line); zero or one member stays on one line. Members keep their text; a body with a comment stays.
fn bodies(
    source: &str,
    tokens: &[(Token, Range<usize>)],
    program: &Program,
) -> Vec<(Range<usize>, String)> {
    let nl = if source.contains("\r\n") {
        "\r\n"
    } else {
        "\n"
    };
    let mut edits = Vec::new();
    for (i, (token, r)) in tokens.iter().enumerate() {
        let is_enum = match token {
            Token::Word(w) if w == "type" => false,
            Token::Word(w) if w == "enum" => true,
            _ => continue,
        };
        let line_start = source[..r.start].rfind('\n').map_or(0, |i| i + 1);
        let indent = &source[line_start..r.start];
        if !indent.trim().is_empty()
            || !matches!(&tokens[i + 1].0, Token::Word(name) if program.types.contains_key(name))
        {
            continue;
        }
        let Some(open) =
            (i + 2..(i + 4).min(tokens.len())).find(|&k| tokens[k].0 == Token::Symbol('{'))
        else {
            continue;
        };
        let close = open
            + tokens[open..]
                .iter()
                .position(|(t, _)| *t == Token::Symbol('}'))
                .unwrap();
        if (open..close).any(|k| {
            !source[tokens[k].1.end..tokens[k + 1].1.start]
                .trim()
                .is_empty()
        }) {
            continue;
        }
        let mut members: Vec<Range<usize>> = Vec::new();
        let mut depth = 0;
        for k in open + 1..close {
            let (t, r) = &tokens[k];
            let starts = depth == 0
                && matches!(t, Token::Word(_))
                && (is_enum || tokens[k + 1].0 == Token::Symbol(':'));
            match t {
                Token::Symbol('(') => depth += 1,
                Token::Symbol(')') => depth -= 1,
                _ => {}
            }
            match members.last_mut() {
                Some(m) if !starts => m.end = r.end,
                _ => members.push(r.clone()),
            }
        }
        let text: Vec<&str> = members.iter().map(|m| &source[m.clone()]).collect();
        let body = match text.len() {
            0 => "{}".to_string(),
            1 => format!("{{ {} }}", text[0]),
            _ => {
                let lines: String = text.iter().map(|m| format!("{indent}  {m}{nl}")).collect();
                format!("{{{nl}{lines}{indent}}}")
            }
        };
        edits.push((tokens[open].1.start..tokens[close].1.end, body));
    }
    edits
}

// Cell columns of a clause table (DL-148): 0 the name part, 1.. the arguments, then `->`, output, `! ERR`, `=`.
const ARROW: usize = 1000;
const OUT: usize = 1001;
const ERR: usize = 1002;
const EQUALS: usize = 1003;

// One single-line clause, signature or EFFECT line: its line, line start and (column, cell) pairs.
struct Row {
    line: usize,
    start: usize,
    cells: Vec<(usize, Range<usize>)>,
}

// DL-083, D6B-44, DL-013, DL-148: every block of consecutive single-line clause, signature, EFFECT and ENTRY lines is
// one table. Cells are `fn NAME` (or `effect NAME`), each top-level argument with its comma (the EFFECT input), `->`,
// the output, the `! ERR` part and `=`; each column starts one space after the longest previous cell of the block.
// Only the gaps between cells change.
fn aligned(
    source: &str,
    tokens: &[(Token, Range<usize>)],
    program: &Program,
) -> Vec<(Range<usize>, String)> {
    // ponytail: line numbers by counting from the file start, O(rows * size); fine under the 256 KiB limit.
    let line_of = |at: usize| {
        source.as_bytes()[..at]
            .iter()
            .filter(|&&b| b == b'\n')
            .count()
    };
    let items = program
        .clauses
        .iter()
        .map(|c| c.source_range.clone())
        .chain(program.signature_lines.iter().map(|l| l.start..l.end))
        .chain(program.effects.iter().map(|e| e.source_range.clone()))
        // Slice 6d (R6D-06): an ENTRY LINE is an EFFECT line; its head normalizes the same way.
        .chain(program.entries.iter().map(|e| e.source_range.clone()));
    let mut rows = Vec::new();
    for range in items {
        let first = tokens
            .iter()
            .position(|(_, r)| r.start == range.start)
            .unwrap();
        let last = first
            + tokens[first..]
                .iter()
                .position(|(_, r)| r.end == range.end)
                .unwrap();
        let line = line_of(range.start);
        let next = &tokens[last + 1];
        if source[range.clone()].contains('\n')
            || (first > 0 && line_of(tokens[first - 1].1.end) == line)
            || (next.0 != Token::End && line_of(next.1.start) == line)
        {
            continue;
        }
        let mut cells = vec![(0, tokens[first].1.start..tokens[first + 1].1.end)];
        let (mut open, mut depth, mut column) = (None::<Range<usize>>, 0, 1);
        for (token, r) in &tokens[first + 2..=last] {
            match token {
                Token::Symbol('(' | '{') => depth += 1,
                Token::Symbol(')' | '}') => depth -= 1,
                _ => {}
            }
            let mark = match token {
                _ if depth != 0 => None,
                Token::Arrow if column < ARROW => Some(ARROW),
                Token::Symbol('!') if column == OUT => Some(ERR),
                Token::Symbol('=') if column >= OUT => Some(EQUALS),
                _ => None,
            };
            if let Some(mark) = mark {
                cells.extend(open.take().map(|o| (column, o)));
                if mark == ERR {
                    (column, open) = (ERR, Some(r.clone()));
                    continue;
                }
                cells.push((mark, r.clone()));
                if mark == EQUALS {
                    break;
                }
                column = OUT;
                continue;
            }
            open = Some(open.map_or(r.clone(), |o| o.start..r.end));
            if depth == 0 && column < ARROW && *token == Token::Symbol(',') {
                cells.extend(open.take().map(|o| (column, o)));
                column += 1;
            }
        }
        // A signature line ends without `=`.
        cells.extend(open.take().map(|o| (column, o)));
        let start = source[..range.start].rfind('\n').map_or(0, |i| i + 1);
        rows.push(Row { line, start, cells });
    }
    rows.sort_by_key(|row| row.line);
    let mut edits = Vec::new();
    let mut begin = 0;
    for end in 1..=rows.len() {
        if rows
            .get(end)
            .is_some_and(|b| b.line == rows[end - 1].line + 1)
        {
            continue;
        }
        let group = &rows[begin..end];
        begin = end;
        // cursor: the column after the last placed cell of each row; cell 0 keeps its place.
        let mut cursor: Vec<usize> = group.iter().map(|r| r.cells[0].1.end - r.start).collect();
        let mut columns: Vec<usize> = group
            .iter()
            .flat_map(|r| r.cells[1..].iter().map(|c| c.0))
            .collect();
        columns.sort_unstable();
        columns.dedup();
        for column in columns {
            let at = group
                .iter()
                .zip(&cursor)
                .filter(|(row, _)| row.cells.iter().any(|c| c.0 == column))
                .map(|(_, &c)| c)
                .max()
                .unwrap()
                + 1;
            for (row, cur) in group.iter().zip(cursor.iter_mut()) {
                if let Some(k) = row.cells.iter().position(|c| c.0 == column) {
                    let cell = &row.cells[k].1;
                    edits.push((row.cells[k - 1].1.end..cell.start, " ".repeat(at - *cur)));
                    *cur = at + cell.len();
                }
            }
        }
    }
    edits
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

// Slice 6b step 13 (D6B-102, D6B-122): the Elixir side of the --stored check. It reads the module and the calls from
// stdin, compiles the module in memory and prints one line per call. No `rescue`, `catch` or `try`: any other result
// raises, and the run error follows. The first line is the process marker (E8).
const DRIVER: &str = r#"# beaml-stored-check
%{"module" => module, "name" => name, "calls" => calls} = JSON.decode!(IO.binread(:stdio, :eof))
Code.compile_string(module)
parent = Module.concat([name])

for [fun, type, args] <- calls do
  ok = Module.concat(parent, type)

  case apply(parent, String.to_atom(fun), args) do
    {:ok, %{__struct__: ^ok}} ->
      IO.puts("ok")

    {:ok, {^type, variant, payload}} when is_binary(variant) and is_list(payload) ->
      IO.puts("ok")

    {:error, %{__struct__: failure}} ->
      [^name, short] = Module.split(failure)
      IO.puts("error " <> short)
  end
end
"#;

const ELIXIR_RUN_HELP: &str = "  help: compile the generated module with elixirc to see the error";

// D6B-119, D6B-120, D6B-123: one `elixir -e DRIVER` child with a time limit. The verdict per call: None passes,
// Some(F) fails with F. Child stdout and stderr are never forwarded (D6B-106). One `stored-elixir` event (D6B-107).
fn run_elixir(stdin: &str, failures: &[&[String]]) -> Checked<Vec<Option<String>>> {
    use std::os::unix::process::CommandExt;
    let calls = failures.len();
    let limit =
        match std::env::var("BEAML_STORED_ELIXIR_LIMIT_S") {
            Err(_) => 60,
            Ok(text) => match text.parse::<u64>() {
                Ok(n) if n >= 1 => n,
                _ => return Err(
                    "error: BEAML_STORED_ELIXIR_LIMIT_S must be a whole number of seconds from 1"
                        .into(),
                ),
            },
        };
    let started = std::time::Instant::now();
    let spawned = std::process::Command::new("elixir")
        .arg("-e")
        .arg(DRIVER)
        .env("ERL_CRASH_DUMP", "/dev/null")
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .process_group(0)
        .spawn();
    let mut child = match spawned {
        Ok(child) => child,
        Err(e) => {
            action("stored-elixir", "error", &[("ms", 0), ("calls", calls)]);
            return Err(if e.kind() == std::io::ErrorKind::NotFound {
                "error: the --stored check runs the constructors over the stored values in Elixir (DL-121): elixir is not on PATH\n  help: install Elixir 1.18 with Erlang/OTP 27 and put elixir on PATH".into()
            } else {
                format!(
                    "error: the --stored check: the Elixir run of the generated constructors failed (start: {})\n{ELIXIR_RUN_HELP}",
                    e.kind()
                )
            });
        }
    };
    let pid = child.id();
    let input = stdin.to_string();
    let mut pipe = child.stdin.take().expect("piped stdin");
    let (send, receive) = std::sync::mpsc::channel();
    std::thread::spawn(move || {
        // The driver reads all of stdin before it writes, so this write cannot block on a full output pipe.
        let _ = pipe.write_all(input.as_bytes());
        drop(pipe);
        let _ = send.send(child.wait_with_output());
    });
    let outcome = receive.recv_timeout(std::time::Duration::from_secs(limit));
    let ms = started.elapsed().as_millis() as usize;
    let verdicts = match outcome {
        Ok(Ok(output)) => parse_elixir_results(
            output.status,
            &String::from_utf8_lossy(&output.stdout),
            failures,
        ),
        Ok(Err(e)) => Err(format!("wait: {}", e.kind())),
        Err(_) => {
            // The whole process group: `elixir` is a launcher script for the VM.
            let _ = std::process::Command::new("/bin/kill")
                .args(["-KILL", "--", &format!("-{pid}")])
                .status();
            Err(format!("time limit {limit} s"))
        }
    };
    let result = match &verdicts {
        Ok(v) if v.iter().any(Option::is_some) => "blocked",
        Ok(_) => "ok",
        Err(_) => "error",
    };
    action("stored-elixir", result, &[("ms", ms), ("calls", calls)]);
    verdicts.map_err(|why| {
        format!("error: the --stored check: the Elixir run of the generated constructors failed ({why})\n{ELIXIR_RUN_HELP}")
    })
}

// D6B-121: success needs a clean exit and exactly one line per call, each `ok` or `error F` with F in the failure
// list of that call. Else the reason for the run error.
fn parse_elixir_results(
    status: std::process::ExitStatus,
    stdout: &str,
    failures: &[&[String]],
) -> Result<Vec<Option<String>>, String> {
    use std::os::unix::process::ExitStatusExt;
    if !status.success() {
        return Err(match (status.code(), status.signal()) {
            (Some(code), _) => format!("exit {code}"),
            (None, Some(signal)) => format!("signal {signal}"),
            (None, None) => "exit unknown".into(),
        });
    }
    let lines: Vec<&str> = stdout.lines().collect();
    if lines.len() != failures.len() {
        return Err("result lines".into());
    }
    lines
        .iter()
        .zip(failures)
        .map(|(line, allowed)| match line.strip_prefix("error ") {
            None if *line == "ok" => Ok(None),
            Some(f) if allowed.iter().any(|a| a == f) => Ok(Some(f.to_string())),
            _ => Err("result lines".to_string()),
        })
        .collect()
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
        // D6B-188: one write of one full line, so parallel runs never interleave pieces of a line.
        // ponytail: relies on one short O_APPEND write landing whole (local APFS, ext4); add a flock for a network
        // file system or a much longer event.
        let line = format!(
            "{{\"ts\":{ts},\"source\":\"cli\",\"action\":\"{action}\",\"target\":\"experiment-0001\",\"result\":\"{result}\"{count}}}\n"
        );
        file.write_all(line.as_bytes())
    })();
}
fn main() {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    let remove = matches!(args.as_slice(), [_, flag, _, last, ..] if flag == "--stored" && last == "--remove-dead");
    let assume_complete =
        matches!(args.as_slice(), [_, _, _, _, last] if last == "--assume-complete");
    let fmt = matches!(args.as_slice(), [command, _] if command == "fmt");
    let result = (|| -> Checked<Vec<(&str, usize)>> {
        if fmt {
            let changed = fmt_file(std::path::Path::new(&args[1]), &args[1].to_string_lossy())?;
            return Ok(vec![("changed", changed)]);
        }
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
    let name = if fmt {
        "fmt"
    } else if remove {
        "remove-dead"
    } else {
        "compile"
    };
    match &result {
        Ok(counts) => action(name, "ok", counts),
        Err(_) if fmt => action(name, "error", &[("changed", 0)]),
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
    fn constructor_types_are_structs() {
        // DL-106, D6B-75, D6B-76: literal, pattern and input check of a constructor TYPE use the struct.
        let out = compile("type N { value: Int }\nfn N n: Int -> N\nfn N n -> N = N { value: n }\nfn read N { value } -> Int = value\n").unwrap();
        assert!(out.contains("defp __beaml_new_N_1(v_n), do: %__MODULE__.N{value: v_n}"));
        assert!(out.contains("defp __beaml_read(%__MODULE__.N{value: v_value}), do: v_value"));
        assert!(
            out.contains("when is_struct(v, __MODULE__.N), do: __beaml_valid__(Map.get(v, :value)")
        );
        assert!(out.contains(
            "def new(%{n: a0} = m) when map_size(m) == 1, do: {:ok, @parent.new_N_1(a0)}"
        ));
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
    fn fmt_mark_follows_dl104() {
        // D6B-43: (mark, chain) -> the mark that `fmt` writes.
        assert_eq!(fmt_mark(Some(3), Some((1, 3))), None);
        assert_eq!(fmt_mark(None, Some((1, 2))), None);
        assert_eq!(fmt_mark(Some(3), None), Some(3));
        assert_eq!(fmt_mark(Some(1), None), Some(1));
        assert_eq!(fmt_mark(None, Some((4, 5))), Some(5));
        assert_eq!(fmt_mark(Some(5), Some((4, 5))), Some(5));
        assert_eq!(fmt_mark(None, None), None);
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

    // U1 (D6B-121): the strict result protocol of the Elixir run.
    #[test]
    fn elixir_results_are_strict() {
        use std::os::unix::process::ExitStatusExt;
        let ok = std::process::ExitStatus::from_raw(0);
        let fails = vec!["NoCurrency".to_string()];
        let two: Vec<&[String]> = vec![&fails, &fails];
        assert_eq!(
            Ok(vec![None, Some("NoCurrency".to_string())]),
            parse_elixir_results(ok, "ok\nerror NoCurrency\n", &two)
        );
        for (stdout, why) in [
            ("ok\n", "result lines"),
            ("ok\nok\nok\n", "result lines"),
            ("ok\nokay\n", "result lines"),
            ("ok\nerror\n", "result lines"),
            ("ok\nerror Other\n", "result lines"),
        ] {
            assert_eq!(
                Err(why.to_string()),
                parse_elixir_results(ok, stdout, &two),
                "{stdout:?}"
            );
        }
        let exit1 = std::process::ExitStatus::from_raw(1 << 8);
        let signal9 = std::process::ExitStatus::from_raw(9);
        assert_eq!(
            Err("exit 1".to_string()),
            parse_elixir_results(exit1, "ok\nok\n", &two)
        );
        assert_eq!(
            Err("signal 9".to_string()),
            parse_elixir_results(signal9, "ok\nok\n", &two)
        );
        // O1 (RED review): the kill check of E8 finds the child by the marker in its args.
        assert!(DRIVER.starts_with("# beaml-stored-check\n"));
        assert!(
            !["rescue", "catch", "try"]
                .iter()
                .any(|w| DRIVER.contains(w))
        );
    }

    #[test]
    fn module_name_from_stem() {
        // N15, Q6E-1: one capital per `_` segment.
        for (stem, module) in [
            ("orders", "Orders"),
            ("order_flow", "OrderFlow"),
            ("v2_orders", "V2Orders"),
        ] {
            assert_eq!(module, super::module_name_from_stem(stem));
        }
    }

    #[test]
    fn effect_reach_is_transitive() {
        // E9, D6B-84, D6B-115: the reach map through a chain, a reaching cycle and a pure cycle.
        let source = "type O { id: String }\ntype E { reason: String }\n\
            effect pay.go O -> O ! E = http.post(\"pay/go\")\n\
            fn place o: O -> O ! E = o |> pay.go\n\
            fn c1 o: O -> O ! E = o |> c2\nfn c2 o: O -> O ! E = o |> place\n\
            fn ping o: O -> O ! E = o |> pong\nfn pong o: O -> O ! E = o |> ping |> place\n\
            fn a o: O -> O = o |> b\nfn b o: O -> O = o |> a\n";
        let program = Parser {
            tokens: lex(source).unwrap(),
            at: 0,
        }
        .program()
        .unwrap();
        let mut checker = Checker::new(&program).unwrap();
        checker.validate().unwrap();
        let go = BTreeSet::from(["pay.go".to_string()]);
        for name in ["place", "c1", "c2", "ping", "pong"] {
            assert_eq!(checker.reach[name], go, "{name}");
        }
        assert!(checker.reach["a"].is_empty() && checker.reach["b"].is_empty());
    }
}
