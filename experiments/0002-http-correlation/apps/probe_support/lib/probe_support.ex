defmodule ProbeSupport do
  require Logger
  def config(key), do: Application.fetch_env!(:probe_support, key)
  def json(value), do: value |> :json.encode() |> IO.iodata_to_binary()

  def setup do
    {:otel_tracer_default, _} = :opentelemetry.get_tracer(:beaml_probe)
    :persistent_term.put(:probe_count, :atomics.new(1, []))
    :logger.add_handler(:probe_json, ProbeSupport.LoggerHandler, %{})
  end

  def count, do: :atomics.get(:persistent_term.get(:probe_count), 1)
  def increment, do: :atomics.add_get(:persistent_term.get(:probe_count), 1, 1)

  # shortcut: fixed release files, verify the loaded object if hot upgrades are added.
  def beam_hash(module) do
    beam = File.read!(:code.which(module))
    Base.encode16(:crypto.hash(:sha256, beam), case: :lower)
  end

  def body(conn) do
    case Plug.Conn.read_body(conn, length: 1024, read_length: 1024, read_timeout: 2000) do
      {:ok, bytes, conn} -> {:json.decode(bytes), conn}
      _ -> raise ArgumentError
    end
  end

  def reply(conn, status, value),
    do:
      conn
      |> Plug.Conn.put_resp_content_type("application/json")
      |> Plug.Conn.send_resp(status, json(value))

  def valid_order!(%{"order_id" => "order-1"} = order) when map_size(order) == 1, do: order
  def valid_order!(_), do: raise(ArgumentError)

  def valid_payment!(value, order) do
    unless value == %{"order_id" => order["order_id"], "status" => "authorized"},
      do: raise(ArgumentError)

    value
  end

  def span(name, kind, order, function, fun) do
    attrs = %{order_id: order["order_id"]}

    attrs =
      if function do
        service = config(:service)

        file =
          Path.join(
            :code.priv_dir(String.to_existing_atom(service <> "_api")),
            service <> ".beaml"
          )

        Map.merge(attrs, %{
          source: "apps/#{service}_api/priv/#{service}.beaml",
          source_hash: Base.encode16(:crypto.hash(:sha256, File.read!(file)), case: :lower),
          function: function
        })
      else
        attrs
      end

    :otel_tracer.with_span(
      :opentelemetry.get_tracer(:beaml_probe),
      name,
      %{kind: kind, attributes: attrs},
      fn ctx ->
        try do
          result = fun.()
          :otel_span.set_attribute(ctx, :outcome, "ok")
          :otel_span.set_status(ctx, :ok)
          result
        rescue
          error ->
            :otel_span.set_attribute(ctx, :outcome, "error")
            :otel_span.set_status(ctx, :error)
            reraise error, __STACKTRACE__
        end
      end
    )
  end

  def event(event, operation) do
    ctx = OpenTelemetry.Tracer.current_span_ctx()

    Logger.info("probe observation",
      probe_record: %{
        event: event,
        operation: operation,
        service: config(:service),
        order_id: "order-1",
        trace_id: OpenTelemetry.Span.hex_trace_id(ctx),
        span_id: OpenTelemetry.Span.hex_span_id(ctx)
      }
    )
  end

  def control(conn) do
    Logger.flush()
    :otel_tracer_provider.force_flush()
    sibling = if config(:service) == "orders", do: :payments_api, else: :orders_api
    own_module = if config(:service) == "orders", do: OrdersApi.Router, else: PaymentsApi.Router

    own_generated =
      if config(:service) == "orders", do: OrdersBeamlSpike, else: PaymentsBeamlSpike

    sibling_module =
      if config(:service) == "orders", do: PaymentsApi.Router, else: OrdersApi.Router

    sibling_generated =
      if config(:service) == "orders", do: PaymentsBeamlSpike, else: OrdersBeamlSpike

    reply(conn, 200, %{
      count: count(),
      capture: ProbeSupport.Capture.status(),
      pid: System.pid(),
      node: Atom.to_string(node()),
      applications:
        Enum.map(Application.started_applications(), fn {app, _, _} -> Atom.to_string(app) end),
      sibling_available:
        :code.which(sibling_module) != :non_existing or
          :code.which(sibling_generated) != :non_existing,
      sibling_loaded: :code.is_loaded(sibling_module) != false,
      own_loaded: :code.is_loaded(own_module) != false,
      sibling: sibling,
      beam_hash: beam_hash(own_generated),
      listener: "127.0.0.1"
    })
  end
end
