defmodule OrdersApi.MixProject do
  use Mix.Project

  def project do
    [
      app: :orders_api,
      version: "0.1.0",
      build_path: "../../_build",
      config_path: "../../config/config.exs",
      deps_path: "../../deps",
      lockfile: "../../mix.lock",
      deps: [{:probe_support, in_umbrella: true}]
    ]
  end

  def application, do: [extra_applications: [:logger, :inets], mod: {OrdersApi.Application, []}]
end
