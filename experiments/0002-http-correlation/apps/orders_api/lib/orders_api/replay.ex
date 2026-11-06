defmodule OrdersApi.Replay do
  # REPLAY RUN (EXPERIMENT 0003 gate 4): a debug runner outside the router. No transport.
  # Checks the saved response record before decode, then uses the live decode, finish and validation.
  def run(order, trace_id, records) do
    order = ProbeSupport.valid_order!(order)
    request = OrdersBeamlSpike.prepare(order)

    with {:ok, record} <- select(records, trace_id),
         :ok <- expect(record["operation"], "payments.authorize", :operation_mismatch),
         :ok <- expect(record["attempt"], 1, :attempt_mismatch),
         :ok <- expect(record["request"], request, :request_mismatch),
         :ok <- expect(record["status"], 200, :status_mismatch),
         {:ok, bytes} <- body(record) do
      payment =
        bytes
        |> OrdersApi.PaymentHttp.decode()
        |> OrdersBeamlSpike.finish()
        |> ProbeSupport.valid_payment!(order)

      {:ok, payment}
    end
  end

  # Exactly one record for the trace.
  defp select(records, trace_id) do
    case Enum.filter(records, &(&1["trace_id"] == trace_id)) do
      [record] -> {:ok, record}
      _ -> {:error, :missing_response}
    end
  end

  # Strict match: 200.0 is not 200.
  defp expect(value, value, _reason), do: :ok
  defp expect(_value, _expected, reason), do: {:error, reason}

  defp body(%{"body_base64" => text, "body_length" => length, "body_sha256" => sha256})
       when is_binary(text) do
    with {:ok, bytes} <- Base.decode64(text),
         true <- byte_size(bytes) === length,
         true <- Base.encode16(:crypto.hash(:sha256, bytes), case: :lower) === sha256 do
      {:ok, bytes}
    else
      _ -> {:error, :body_digest_mismatch}
    end
  end

  defp body(_record), do: {:error, :body_digest_mismatch}
end
