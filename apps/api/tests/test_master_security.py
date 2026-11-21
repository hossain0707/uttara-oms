"""Synthetic owner authority, two-person review, live expiry and revocation."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID
import pytest
from fastapi import HTTPException
from test_endpoints import context
from app.models import AuditLog, RoleGrant, AppUser
from app import security_policy as policy
from app.auth import account_actor


def setup_owner(context):
    c,h,w,unit,_=context
    with h['session_factory']() as db:
        for name,role,scope in [('admin','THANA_ADMIN',None),('admin2','THANA_ADMIN',None),('editor','UNIT_EDITOR',unit.id)]:
            db.add(RoleGrant(user_id=w[name].id,role=role,scope_node_id=scope))
        db.add(AuditLog(actor_id=w['admin'].id,action=policy.OWNER_EVENT,target_id=str(w['admin'].id),detail='Synthetic owner configuration'))
        db.commit()
    h['actor']=w['admin']
    return c,h,w,unit


def login_as(context, monkeypatch, name, aal='aal1'):
    _,h,w,*_=context
    monkeypatch.setattr('app.auth.jwt_claims',lambda _: {'sub':str(w[name].id),'aal':aal})
    with h['session_factory']() as db:
        return account_actor(SimpleNamespace(credentials='synthetic'),db)


def test_owner_exceptions_independent_approval_revocation(context,monkeypatch):
    c,h,w,unit=setup_owner(context)
    assert c.get('/api/v1/master/security').json()['is_owner'] is True
    body={'user_id':str(w['editor'].id),'reason':'Temporary phone replacement','until':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}
    own=c.post('/api/v1/master/exceptions',json={**body,'user_id':str(w['admin'].id)})
    assert own.status_code==403
    h['actor']=w['admin2']
    assert c.post('/api/v1/master/exceptions',json=body).status_code==403
    assert c.get('/api/v1/master/security').json()['items']==[]
    h['actor']=w['admin']
    request=c.post('/api/v1/master/exceptions',json=body)
    assert request.status_code==201,request.text
    rid=request.json()['id']
    assert c.post('/api/v1/master/exceptions',json=body).status_code==409
    assert c.post(f'/api/v1/master/exceptions/{rid}/decision',json={'approve':True}).status_code==403
    with pytest.raises(HTTPException,match='Administrator MFA required'):
        login_as(context,monkeypatch,'editor')
    h['actor']=w['admin2']
    approved=c.post(f'/api/v1/master/exceptions/{rid}/decision',json={'approve':True})
    assert approved.status_code==200,approved.text
    assert c.post(f'/api/v1/master/exceptions/{rid}/decision',json={'approve':True}).status_code==409
    assert login_as(context,monkeypatch,'editor').mfa is False
    with pytest.raises(HTTPException,match='Administrator MFA required'):
        login_as(context,monkeypatch,'admin')
    h['actor']=w['admin']
    data=c.get('/api/v1/master/security').json()
    target=next(a for a in data['items'] if a['id']==str(w['editor'].id))
    assert target['policy']['exempt'] is True
    pid=target['policy']['id']
    assert c.post(f'/api/v1/master/exceptions/{w["editor"].id}/revoke',json={'expected_policy_id':str(w['admin'].id)}).status_code==409
    assert c.post(f'/api/v1/master/exceptions/{w["editor"].id}/revoke',json={'expected_policy_id':pid}).status_code==200
    with pytest.raises(HTTPException,match='Administrator MFA required'):
        login_as(context,monkeypatch,'editor')


def test_expired_exceptions_owner_protection_and_account_status(context,monkeypatch):
    c,h,w,_=setup_owner(context)
    with h['session_factory']() as db:
        for who in ['editor','admin']:
            policy.event(db,w['admin2'],policy.POLICY_EVENT,w[who].id,{'exempt':True,'until':(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),'reason':'Expired synthetic rule'})
        db.commit()
    with pytest.raises(HTTPException,match='Administrator MFA required'):
        login_as(context,monkeypatch,'editor')
    with pytest.raises(HTTPException,match='Administrator MFA required'):
        login_as(context,monkeypatch,'admin')
    assert c.post(f'/api/v1/master/accounts/{w["admin"].id}/status',json={'expected_active':True,'active':False}).status_code==403
    # Maintain two independent Thana administrators.
    assert c.post(f'/api/v1/master/accounts/{w["admin2"].id}/status',json={'expected_active':True,'active':False}).status_code==409
    suspended=c.post(f'/api/v1/master/accounts/{w["editor"].id}/status',json={'expected_active':True,'active':False})
    assert suspended.status_code==200,suspended.text
    with pytest.raises(HTTPException,match='Account has not been approved'):
        login_as(context,monkeypatch,'editor','aal2')
    assert c.post(f'/api/v1/master/accounts/{w["editor"].id}/status',json={'expected_active':True,'active':True}).status_code==409
    assert c.post(f'/api/v1/master/accounts/{w["editor"].id}/status',json={'expected_active':False,'active':True}).status_code==200
    assert login_as(context,monkeypatch,'admin','aal2').is_master_admin is True
    assert login_as(context,monkeypatch,'admin2','aal2').is_master_admin is False


def test_target_admin_cannot_approve_own_exception_and_expiry_validation(context):
    c,h,w,_=setup_owner(context)
    body={'user_id':str(w['admin2'].id),'reason':'Temporary replacement'}
    assert c.post('/api/v1/master/exceptions',json={**body,'until':'2020-01-01T00:00:00Z'}).status_code==422
    response=c.post('/api/v1/master/exceptions',json=body)
    assert response.status_code==201,response.text
    h['actor']=w['admin2']
    rid=response.json()['id']
    assert c.post(f'/api/v1/master/exceptions/{rid}/decision',json={'approve':True}).status_code==403
    assert c.post(f'/api/v1/master/exceptions/{rid}/decision',json={'approve':False}).status_code==200
    assert c.get('/api/v1/master/security').json()['pending']==[]


def test_protected_owner_role_and_suspended_account_cannot_be_reenabled_by_grant(context):
    c,h,w,_=setup_owner(context)
    h['actor']=w['admin2']
    request=c.post('/api/v1/access/requests',json={'auth_sub':str(w['admin'].id),'email':w['admin'].email,'role':'THANA_ADMIN','operation':'REVOKE'})
    assert request.status_code==201,request.text
    h['actor']=w['admin']
    result=c.post('/api/v1/access/requests/'+request.json()['id']+'/decision',json={'approve':True})
    assert result.status_code==403 and 'protected' in result.text
    c.post(f'/api/v1/master/accounts/{w["editor"].id}/status',json={'expected_active':True,'active':False})
    request=c.post('/api/v1/access/requests',json={'auth_sub':str(w['editor'].id),'email':w['editor'].email,'role':'THANA_ADMIN','operation':'GRANT'})
    assert request.status_code==201,request.text
    h['actor']=w['admin2']
    result=c.post('/api/v1/access/requests/'+request.json()['id']+'/decision',json={'approve':True})
    assert result.status_code==409 and 'reactivate' in result.text


def test_policy_without_owner_configuration_and_non_mfa_admin_fail_closed(context,monkeypatch):
    from app.auth import Actor
    c,h,w,_=setup_owner(context)
    with h['session_factory']() as db:
        policy.event(db,w['admin2'],policy.POLICY_EVENT,w['editor'].id,{'exempt':True,'until':None,'reason':'Synthetic rule'})
        db.query(AuditLog).filter(AuditLog.action==policy.OWNER_EVENT).delete()
        db.commit()
    with pytest.raises(HTTPException,match='Administrator MFA required'):
        login_as(context,monkeypatch,'editor')
    h['actor']=Actor(w['admin'].id,w['admin'].email,w['admin'].grants,False)
    assert c.get('/api/v1/master/security').status_code==403
