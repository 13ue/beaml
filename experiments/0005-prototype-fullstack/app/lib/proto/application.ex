defmodule Proto.Application do
  # See https://hexdocs.pm/elixir/Application.html
  # for more information on OTP Applications
  @moduledoc false

  use Application

  @impl true
  def start(_type, _args) do
    ProbeSupport.setup()

    children = [
      ProbeSupport.Capture,
      ProtoWeb.Telemetry,
      Proto.Repo,
      {DNSCluster, query: Application.get_env(:proto, :dns_cluster_query) || :ignore},
      {Phoenix.PubSub, name: Proto.PubSub},
      # Start a worker by calling: Proto.Worker.start_link(arg)
      # {Proto.Worker, arg},
      # Start to serve requests, typically the last entry
      ProtoWeb.Endpoint
    ]

    # See https://hexdocs.pm/elixir/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: Proto.Supervisor]
    Supervisor.start_link(children, opts)
  end

  # Tell Phoenix to update the endpoint configuration
  # whenever the application is updated.
  @impl true
  def config_change(changed, _new, removed) do
    ProtoWeb.Endpoint.config_change(changed, removed)
    :ok
  end
end
