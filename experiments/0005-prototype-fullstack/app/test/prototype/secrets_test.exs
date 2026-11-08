defmodule Proto.Prototype.SecretsTest do
  # EXPERIMENT 0005 N13 (P5-04, P5-02): no secret in git. Key presence only: a finding prints file and line,
  # never a value. A guard: the scaffold already meets it, GREEN must keep it.
  use ExUnit.Case, async: true

  @app Proto.Prototype.app()

  @tag use_case: "N13"
  test "N13 git holds no database dir, no env file and no secret literal in config" do
    {files, 0} = System.cmd("git", ["ls-files", "."], cd: @app)

    tracked =
      files
      |> String.split("\n", trim: true)
      |> Enum.filter(
        &(&1 =~ ~r{(^|/)(\.pgdata|\.pgsock|\.capture)(/|$)|(^|/)\.env|\.envrc$|secrets\.env$})
      )

    assert tracked == []

    hits =
      for path <- Path.wildcard(Path.join(@app, "config/*.exs")),
          {line, n} <- path |> File.read!() |> String.split("\n") |> Enum.with_index(1),
          line =~ ~r/(secret_key_base|signing_salt|password)\s*:\s*"/,
          do: "#{Path.basename(path)}:#{n}"

    assert hits == []
  end
end
