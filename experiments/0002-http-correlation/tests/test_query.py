import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("query", ROOT / "query.py")
query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query)

class QueryTest(unittest.TestCase):
    def test_complete_and_missing_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            self.assertTrue(query.check_run(root)["complete"])
            (root / "payments.logs.jsonl").write_text("")
            result = query.check_run(root)
            self.assertFalse(result["complete"])
            self.assertIn("missing_log", [g["code"] for g in result["gaps"]])

    def fixture(self, root):
        import hashlib
        (root / "orders.beaml").write_text("synthetic orders")
        (root / "payments.beaml").write_text("synthetic payments")
        descriptors = {service: {"source": "apps/" + service + "_api/priv/" + service + ".beaml", "source_hash": hashlib.sha256((root / (service + ".beaml")).read_bytes()).hexdigest()} for service in ("orders", "payments")}
        artifacts = {}
        processes = {}
        for service in descriptors:
            generated = root / (service + ".generated.ex")
            generated.write_text("synthetic generated " + service)
            beam_hash = hashlib.sha256(("synthetic BEAM " + service).encode()).hexdigest()
            artifacts[service] = dict(generated_hash=hashlib.sha256(generated.read_bytes()).hexdigest(), beam_hash=beam_hash)
            processes[service] = dict(beam_hash=beam_hash)
        (root / "manifest.json").write_text(json.dumps(dict(fixtures=descriptors, artifacts=artifacts, processes=processes, capture={service: {"loss": []} for service in descriptors})))
        names = [("orders.request", "server", None), ("orders.prepare", "internal", "1"), ("orders.payment_http", "client", "1"), ("payments.request", "server", "3"), ("payments.authorize", "internal", "4"), ("orders.finish", "internal", "1")]
        spans = []
        for i, (name, kind, parent) in enumerate(names, 1):
            service, operation = name.split(".")
            attrs = {"order_id": "order-1", "outcome": "ok"}
            if kind == "internal":
                attrs.update(descriptors[service], function=operation)
            spans.append(dict(name=name, kind=kind, parent_span_id=parent.zfill(16) if parent else None, parent_remote=name == "payments.request", trace_id="a"*32, span_id=str(i).zfill(16), service=service, ended=True, attributes=attrs))
        for service in ("orders", "payments"):
            (root / (service + ".spans.jsonl")).write_text("".join(json.dumps(s) + "\n" for s in spans if s["service"] == service))
        for service, event, operation, sid in [("orders", "payment_request_prepared", "prepare", "2"), ("payments", "payment_stub_returned", "authorize", "5")]:
            (root / (service + ".logs.jsonl")).write_text(json.dumps(dict(service=service,event=event,operation=operation,order_id="order-1",trace_id="a"*32,span_id=sid.zfill(16)))+"\n")

    def test_split_trace_reports_missing_edge(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root)
            for kind in ('logs','spans'):
                p=root/('payments.'+kind+'.jsonl')
                rows=[json.loads(line) for line in p.read_text().splitlines()]
                for row in rows:
                    row['trace_id']='b'*32
                    if row.get('name')=='payments.request':
                        row['parent_span_id']=None
                        row['parent_remote']=False
                p.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            result=query.check_run(root)
            self.assertFalse(result['complete'])
            self.assertEqual(len(result['traces']),2)
            self.assertIn('missing_causal_edge',[g['code'] for g in result['gaps']])
            self.assertFalse(any(edge['parent_span_id']=='3'.zfill(16) for edge in result['edges']))

    def test_two_traces_stay_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root)
            for p in root.glob('*.jsonl'):
                rows=[json.loads(line) for line in p.read_text().splitlines()]
                second=[]
                for row in rows:
                    copied=json.loads(json.dumps(row));copied['trace_id']='b'*32;second.append(copied)
                p.write_text(''.join(json.dumps(row)+'\n' for row in rows+second))
            result=query.check_run(root)
            self.assertTrue(result['complete'])
            self.assertEqual(len(result['traces']),2)
            self.assertEqual(len(result['edges']),10)

    def test_payments_ingress_requires_remote_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            self.assertTrue(query.check_run(root)["complete"])
            path = root / "payments.spans.jsonl"
            spans = [json.loads(line) for line in path.read_text().splitlines()]
            for span in spans:
                if span["name"] == "payments.request":
                    span["parent_remote"] = False
            path.write_text("".join(json.dumps(span) + "\n" for span in spans))
            result = query.check_run(root)
            self.assertEqual(result["complete"], False, result["gaps"])
            self.assertIn("remote_parent", [gap["code"] for gap in result["gaps"]])

    def test_missing_artifact_metadata_is_a_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            self.assertTrue(query.check_run(root)["complete"])
            path = root / "manifest.json"
            manifest = json.loads(path.read_text())
            del manifest["artifacts"]
            path.write_text(json.dumps(manifest))
            result = query.check_run(root)
            self.assertEqual(result["complete"], False, result["gaps"])
            self.assertIn("missing_artifacts", [gap["code"] for gap in result["gaps"]])

    def test_corruptions(self):
        for corruption in ("parent", "duplicate", "kind", "hash", "malformed", "null", "array", "log_link"):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as directory:
                root=Path(directory); self.fixture(root)
                path=root/"orders.spans.jsonl"
                rows=[json.loads(line) for line in path.read_text().splitlines()]
                if corruption=="parent": rows[1]["parent_span_id"]="unknown"
                if corruption=="duplicate": rows.append(rows[0])
                if corruption=="kind": rows[0]["kind"]="client"
                if corruption=="hash": rows[1]["attributes"]["source_hash"]="wrong"
                path.write_text("".join(json.dumps(row)+"\n" for row in rows))
                if corruption=="malformed": path.write_text("{broken\n")
                if corruption=="null": path.write_text("null\n")
                if corruption=="array": path.write_text("[]\n")
                if corruption=="log_link":
                    p=root/"orders.logs.jsonl"; row=json.loads(p.read_text()); row["span_id"]="6"; p.write_text(json.dumps(row)+"\n")
                self.assertFalse(query.check_run(root)["complete"])

if __name__ == "__main__": unittest.main()
