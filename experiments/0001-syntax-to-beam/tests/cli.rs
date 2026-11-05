use std::{
    fs,
    process::Command,
    time::{SystemTime, UNIX_EPOCH},
};

#[test]
fn invalid_source_emits_no_code_and_actions_do_not_capture_source() {
    let folder = std::env::temp_dir().join(format!(
        "beaml-cli-{}-{}",
        std::process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&folder).unwrap();
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
