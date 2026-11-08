# This file is responsible for configuring your application
# and its dependencies with the aid of the Config module.
#
# This configuration file is loaded before any dependency and
# is restricted to this project.

# General application configuration
import Config

config :proto,
  ecto_repos: [Proto.Repo],
  generators: [timestamp_type: :utc_datetime]

# Configure the endpoint
config :proto, ProtoWeb.Endpoint,
  url: [host: "localhost"],
  adapter: Bandit.PhoenixAdapter,
  render_errors: [
    formats: [html: ProtoWeb.ErrorHTML, json: ProtoWeb.ErrorJSON],
    layout: false
  ],
  pubsub_server: Proto.PubSub,
  live_view: []

# Configure esbuild (the version is required)
config :esbuild,
  version: "0.25.4",
  proto: [
    args:
      ~w(js/app.js --bundle --target=es2022 --outdir=../priv/static/assets/js --external:/fonts/* --external:/images/* --alias:@=.),
    cd: Path.expand("../assets", __DIR__),
    env: %{"NODE_PATH" => [Path.expand("../deps", __DIR__), Mix.Project.build_path()]}
  ]

# Configure tailwind (the version is required)
config :tailwind,
  version: "4.1.12",
  proto: [
    args: ~w(
      --input=assets/css/app.css
      --output=priv/static/assets/css/app.css
    ),
    cd: Path.expand("..", __DIR__)
  ]

# Configure Elixir's Logger
config :logger, :default_formatter,
  format: "$time $metadata[$level] $message\n",
  metadata: [:request_id]

# Use Jason for JSON parsing in Phoenix
config :phoenix, :json_library, Jason

# OTel config copied from the 0002 umbrella (P5-24): a path dep brings no umbrella config.
config :opentelemetry,
  resource_detectors: [:otel_resource_app_env],
  resource: [],
  sampler: :always_on,
  processors: [{:otel_simple_processor, %{exporter: {ProbeSupport.Exporter, %{}}}}]

config :opentelemetry, :text_map_propagators, [:trace_context]

# Import environment specific config. This must remain at the bottom
# of this file so it overrides the configuration defined above.
import_config "#{config_env()}.exs"
