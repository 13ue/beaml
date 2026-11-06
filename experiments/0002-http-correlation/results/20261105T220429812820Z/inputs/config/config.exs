import Config

config :opentelemetry,
  resource_detectors: [:otel_resource_app_env],
  resource: [],
  sampler: :always_on,
  processors: [{:otel_simple_processor, %{exporter: {ProbeSupport.Exporter, %{}}}}]

config :opentelemetry, :text_map_propagators, [:trace_context]
config :logger, level: :info
