defmodule OrdersApi.Router do
  use Plug.Router
  plug(:match)
  plug(:dispatch)
  get("/control", do: ProbeSupport.control(conn))

  # EXPERIMENT 0004 arm GEN: the flow, the HTTP EFFECT, the decode and the CAPTURE are generated
  # from orders.beaml. The host keeps the request span, the domain validation and the reply.
  post "/orders" do
    token = :otel_ctx.attach(%{})

    try do
      {order, conn} = ProbeSupport.body(conn)
      order = ProbeSupport.valid_order!(order)

      ProbeSupport.span("orders.request", :server, order, nil, fn ->
        try do
          case OrdersBeamlSpike.place(order) do
            {:ok, payment} -> ProbeSupport.reply(conn, 200, ProbeSupport.valid_payment!(payment, order))
            {:error, _} -> ProbeSupport.reply(conn, 502, %{error: "downstream_failure"})
          end
        rescue
          _ -> ProbeSupport.reply(conn, 502, %{error: "downstream_failure"})
        end
      end)
    rescue
      _ -> ProbeSupport.reply(conn, 400, %{error: "invalid_request"})
    after
      :otel_ctx.detach(token)
    end
  end

  match(_, do: ProbeSupport.reply(conn, 404, %{error: "not_found"}))
end
