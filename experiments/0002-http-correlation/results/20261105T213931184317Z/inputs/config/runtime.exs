import Config

if config_env() == :prod do
  service = System.fetch_env!("PROBE_SERVICE")
  true = service in ["orders", "payments"]
  config :opentelemetry, :resource, %{service: %{name: service}}

  config :probe_support,
    service: service,
    output: System.fetch_env!("PROBE_OUTPUT"),
    payments_port: String.to_integer(System.get_env("PROBE_PAYMENTS_PORT", "0")),
    drop_context: System.get_env("PROBE_DROP_CONTEXT", "false") == "true"
end
