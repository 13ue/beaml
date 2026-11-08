defmodule Mix.Tasks.Beaml.Stored do
  @shortdoc "Writes the live ROW SNAPSHOT of `records` to DIR (EXPERIMENT 0005, Q5-4 B)"
  @moduledoc """
  `mix beaml.stored DIR` writes `DIR/rows.jsonl` (one ROW CORE per row, plus `source: "db"` and `row_id`),
  an empty `DIR/responses.jsonl` and `DIR/snapshot-meta.json`. It prints no stored value.
  """
  use Mix.Task
  alias Proto.Repo

  @requirements ["app.start"]

  @impl true
  def run([dir]) do
    %{rows: [[query_time, database]]} = Repo.query!("SELECT now(), current_database()")
    rows = Repo.query!("SELECT id, value::text FROM records ORDER BY id").rows

    lines =
      for [id, json] <- rows,
          do: [
            Jason.decode!(json)
            |> Map.merge(%{"source" => "db", "row_id" => id})
            |> Jason.encode!(),
            "\n"
          ]

    ids = Enum.map(rows, &hd/1)

    meta = %{
      table: "records",
      database: database,
      query_time: DateTime.to_iso8601(query_time),
      row_count: length(ids),
      row_ids: ids
    }

    File.mkdir_p!(dir)
    File.write!(Path.join(dir, "rows.jsonl"), lines)
    File.write!(Path.join(dir, "responses.jsonl"), "")
    File.write!(Path.join(dir, "snapshot-meta.json"), Jason.encode!(meta))
  end

  def run(_), do: Mix.raise("usage: mix beaml.stored DIR")
end
