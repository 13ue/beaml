use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
    time::{SystemTime, UNIX_EPOCH},
};

fn temporary_folder() -> PathBuf {
    let folder = std::env::temp_dir().join(format!(
        "beaml-cli-{}-{}",
        std::process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&folder).unwrap();
    folder
}

#[test]
fn payments_cli_emits_checked_authorize_reference() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let fixture =
        root.join("experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml");
    let source = fs::read_to_string(&fixture).unwrap();
    let declaration = source.find("\nfn authorize ").unwrap() + 1;
    let end = source.trim_end().len();

    let prefix = "// Prüfung\n";
    let folder = temporary_folder();
    let variant = folder.join("payments-with-comments.beaml");
    fs::write(
        &variant,
        format!("{prefix}{}  // after declaration\n", source.trim_end()),
    )
    .unwrap();
    let outputs = [&fixture, &variant].map(|path| {
        Command::new(env!("CARGO_BIN_EXE_beaml-spike"))
            .arg(path)
            .current_dir(&root)
            .output()
            .unwrap()
    });
    fs::remove_dir_all(folder).unwrap();

    let generated = outputs.map(|result| {
        assert!(
            result.status.success(),
            "{}",
            String::from_utf8_lossy(&result.stderr)
        );
        let stdout = String::from_utf8(result.stdout).unwrap();
        assert!(stdout.contains("  def authorize("));
        assert!(stdout.contains("  defp __beaml_authorize("));
        stdout
    });
    for (stdout, offset) in generated.iter().zip([0, prefix.len()]) {
        let references: Vec<_> = stdout
            .lines()
            .filter_map(|line| {
                line.trim()
                    .strip_prefix("# beaml-declaration-v1 authorize ")
            })
            .collect();
        let expected = format!("{} {}", declaration + offset, end + offset);
        assert_eq!(
            references,
            [expected.as_str()],
            "checked authorize byte range"
        );
    }
}

#[test]
fn invalid_source_emits_no_code_and_actions_do_not_capture_source() {
    let folder = temporary_folder();
    let source = folder.join("input.beaml");
    for text in [
        "type Box { text: String } fn bad -> Box = Box {}",
        "type Inner { text: String } type Outer { inner: Inner } fn bad -> Outer = Outer { inner: \"wrong\" }",
        "enum R { Ok(String) Error(String) } fn f Ok(x) -> String = x",
        "fn f x: String -> String = x fn f \"late\" -> String = \"late\"",
        "fn f a: String, b: String -> String = a fn sample -> String = f(\"one\")",
    ] {
        fs::write(&source, text).unwrap();
        let result = Command::new(env!("CARGO_BIN_EXE_beaml-spike"))
            .arg(&source)
            .current_dir(&folder)
            .output()
            .unwrap();
        assert!(!result.status.success(), "{text}");
        assert!(result.stdout.is_empty());
        assert!(!result.stderr.is_empty());
    }
    let log = fs::read_to_string(folder.join(".beaml/actions.jsonl")).unwrap();
    assert_eq!(log.lines().count(), 5);
    assert!(!log.contains("wrong") && !log.contains("input.beaml"));
    fs::remove_dir_all(folder).unwrap();
}

// EXPERIMENT 0004 slice 1, cases (a) and (b). Fixtures live in experiments/0004-generated-replay.
// RED written 2026-11-06 before any compiler change (implement-step, Solve / RED).

fn repository() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn slice_one(relative: &str) -> PathBuf {
    repository()
        .join("experiments/0004-generated-replay")
        .join(relative)
}

fn compile_file(path: &Path) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_beaml-spike"))
        .arg(path)
        .current_dir(repository())
        .output()
        .unwrap()
}

/// The emitter writes BEAML strings as byte lists. Accept the plain text or that form.
fn mentions(stdout: &str, text: &str) -> bool {
    let bytes = text.bytes().map(|b| b.to_string()).collect::<Vec<_>>();
    stdout.contains(text)
        || stdout.contains(&format!("<<{}>>", bytes.join(",")))
        || stdout.contains(&format!("<<{}>>", bytes.join(", ")))
}

/// Argument count of the first `def NAME(` line, or None when the function is absent.
fn arity(stdout: &str, name: &str) -> Option<usize> {
    head_arity(stdout, &format!("def {name}("))
}

/// Argument count of the first line that starts with `head` (for example `defp NAME(`).
fn head_arity(stdout: &str, head: &str) -> Option<usize> {
    let line = stdout
        .lines()
        .find(|line| line.trim_start().starts_with(head))?;
    let start = line.find(head).unwrap() + head.len();
    let mut depth = 1;
    let mut count = 1;
    let mut empty = true;
    for ch in line[start..].chars() {
        match ch {
            '(' | '{' | '[' => depth += 1,
            ')' | '}' | ']' => {
                depth -= 1;
                if depth == 0 {
                    break;
                }
            }
            ',' if depth == 1 => count += 1,
            c if !c.is_whitespace() => empty = false,
            _ => {}
        }
    }
    Some(if empty { 0 } else { count })
}

/// EXPERIMENT 0004 slice 2, case C10: a source with an `effect` needs a RECORD SNAPSHOT.
/// The slice 1 tests pass the empty snapshot, so their slice 1 outcomes stay.
fn empty_snapshot() -> PathBuf {
    slice_one("stored/empty.jsonl")
}

fn compile_stored(path: &Path, stored: &Path) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_beaml-spike"))
        .arg(path)
        .arg("--stored")
        .arg(stored)
        .current_dir(repository())
        .output()
        .unwrap()
}

fn assert_compiles_stored(path: &Path) -> String {
    let result = compile_stored(path, &empty_snapshot());
    assert!(
        result.status.success(),
        "expected exit 0 for {} with --stored {}; stderr: {}",
        path.display(),
        empty_snapshot().display(),
        String::from_utf8_lossy(&result.stderr)
    );
    String::from_utf8(result.stdout).unwrap()
}

fn assert_compiles(path: &Path) -> String {
    let result = compile_file(path);
    assert!(
        result.status.success(),
        "expected exit 0 for {}; stderr: {}",
        path.display(),
        String::from_utf8_lossy(&result.stderr)
    );
    String::from_utf8(result.stdout).unwrap()
}

fn assert_rejected(fixture: &str, names: &[&str]) {
    let result = compile_file(&slice_one(fixture));
    let stderr = String::from_utf8_lossy(&result.stderr).to_string();
    assert!(!result.status.success(), "{fixture}: expected exit != 0");
    assert!(result.stdout.is_empty(), "{fixture}: expected no stdout");
    // The new syntax must parse. The reject must come from the check, not from the old parser.
    assert!(
        !stderr.contains("expected type, enum, effect, migrate, retire or fn"),
        "{fixture}: rejected by the old parser, not by the check: {stderr}"
    );
    for name in names {
        assert!(
            stderr.contains(name),
            "{fixture}: message must name {name}; actual: {stderr}"
        );
    }
}

#[test]
fn orders_cli_accepts_effect_pipe_place() {
    let stdout = assert_compiles_stored(&slice_one("arms/gen/orders.beaml"));
    assert!(stdout.contains("  def place("), "expected def place(");
}

#[test]
fn orders_cli_rejects_unknown_pipe_step() {
    assert_rejected("bad/unknown_pipe_step.beaml", &["charge"]);
}

#[test]
fn orders_cli_rejects_pipe_type_mismatch() {
    assert_rejected(
        "bad/pipe_type_mismatch.beaml",
        &["finish", "Order", "Payment"],
    );
}

#[test]
fn orders_cli_rejects_undeclared_pipe_failure() {
    assert_rejected(
        "bad/undeclared_failure.beaml",
        &["payments.authorize", "PaymentError"],
    );
}

#[test]
fn orders_cli_rejects_field_not_in_type() {
    assert_rejected("bad/field_not_in_type.beaml", &["amount", "Payment"]);
}

#[test]
fn orders_cli_rejects_unsupported_effect_kind() {
    assert_rejected("bad/unsupported_effect_kind.beaml", &["db.get"]);
}

#[test]
fn orders_cli_emits_flow_effect_decode_and_replay() {
    let fixture = slice_one("arms/gen/orders.beaml");
    let source = fs::read_to_string(&fixture).unwrap();
    let stdout = assert_compiles_stored(&fixture);
    let mut missing = Vec::new();
    // One module: 0002 run.py and the 0003 tests rename exactly one `defmodule BeamlSpike do`.
    if stdout.matches("defmodule BeamlSpike do").count() != 1 {
        missing.push("one defmodule BeamlSpike".to_string());
    }
    for (name, expected) in [
        ("place", 1),
        ("payments_authorize", 1),
        ("record", 3),
        ("run", 3),
    ] {
        if arity(&stdout, name) != Some(expected) {
            missing.push(format!("def {name}/{expected}"));
        }
    }
    // The typed decode has a fixed name and takes one argument (review objection 1).
    if decode_heads()
        .iter()
        .all(|head| head_arity(&stdout, head) != Some(1))
    {
        missing.push(format!("def(p) {DECODE}/1"));
    }
    for text in [
        "defmodule PaymentError do",
        "defstruct",
        "defmodule Replay do",
        ":json.decode(",
    ] {
        if !stdout.contains(text) {
            missing.push(text.to_string());
        }
    }
    // The EFFECT span `<service>.<step>` and the kept Orders log under orders.request (DL-119: pure steps have no span).
    for text in [
        "orders.payments.authorize",
        "payment_request_prepared",
        "payments/authorize",
    ] {
        if !mentions(&stdout, text) {
            missing.push(format!("mentions {text}"));
        }
    }
    // One beaml-declaration-v1 comment per callable declaration, with its exact source range.
    let mut references: Vec<(String, String)> = stdout
        .lines()
        .filter_map(|line| line.trim().strip_prefix("# beaml-declaration-v1 "))
        .map(|rest| {
            let parts: Vec<_> = rest.split(' ').collect();
            let (start, end): (usize, usize) =
                (parts[1].parse().unwrap(), parts[2].parse().unwrap());
            let head = source
                .get(start..end)
                .unwrap_or("")
                .split_whitespace()
                .take(2)
                .collect::<Vec<_>>()
                .join(" ");
            (parts[0].to_string(), head)
        })
        .collect();
    references.sort();
    let expected: Vec<(String, String)> = [
        ("finish", "fn finish"),
        ("payments.authorize", "effect payments.authorize"),
        ("place", "fn place"),
        ("prepare", "fn prepare"),
    ]
    .iter()
    .map(|(a, b)| (a.to_string(), b.to_string()))
    .collect();
    if references != expected {
        missing.push(format!("declaration references {references:?}"));
    }
    assert!(
        missing.is_empty(),
        "missing in generated module: {missing:?}"
    );
}

/// The generated typed decode of the TYPE `Payment` has this fixed name (RED repair, review objection 1).
const DECODE: &str = "__beaml_decode_payment";

fn decode_heads() -> [String; 2] {
    [format!("def {DECODE}("), format!("defp {DECODE}(")]
}

/// Source of the generated decode only: from its first head line to its last clause `end`.
/// The slice stops at the first other line with the same or a smaller indentation.
fn decode_body(stdout: &str) -> Option<String> {
    let heads = decode_heads();
    let is_head = |text: &str| heads.iter().any(|head| text.starts_with(head.as_str()));
    let indent = |line: &str| line.len() - line.trim_start().len();
    let lines: Vec<&str> = stdout.lines().collect();
    let start = lines.iter().position(|line| is_head(line.trim_start()))?;
    let level = indent(lines[start]);
    let mut body = vec![lines[start]];
    for line in &lines[start + 1..] {
        let text = line.trim_start();
        if !text.is_empty() {
            if indent(line) < level {
                break;
            }
            if indent(line) == level && text != "end" && !is_head(text) {
                break;
            }
        }
        body.push(line);
    }
    Some(body.join("\n"))
}

fn assert_decode_names(label: &str, stdout: &str, present: &[&str], absent: &[&str]) {
    let body = decode_body(stdout)
        .unwrap_or_else(|| panic!("{label}: no generated decode `def(p) {DECODE}(`"));
    for name in present {
        assert!(
            mentions(&body, name),
            "{label}: decode body must name {name}: {body}"
        );
    }
    for name in absent {
        assert!(
            !mentions(&body, name),
            "{label}: decode body must not name {name}: {body}"
        );
    }
}

#[test]
fn orders_cli_template_control_drift_r_decode_names_reference() {
    // A template emitter does not see the new Payment field. A derived decode does.
    // The names are checked inside the decode only: `finish/1` and `__beaml_valid__`
    // name every field anyway (review objection 1).
    let base = assert_compiles_stored(&slice_one("arms/gen/orders.beaml"));
    let drift = assert_compiles_stored(&slice_one("drift/R/orders.beaml"));
    assert!(
        !mentions(&base, "reference"),
        "base output must not name reference"
    );
    assert_decode_names("base", &base, &["order_id", "status"], &["reference"]);
    assert_decode_names("DRIFT-R", &drift, &["order_id", "status", "reference"], &[]);
}

#[test]
fn orders_cli_template_control_drift_n_decode_follows_field_rename() {
    // DRIFT-N renames the Payment field `status` to `state`. The decode must follow the TYPE.
    let base = assert_compiles_stored(&slice_one("arms/gen/orders.beaml"));
    let drift = assert_compiles_stored(&slice_one("drift/N/orders.beaml"));
    assert_decode_names("base", &base, &["order_id", "status"], &["state"]);
    assert_decode_names("DRIFT-N", &drift, &["order_id", "state"], &["status"]);
}

#[test]
fn payments_cli_output_stays_byte_identical() {
    // Guard, not RED: the slice 1 compiler change must not change the payments.beaml output.
    let fixture = repository()
        .join("experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml");
    let expected = fs::read_to_string(slice_one("tests/payments.generated.snapshot")).unwrap();
    assert_eq!(assert_compiles(&fixture), expected);
}

// EXPERIMENT 0004 slice 2 (README revision 6). The snapshot-dependent cases are in
// experiments/0004-generated-replay/tests/stored_types_test.py.

#[test]
fn orders_cli_effect_source_without_stored_is_rejected() {
    // C8: an unknown store is not an empty store (OWNER answer O2).
    let result = compile_file(&slice_one("arms/gen/orders.beaml"));
    let stderr = String::from_utf8_lossy(&result.stderr).to_string();
    assert!(!result.status.success(), "C8: expected exit != 0");
    assert!(result.stdout.is_empty(), "C8: expected no stdout");
    assert!(
        stderr.contains("stored TYPE VERSIONS unknown"),
        "C8: message must say stored TYPE VERSIONS unknown; actual: {stderr}"
    );
}

#[test]
fn orders_cli_parse_and_type_errors_come_before_stored_check() {
    // C16: guard. The pipe check names `charge`; the missing `--stored` input is not reported.
    let result = compile_file(&slice_one("bad/unknown_pipe_step.beaml"));
    let stderr = String::from_utf8_lossy(&result.stderr).to_string();
    assert!(!result.status.success(), "C16: expected exit != 0");
    assert!(
        stderr.contains("charge"),
        "C16: message must name charge: {stderr}"
    );
    assert!(
        !stderr.contains("stored TYPE VERSIONS unknown"),
        "C16: the stored check must come after the pipe check: {stderr}"
    );
}
