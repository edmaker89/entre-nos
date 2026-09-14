"""T28: exercise the disposable Compose stack and verify pg_dump restoration.
Run only against the isolated expense-flow-validation project.
"""
import http.cookiejar
import json
import os
import secrets
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from uuid import uuid4

CMD=['docker','compose','--env-file','.env.compose-test','-p','expense-flow-validation']

def command(*args,input=None):
    return subprocess.check_output([*CMD,*args],input=input)


def sql(statement,db='expense'):
    return command('exec','-T','db','psql','-U','expense_owner','-d',db,'-At','-c',statement).decode().strip()


def main():
    config=json.loads(command('config','--format','json'))
    assert not config['services']['db'].get('ports')
    assert not config['services']['api'].get('ports')
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    base='http://localhost:8089'
    def request(path,data=None,headers=None):
        req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json',**(headers or {})})
        with client.open(req,timeout=10) as response:
            return json.load(response)
    assert request('/health')=={'status':'ok'}
    readiness=request('/ready')
    assert readiness['status']=='ready'
    assert readiness['database']=='ok'
    assert readiness['email_provider']=='memory'
    try:
        request('/api/v1/auth/me')
        raise AssertionError('Anonymous session accepted')
    except urllib.error.HTTPError as error:
        assert error.code==401
    email=f'{uuid4()}@compose.test'
    password=secrets.token_urlsafe(24)
    script="from app.cli import provision; import sys,json; print(json.dumps(provision('Compose test','Tester',sys.argv[1],sys.argv[2])))"
    family,user=json.loads(command('run','--rm','--no-deps','migrate','python','-c',script,email,password))
    login=request('/api/v1/auth/login',{'email':email,'password':password})
    assert login['user']['id']==user
    headers={'X-CSRF-Token':login['csrf_token'],'Idempotency-Key':str(uuid4())}
    saved=request('/api/v1/commitments',{'description':'Compose persistence','buyer_id':user,'purchased_at':'2026-09-24','first_month':'2026-10-01','total_cents':10000,'count':1,'shares':[{'user_id':user,'weight':10000}]},headers)
    assert saved['installments'][0]['amount_cents']==10000
    # Runtime role is actually in use and cannot bypass family RLS.
    assert sql("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname='expense_runtime'")=='f'
    with tempfile.NamedTemporaryFile(suffix='.dump') as backup:
        os.chmod(backup.name,0o600)
        backup.write(command('exec','-T','db','pg_dump','-U','expense_owner','-d','expense','-Fc'))
        backup.flush()
        restore='verify_'+uuid4().hex[:16]
        sql('CREATE DATABASE '+restore)
        try:
            backup.seek(0)
            command('exec','-T','db','pg_restore','-U','expense_owner','-d',restore,'--exit-on-error',input=backup.read())
            assert sql("SELECT total_cents FROM commitments WHERE id='"+saved['id']+"'",restore)=='10000'
        finally:
            sql('DROP DATABASE '+restore)
    command('restart','api')
    for _ in range(30):
        try:
            if request('/health')=={'status':'ok'}:
                break
        except (urllib.error.URLError,TimeoutError):
            time.sleep(1)
    assert request('/api/v1/commitments/'+saved['id'])['installments'][0]['amount_cents']==10000
    print('PASS: private ports, readiness without email, login, runtime role, persistence and backup restoration.')

if __name__=='__main__':
    main()
