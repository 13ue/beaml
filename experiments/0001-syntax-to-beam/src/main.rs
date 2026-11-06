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
                while chars
                    .peek()
                    .is_some_and(|(_, c)| c.is_ascii_alphanumeric() || *c == '_')
                {
                    word.push(chars.next().unwrap().1);
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
            '{' | '}' | '(' | ')' | ':' | ',' | '=' | '+' => Token::Symbol(ch),
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
    body: Node,
    source_range: Range<usize>,
}
#[derive(Default)]
struct Program {
    types: BTreeMap<String, Definition>,
    clauses: Vec<Clause>,
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
        if let Token::Word(word) = self.peek().clone() {
            self.at += 1;
            Ok(word)
        } else {
            Err(self.error("expected identifier"))
        }
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
                    if self.peek() != &Token::Arrow {
                        return Err(self.error("expected '->'"));
                    }
                    self.at += 1;
                    let output = self.word()?;
                    self.expect('=')?;
                    let body = self.node(0)?;
                    program.clauses.push(Clause {
                        name,
                        args,
                        output,
                        body,
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
            let signature = (args, clause.output.clone());
            if let Some(previous) = checker
                .signatures
                .insert(clause.name.clone(), signature.clone())
                && previous != signature
            {
                return Err(format!("inconsistent function signature: {}", clause.name));
            }
        }
        Ok(checker)
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
            Node::Plus(_, _) => return Err("expressions are not patterns".into()),
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
                self.require_type(&self.expression(&clause.body, &vars)?, &clause.output)?;
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
    fn emit(&self) -> String {
        let mut out = String::from(
            "# Generated by experiment 0001. Not a stable ABI.\ndefmodule BeamlSpike do\n  import Kernel, only: [and: 2, is_binary: 1, is_map: 1, map_size: 1, ==: 2, <>: 2, if: 2, raise: 2, def: 2, defp: 2]\n",
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
            out.push_str(&format!("  def {name}({}) do\n    if {} do\n      result = __beaml_{name}({})\n      if __beaml_valid__(result, {}), do: result, else: raise(ArgumentError, \"invalid BEAML output\")\n    else\n      raise ArgumentError, \"invalid BEAML input\"\n    end\n  end\n", args.join(", "), if checks.is_empty() { "true".into() } else { checks.join(" and ") }, args.join(", "), binary(output)));
            for clause in self.program.clauses.iter().filter(|c| &c.name == name) {
                out.push_str(&format!(
                    "  # beaml-declaration-v1 {name} {} {}\n",
                    clause.source_range.start, clause.source_range.end
                ));
                let mut used = BTreeSet::new();
                referenced_names(&clause.body, &mut used);
                out.push_str(&format!(
                    "  defp __beaml_{name}({}), do: {}\n",
                    clause
                        .args
                        .iter()
                        .map(|n| self.emit_node(&omit_unused(n, &used)))
                        .collect::<Vec<_>>()
                        .join(", "),
                    self.emit_node(&clause.body)
                ));
            }
        }
        out.push_str("end\n");
        out
    }
}

pub fn compile(source: &str) -> Checked<String> {
    let program = Parser {
        tokens: lex(source)?,
        at: 0,
    }
    .program()?;
    let checker = Checker::new(&program)?;
    checker.validate()?;
    Ok(checker.emit())
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
        let code = compile(&source)?;
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
