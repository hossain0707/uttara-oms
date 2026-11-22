"""Synthetic profile-to-official conversion, aggregate visibility and ledger conservation."""
from uuid import UUID
from test_endpoints import context, make_body
from test_master_security import setup_owner
from app.models import PersonalProfile, Member, MembershipDelta, OrgNode, AppUser, RoleGrant
from app.routes.personal import pack


def saved(h, w, who='editor', **changes):
    details = {'full_name':'Synthetic Hossain', 'category':'SUPPORTER', 'phone':'01700000009',
               'consent':True, 'identity_number':'1000000000', 'address':'Private address'}
    details.update(changes)
    with h['session_factory']() as db:
        db.add(PersonalProfile(user_id=w[who].id, details_encrypted=pack(details)))
        db.commit()


def body(unit, **changes):
    result = {'expected_profile_version':1,'mode':'CREATE','category':'WORKER','org_node_id':str(unit.id),
              'consent_attested':True,'duplicates_reviewed':True,'joined_on':'2020-01-01'}
    result.update(changes)
    return result


def test_current_profiles_separate_from_ledger_and_atomic_creation(context):
    c,h,w,unit=setup_owner(context)
    saved(h,w)
    saved(h,w,'outsider',full_name='বাংলা নাম',category=None,phone='01700000008')
    summary=c.get('/api/v1/reports/registered-summary').json()
    assert (summary['active_accounts'],summary['total_profiles'],summary['awaiting_confirmation'],summary['profiles_missing'])==(6,2,2,4)
    assert summary['by_category']['SUPPORTER']==1 and summary['by_category']['UNSPECIFIED']==1
    assert c.get('/api/v1/reports/dashboard').json()['total_active']==0
    assert c.get('/api/v1/master/confirmation-queue?q=হো').json()['total']==0
    assert c.get('/api/v1/master/confirmation-queue?q=বাংলা').json()['total']==1
    preview=c.get(f'/api/v1/master/accounts/{w["editor"].id}/membership').json()
    assert '1000000000' not in str(preview) and 'Private address' not in str(preview)
    path=f'/api/v1/master/accounts/{w["editor"].id}/membership'
    r=c.post(path,json=body(unit)); assert r.status_code==200,r.text
    member_id=UUID(r.json()['member_id'])
    assert c.post(path,json=body(unit)).status_code==409
    with h['session_factory']() as db:
        assert db.query(Member).count()==1 and db.query(MembershipDelta).count()==1
        m=db.get(Member,member_id)
        assert m.category=='WORKER' and m.address_encrypted is None
        assert db.get(PersonalProfile,w['editor'].id).member_id==m.id
        assert db.query(RoleGrant).filter_by(user_id=w['editor'].id).count()==1  # unchanged setup grant
    summary=c.get('/api/v1/reports/registered-summary').json()
    assert summary['awaiting_confirmation']==1 and summary['linked_profiles']==1
    assert summary['by_category']['SUPPORTER']==1  # saved category remains self-reported
    assert c.get('/api/v1/reports/dashboard?start_date=2020-01-01&end_date=2020-01-31').json()['total_active']==0
    assert c.get('/api/v1/reports/dashboard').json()['total_active']==1
    assert any(a['action']=='MEMBERSHIP_CONFIRMED' for a in c.get('/api/v1/master/activity').json()['items'])


def test_existing_phone_link_preserves_member_and_counts(context):
    c,h,w,unit=setup_owner(context);saved(h,w)
    existing=c.post('/api/v1/members',json=make_body(unit.id,phone='01700000009')).json()
    path=f'/api/v1/master/accounts/{w["editor"].id}/membership'
    assert c.get(path).json()['matches'][0]['match']=='PHONE'
    assert c.post(path,json=body(unit)).status_code==409
    link=body(unit,mode='LINK',member_id=existing['id'],expected_member_version=999)
    assert c.post(path,json=link).status_code==409
    link['expected_member_version']=existing['version']
    assert c.post(path,json=link).status_code==200
    with h['session_factory']() as db:
        assert db.query(Member).count()==1 and db.query(MembershipDelta).count()==1
        assert db.get(Member,UUID(existing['id'])).category=='SUPPORTER'
    saved(h,w,'outsider',phone='01700000009')
    path2=f'/api/v1/master/accounts/{w["outsider"].id}/membership'
    assert c.post(path2,json=link).status_code==409


def test_guards_stale_versions_inactive_units_and_rollback(context):
    c,h,w,unit=setup_owner(context);saved(h,w)
    path=f'/api/v1/master/accounts/{w["editor"].id}/membership'
    for key in ['consent_attested','duplicates_reviewed']:
        assert c.post(path,json=body(unit,**{key:False})).status_code==422
    assert c.post(path,json=body(unit,expected_profile_version=9)).status_code==409
    with h['session_factory']() as db:
        db.get(OrgNode,unit.parent_id).active=False;db.commit()
    assert c.post(path,json=body(unit)).status_code==422
    with h['session_factory']() as db:
        db.get(OrgNode,unit.parent_id).active=True;db.commit()
    c.post('/api/v1/members',json=make_body(unit.id,number='TAKEN'))
    assert c.post(path,json=body(unit,member_number='TAKEN')).status_code==409
    with h['session_factory']() as db:
        assert db.query(Member).count()==1 and db.query(MembershipDelta).count()==1
        assert db.get(PersonalProfile,w['editor'].id).member_id is None
    from dataclasses import replace
    h['actor']=replace(w['admin'], mfa=False)
    assert c.post(path,json=body(unit)).status_code==403
    h['actor']=w['admin2']
    assert c.post(path,json=body(unit)).status_code==403
    assert c.get('/api/v1/master/confirmation-queue').status_code==403
    h['actor']=w['editor']
    summary=c.get('/api/v1/reports/registered-summary').json()
    assert summary['total_profiles']==0  # requested/unlinked profiles never expand staff scope


def test_summary_excludes_incomplete_nonconsented_and_inactive(context):
    c,h,w,unit=setup_owner(context)
    saved(h,w,consent=False);saved(h,w,'outsider',full_name='   ');saved(h,w,'reviewer')
    with h['session_factory']() as db:
        db.get(AppUser,w['reviewer'].id).active=False;db.commit()
    r=c.get('/api/v1/reports/registered-summary').json()
    assert r['active_accounts']==5 and r['total_profiles']==0 and r['profiles_missing']==5
    assert c.get('/api/v1/master/confirmation-queue').json()['total']==0
    assert c.post(f'/api/v1/master/accounts/{w["editor"].id}/membership',json=body(unit)).status_code==422


def test_scoped_summary_only_sees_official_links_in_approved_scope(context):
    c,h,w,unit=setup_owner(context);saved(h,w);saved(h,w,'outsider',phone='01700000008')
    c.post(f'/api/v1/master/accounts/{w["editor"].id}/membership',json=body(unit))
    h['actor']=w['reviewer']
    summary=c.get('/api/v1/reports/registered-summary').json()
    assert not summary['global_scope'] and summary['total_profiles']==1 and summary['awaiting_confirmation']==0
    h['actor']=w['outsider']
    assert c.get('/api/v1/reports/registered-summary').json()['total_profiles']==0
    h['actor']=w['viewer']
    summary=c.get('/api/v1/reports/registered-summary').json()
    assert summary['global_scope'] and summary['total_profiles']==2
    assert 'Synthetic Hossain' not in str(summary)
