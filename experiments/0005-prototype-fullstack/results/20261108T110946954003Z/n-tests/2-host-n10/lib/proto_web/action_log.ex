defmodule ProtoWeb.ActionLog do
  @moduledoc """
  One action event per page action (P5-13) to `<repo>/.beaml/actions.jsonl`. Never a form value, a path or
  source text: only the UI EVENT name, the page, the result and the key count. Logging never raises.
  """
  @file_path Path.expand("../../../../../.beaml/actions.jsonl", __DIR__)

  def log(action, target, result, params \\ %{}) do
    # ponytail: ts in whole seconds, so no fraction can echo a form value such as "12.50" (N12).
    line =
      Jason.encode!(%{
        ts: DateTime.utc_now() |> DateTime.truncate(:second) |> DateTime.to_iso8601(),
        source: "ui",
        action: action,
        target: target,
        result: result,
        keys: if(is_map(params), do: map_size(params), else: 0)
      })

    File.mkdir_p(Path.dirname(@file_path))
    File.write(@file_path, line <> "\n", [:append])
  rescue
    _ -> :error
  end

  @doc "The action result of an ENTRY LINE call: ok, rejected:<reason> or store_error."
  def result({:ok, _}), do: "ok"
  def result({:error, %Orders.Rejected{reason: r}}), do: "rejected:" <> r
  def result({:error, _}), do: "store_error"

  @doc "The flash text of a failed ENTRY LINE call (P5-12). The reason is a BEAML word, never a value."
  def message(%Orders.Rejected{reason: r}), do: "form rejected: " <> r
  def message(%Orders.StoreError{reason: r}), do: "store failed: " <> r
end
