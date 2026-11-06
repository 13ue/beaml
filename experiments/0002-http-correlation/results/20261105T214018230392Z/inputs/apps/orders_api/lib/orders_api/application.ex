defmodule OrdersApi.Application do
  use Application

  def start(_, _) do
    ProbeSupport.setup()

    children = [
      ProbeSupport.Capture,
      {Plug.Cowboy,
       scheme: :http,
       plug: OrdersApi.Router,
       options: [ip: {127, 0, 0, 1}, port: 0, ref: :probe_http]}
    ]

    result = Supervisor.start_link(children, strategy: :one_for_one)

    File.write!(
      Path.join(ProbeSupport.config(:output), "ready.json"),
      ProbeSupport.json(%{port: :ranch.get_port(:probe_http)})
    )

    result
  end
end
