"""Bounded real-release experiment. Every invocation retains its own terminal record."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from query import check_run, event

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value): Path(path).write_text(json.dumps(value,indent=2)+'\n')

def stop(process):
    if process.poll() is None:
        os.killpg(process.pid,signal.SIGTERM)
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)

def request(port,path='/control',body=None):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request('http://127.0.0.1:%s%s'%(port,path),data=data,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=5) as response:return response.status,json.load(response)
    except urllib.error.HTTPError as response:return response.code,json.load(response)

def execute(fail_after_start=False):
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=ROOT/'results'/stamp;run.mkdir(parents=True)
    result={'status':'fail','cases':{},'commands':[]};processes=[];handles=[]
    event('start','http-correlation','running')
    def command(name,args,cwd=ROOT,env=None):
        result['commands'].append(dict(name=name,args=[str(a) for a in args]));save(run/'commands.json',result['commands'])
        with (run/(name+'.stdout')).open('wb') as out,(run/(name+'.stderr')).open('wb') as err:
            cp=subprocess.run([str(a) for a in args],cwd=cwd,env=env,stdout=out,stderr=err,timeout=180)
        if cp.returncode:raise RuntimeError('command_failed:'+name)
    def step(case,description):event('step',case,description)
    def case(case,fun):
        event('start',case,'running')
        try:details=fun();result['cases'][case]=dict(status='pass',details=details);event('pass',case,'pass')
        except Exception:result['cases'][case]=dict(status='fail');event('fail',case,'fail');raise
        finally:save(run/'result.json',result)
    try:
        inputs = [ROOT/'mix.exs',ROOT/'mix.lock',ROOT/'run.py',ROOT/'query.py'] + list((ROOT/'config').glob('*.exs')) + list((ROOT/'apps').glob('*/mix.exs')) + list((ROOT/'apps').glob('*/lib/**/*.ex')) + list((ROOT/'apps').glob('*/priv/*.beaml'))
        hashes={}
        for source in inputs:
            if source.name=='generated.ex': continue
            relative=source.relative_to(ROOT);target=run/'inputs'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);hashes[str(relative)]=digest(source)
        hashes['compiler0001']=digest(REPO/'experiments/0001-syntax-to-beam/src/main.rs')
        save(run/'input-hashes.json',hashes)
        for name,args in [('elixir-version',['elixir','--version']),('python-version',[sys.executable,'--version']),('cargo-version',['cargo','--version']),('rust-version',['rustc','--version'])]:command(name,args)
        for service in ('orders','payments'):
            fixture=ROOT/'apps'/(service+'_api')/'priv'/(service+'.beaml')
            command('generate-'+service,['cargo','run','--quiet','--manifest-path',REPO/'experiments/0001-syntax-to-beam/Cargo.toml','--',fixture],cwd=REPO)
            raw=(run/('generate-'+service+'.stdout')).read_text();assert raw.count('defmodule BeamlSpike do')==1
            (ROOT/'apps'/(service+'_api')/'lib/generated.ex').write_text(raw.replace('defmodule BeamlSpike do','defmodule '+service.title()+'BeamlSpike do'))
        command('dependencies',['mix','deps.get','--offline'])
        command('format-generated',['mix','format','apps/orders_api/lib/generated.ex','apps/payments_api/lib/generated.ex'])
        command('format',['mix','format','--check-formatted'])
        for service in ('orders','payments'):
            command('release-'+service,['mix','release',service,'--overwrite'],env=dict(PATH='/Users/lennart/.asdf/installs/elixir/1.18.1-otp-27/bin:/Users/lennart/.asdf/installs/erlang/27.3.4/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',HOME='/Users/lennart',MIX_HOME='/Users/lennart/.asdf/installs/elixir/1.18.1-otp-27/.mix',MIX_ENV='prod'))
        command('compile-strict',['mix','compile','--force','--warnings-as-errors'],env=dict(PATH='/Users/lennart/.asdf/installs/elixir/1.18.1-otp-27/bin:/Users/lennart/.asdf/installs/erlang/27.3.4/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',HOME='/Users/lennart',MIX_HOME='/Users/lennart/.asdf/installs/elixir/1.18.1-otp-27/.mix',MIX_ENV='prod'))
        command('python-tests',[sys.executable,'-m','unittest','discover','-s','tests'])
        for service in ('orders','payments'):
            command('fixture-tests-'+service,['elixir','-pa',ROOT/'_build/prod/lib/probe_support/ebin','-pa',ROOT/'_build/prod/lib'/(service+'_api')/'ebin','tests/fixture_test.exs'])
        command('capture-tests',['elixir','-pa',ROOT/'_build/prod/lib/probe_support/ebin','tests/capture_test.exs'])
        def pair(name,drop=False):
            evidence=run/name;evidence.mkdir()
            manifest={'fixtures':{},'capture':{},'processes':{}}
            ports={}
            for service in ('payments','orders'):
                out=evidence/service;out.mkdir()
                for kind in ('logs','spans'):(out/(kind+'.jsonl')).touch()
                env=dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',HOME='/tmp',PROBE_SERVICE=service,PROBE_OUTPUT=str(out),PROBE_PAYMENTS_PORT=str(ports.get('payments',0)),PROBE_DROP_CONTEXT=str(drop).lower(),RELEASE_DISTRIBUTION='none')
                handle=(out/'process.log').open('wb');handles.append(handle)
                binary=ROOT/'_build/prod/rel'/service/'bin'/service
                process=subprocess.Popen([str(binary),'start'],env=env,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True);processes.append(process)
                deadline=time.monotonic()+20
                while not (out/'ready.json').exists():
                    if process.poll() is not None:raise RuntimeError('service_exited:'+service)
                    if time.monotonic()>deadline:raise RuntimeError('readiness_timeout:'+service)
                    time.sleep(.05)
                ports[service]=json.loads((out/'ready.json').read_text())['port']
                status,control=request(ports[service]);save(out/'startup-control.json',control);assert status==200
                assert control['node']=='nonode@nohost' and control['own_loaded'] and not control['sibling_loaded'] and not control['sibling_available']
                assert control['sibling'] not in control['applications'] and service+'_api' in control['applications'] and control['listener']=='127.0.0.1'
                manifest['processes'][service]=dict(control,launcher_pid=process.pid,port=ports[service])
                fixture=ROOT/'apps'/(service+'_api')/'priv'/(service+'.beaml');shutil.copyfile(fixture,evidence/(service+'.beaml'))
                generated=ROOT/'apps'/(service+'_api')/'lib/generated.ex';shutil.copyfile(generated,evidence/(service+'.generated.ex'))
                beam=ROOT/'_build/prod/rel'/service/'lib'/(service+'_api-0.1.0')/('ebin/Elixir.'+service.title()+'BeamlSpike.beam')
                assert control['beam_hash']==digest(beam)
                manifest['fixtures'][service]=dict(source='apps/'+service+'_api/priv/'+service+'.beaml',source_hash=digest(fixture))
                manifest.setdefault('artifacts',{})[service]=dict(generated_hash=digest(generated),beam_hash=digest(beam))
            assert manifest['processes']['orders']['pid']!=manifest['processes']['payments']['pid']
            def snapshot():
                for service in ('orders','payments'):
                    status,control=request(ports[service]);assert status==200
                    manifest['capture'][service]=control['capture']
                    for kind in ('spans','logs'):shutil.copyfile(evidence/service/(kind+'.jsonl'),evidence/(service+'.'+kind+'.jsonl'))
                save(evidence/'manifest.json',manifest)
                return check_run(evidence)
            return evidence,ports,snapshot
        normal,ports,snapshot=pair('normal')
        if fail_after_start:raise RuntimeError('injected_post_start_failure')
        def valid():
            step('H01','http_post');status,body=request(ports['orders'],'/orders',{'order_id':'order-1'});assert (status,body)==(200,{'order_id':'order-1','status':'authorized'})
            checked=snapshot();save(normal/'query-H01.json',checked);assert checked['complete'] and len(checked['traces'])==1;return checked
        case('H01',valid)
        def repeat():
            step('H02','http_post');status,body=request(ports['orders'],'/orders',{'order_id':'order-1'});assert status==200
            checked=snapshot();save(normal/'query-H02.json',checked);assert checked['complete'] and len(checked['traces'])==2;return checked
        case('H02',repeat)
        def rejected():
            step('H05','count_before');before=request(ports['payments'])[1]['count']
            status,body=request(ports['orders'],'/orders',{'order_id':'order-1','extra':'invalid'})
            after=request(ports['payments'])[1]['count'];assert status==400 and body=={'error':'invalid_request'} and before==after
            return dict(status=status,before=before,after=after)
        case('H05',rejected)
        snapshot()
        for process in processes:stop(process)
        broken,bports,bsnapshot=pair('context-drop',True)
        def dropped():
            step('H03','http_post');assert request(bports['orders'],'/orders',{'order_id':'order-1'})[0]==200
            checked=bsnapshot();save(broken/'query.json',checked);assert not checked['complete'] and len(checked['traces'])==2 and any(g['code']=='missing_causal_edge' for g in checked['gaps']);return checked
        case('H03',dropped)
        def missing():
            step('H04','derivative_copy');original={p.name:digest(p) for p in normal.glob('*.jsonl')}
            derivative=run/'missing-log';shutil.copytree(normal,derivative)
            path=derivative/'payments.logs.jsonl';lines=path.read_text().splitlines();assert lines;path.write_text('\n'.join(lines[1:])+('\n' if len(lines)>1 else ''))
            save(derivative/'mutation.json',dict(kind='remove_required_log',removed=1,original_hashes=original))
            cp=subprocess.run([sys.executable,str(ROOT/'query.py'),'--run',str(derivative)],capture_output=True,timeout=10)
            (derivative/'query.stdout').write_bytes(cp.stdout);(derivative/'query.stderr').write_bytes(cp.stderr)
            checked=json.loads(cp.stdout);assert cp.returncode==1 and any(g['code']=='missing_log' for g in checked['gaps'])
            assert original=={p.name:digest(p) for p in normal.glob('*.jsonl')};return dict(exit_code=cp.returncode,gaps=checked['gaps'],original_unchanged=True)
        case('H04',missing)
        for process in processes: stop(process)
        boundary,boundary_ports,_=pair('boundary-controls')
        before=request(boundary_ports['payments'])[1]['count']
        for payload in ({},{'order_id':42},{'order_id':'order-1','extra':'x'}):
            assert request(boundary_ports['orders'],'/orders',payload)==(400,{'error':'invalid_request'})
        malformed=urllib.request.Request('http://127.0.0.1:%s/orders'%boundary_ports['orders'],data=b'{invalid',headers={'Content-Type':'application/json'})
        try:
            urllib.request.urlopen(malformed,timeout=5)
            raise AssertionError('malformed_json_accepted')
        except urllib.error.HTTPError as response:
            assert response.code==400 and json.load(response)=={'error':'invalid_request'}
        assert request(boundary_ports['payments'])[1]['count']==before
        # Deliberate writer failure belongs only to this separate boundary-control pair.
        failed_file=boundary/'orders/spans.jsonl';failed_file.unlink();failed_file.mkdir()
        assert request(boundary_ports['orders'],'/orders',{'order_id':'order-1'})==(200,{'order_id':'order-1','status':'authorized'})
        control=request(boundary_ports['orders'])[1]
        assert 'spans' in control['capture']['loss']
        save(boundary/'writer-loss.json',control)
        stop(processes[-2])
        assert request(boundary_ports['orders'],'/orders',{'order_id':'order-1'})==(502,{'error':'downstream_failure'})
        save(boundary/'checks.json',dict(invalid_shapes_rejected=True,malformed_json_rejected=True,payments_not_called=True,writer_failure_preserves_200=True,capture_loss_reported=True,transport_failure_returns_502=True))
        result['status']='pass'
    except Exception as error:
        result['error']=type(error).__name__+':'+str(error)
    finally:
        for process in processes:stop(process)
        for handle in handles:handle.close()
        result['cleanup']=[dict(pid=p.pid,exit_code=p.poll()) for p in processes]
        save(run/'result.json',result);event('finish','http-correlation',result['status'])
    return run,result

if __name__=='__main__':
    run,result=execute('--fail-after-start' in sys.argv);print(json.dumps(dict(run=str(run),status=result['status'],error=result.get('error'))));raise SystemExit(0 if result['status']=='pass' else 1)
