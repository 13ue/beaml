defmodule BeamlDb do
  @moduledoc """
  EXPERIMENT 0005 host store (Q5-8 A, PDB-30): the generated DB TRANSPORTS call it. One table `records`, no Ecto
  schema (DL-127). JSON binaries in and out: the record core goes in as given and comes back as `value::text`.
  Only the table "records" exists; any other name raises, and generated code maps that to `transport`.
  """
  alias Proto.Repo

  @row "SELECT id, version, value::text FROM records WHERE type = $1"

  def put("records", {type, version}, json) when is_binary(json) do
    sql =
      "INSERT INTO records (type, version, value) VALUES ($1, $2, $3::text::jsonb) RETURNING id"

    with {:ok, %{rows: [[id]]}} <- Repo.query(sql, [type, version, json]), do: {:ok, id}
  end

  # Q5-2 A: order and limit are fixed here, newest first.
  def list("records", type, _query) do
    with {:ok, %{rows: rows}} <-
           Repo.query(@row <> " ORDER BY inserted_at DESC, id DESC LIMIT 100", [type]),
         do: {:ok, Enum.map(rows, &out/1)}
  end

  # Q5-1 B: the key is a map of domain fields; the newest matching row wins (QDB-3 A). Not found: {:ok, nil}.
  def get("records", type, key) when is_map(key) do
    sql =
      @row <> " AND value->'value' @> $2::text::jsonb ORDER BY inserted_at DESC, id DESC LIMIT 1"

    with {:ok, %{rows: rows}} <- Repo.query(sql, [type, IO.iodata_to_binary(:json.encode(key))]),
         do: {:ok, Enum.map(rows, &out/1) |> List.first()}
  end

  defp out([id, version, value]), do: %{"id" => id, "version" => version, "value" => value}
end
