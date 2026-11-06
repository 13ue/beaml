defmodule OrdersApi.Replay do
  # RED scaffolding (EXPERIMENT 0003 gate 4): entry point only, no logic.
  # GREEN contract: {:ok, payment} | {:error, reason}. Outside the router; no transport.
  def run(_order, _trace_id, _records), do: {:error, :not_implemented}
end
