--- experiments/0003-source-linked-replay/tests/replay_run_test.py
+++ experiments/0003-source-linked-replay/tests/replay_run_test.py
@@ -25,10 +25,10 @@
 TEST = "test_separate_runner_replays_first_call_and_rejects_invalid_records"
 SERVICES = ("payments", "orders")
 ORDER = {"order_id": "order-1"}
-PAYMENT = {"order_id": "order-1", "status": "authorized"}
+PAYMENT = {"order_id": "order-1", "status": "authorized", "reference": "ref-1"}
 OPERATION, ATTEMPT = "payments.authorize", 1
 # A1: valid PAYMENT with non-canonical JSON. Payments itself sends compact JSON.
-STUB_BODY = b'{ "status" : "authorized",\n  "order_id" : "order-1" }'
+STUB_BODY = b'{ "status" : "authorized",\n  "order_id" : "order-1",\n  "reference" : "ref-1" }'
 WATCHED = ("OrdersApi.Router.call/2", "OrdersBeamlSpike.payments_authorize/1", ":gen_tcp.connect/4",
            "OrdersBeamlSpike.prepare/1", ":json.decode/1", "OrdersBeamlSpike.finish/1",
            "ProbeSupport.valid_payment!/2")
