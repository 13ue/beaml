--- experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex
+++ experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex
@@ -35,7 +35,7 @@
   def valid_order!(_), do: raise(ArgumentError)
 
   def valid_payment!(value, order) do
-    unless value == %{"order_id" => order["order_id"], "status" => "authorized"},
+    unless value == %{"order_id" => order["order_id"], "state" => "authorized"},
       do: raise(ArgumentError)
 
     value
