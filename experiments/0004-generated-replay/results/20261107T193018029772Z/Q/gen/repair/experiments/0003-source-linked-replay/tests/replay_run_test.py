--- experiments/0003-source-linked-replay/tests/replay_run_test.py
+++ experiments/0003-source-linked-replay/tests/replay_run_test.py
@@ -223,7 +223,7 @@
         assert [r["trace_id"] for r in records] == [r["trace_id"] for r in receipts]
         first = records[0]
         assert (first["artifact_id"], first["operation"], first["attempt"], first["request"], first["status"]) == (
-            orders_artifact, OPERATION, ATTEMPT, ORDER, 200)
+            orders_artifact, OPERATION, ATTEMPT, {**ORDER, "channel": "web"}, 200)
         assert json.loads(base64.b64decode(first["body_base64"])) == PAYMENT
         responses = evidence / "orders.responses.jsonl"
         shutil.copyfile(run / "orders/responses.jsonl", responses)
