defmodule OrdersApi.ReplayDescriptor do
  # Comparison arm LIB (EXPERIMENT 0004): one descriptor per EFFECT. No key list, no field name, no TYPE fact.
  def authorize do
    %{
      operation: "payments.authorize",
      attempt: 1,
      code: 200,
      artifact: OrdersBeamlSpike,
      request: &OrdersBeamlSpike.prepare/1,
      decode: &OrdersApi.PaymentHttp.decode/1,
      finish: &OrdersBeamlSpike.finish/1
    }
  end
end
