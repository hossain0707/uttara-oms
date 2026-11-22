"""Synthetic direct-owner controls, privacy, pagination and irreversible workspace erasure."""
from uuid import uuid4, UUID
from dataclasses import replace
from datetime import date
from test_endpoints import context, make_body
from test_master_security import setup_owner, login_as
from app.models import AppUser, PersonalProfile, PersonalReport, RoleGrant, AuditLog, AccessRequest
from app.routes.personal import pack, unpack
from app import security_policy as policy
from fastapi import HTTPException
import pytest


def account(c, user):
    result=c.get('/api/v1/master/accounts',params={'q':user.email})
    assert result.status_code==200,result.text
    return next(a for a in result.json()['items'] if a['id']==str(user.id))


def role_body(a, operation='GRANT', role='THANA_VIEWER', **extra):
    return {'operation':operation,'role':role,'expected_roles_version':a['roles_version'],**extra}


def test_owner_roles_replace_stale_and_ordinary_review_stays(context):
    c,h,w,unit=setup_owner(context)
    a=account(c,w['editor']);path=f'/api/v1/master/accounts/{a["id"]}/roles'
    assert c.post(path,json=role_body(a)).json()['status']=='APPLIED'
    assert c.post(path,json=role_body(a,role='THANA_ADMIN')).status_code==409
    a=account(c,w['editor']);old=next(g for g in a['roles'] if g['role']=='UNIT_EDITOR')
    # Invalid replacement cannot remove the prior permission.
    assert c.post(path,json=role_body(a,'REPLACE','WARD_ADMIN',grant_id=old['id'],scope_node_id=str(unit.id))).status_code==422
    assert len(account(c,w['editor'])['roles'])==2
    assert c.post(path,json=role_body(a,'REPLACE','THANA_ADMIN',grant_id=old['id'])).status_code==200
    a=account(c,w['editor']);assert {g['role'] for g in a['roles']}=={'THANA_ADMIN','THANA_VIEWER'}
    grant=next(g for g in a['roles'] if g['role']=='THANA_ADMIN')
    assert c.post(path,json=role_body(a,'REVOKE',grant['role'],grant_id=grant['id'])).status_code==200
    # The owner can remove the other administrator, but never their own protected grant.
    a=account(c,w['admin2']);g=a['roles'][0]
    assert c.post(f'/api/v1/master/accounts/{a["id"]}/roles',json=role_body(a,'REVOKE',g['role'],grant_id=g['id'])).status_code==200
    owner=account(c,w['admin']);g=owner['roles'][0]
    assert c.post(f'/api/v1/master/accounts/{owner["id"]}/roles',json=role_body(owner,'REVOKE',g['role'],grant_id=g['id'])).status_code==403
    h['actor']=w['admin2']
    request=c.post('/api/v1/access/requests',json={'auth_sub':str(w['editor'].id),'email':w['editor'].email,'role':'THANA_ADMIN','operation':'GRANT'})
    assert request.json()['status']=='PENDING'
    assert c.post('/api/v1/access/requests/'+request.json()['id']+'/decision',json={'approve':True}).status_code==403
    h['actor']=w['admin']
    assert c.post('/api/v1/access/requests/'+request.json()['id']+'/decision',json={'approve':True}).status_code==200


def test_owner_authority_cannot_be_forged_or_used_without_mfa(context):
    c,h,w,_=setup_owner(context)
    a=account(c,w['editor'])
    for actor in [replace(w['admin2'],is_master_admin=True),replace(w['admin'],mfa=False,is_master_admin=True),w['reviewer']]:
        h['actor']=actor
        assert c.get('/api/v1/master/accounts').status_code==403
        assert c.get('/api/v1/master/requests').status_code==403
        assert c.get(f'/api/v1/master/accounts/{a["id"]}/deletion-preview').status_code==403
        assert c.post(f'/api/v1/master/accounts/{a["id"]}/roles',json=role_body(a)).status_code==403


def test_more_than_1000_accounts_name_search_and_minimal_projection(context):
    c,h,w,_=setup_owner(context)
    with h['session_factory']() as db:
        for i in range(1001):
            uid=uuid4();db.add(AppUser(id=uid,auth_sub=str(uid),email=f'synthetic-{i:04d}@example.invalid',active=True))
            if i==1000:
                db.flush();db.add(PersonalProfile(user_id=uid,details_encrypted=pack({'full_name':'মোঃ হোসাইন','identity_number':'1234567890','books':[{'title':'Private'}],'consent':True})))
        db.commit()
    response=c.get('/api/v1/master/accounts?limit=20&offset=1000').json()
    assert response['total']==1007 and len(response['items'])==7
    assert response['stats']['registered']==1007
    result=c.get('/api/v1/master/accounts',params={'q':'হো'}).json()
    assert result['total']==1 and result['items'][0]['full_name']=='মোঃ হোসাইন'
    assert not {'identity_number','photo','books','reports','phone','details'} & result['items'][0].keys()
    assert c.get('/api/v1/master/accounts?q=%25_').json()['total']==0


def test_direct_membership_change_and_owner_pending_decision(context):
    c,h,w,unit=setup_owner(context)
    member=c.post('/api/v1/members',json=make_body(unit.id)).json()
    response=c.post(f'/api/v1/approvals/members/{member["id"]}',json={'kind':'CATEGORY','proposed_value':'WORKER'})
    assert response.status_code==201 and response.json()['status']=='APPROVED'
    assert c.get('/api/v1/members/'+member['id']).json()['category']=='WORKER'
    h['actor']=w['editor']
    request=c.post(f'/api/v1/approvals/members/{member["id"]}',json={'kind':'DEACTIVATE','proposed_value':'INACTIVE'}).json()
    assert request['status']=='PENDING'
    h['actor']=w['admin']
    pending=c.get('/api/v1/master/requests?kind=member').json()
    assert pending['total']==1
    assert c.post('/api/v1'+pending['items'][0]['path'],json={'approve':True}).status_code==200
    assert c.get('/api/v1/members/'+member['id']).json()['status']=='INACTIVE'


def test_delete_workspace_is_guarded_permanent_and_preserves_history(context,monkeypatch):
    c,h,w,unit=setup_owner(context)
    member=c.post('/api/v1/members',json=make_body(unit.id)).json()
    target=w['editor'];base=f'/api/v1/master/accounts/{target.id}'
    with h['session_factory']() as db:
        db.add(PersonalProfile(user_id=target.id,member_id=UUID(member['id']),details_encrypted=pack({'full_name':'Private Name','identity_number':'1234567890','consent':True}),goals_encrypted=pack({'items':[{'metric':'prayers','target':140}]})))
        db.add(PersonalReport(user_id=target.id,month=date(2020,1,1),content_encrypted=pack({'entries':[{'notes':'Private notes'}]}),version=1))
        policy.event(db,w['admin'],policy.REQUEST_EVENT,target.id,{'until':None,'reason':'Legacy synthetic','previous':None})
        db.add(AccessRequest(auth_sub=str(target.id),email=target.email,role='THANA_ADMIN',operation='GRANT',requested_by=w['admin2'].id))
        db.commit()
    assert c.get(f'/api/v1/master/accounts/{w["admin"].id}/deletion-preview').status_code==403
    preview=c.get(base+'/deletion-preview').json();assert preview['reports']==1
    assert c.post(base+'/delete-workspace',json={'confirmation_email':'wrong@example.invalid','expected_revision':preview['revision']}).status_code==409
    with h['session_factory']() as db:
        db.get(PersonalProfile,target.id).version+=1;db.commit()
    assert c.post(base+'/delete-workspace',json={'confirmation_email':target.email,'expected_revision':preview['revision']}).status_code==409
    preview=c.get(base+'/deletion-preview').json()
    result=c.post(base+'/delete-workspace',json={'confirmation_email':target.email,'expected_revision':preview['revision']})
    assert result.status_code==200 and result.json()['auth_identity_retained']
    assert c.post(base+'/status',json={'expected_active':False,'active':True}).status_code==409
    assert c.get('/api/v1/master/requests?kind=access').json()['total']==0
    assert c.get('/api/v1/master/requests?kind=security').json()['total']==0
    with h['session_factory']() as db:
        assert not db.get(AppUser,target.id).active
        assert db.get(PersonalProfile,target.id).details_encrypted is None
        report=db.query(PersonalReport).filter_by(user_id=target.id).one()
        assert unpack(report.content_encrypted)=={'entries':[],'summary':'','goals':[]}
        assert db.query(RoleGrant).filter_by(user_id=target.id).count()==0
        assert db.query(AuditLog).filter_by(action='MASTER_ACCOUNT_DELETED',target_id=str(target.id)).count()==1
    assert c.get('/api/v1/members/'+member['id']).status_code==200
    assert c.get('/api/v1/master/accounts?state=deleted').json()['total']==1
    with pytest.raises(HTTPException):login_as(context,monkeypatch,'editor','aal2')
