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

def summarize_payments(run, manifest, spans, order_id, source, generated, gap):
    selected = manifest['function_lookup']
    artifact_id = manifest['artifacts']['payments']['beam_hash']
    source_id = {
        'qualified_name': 'payments.authorize',
        'source_sha256': manifest['fixtures']['payments']['source_hash'],
    }
    if selected['artifact_id'] != artifact_id or selected['source_id'] != source_id:
        gap('function_identity')
        return

    beam = 'Elixir.PaymentsBeamlSpike.beam.bin'
    if hashlib.sha256((run / beam).read_bytes()).hexdigest() != artifact_id:
        gap('beam_hash', service='payments')
        return
    ranges = re.findall(rb'^  # beaml-declaration-v1 authorize ([0-9]+) ([0-9]+)$', generated, re.M)
    if len(ranges) != 1:
        gap('declaration_reference')
        return
    start, end = map(int, ranges[0])
    if (selected['byte_range'] != [start, end] or not 0 <= start < end <= len(source)
            or not source[start:end].startswith(b'fn authorize ')):
        gap('declaration_reference')
        return

    receipts = manifest['receipts']
    if len(receipts) != 2 or any(
        type(receipt['call']) is not int or receipt['call'] != call or receipt['status'] != 200
        or receipt['body'] != {'order_id': order_id, 'status': 'authorized'}
        for call, receipt in enumerate(receipts, start=1)
    ):
        gap('receipt_coverage')
        return
    # Receipt order must match the start order of sequential Orders roots from one VM.
    receipt_traces = [receipt['trace_id'] for receipt in receipts]
    roots = [row for row in spans if row['name'] == 'orders.request']
    if any(type(row.get(key)) is not int for row in roots for key in ('start_time', 'end_time')):
        gap('receipt_coverage')
        return
    roots.sort(key=lambda row: row['start_time'])
    if ([row['trace_id'] for row in roots] != receipt_traces
            or any(a['end_time'] > b['start_time'] for a, b in zip(roots, roots[1:]))):
        gap('receipt_coverage')
        return

    # Bind the roots to the recorded UTC window with the VM's own wall-clock conversion.
    window = manifest.get('window')
    if not isinstance(window, dict) or not {'start_utc', 'end_utc'} <= window.keys():
        gap('missing_window')
        return
    bounds = []
    for key in ('start_utc', 'end_utc'):
        moment = datetime.datetime.fromisoformat(window[key])
        if moment.utcoffset() != datetime.timedelta(0):
            raise ValueError('window_utc')
        bounds.append((moment - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
                      // datetime.timedelta(microseconds=1) * 1000)
    if any(type(row.get(key)) is not int for row in roots
           for key in ('start_time_unix_nano', 'end_time_unix_nano')):
        gap('missing_clock')
        return
    if not bounds[0] <= roots[0]['start_time_unix_nano'] <= roots[-1]['end_time_unix_nano'] <= bounds[1]:
        gap('outside_window')
        return

    # The graph check already requires one ended, successful function span per trace.
    calls = [row for row in spans if row['name'] == source_id['qualified_name']]
    if len(calls) != len(receipts) or any(
        row['attributes'].get('artifact_id') != artifact_id
        or row['attributes'].get('source_hash') != source_id['source_sha256']
        for row in calls
    ):
        gap('function_span_identity')
        return

    return dict(
        artifact_id=artifact_id, source_id=source_id, matched_calls=len(calls),
        completed_calls=len(receipts), successful_outcomes=len(calls),
        first_trace_id=receipt_traces[0], declaration=source[start:end].decode(),
        byte_range=[start, end], source='payments.beaml', generated='payments.generated.ex', beam=beam,
    )

def event(action, target, result):
    try:
        root = Path(__file__).resolve().parents[2]
        (root / '.beaml').mkdir(exist_ok=True)
        with (root / '.beaml/actions.jsonl').open('a') as output:
            output.write(json.dumps(dict(ts=datetime.datetime.now(datetime.timezone.utc).isoformat(), source='cli', action=action, target=target, result=result))+'\n')
    except OSError:
        pass

def check_run(run, order_id='order-1', *, context_drop=False):
    run=Path(run); gaps=[]; spans=[]; logs=[]; edges=[]
    lookup = False
    payment_inputs = ()
    def gap(code, **data): gaps.append(dict(code=code, **data))
    try:
        manifest=json.loads((run/'manifest.json').read_text())
        lookup = 'function_lookup' in manifest
        for service in ('orders','payments'):
            fixture=manifest['fixtures'][service]
            source=(run/(service+'.beaml')).read_bytes()
            if hashlib.sha256(source).hexdigest()!=fixture['source_hash']: gap('source_hash',service=service)
            if fixture['source']!='apps/'+service+'_api/priv/'+service+'.beaml': gap('fixture_source',service=service)
            artifacts=manifest.get('artifacts',{}).get(service,{})
            beam_hash=artifacts.get('beam_hash')
            if not {'generated_hash','beam_hash'} <= artifacts.keys():
                gap('missing_artifacts',service=service)
            else:
                generated=(run/(service+'.generated.ex')).read_bytes()
                if service == 'payments':
                    payment_inputs = (source, generated)
                if hashlib.sha256(generated).hexdigest()!=artifacts['generated_hash']:
                    gap('generated_hash',service=service)
                if (not isinstance(beam_hash,str) or not re.fullmatch('[0-9a-f]{64}',beam_hash)
                        or beam_hash!=manifest['processes'][service]['beam_hash']):
                    gap('beam_hash',service=service)
            if manifest['capture'][service]['loss']: gap('capture_loss',service=service)
            for kind, records in [('spans',spans),('logs',logs)]:
                path=run/(service+'.'+kind+'.jsonl')
                if path.stat().st_size>1048576: gap('capture_size',service=service);raise ValueError('capture_size')
                if kind in manifest['capture'][service].get('bytes',{}) and manifest['capture'][service]['bytes'][kind]!=path.stat().st_size: gap('capture_count',service=service,kind=kind)
                for line in path.read_text().splitlines():
                    row=json.loads(line)
                    if not isinstance(row,dict) or not isinstance(row.get('attributes',{}),dict): raise ValueError('record_shape')
                    if not isinstance(row.get('trace_id'),str) or not re.fullmatch('[0-9a-f]{32}',row['trace_id']) or row['trace_id']=='0'*32: raise ValueError('trace_id')
                    if not isinstance(row.get('span_id'),str) or not re.fullmatch('[0-9a-f]{16}',row['span_id']) or row['span_id']=='0'*16: raise ValueError('span_id')
                    if kind=='spans' and (not isinstance(row.get('name'),str) or not isinstance(row.get('kind'),str) or not isinstance(row.get('ended'),bool)): raise ValueError('span_shape')
                    if kind=='logs' and (not isinstance(row.get('event'),str) or not isinstance(row.get('operation'),str) or not isinstance(row.get('order_id'),str)): raise ValueError('log_shape')
                    if row.get('service')!=service: gap('service_file',service=service)
                    if row.get('attributes',{}).get('order_id')==order_id or row.get('order_id')==order_id: records.append(row)
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:
        if lookup and isinstance(error, FileNotFoundError) and error.filename == str(run/'payments.beaml'):
            gap('missing_source', service='payments')
        else:
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
        services={s.get('service') for s in group}
        expected={name for name,(service,_,_) in CONTRACT.items() if not context_drop or service in services}
        if set(byname)!=expected or len(group)!=len(expected) or (context_drop and len(services)!=1):
            gap('trace_shape',trace_id=trace)
        for name,row in byname.items():
            if name not in CONTRACT: gap('unknown_span',trace_id=trace); continue
            service,kind,parent=CONTRACT[name]
            if row.get('service')!=service or row.get('kind')!=kind or row.get('ended') is not True or row.get('attributes',{}).get('outcome')!='ok': gap('span_shape',trace_id=trace,span_id=row.get('span_id'))
            parentrow=byname.get(parent)
            if parent:
                if not parentrow or row.get('parent_span_id')!=parentrow.get('span_id'):
                    gap('missing_causal_edge',trace_id=trace,span=name,parent=parent)
                elif name=='payments.request' and row.get('parent_remote') is not True:
                    gap('remote_parent',trace_id=trace,span=name)
                else: edges.append(dict(trace_id=trace,parent_span_id=parentrow['span_id'],span_id=row['span_id']))
            elif row.get('parent_span_id') is not None: gap('root_parent',trace_id=trace)
            if context_drop and name=='payments.request':
                if row.get('parent_span_id') is not None: gap('root_parent',trace_id=trace)
                if row.get('parent_remote') is not False: gap('remote_parent',trace_id=trace,span=name)
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
    summary = None
    if lookup and not gaps:
        try:
            summary = summarize_payments(run, manifest, spans, order_id, *payment_inputs, gap)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            gap('invalid_evidence')
    result = dict(complete=not gaps,gaps=gaps,traces=traces,edges=edges,logs=logs,fixtures=manifest['fixtures'])
    if summary is not None:
        result['function_summary'] = summary
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--order-id',default='order-1');args=parser.parse_args()
    event('start','query','running');result=check_run(args.run,args.order_id);print(json.dumps(result,indent=2));event('finish','query','pass' if result['complete'] else 'incomplete');return 0 if result['complete'] else 1
if __name__=='__main__': raise SystemExit(main())
