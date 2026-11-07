--- experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex
+++ experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex
@@ -32,6 +32,7 @@
       |> Plug.Conn.send_resp(status, json(value))
 
   def valid_order!(%{"order_id" => "order-1"} = order) when map_size(order) == 1, do: order
+  def valid_order!(%{"order_id" => "order-1", "channel" => "web"} = order) when map_size(order) == 2, do: order
   def valid_order!(_), do: raise(ArgumentError)
 
   def valid_payment!(value, order) do
