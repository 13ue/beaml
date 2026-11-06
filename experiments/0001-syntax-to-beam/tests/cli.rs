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
        "interface Box { text: String } fn bad -> Box = Box {}",
        "interface Inner { text: String } interface Outer { inner: Inner } fn bad -> Outer = Outer { inner: \"wrong\" }",
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
