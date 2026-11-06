defmodule HttpProbe.MixProject do
  use Mix.Project

  def project do
    [
      apps_path: "apps",
      version: "0.1.0",
      start_permanent: Mix.env() == :prod,
      releases: [
        orders: [applications: [orders_api: :permanent]],
        payments: [applications: [payments_api: :permanent]]
      ]
    ]
  end
end
