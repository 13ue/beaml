defmodule ProbeSupport.LoggerHandler do
  def adding_handler(config), do: {:ok, config}
  def removing_handler(_), do: :ok
  def changing_config(_, old, new), do: {:ok, Map.merge(old, new)}

  def log(%{meta: %{probe_record: %{event: event} = record}}, _)
      when event in ["payment_request_prepared", "payment_stub_returned"] do
    ProbeSupport.Capture.write(
      "logs",
      Map.take(record, [:event, :service, :operation, :order_id, :trace_id, :span_id])
    )

    :ok
  end

  def log(_, _), do: :ok
end
