defmodule ReplayLib do
  # Comparison arm LIB (EXPERIMENT 0004): record and replay one EFFECT from a descriptor map.
  # Whole values: the whole request and the whole body bytes. The caller validates domain values.
  defmodule Error, do: defstruct([:step, :reason])

  # RESPONSE RECORD format version 1, predecode. The capture store bounds it and reports loss.
  def record(d, request, status, bytes) do
    ctx = OpenTelemetry.Tracer.current_span_ctx()

    ProbeSupport.Capture.write("responses", %{
      version: 1, trace_id: OpenTelemetry.Span.hex_trace_id(ctx), client_span_id: OpenTelemetry.Span.hex_span_id(ctx),
      artifact_id: ProbeSupport.beam_hash(d.artifact), operation: d.operation, attempt: d.attempt,
      request: request, status: status, body_base64: Base.encode64(bytes), body_length: byte_size(bytes),
      body_sha256: digest(bytes)
    })
  end

  # REPLAY RUN: {:ok, value} or {:error, reason}. The six 0003 checks in the 0003 order, then decode and finish.
  def run(d, order, trace_id, records) do
    request = d.request.(order)

    with {:ok, record} <- select(List.wrap(records), trace_id),
         :ok <- expect(record["operation"], d.operation, :operation_mismatch),
         :ok <- expect(record["attempt"], d.attempt, :attempt_mismatch),
         :ok <- expect(record["request"], request, :request_mismatch),
         :ok <- expect(record["status"], d.code, :status_mismatch),
         {:ok, bytes} <- body(record),
         {:ok, decoded} <- step("decode", d.decode, bytes),
         do: step("finish", d.finish, decoded)
  end

  # One rescue for decode and finish: a typed error, never a raise.
  defp step(name, fun, value) do
    {:ok, fun.(value)}
  rescue
    error -> {:error, %Error{step: name, reason: inspect(error.__struct__)}}
  catch
    kind, _ -> {:error, %Error{step: name, reason: Atom.to_string(kind)}}
  end

  # Exactly one record for the trace. Strict match: 200.0 is not 200.
  defp select(records, id) do
    case Enum.filter(records, &(is_map(&1) and &1["trace_id"] == id)) do
      [record] -> {:ok, record}
      _ -> {:error, :missing_response}
    end
  end

  defp expect(value, value, _reason), do: :ok
  defp expect(_value, _expected, reason), do: {:error, reason}
  defp digest(bytes), do: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower)

  defp body(%{"body_base64" => text, "body_length" => length, "body_sha256" => sha256}) when is_binary(text) do
    with {:ok, bytes} <- Base.decode64(text), true <- byte_size(bytes) === length, true <- digest(bytes) === sha256,
         do: {:ok, bytes}, else: (_ -> {:error, :body_digest_mismatch})
  end

  defp body(_record), do: {:error, :body_digest_mismatch}
end
