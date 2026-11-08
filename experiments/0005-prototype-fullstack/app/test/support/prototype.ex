defmodule Proto.Prototype do
  @moduledoc """
  Helpers of the EXPERIMENT 0005 N-TESTS (RED 2026-11-08, ledger `workflow/2026-11-08/`).

  Expected values come from the plan (`workflow/2026-11-07/plan.md`) and the P4 texts, never from the
  generated module. No helper prints or logs a stored value.
  """
  import ExUnit.Assertions
  alias Proto.Repo

  @app Path.expand("../..", __DIR__)
  @beaml Path.join(@app, "beaml")
  @migrations Path.join(@app, "priv/repo/migrations")

  # N11: the host DDL state of the scaffold (P5-07, scaffold-output.md). A TYPE change never moves it.
  @migration_files [".formatter.exs", "20261107000000_create_records.exs"]
  @columns [
    ["id", "bigint"],
    ["type", "text"],
    ["version", "integer"],
    ["value", "jsonb"],
    ["inserted_at", "timestamp without time zone"]
  ]

  def app, do: @app

  def source(nil), do: Path.join(@beaml, "orders.beaml")
  def source(variant), do: Path.join([@beaml, "variants", variant, "orders.beaml"])

  def good do
    %{
      "order_id" => "order-1",
      "amount" => %{"value" => "12.50", "currency" => "EUR"},
      "channel" => "web"
    }
  end

  def spike do
    System.get_env("BEAML_SPIKE") ||
      flunk("BEAML_SPIKE is not set: run.py builds the compiler and sets it")
  end

  def run_dir do
    System.get_env("BEAML_RUN_DIR") || Path.join(System.tmp_dir!(), "exp0005-test")
  end

  defp fresh(label) do
    dir =
      Path.join([
        run_dir(),
        "n-tests",
        "#{System.unique_integer([:positive, :monotonic])}-#{label}"
      ])

    File.mkdir_p!(dir)
    dir
  end

  @doc "All rows of `records`, read by SQL (not through BEAML): {id, type, version, value map}."
  def rows do
    Repo.query!("SELECT id, type, version, value::text FROM records ORDER BY id").rows
    |> Enum.map(fn [id, type, version, json] -> {id, type, version, Jason.decode!(json)} end)
  end

  def truncate!, do: Repo.query!("TRUNCATE records RESTART IDENTITY")

  # --- capture streams (Q5-7 A) and the action log (P5-13) ------------------------------------

  def capture_file(kind),
    do: Path.join(Application.fetch_env!(:probe_support, :output), kind <> ".jsonl")

  def actions_file, do: Path.expand("../../../../../.beaml/actions.jsonl", __DIR__)

  def mark(path), do: if(File.exists?(path), do: File.stat!(path).size, else: 0)

  def lines_since(path, offset) do
    case File.read(path) do
      {:ok, bytes} when byte_size(bytes) >= offset ->
        bytes |> binary_part(offset, byte_size(bytes) - offset) |> String.split("\n", trim: true)

      _ ->
        []
    end
  end

  def records_since(kind, offset),
    do: kind |> capture_file() |> lines_since(offset) |> Enum.map(&Jason.decode!/1)

  @doc "The offsets of the `entries` and `responses` capture streams, for `through_beaml!/3`."
  def marks, do: {mark(capture_file("entries")), mark(capture_file("responses"))}

  @doc """
  RED repair O1: proves a page action ran through BEAML since `marks`. Every new ENTRY RECORD is ENTRY_OP,
  every new db record is DB_OP, all `accepted` with version 3, and each ENTRY RECORD shares its `trace_id` with
  exactly one db record. A mount may run twice (dead and live render), so pairs are matched, not counted.
  Returns the db records. Asserts compare operations, outcomes and trace ids only.
  """
  def through_beaml!(entry_op, db_op, {entries, responses}) do
    es = records_since("entries", entries)
    ds = records_since("responses", responses)
    assert es != [], "no #{entry_op} ENTRY RECORD: the page did not call the ENTRY LINE"
    assert Enum.uniq(Enum.map(es, & &1["operation"])) == [entry_op]
    assert Enum.uniq(Enum.map(ds, & &1["operation"])) == [db_op]
    assert Enum.uniq(Enum.map(es ++ ds, &{&1["version"], &1["outcome"]})) == [{3, "accepted"}]
    traces = Enum.map(es, & &1["trace_id"])
    assert traces == Enum.uniq(traces) and Enum.all?(traces, &(&1 =~ ~r/\A[0-9a-f]{32}\z/))
    assert Enum.sort(traces) == Enum.sort(Enum.map(ds, & &1["trace_id"]))
    ds
  end

  # --- the live ROW SNAPSHOT (Q5-4 B, P5-19) and the compiler ----------------------------------

  @doc """
  Runs the host task `mix beaml.stored DIR` in this VM (same Repo, a committed connection) and checks the
  snapshot provenance (N8c) at once: the files did not exist before; the row ids and the count equal a fresh
  `psql` read of `records`. Returns the snapshot directory.
  """
  def snapshot!(label) do
    dir = fresh(label)

    for f <- ["rows.jsonl", "responses.jsonl", "snapshot-meta.json"],
        do: refute(File.exists?(Path.join(dir, f)), "N8c: #{f} exists before the snapshot step")

    Mix.Task.rerun("beaml.stored", [dir])
    provenance!(dir)
    dir
  end

  def provenance!(dir) do
    meta = dir |> Path.join("snapshot-meta.json") |> File.read!() |> Jason.decode!()
    ids = psql_ids()

    row_ids =
      dir
      |> Path.join("rows.jsonl")
      |> File.read!()
      |> String.split("\n", trim: true)
      |> Enum.map(&(&1 |> Jason.decode!() |> Map.fetch!("row_id")))

    assert File.read!(Path.join(dir, "responses.jsonl")) == ""

    assert {Enum.sort(Map.keys(meta)), meta["table"], meta["database"], meta["row_count"],
            meta["row_ids"],
            Enum.sort(row_ids)} ==
             {["database", "query_time", "row_count", "row_ids", "table"], "records",
              Repo.config()[:database], length(ids), ids, ids}

    assert {:ok, _, 0} = DateTime.from_iso8601(meta["query_time"])
    :ok
  end

  @doc "The row ids of `records` read by a separate psql process (N8c). Ids only, never values."
  def psql_ids do
    config = Repo.config()

    {out, 0} =
      System.cmd("psql", [
        "-h",
        config[:socket_dir],
        "-U",
        config[:username],
        "-d",
        config[:database],
        "-At",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        "SELECT id FROM records ORDER BY id"
      ])

    out |> String.split("\n", trim: true) |> Enum.map(&String.to_integer/1)
  end

  @doc "beaml-spike SOURCE --stored DIR/responses.jsonl: {exit, stdout, stderr lines}. Both streams kept in DIR."
  def build(variant, dir) do
    err = Path.join(dir, "build.stderr")

    {out, code} =
      System.cmd("sh", [
        "-c",
        ~s("$0" "$1" --stored "$2" 2>"$3"),
        spike(),
        source(variant),
        Path.join(dir, "responses.jsonl"),
        err
      ])

    File.write!(Path.join(dir, "build.stdout"), out)
    {code, out, err |> File.read!() |> String.split("\n", trim: true)}
  end

  def live_build(variant, label) do
    dir = snapshot!(label)
    {code, out, lines} = build(variant, dir)
    {code, out, lines, dir}
  end

  def counted(n, k, m), do: "rows: #{n} rows, #{k} checked, #{m} not decodable"

  # --- N11 ------------------------------------------------------------------------------------

  def assert_no_ddl! do
    files = @migrations |> File.ls!() |> Enum.sort()

    columns =
      Repo.query!(
        "SELECT column_name::text, data_type::text FROM information_schema.columns " <>
          "WHERE table_name = 'records' ORDER BY ordinal_position"
      ).rows

    assert {files, columns} == {@migration_files, @columns}
  end

  # --- N1 and N10: a host build of a copy of app/ with one generated source ---------------------

  @doc """
  Generates VARIANT over a live snapshot into a copy of the host (lib, config, test/support, _build/test
  without the proto app, the same deps) and runs `mix compile --warnings-as-errors` there.
  Returns {compile exit, compile output, generated text}.
  """
  def host_build(variant, label) do
    {code, out, lines, _} = live_build(variant, label)
    assert {code, lines} == {0, [counted(0, 0, 0)]}

    copy = fresh("host-" <> label)

    for f <- ["mix.exs", "mix.lock", ".formatter.exs"],
        do: File.cp!(Path.join(@app, f), Path.join(copy, f))

    for d <- ["config", "lib", "test/support"],
        do: File.cp_r!(Path.join(@app, d), Path.join(copy, d))

    File.cp_r!(Path.join(@app, "_build/test"), Path.join(copy, "_build/test"))

    # Compile proto from clean: --warnings-as-errors only sees files compiled in this run (scaffold note).
    File.rm_rf!(Path.join(copy, "_build/test/lib/proto"))

    probe = Path.expand("../0002-http-correlation/apps/probe_support", Path.dirname(@app))
    mix = File.read!(Path.join(copy, "mix.exs"))
    rel = ~s(path: "../../0002-http-correlation/apps/probe_support")
    assert mix =~ rel
    File.write!(Path.join(copy, "mix.exs"), String.replace(mix, rel, ~s(path: "#{probe}")))

    File.mkdir_p!(Path.join(copy, "lib/generated"))
    File.write!(Path.join(copy, "lib/generated/orders.ex"), out)

    {output, exit} =
      System.cmd("mix", ["compile", "--warnings-as-errors"],
        cd: copy,
        env: [{"MIX_ENV", "test"}, {"MIX_DEPS_PATH", Path.join(@app, "deps")}],
        stderr_to_stdout: true
      )

    File.write!(Path.join(copy, "compile.output"), output)
    {exit, output, out}
  end
end
