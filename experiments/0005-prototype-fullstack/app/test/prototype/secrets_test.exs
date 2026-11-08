defmodule Proto.Prototype.SecretsTest do
  # EXPERIMENT 0005 N13 (P5-04, P5-02): no secret in git. Key presence only: a finding prints file and line,
  # never a value. A guard: the scaffold already meets it, GREEN must keep it.
  use ExUnit.Case, async: true

  @app Proto.Prototype.app()

  @tag use_case: "N13"
  test "N13 git holds no database dir, no env file and no secret literal in config or lib" do
    {files, 0} = System.cmd("git", ["ls-files", "."], cd: @app)

    tracked =
      files
      |> String.split("\n", trim: true)
      |> Enum.filter(
        &(&1 =~ ~r{(^|/)(\.pgdata|\.pgsock|\.capture)(/|$)|(^|/)\.env|\.envrc$|secrets\.env$})
      )

    assert tracked == []

    # RED repair O3: config and lib, the `key: "`, `= "` and `@attr "` forms.
    keys = "(secret_key_base|signing_salt|password|token)"
    literal = ~r/#{keys}\s*(:|=)\s*"|@\w*#{keys}\w*\s+"/

    hits =
      for path <-
            Path.wildcard(Path.join(@app, "config/**/*.exs")) ++
              Path.wildcard(Path.join(@app, "lib/**/*.{ex,exs,heex}")),
          {line, n} <- path |> File.read!() |> String.split("\n") |> Enum.with_index(1),
          line =~ literal,
          do: "#{Path.relative_to(path, @app)}:#{n}"

    assert hits == []
  end
end
