"""Fixed HTTP fixture evidence checker; order equality never creates an edge."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import datetime

CONTRACT = {
    'orders.request': ('orders', 'server', None),
    'orders.prepare': ('orders', 'internal', 'orders.request'),
    'orders.payment_http': ('orders', 'client', 'orders.request'),
    'payments.request': ('payments', 'server', 'orders.payment_http'),
    'payments.authorize': ('payments', 'internal', 'payments.request'),
    'orders.finish': ('orders', 'internal', 'orders.request'),
}
LOGS = [('payment_request_prepared', 'orders.prepare'), ('payment_stub_returned', 'payments.authorize')]

def event(action, target, result):
    try:
        root = Path(__file__).resolve().parents[2]
        (root / '.beaml').mkdir(exist_ok=True)
        with (root / '.beaml/actions.jsonl').open('a') as output:
            output.write(json.dumps(dict(ts=datetime.datetime.now(datetime.timezone.utc).isoformat(), source='cli', action=action, target=target, result=result))+'\n')
    except OSError:
        pass

def check_run(run, order_id='order-1'):
    run=Path(run); gaps=[]; spans=[]; logs=[]; edges=[]
    def gap(code, **data): gaps.append(dict(code=code, **data))
    try:
        manifest=json.loads((run/'manifest.json').read_text())
        for service in ('orders','payments'):
            fixture=manifest['fixtures'][service]
            if hashlib.sha256((run/(service+'.beaml')).read_bytes()).hexdigest()!=fixture['source_hash']: gap('source_hash',service=service)
            if fixture['source']!='apps/'+service+'_api/priv/'+service+'.beaml': gap('fixture_source',service=service)
            if 'artifacts' in manifest and hashlib.sha256((run/(service+'.generated.ex')).read_bytes()).hexdigest()!=manifest['artifacts'][service]['generated_hash']: gap('generated_hash',service=service)
            if manifest['capture'][service]['loss']: gap('capture_loss',service=service)
            for kind, records in [('spans',spans),('logs',logs)]:
                path=run/(service+'.'+kind+'.jsonl')
                if path.stat().st_size>1048576: gap('capture_size',service=service);raise ValueError('capture_size')
                for line in path.read_text().splitlines():
                    row=json.loads(line)
                    if not isinstance(row,dict) or not isinstance(row.get('attributes',{}),dict): raise ValueError('record_shape')
                    if not isinstance(row.get('trace_id'),str) or not re.fullmatch('[0-9a-f]{32}',row['trace_id']) or row['trace_id']=='0'*32: raise ValueError('trace_id')
                    if not isinstance(row.get('span_id'),str) or not re.fullmatch('[0-9a-f]{16}',row['span_id']) or row['span_id']=='0'*16: raise ValueError('span_id')
                    if kind=='spans' and (not isinstance(row.get('name'),str) or not isinstance(row.get('kind'),str) or not isinstance(row.get('ended'),bool)): raise ValueError('span_shape')
                    if row.get('service')!=service: gap('service_file',service=service)
                    if row.get('attributes',{}).get('order_id')==order_id or row.get('order_id')==order_id: records.append(row)
    except (OSError,ValueError,KeyError,TypeError):
        gap('invalid_evidence')
        return dict(complete=False,gaps=gaps,traces=[],edges=[],logs=[],fixtures=[])
    traces=sorted({s.get('trace_id','') for s in spans})
    identities=set()
    for row in spans:
        key=(row.get('trace_id'),row.get('span_id'))
        if not isinstance(key[0],str) or not isinstance(key[1],str): gap('invalid_identity');continue
        if key in identities: gap('duplicate_span',trace_id=key[0],span_id=key[1])
        identities.add(key)
    if not traces: gap('no_traces')
    for trace in traces:
        group=[s for s in spans if s.get('trace_id')==trace]
        byname={s.get('name'):s for s in group}
        if set(byname)!=set(CONTRACT) or len(group)!=6: gap('trace_shape',trace_id=trace)
        for name,row in byname.items():
            if name not in CONTRACT: gap('unknown_span',trace_id=trace); continue
            service,kind,parent=CONTRACT[name]
            if row.get('service')!=service or row.get('kind')!=kind or row.get('ended') is not True or row.get('attributes',{}).get('outcome')!='ok': gap('span_shape',trace_id=trace,span_id=row.get('span_id'))
            parentrow=byname.get(parent)
            if parent:
                if not parentrow or row.get('parent_span_id')!=parentrow.get('span_id'):
                    gap('missing_causal_edge',trace_id=trace,span=name,parent=parent)
                else: edges.append(dict(trace_id=trace,parent_span_id=parentrow['span_id'],span_id=row['span_id']))
            elif row.get('parent_span_id') is not None: gap('root_parent',trace_id=trace)
            if kind=='internal':
                attrs=row.get('attributes',{})
                expected=dict(manifest['fixtures'][service],function=name.split('.')[1])
                if any(attrs.get(k)!=v for k,v in expected.items()): gap('fixture_descriptor',trace_id=trace,span_id=row.get('span_id'))
        for eventname,spanname in LOGS:
            row=byname.get(spanname)
            if row:
                matches=[log for log in logs if log.get('event')==eventname and log.get('trace_id')==trace and log.get('span_id')==row.get('span_id') and log.get('service')==row.get('service') and log.get('operation')==spanname.split('.')[1]]
                if len(matches)!=1: gap('missing_log',trace_id=trace,span_id=row.get('span_id'),event=eventname)
    for log in logs:
        expected=dict(LOGS).get(log.get('event'))
        if not any(s.get('trace_id')==log.get('trace_id') and s.get('span_id')==log.get('span_id') and s.get('name')==expected for s in spans): gap('unlinked_log',event=log.get('event'))
    return dict(complete=not gaps,gaps=gaps,traces=traces,edges=edges,logs=logs,fixtures=manifest['fixtures'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--order-id',default='order-1');args=parser.parse_args()
    event('start','query','running');result=check_run(args.run,args.order_id);print(json.dumps(result,indent=2));event('finish','query','pass' if result['complete'] else 'incomplete');return 0 if result['complete'] else 1
if __name__=='__main__': raise SystemExit(main())
