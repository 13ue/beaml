defmodule ProbeSupport.Exporter do
  @behaviour :otel_exporter_traces
  require Record
  Record.defrecordp(:span, Record.extract(:span, from_lib: "opentelemetry/include/otel_span.hrl"))
  def init(_), do: {:ok, nil}
  def shutdown(_), do: :ok

  def export(table, _, _) do
    :ets.foldl(
      fn row, _ ->
        ProbeSupport.Capture.write("spans", %{
          trace_id: hex(span(row, :trace_id), 32),
          span_id: hex(span(row, :span_id), 16),
          parent_span_id: hex(span(row, :parent_span_id), 16),
          parent_remote: span(row, :parent_span_is_remote) == true,
          name: span(row, :name),
          kind: span(row, :kind),
          service: ProbeSupport.config(:service),
          ended: is_integer(span(row, :end_time)),
          start_time: span(row, :start_time),
          end_time: span(row, :end_time),
          start_time_unix_nano: unix_nano(span(row, :start_time)),
          end_time_unix_nano: unix_nano(span(row, :end_time)),
          attributes: :otel_attributes.map(span(row, :attributes))
        })
      end,
      :ok,
      table
    )

    :ok
  catch
    _, _ -> :error
  end

  # Wall-clock conversion in this VM, so a run window can bind the monotonic span times.
  defp unix_nano(time) when is_integer(time), do: :opentelemetry.timestamp_to_nano(time)
  defp unix_nano(_), do: :null

  defp hex(:undefined, _), do: :null

  defp hex(value, size),
    do: value |> Integer.to_string(16) |> String.downcase() |> String.pad_leading(size, "0")
end
