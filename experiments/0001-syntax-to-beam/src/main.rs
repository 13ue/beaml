use std::collections::{BTreeMap, BTreeSet};
use std::io::Write;
use std::ops::Range;

type Checked<T> = Result<T, String>;

#[derive(Clone, Debug, PartialEq)]
enum Token {
    Word(String),
    Text(String),
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
    Name(String),
    Call(String, Vec<Node>),
    Record(String, Vec<(String, Node)>),
    Plus(Box<Node>, Box<Node>),
    Annotated(Box<Node>, String),
    // `head |> step |> step`: only a whole function body (slice 1).
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
    args: Vec<Node>,
    output: String,
    failures: Vec<String>,
    body: Node,
    source_range: Range<usize>,
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
#[derive(Default)]
struct Program {
    types: BTreeMap<String, Definition>,
    clauses: Vec<Clause>,
    effects: Vec<Effect>,
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
    fn arrow(&mut self) -> Checked<()> {
        if self.peek() != &Token::Arrow {
            return Err(self.error("expected '->'"));
        }
        self.at += 1;
        Ok(())
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
                            args.push(self.node(depth + 1)?);
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
                                self.node(depth + 1)?
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
    fn program(mut self) -> Checked<Program> {
        let mut program = Program::default();
        while self.peek() != &Token::End {
            let start = self.tokens[self.at].1.start;
            match self.word()?.as_str() {
                "interface" => {
                    let name = self.word()?;
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
                    while !self.eat('}') {
                        let variant = self.word()?;
                        self.expect('(')?;
                        let mut args = Vec::new();
                        if !self.eat(')') {
                            loop {
                                args.push(self.word()?);
                                if self.eat(')') {
                                    break;
                                }
                                self.expect(',')?;
                            }
                        }
                        variants.push((variant, args));
                        self.eat(',');
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
                    self.expect('=')?;
                    let mut body = self.node(0)?;
                    if self.peek() == &Token::Pipe {
                        let mut steps = Vec::new();
                        while self.peek() == &Token::Pipe {
                            self.at += 1;
                            steps.push(self.dotted()?);
                        }
                        body = Node::Pipe(Box::new(body), steps);
                    }
                    program.clauses.push(Clause {
                        name,
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
                _ => return Err(self.error("expected interface, enum, or fn")),
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
        };
        for (name, def) in &program.types {
            if !upper(name) || name == "String" {
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
                }
            }
        }
        for name in program.types.keys() {
            checker.check_type(name, &mut Vec::new())?;
        }
        if program.clauses.is_empty() {
            return Err("expected at least one function".into());
        }
        for clause in &program.clauses {
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
                "is_map",
                "map_size",
            ];
            if !lower(&clause.name) || reserved.contains(&clause.name.as_str()) {
                return Err(format!("invalid function name: {}", clause.name));
            }
            checker.check_type(&clause.output, &mut Vec::new())?;
            let mut vars = BTreeMap::new();
            let mut args = Vec::new();
            for pattern in &clause.args {
                args.push(checker.pattern(pattern, None, &mut vars)?);
            }
            checker.failure_types(&clause.failures)?;
            let signature = (args, clause.output.clone());
            if let Some(previous) = checker
                .signatures
                .insert(clause.name.clone(), signature.clone())
                && previous != signature
            {
                return Err(format!("inconsistent function signature: {}", clause.name));
            }
            if let Some(previous) = checker
                .failures
                .insert(clause.name.clone(), clause.failures.clone())
                && previous != clause.failures
            {
                return Err(format!("inconsistent function signature: {}", clause.name));
            }
        }
        for clause in &program.clauses {
            if matches!(clause.body, Node::Pipe(..))
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
        Ok(checker)
    }
    fn failure_types(&self, failures: &[String]) -> Checked<()> {
        unique(failures.iter().cloned())?;
        for failure in failures {
            // Each failure TYPE becomes a nested struct module next to `Replay` and `Http`.
            if failure == "Replay" || failure == "Http" {
                return Err(format!("reserved failure type name: {failure}"));
            }
            self.record(failure)?;
        }
        Ok(())
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
            let segments: Vec<&str> = name.split('.').collect();
            if segments.len() != 2 || !segments.iter().all(|s| lower(s)) {
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
            self.check_type(&effect.input, &mut Vec::new())?;
            for (field, ty) in self.record(&effect.output)? {
                if ty != "String" {
                    return Err(format!(
                        "effect {name}: slice 1 decodes String fields only, not {}.{field}",
                        effect.output
                    ));
                }
            }
            self.failure_types(&effect.failures)?;
            match effect.failures.as_slice() {
                [failure]
                    if self
                        .record(failure)?
                        .iter()
                        .any(|(f, t)| f == "reason" && t == "String") => {}
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
    fn check_type(&self, name: &str, path: &mut Vec<String>) -> Checked<()> {
        if name == "String" {
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
            _ => Err(format!("unknown interface: {name}")),
        }
    }
    fn same_type(&self, left: &str, right: &str) -> bool {
        if left == right {
            return true;
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
                    let (args, output) = self
                        .signatures
                        .get(name)
                        .ok_or(format!("unknown function: {name}"))?;
                    if !self.failures[name].is_empty() {
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
            Node::Pipe(_, _) => Err("a pipe is only supported as a whole function body".into()),
        }
    }
    // Pipe check: each step is a known one-argument fn or an EFFECT, its input TYPE is the
    // previous output TYPE, and each of its failure TYPES is in the `!` list of the enclosing fn.
    fn body(&self, clause: &Clause, vars: &BTreeMap<String, String>) -> Checked<String> {
        let Node::Pipe(head, steps) = &clause.body else {
            return self.expression(&clause.body, vars);
        };
        let mut ty = self.expression(head, vars)?;
        for step in steps {
            let (input, output, failures) = if let Some(effect) = self.effect(step) {
                (&effect.input, &effect.output, &effect.failures)
            } else if let Some((args, output)) = self.signatures.get(step) {
                if args.len() != 1 {
                    return Err(format!("pipe step {step} must take one argument"));
                }
                (&args[0], output, &self.failures[step])
            } else {
                return Err(format!("unknown pipe step: {step}"));
            };
            if !self.same_type(&ty, input) {
                return Err(format!(
                    "type mismatch in pipe step {step}: expected {input}, got {ty}"
                ));
            }
            for failure in failures {
                if !clause.failures.contains(failure) {
                    return Err(format!(
                        "pipe step {step} can fail with {failure}, which is not in the ! list of {}",
                        clause.name
                    ));
                }
            }
            ty = output.clone();
        }
        Ok(ty)
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
            Pattern::Constructor(tag, _) if types[0] == "String" => vec![(tag.clone(), vec![])],
            _ if types[0] == "String" => {
                let mut tags = BTreeSet::new();
                for row in rows {
                    if let Pattern::Constructor(tag, _) = &row[0] {
                        tags.insert(tag.clone());
                    }
                }
                // This sentinel is outside the text: prefix used for all string literals.
                tags.insert("other-string".into());
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
        for (name, (types, _)) in &self.signatures {
            let mut rows = Vec::new();
            let mut budget = 20_000;
            for clause in self.program.clauses.iter().filter(|c| &c.name == name) {
                let mut vars = BTreeMap::new();
                for (arg, ty) in clause.args.iter().zip(types) {
                    self.pattern(arg, Some(ty), &mut vars)?;
                }
                self.require_type(&self.body(clause, &vars)?, &clause.output)?;
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
    fn emit_node(&self, node: &Node) -> String {
        match node {
            Node::Text(s) => binary(s),
            Node::Name(name) if name == "_" => "_".into(),
            Node::Name(name) => format!("v_{name}"),
            Node::Annotated(n, _) => self.emit_node(n),
            Node::Plus(a, b) => format!("({} <> {})", self.emit_node(a), self.emit_node(b)),
            Node::Pipe(_, _) => unreachable!("a pipe is emitted as a whole function body"),
            Node::Record(_, fields) => format!(
                "%{{{}}}",
                fields
                    .iter()
                    .map(|(n, v)| format!("{} => {}", binary(n), self.emit_node(v)))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Node::Call(name, args) => {
                let args = args
                    .iter()
                    .map(|n| self.emit_node(n))
                    .collect::<Vec<_>>()
                    .join(", ");
                if let Some((owner, _)) = self.variants.get(name) {
                    format!("{{{}, {}, [{}]}}", binary(owner), binary(name), args)
                } else {
                    format!("__MODULE__.{name}({args})")
                }
            }
        }
    }
    fn emit(&self, service: &str) -> String {
        // Nested modules (failure structs, Http, Replay) need `defmodule`; payments.beaml output stays unchanged.
        let nested = if self.structs().is_empty() && self.program.effects.is_empty() {
            ""
        } else {
            ", defmodule: 2"
        };
        let mut out = format!(
            "# Generated by experiment 0001. Not a stable ABI.\ndefmodule BeamlSpike do\n  import Kernel, only: [and: 2, is_binary: 1, is_map: 1, map_size: 1, ==: 2, <>: 2, if: 2, raise: 2, def: 2, defp: 2{nested}]\n",
        );
        out.push_str("  defp __beaml_valid__(v, <<83,116,114,105,110,103>>), do: is_binary(v) and String.valid?(v)\n");
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
        for (name, (types, output)) in &self.signatures {
            let args: Vec<_> = (0..types.len()).map(|i| format!("a{i}")).collect();
            let checks: Vec<_> = args
                .iter()
                .zip(types)
                .map(|(a, t)| format!("__beaml_valid__({a}, {})", binary(t)))
                .collect();
            let fails = !self.failures[name].is_empty();
            if fails {
                // `name/n` of a function that can fail: `{:ok, value}` or `{:error, error}`.
                out.push_str(&format!("  def {name}({}) do\n    if {} do\n      case __beaml_{name}({}) do\n        {{:ok, result}} ->\n          if __beaml_valid__(result, {}), do: {{:ok, result}}, else: raise(ArgumentError, \"invalid BEAML output\")\n\n        {{:error, error}} ->\n          {{:error, error}}\n      end\n    else\n      raise ArgumentError, \"invalid BEAML input\"\n    end\n  end\n", args.join(", "), if checks.is_empty() { "true".into() } else { checks.join(" and ") }, args.join(", "), binary(output)));
            } else {
                out.push_str(&format!("  def {name}({}) do\n    if {} do\n      result = __beaml_{name}({})\n      if __beaml_valid__(result, {}), do: result, else: raise(ArgumentError, \"invalid BEAML output\")\n    else\n      raise ArgumentError, \"invalid BEAML input\"\n    end\n  end\n", args.join(", "), if checks.is_empty() { "true".into() } else { checks.join(" and ") }, args.join(", "), binary(output)));
            }
            for clause in self.program.clauses.iter().filter(|c| &c.name == name) {
                out.push_str(&format!(
                    "  # beaml-declaration-v1 {name} {} {}\n",
                    clause.source_range.start, clause.source_range.end
                ));
                let mut used = BTreeSet::new();
                referenced_names(&clause.body, &mut used);
                let params = clause
                    .args
                    .iter()
                    .map(|n| self.emit_node(&omit_unused(n, &used)))
                    .collect::<Vec<_>>()
                    .join(", ");
                if let Node::Pipe(head, steps) = &clause.body {
                    out.push_str(&format!(
                        "  defp __beaml_{name}({params}) do\n    p0 = {}\n{}  end\n",
                        self.emit_node(head),
                        self.emit_chain(steps, fails, service, "    ", Step::Live)
                    ));
                } else if fails {
                    out.push_str(&format!(
                        "  defp __beaml_{name}({params}), do: {{:ok, {}}}\n",
                        self.emit_node(&clause.body)
                    ));
                } else {
                    out.push_str(&format!(
                        "  defp __beaml_{name}({params}), do: {}\n",
                        self.emit_node(&clause.body)
                    ));
                }
            }
        }
        for effect in &self.program.effects {
            out.push_str(&self.emit_effect(effect, service));
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
    // Failure TYPES named in any `!` list; each becomes a nested struct module.
    fn structs(&self) -> BTreeSet<String> {
        let clauses = self.program.clauses.iter().map(|c| &c.failures);
        let effects = self.program.effects.iter().map(|e| &e.failures);
        clauses.chain(effects).flatten().cloned().collect()
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
        fails: bool,
        service: &str,
        indent: &str,
        mode: Step,
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
                    clauses.push(format!(
                        "{{:ok, {output}}} <- @parent.__beaml_attempt__(fn -> ProbeSupport.span({}, :internal, p0, nil, fn -> @parent.__beaml_result_{}(bytes) end) end)",
                        binary(&format!("{service}.{step}")),
                        effect.name.replace('.', "_")
                    ));
                }
                matched = true;
                continue;
            }
            let failing = !self.failures[step].is_empty();
            let call = format!("{owner}.{step}({input})");
            let expression = match (mode, steps.get(index + 1).and_then(|s| self.effect(s))) {
                (Step::Replay, _) => call,
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
        let result = if fails {
            format!("{{:ok, {last}}}")
        } else {
            last
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
        let Node::Pipe(_, steps) = &flow.body else {
            unreachable!()
        };
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
        out.push_str(&format!(
            "  def {decode}(a0) do\n    declared = [{}]\n\n    value =\n      try do\n        :json.decode(a0)\n      rescue\n        _ -> nil\n      end\n\n    shape = if is_map(value), do: Map.take(value, declared), else: nil\n\n    if __beaml_valid__(shape, {output}),\n      do: {{:ok, shape, Enum.sort(Map.keys(Map.drop(value, declared)))}},\n      else: :error\n  end\n",
            declared.join(", "),
            output = binary(&effect.output),
        ));
        out.push_str(&format!(
            "  def __beaml_result_{elixir}(a0) do\n    case {decode}(a0) do\n      {{:ok, value, []}} ->\n        {{:ok, value}}\n\n      {{:ok, value, keys}} ->\n        :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :unknown_keys, keys)\n        {{:ok, value}}\n\n      :error ->\n        __beaml_fail_{elixir}({decode_reason})\n    end\n  end\n  def __beaml_fail_{elixir}(a0) do\n    :otel_span.set_attribute(OpenTelemetry.Tracer.current_span_ctx(), :reason, a0)\n    raise(__MODULE__.BeamlFailure, error: Kernel.struct!(__MODULE__.{failure}, reason: a0))\n  end\n  def __beaml_attempt__(a0) do\n    try do\n      a0.()\n    rescue\n      failure in __MODULE__.BeamlFailure -> {{:error, failure.error}}\n    end\n  end\n",
            decode_reason = binary("decode"),
        ));
        for failure in self.structs() {
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
        out.push_str("  defmodule BeamlFailure do\n    import Kernel\n    defexception [:error]\n\n    @impl true\n    def message(_), do: \"BEAML failure\"\n  end\n");
        out.push_str(HTTP);
        out.push_str(&format!(
            "  defmodule Replay do\n    import Kernel\n    @parent __MODULE__ |> Module.split() |> Enum.drop(-1) |> Module.concat()\n\n    def record(request, status, bytes) do\n      ctx = OpenTelemetry.Tracer.current_span_ctx()\n\n      unknown_keys =\n        case @parent.{decode}(bytes) do\n          {{:ok, _, keys}} -> keys\n          _ -> []\n        end\n\n      ProbeSupport.Capture.write(\"responses\", %{{\n        version: 1,\n        trace_id: OpenTelemetry.Span.hex_trace_id(ctx),\n        client_span_id: OpenTelemetry.Span.hex_span_id(ctx),\n        artifact_id: ProbeSupport.beam_hash(@parent),\n        operation: {operation},\n        attempt: 1,\n        request: request,\n        status: status,\n        body_base64: Base.encode64(bytes),\n        body_length: byte_size(bytes),\n        body_sha256: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower),\n        unknown_keys: unknown_keys\n      }})\n    end\n\n    def run(a0, trace_id, records) do\n      p0 = a0\n{chain}    end\n{REPLAY_HELPERS}  end\n",
            operation = binary(name),
            chain = self.emit_chain(steps, true, service, "      ", Step::Replay),
        ));
        out
    }
}

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

pub fn compile(source: &str) -> Checked<String> {
    compile_service(source, None)
}

// `service` is the source file stem (`orders`). Pipes and EFFECTS name their spans `<service>.<step>`.
pub fn compile_service(source: &str, service: Option<&str>) -> Checked<String> {
    let program = Parser {
        tokens: lex(source)?,
        at: 0,
    }
    .program()?;
    let checker = Checker::new(&program)?;
    checker.validate()?;
    let spans = !program.effects.is_empty()
        || program
            .clauses
            .iter()
            .any(|c| matches!(c.body, Node::Pipe(..)));
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
    Ok(checker.emit(service))
}

fn action(result: &str) {
    // Logging must never prevent compilation. Source text and file paths are not recorded.
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
        writeln!(
            file,
            "{{\"ts\":{ts},\"source\":\"cli\",\"action\":\"compile\",\"target\":\"experiment-0001\",\"result\":\"{result}\"}}"
        )
    })();
}
fn main() {
    let result = (|| -> Checked<()> {
        let args: Vec<_> = std::env::args_os().skip(1).collect();
        if args.len() != 1 {
            return Err("usage: beaml-spike SOURCE.beaml (Elixir source goes to stdout)".into());
        }
        let source = std::fs::read_to_string(&args[0])
            .map_err(|e| format!("cannot read source: {}", e.kind()))?;
        let stem = std::path::Path::new(&args[0])
            .file_stem()
            .and_then(|stem| stem.to_str());
        let code = compile_service(&source, stem)?;
        std::io::stdout()
            .write_all(code.as_bytes())
            .map_err(|e| format!("cannot write output: {}", e.kind()))?;
        Ok(())
    })();
    action(if result.is_ok() { "ok" } else { "error" });
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
            compile("interface Box { text: String } fn bad text: String -> Box = text")
                .unwrap_err()
                .contains("type mismatch")
        );
    }
    #[test]
    fn checks_exact_construction_and_pattern_fields() {
        for (source, error) in [
            (
                "interface Box { text: String } fn bad -> Box = Box {}",
                "missing required field",
            ),
            (
                "interface Box { text: String } fn bad -> Box = Box { text: \"x\", extra: \"x\" }",
                "unknown field",
            ),
            (
                "interface Box { text: String } fn bad Box { extra } -> String = extra",
                "unknown field",
            ),
            (
                "interface Box { text: String } fn bad -> Box = Box { text: \"x\", text: \"y\" }",
                "duplicate name",
            ),
        ] {
            assert!(compile(source).unwrap_err().contains(error), "{source}");
        }
    }
    #[test]
    fn checks_coverage_and_clause_order() {
        let prefix = "interface Box { text: String } enum R { Ok(Box) Error(String) } ";
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
            "interface A { a: A } fn test -> String = \"x\"",
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
            compile("interface A { text: String } interface B { text: String } fn f a: A -> B = a")
                .is_ok()
        );
        assert!(compile("interface A { text: String } interface B { text: String, extra: String } fn f a: A -> B = a").is_err());
    }
    #[test]
    fn coverage_handles_multiple_arguments_and_empty_shapes() {
        assert!(
            compile(
                "fn f \"a\", \"b\" -> String = \"pair\" fn f a: String, b: String -> String = a + b"
            )
            .is_ok()
        );
        assert!(compile("interface Empty {} enum State { Waiting() Done(Empty) } fn f Waiting() -> String = \"wait\" fn f Done(Empty {}) -> String = \"done\"").is_ok());
        assert!(compile("interface Box { text: String } fn f Box {} -> String = \"all\" fn f Box { text: \"a\" } -> String = \"late\"").unwrap_err().contains("unreachable"));
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
}
