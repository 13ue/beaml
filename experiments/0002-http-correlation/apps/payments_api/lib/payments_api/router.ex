defmodule PaymentsApi.Router do
  use Plug.Router
  plug(:match)
  plug(:dispatch)
  get("/control", do: ProbeSupport.control(conn))

  post "/payments/authorize" do
    ProbeSupport.increment()
    token = :otel_ctx.attach(:otel_propagator_text_map.extract_to(%{}, conn.req_headers))

    try do
      {order, conn} = ProbeSupport.body(conn)

      order = ProbeSupport.valid_order!(order)

      ProbeSupport.span("payments.request", :server, order, nil, fn ->
        result =
          ProbeSupport.span("payments.authorize", :internal, order, "authorize", fn ->
            :otel_span.set_attribute(
              OpenTelemetry.Tracer.current_span_ctx(),
              :artifact_id,
              ProbeSupport.beam_hash(PaymentsBeamlSpike)
            )

            result = PaymentsBeamlSpike.authorize(order)
            ProbeSupport.event("payment_stub_returned", "authorize")
            result
          end)

        ProbeSupport.reply(conn, 200, result)
      end)
    rescue
      _ -> ProbeSupport.reply(conn, 400, %{error: "invalid_request"})
    after
      :otel_ctx.detach(token)
    end
  end

  match(_, do: ProbeSupport.reply(conn, 404, %{error: "not_found"}))
end
