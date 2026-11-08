defmodule Proto.Prototype.GuardTest do
  # RED re-check R1 (red-review.md): the pages render only from BEAML values, never from SQL. No use_case tag: a
  # guard in phase A, outside the 20 EXPECTED pairs of run.py.
  use ExUnit.Case, async: true

  test "R1 lib/proto_web holds no Repo call and no records table name" do
    hits =
      for path <-
            Path.wildcard(Path.join(Proto.Prototype.app(), "lib/proto_web/**/*.{ex,exs,heex}")),
          {line, n} <- path |> File.read!() |> String.split("\n") |> Enum.with_index(1),
          line =~ ~r/Repo\.|"records"/,
          do: "#{Path.relative_to(path, Proto.Prototype.app())}:#{n}"

    assert hits == []
  end
end
