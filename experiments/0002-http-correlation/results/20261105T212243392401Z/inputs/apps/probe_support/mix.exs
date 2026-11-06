defmodule ProbeSupport.MixProject do
  use Mix.Project

  def project do
    [
      app: :probe_support,
      version: "0.1.0",
      build_path: "../../_build",
      config_path: "../../config/config.exs",
      deps_path: "../../deps",
      lockfile: "../../mix.lock",
      deps: [
        {:plug_cowboy, "== 2.8.1"},
        {:opentelemetry_api, "== 1.5.0"},
        {:opentelemetry, "== 1.7.0"}
      ]
    ]
  end

  def application, do: [extra_applications: [:logger, :crypto]]
end
