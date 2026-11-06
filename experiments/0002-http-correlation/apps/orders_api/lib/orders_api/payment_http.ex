defmodule OrdersApi.PaymentHttp do
  def authorize(request, carrier) do
    port = ProbeSupport.config(:payments_port)
    body = ProbeSupport.json(request)
    headers = Enum.map(carrier, fn {key, value} -> [key, ": ", value, "\r\n"] end)
    # Transport observer: count every entry, also when connect fails.
    ProbeSupport.increment()

    {:ok, socket} =
      :gen_tcp.connect(
        {127, 0, 0, 1},
        port,
        [:binary, active: false, packet: :http_bin, packet_size: 8192, send_timeout: 1000],
        1000
      )

    try do
      :ok =
        :gen_tcp.send(socket, [
          "POST /payments/authorize HTTP/1.1\r\n",
          "Host: 127.0.0.1:#{port}\r\n",
          "Connection: close\r\n",
          "Content-Type: application/json\r\n",
          "Content-Length: #{byte_size(body)}\r\n",
          headers,
          "\r\n",
          body
        ])

      deadline = System.monotonic_time(:millisecond) + 2000
      {:ok, {:http_response, {1, minor}, 200, _}} = recv(socket, 0, deadline)
      true = minor in [0, 1]
      :ok = :inet.setopts(socket, packet: :httph_bin)

      # shortcut: accept only the bounded Content-Length response, extend if Payments changes framing
      length = content_length(socket, deadline, 32, nil)
      :ok = :inet.setopts(socket, packet: :raw)
      {:ok, bytes} = recv(socket, length, deadline)
      capture(request, 200, bytes)
      decode(bytes)
    after
      :gen_tcp.close(socket)
    end
  end

  # Shared decode of the response bytes: live authorize/2 and OrdersApi.Replay.run/3 (review A2).
  def decode(bytes), do: :json.decode(bytes)

  # Predecode response record. The capture store bounds it and reports loss.
  defp capture(request, status, bytes) do
    ctx = OpenTelemetry.Tracer.current_span_ctx()

    ProbeSupport.Capture.write("responses", %{
      version: 1,
      trace_id: OpenTelemetry.Span.hex_trace_id(ctx),
      client_span_id: OpenTelemetry.Span.hex_span_id(ctx),
      artifact_id: ProbeSupport.beam_hash(OrdersBeamlSpike),
      operation: "payments.authorize",
      attempt: 1,
      request: request,
      status: status,
      body_base64: Base.encode64(bytes),
      body_length: byte_size(bytes),
      body_sha256: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower)
    })
  end

  defp content_length(socket, deadline, remaining, length) when remaining >= 0 do
    case recv(socket, 0, deadline) do
      {:ok, :http_eoh} when is_integer(length) ->
        length

      {:ok, {:http_header, _, :"Content-Length", _, <<first, _::binary>> = value}}
      when is_nil(length) and first in ?0..?9 ->
        {size, ""} = Integer.parse(value)
        true = size in 1..1024
        content_length(socket, deadline, remaining - 1, size)

      {:ok, {:http_header, _, name, _, _}}
      when name not in [:"Content-Length", :"Transfer-Encoding"] ->
        content_length(socket, deadline, remaining - 1, length)

      _ ->
        raise ArgumentError
    end
  end

  defp recv(socket, length, deadline) do
    timeout = deadline - System.monotonic_time(:millisecond)
    true = timeout > 0
    :gen_tcp.recv(socket, length, timeout)
  end
end
