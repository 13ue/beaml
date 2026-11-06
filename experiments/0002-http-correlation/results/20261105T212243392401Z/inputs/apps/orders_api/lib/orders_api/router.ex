defmodule OrdersApi.Router do
  use Plug.Router
  plug(:match)
  plug(:dispatch)
  get("/control", do: ProbeSupport.control(conn))

  post "/orders" do
    token = :otel_ctx.attach(%{})

    try do
      {order, conn} = ProbeSupport.body(conn)
      order = ProbeSupport.valid_order!(order)

      ProbeSupport.span("orders.request", :server, order, nil, fn ->
        request =
          ProbeSupport.span("orders.prepare", :internal, order, "prepare", fn ->
            request = OrdersBeamlSpike.prepare(order)
            ProbeSupport.event("payment_request_prepared", "prepare")
            request
          end)

        try do
          result =
            ProbeSupport.span("orders.payment_http", :client, order, nil, fn ->
              carrier =
                if ProbeSupport.config(:drop_context),
                  do: [],
                  else: :otel_propagator_text_map.inject([])

              headers =
                Enum.map(carrier, fn {key, value} ->
                  {String.to_charlist(key), String.to_charlist(value)}
                end)

              url = ~c"http://127.0.0.1:#{ProbeSupport.config(:payments_port)}/payments/authorize"

              {:ok, {{_, 200, _}, _, bytes}} =
                :httpc.request(
                  :post,
                  {url, headers, ~c"application/json", ProbeSupport.json(request)},
                  [timeout: 2000, connect_timeout: 1000],
                  body_format: :binary
                )

              :json.decode(bytes)
            end)

          result =
            ProbeSupport.span("orders.finish", :internal, order, "finish", fn ->
              OrdersBeamlSpike.finish(result) |> ProbeSupport.valid_payment!(order)
            end)

          ProbeSupport.reply(conn, 200, result)
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
