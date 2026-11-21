"""Unified search uses synthetic identities only; no deployment data."""
from test_endpoints import context, make_body
from app.models import PersonalProfile
from app.routes.personal import pack


def save_profile(holder, user, name, **extra):
    with holder['session_factory']() as db:
        row = db.get(PersonalProfile, user.id)
        if row is None:
            row = PersonalProfile(user_id=user.id)
            db.add(row)
        row.details_encrypted = pack(dict(full_name=name, consent=True, category='SUPPORTER',
            identity_number='1234567890', phone='01700000001', current_address='Private address',
            books=[{'title':'Private reading'}], **extra))
        db.commit()


def test_saved_names_partial_matching_and_allowlist(context):
    client, holder, who, _, _ = context
    save_profile(holder, who['editor'], 'Md Hossain')
    save_profile(holder, who['outsider'], 'মোঃ হোসাইন', photo='private-photo')
    holder['actor'] = who['admin']
    result = client.get('/api/v1/directory?q=HOS').json()
    assert result['total'] == 1
    item = result['items'][0]
    assert item['full_name'] == 'Md Hossain'
    assert item['source'] == 'PROFILE' and item['self_reported']
    assert not {'identity_number','identity_type','books','email','current_address','goals'} & item.keys()
    assert item['phone'] is None and item['address'] is None
    bangla = client.get('/api/v1/directory', params={'q':'হো'}).json()
    assert bangla['total'] == 1 and bangla['items'][0]['full_name'] == 'মোঃ হোসাইন'
    assert bangla['items'][0]['photo'] == ''
    assert client.get('/api/v1/directory?q=%25_').json()['total'] == 0
    # Changing one saved name is immediately reflected; no second-language name required.
    save_profile(holder, who['editor'], 'Ahmed')
    assert client.get('/api/v1/directory?q=Hossain').json()['total'] == 0
    assert client.get('/api/v1/directory?q=ah').json()['total'] == 1
    pages = [client.get('/api/v1/directory', params={'limit':1,'offset':n}).json() for n in [0,1]]
    assert all(p['total']==2 for p in pages)
    assert pages[0]['items'][0]['id'] != pages[1]['items'][0]['id']


def test_scope_deduplication_and_authoritative_category(context):
    client, holder, who, unit1, unit2 = context
    first = client.post('/api/v1/members', json=make_body(unit1.id)).json()
    holder['actor'] = who['outsider']
    second = client.post('/api/v1/members', json=make_body(unit2.id,'TEST-0002','01700000002')).json()
    save_profile(holder, who['editor'], 'Linked Alias', photo='shared-photo', directory_sharing=True)
    save_profile(holder, who['outsider'], 'Outside Alias')
    save_profile(holder, who['admin2'], 'Unlinked requested', requested_unit_id=str(unit1.id))
    with holder['session_factory']() as db:
        import uuid
        db.get(PersonalProfile, who['editor'].id).member_id=uuid.UUID(first['id'])
        db.get(PersonalProfile, who['outsider'].id).member_id=uuid.UUID(second['id'])
        db.commit()
    holder['actor'] = who['reviewer']
    result=client.get('/api/v1/directory').json()
    assert result['total']==1 and result['items'][0]['source']=='MEMBER'
    assert result['items'][0]['photo']=='shared-photo'
    assert client.get('/api/v1/directory?q=linked').json()['total']==1
    assert client.get('/api/v1/directory?q=Outside').json()['total']==0
    assert client.get('/api/v1/directory?q=requested').json()['total']==0
    holder['actor']=who['admin']
    assert client.get('/api/v1/directory').json()['total']==3
    assert client.get('/api/v1/directory?category=WORKER').json()['total']==0
    holder['actor']=who['viewer']
    assert client.get('/api/v1/directory').status_code==403
