"""Synthetic ownership, workflow and role-escalation regression tests."""

from test_endpoints import context, registration_claims, real_auth
from app.models import Member, PersonalProfile, PersonalReport, RoleGrant, AppUser
from uuid import UUID
import pytest


def test_private_reports_and_independent_review(context):
    c, h, w, unit, _ = context
    owner = w["editor"]
    body = {
        "expected_version": 0,
        "details": {
            "full_name": "Private synthetic profile",
            "identity_type": "NID", "identity_number": "1000000000",
            "phone": "01700000009",
            "category": "WORKER",
            "consent": True,
        },
    }
    r = c.put("/api/v1/self/profile", json=body)
    assert r.status_code == 200, r.text
    assert c.put("/api/v1/self/profile", json=body).status_code == 409
    assert (
        c.put("/api/v1/self/profile", json={**body, "role": "THANA_ADMIN"}).status_code
        == 422
    )
    with h["session_factory"]() as db:
        assert (
            "Private synthetic"
            not in db.get(PersonalProfile, owner.id).details_encrypted
        )
        db.add(
            RoleGrant(
                user_id=w["reviewer"].id,
                role="WARD_ADMIN",
                scope_node_id=unit.parent_id,
            )
        )
        db.commit()
    report = {
        "month": "2020-02-01",
        "expected_version": 0,
        "entries": [{"day": "2020-02-01", "prayers": 5, "organization": 90}],
        "summary": "Private synthetic report",
        "consent": True,
    }
    draft = c.put("/api/v1/self/reports", json=report)
    assert draft.status_code == 200, draft.text
    assert draft.json()["totals"]["prayers"] == 5
    assert draft.json()["calendar_days"] == 29
    assert (
        c.put(
            "/api/v1/self/reports",
            json={**report, "expected_version": 1, "submit": True},
        ).status_code
        == 422
    )
    h["actor"] = w["outsider"]
    assert c.get("/api/v1/self/reports").json()["items"] == []
    assert c.get("/api/v1/reviews").json()["items"] == []
    h["actor"] = w["admin"]
    assigned = c.put(
        f"/api/v1/access/personal/{owner.id}",
        json={
            "expected_version": 1,
            "reviewer_id": str(w["reviewer"].id),
            "goals": [{"metric": "prayers", "target": 140}],
        },
    )
    assert assigned.status_code == 200, assigned.text
    assert "details" not in assigned.json()
    assert c.get("/api/v1/reviews").json()["items"] == []
    h["actor"] = owner
    submitted = c.put(
        "/api/v1/self/reports", json={**report, "expected_version": 1, "submit": True}
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["progress"][0]["remaining"] == 135
    assert (
        c.put(
            "/api/v1/self/reports", json={**report, "expected_version": 2}
        ).status_code
        == 409
    )
    rid = submitted.json()["id"]
    decision = {
        "expected_version": 2,
        "decision": "RETURNED",
        "note": "Check daily entry",
    }
    assert c.post(f"/api/v1/reviews/{rid}", json=decision).status_code == 403
    h["actor"] = w["reviewer"]
    queue = c.get("/api/v1/reviews").json()["items"]
    assert len(queue) == 1
    assert "identity_number" not in queue[0]["profile"]
    assert "identity_type" not in queue[0]["profile"]
    assert c.post(f"/api/v1/reviews/{rid}", json=decision).status_code == 200
    assert c.post(f"/api/v1/reviews/{rid}", json=decision).status_code == 409
    h["actor"] = owner
    assert (
        c.put(
            "/api/v1/self/reports", json={**report, "expected_version": 3}
        ).status_code
        == 200
    )
    with h["session_factory"]() as db:
        assert (
            "Private synthetic report"
            not in db.get(PersonalReport, UUID(rid)).content_encrypted
        )
        assert db.query(Member).count() == 0


@pytest.mark.parametrize(
    "change",
    [
        {"entries": [{"day": "2020-03-01"}]},
        {"entries": [{"day": "2020-02-01"}, {"day": "2020-02-01"}]},
        {"entries": [{"day": "2020-02-01", "organization": 1441}]},
        {"consent": False},
        {"month": "2020-02-02"},
    ],
)
def test_report_validation(context, change):
    c, *_ = context
    assert (
        c.put(
            "/api/v1/self/reports",
            json={
                "month": "2020-02-01",
                "expected_version": 0,
                "entries": [],
                "consent": True,
                **change,
            },
        ).status_code
        == 422
    )


def test_normal_application_master_approval_and_email_signup(context, monkeypatch):
    claims = registration_claims()
    claims["app_metadata"] = {"provider": "email"}
    c, h, headers = real_auth(context, monkeypatch, claims)
    assert c.post("/api/v1/account/register", headers=headers).status_code == 200
    assert c.get("/api/v1/self/profile", headers=headers).status_code == 200
    assert (
        c.post(
            "/api/v1/access/apply", headers=headers, json={"role": "THANA_ADMIN"}
        ).status_code
        == 422
    )
    request = {"role": "UNIT_EDITOR", "scope_node_id": str(context[3].id)}
    assert (
        c.post(
            "/api/v1/access/apply",
            headers=headers,
            json={**request, "auth_sub": str(context[2]["admin"].id)},
        ).status_code
        == 422
    )
    applied = c.post("/api/v1/access/apply", headers=headers, json=request)
    assert applied.status_code == 201, applied.text
    assert (
        c.post("/api/v1/access/apply", headers=headers, json=request).status_code == 409
    )
    assert (
        len(c.get("/api/v1/access/my-requests", headers=headers).json()["items"]) == 1
    )
    assert c.get("/api/v1/access/requests", headers=headers).status_code == 403
    admin = context[2]["admin"]
    with h["session_factory"]() as db:
        user = db.query(AppUser).filter(AppUser.auth_sub == claims["sub"]).one()
        assert db.query(RoleGrant).filter(RoleGrant.user_id == user.id).count() == 0
        db.add(RoleGrant(user_id=admin.id, role="THANA_ADMIN"))
        db.commit()
    original = claims["sub"]
    claims.update(sub=str(admin.id), aal="aal2")
    assert (
        c.post(
            "/api/v1/access/requests/" + applied.json()["id"] + "/decision",
            headers=headers,
            json={"approve": True},
        ).status_code
        == 200
    )
    claims.update(sub=original, aal="aal1")
    assert (
        c.get("/api/v1/me", headers=headers).json()["detail"]
        == "Administrator MFA required"
    )
    claims["aal"] = "aal2"
    assert (
        c.get("/api/v1/me", headers=headers).json()["roles"][0]["role"] == "UNIT_EDITOR"
    )


@pytest.mark.parametrize(
    "role", ["THANA_ADMIN", "THANA_VIEWER", "WARD_ADMIN", "UNIT_EDITOR"]
)
def test_every_leader_requires_mfa(context, monkeypatch, role):
    claims = registration_claims()
    c, h, headers = real_auth(context, monkeypatch, claims)
    assert c.post("/api/v1/account/register", headers=headers).status_code == 200
    with h["session_factory"]() as db:
        user = db.query(AppUser).filter(AppUser.auth_sub == claims["sub"]).one()
        db.add(
            RoleGrant(
                user_id=user.id,
                role=role,
                scope_node_id=None if role.startswith("THANA") else context[3].id,
            )
        )
        db.commit()
    assert (
        c.get("/api/v1/me", headers=headers).json()["detail"]
        == "Administrator MFA required"
    )
    claims["aal"] = "aal2"
    assert c.get("/api/v1/me", headers=headers).status_code == 200


def test_personal_exports_owner_only_and_spreadsheet_text(context):
    import zipfile
    from io import BytesIO

    c, h, w, *_ = context
    assert (
        c.put(
            "/api/v1/self/profile",
            json={
                "expected_version": 0,
                "details": {"full_name": "Synthetic", "consent": True, "identity_type":"NID", "identity_number":"1000000000"},
            },
        ).status_code
        == 200
    )
    saved = c.put(
        "/api/v1/self/reports",
        json={
            "month": "2020-02-01",
            "expected_version": 0,
            "entries": [
                {
                    "day": "2020-02-01",
                    "prayers": 0,
                    "notes": '=HYPERLINK("https://invalid.example")',
                }
            ],
            "summary": "<script>alert(1)</script>",
            "consent": True,
        },
    )
    rid = saved.json()["id"]
    x = c.get(f"/api/v1/self/reports/{rid}/export/xlsx")
    assert x.status_code == 200
    with zipfile.ZipFile(BytesIO(x.content)) as z:
        assert b"<f>" not in z.read("xl/worksheets/sheet1.xml")
    pdf = c.get(f"/api/v1/self/reports/{rid}/export/pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    h["actor"] = w["admin"]
    assert c.get(f"/api/v1/self/reports/{rid}/export/xlsx").status_code == 404
    assert c.get(f"/api/v1/self/reports/{rid}/export/pdf").status_code == 404


def test_profile_without_identity_photo_and_directory_privacy(context):
    import base64
    from io import BytesIO
    from PIL import Image
    from test_endpoints import make_body
    from app.routes.personal import unpack

    c, h, w, unit, _ = context
    image = BytesIO()
    Image.new("RGB", (40, 40), "green").save(image, format="JPEG")
    photo = "data:image/jpeg;base64," + base64.b64encode(image.getvalue()).decode()
    details = {"full_name": "Synthetic owner", "identity_type": "NID",
               "identity_number": "১০০০০০০০০০", "photo": photo, "consent": True}
    assert c.put("/api/v1/self/profile", json={"expected_version": 0, "details": {"consent": True}}).status_code == 422
    assert c.put("/api/v1/self/profile", json={"expected_version": 0, "details": {**details, "photo": "data:image/svg+xml;base64,PHN2Zz4="}}).status_code == 422
    saved = c.put("/api/v1/self/profile", json={"expected_version": 0, "details": details})
    assert saved.status_code == 200, saved.text
    assert "identity_number" not in saved.json()["details"]
    assert "identity_type" not in saved.json()["details"]
    member = c.post("/api/v1/members", json=make_body(unit.id)).json()
    with h["session_factory"]() as db:
        profile = db.get(PersonalProfile, w["editor"].id)
        assert "1000000000" not in profile.details_encrypted
        assert "data:image" not in profile.details_encrypted
        profile.member_id = UUID(member["id"])
        db.commit()
    assert c.get("/api/v1/members").json()["items"][0]["photo"] == ""
    # Sharing is explicit, restricted to an independently linked record and existing scope.
    shared = c.put("/api/v1/self/profile", json={"expected_version": 1, "details": {**details, "directory_sharing": True}})
    assert shared.status_code == 200
    directory = c.get("/api/v1/members").json()
    assert directory["items"][0]["photo"].startswith("data:image/jpeg;base64,")
    assert "identity_number" not in str(directory)
    assert "1000000000" not in str(directory)
    assert "identity_number" not in c.get(f'/api/v1/members/{member["id"]}').text
    h["actor"] = w["outsider"]
    assert c.get("/api/v1/members").json()["items"] == []
    assert c.get(f'/api/v1/members/{member["id"]}').status_code == 403
    h["actor"] = w["editor"]
    # Reading-only saves retain sharing settings and do not restore removed identity fields.
    reading = c.put("/api/v1/self/profile", json={"expected_version": 2, "section": "reading", "details": {"consent": True, "books": [{"title": "Synthetic book"}]}})
    assert reading.status_code == 200, reading.text
    assert "identity_number" not in reading.json()["details"]
    assert reading.json()["details"]["directory_sharing"] is True
    revoked = c.put("/api/v1/self/profile", json={"expected_version": 3, "details": {**details, "directory_sharing": False}})
    assert revoked.status_code == 200
    assert c.get("/api/v1/members").json()["items"][0]["photo"] == ""


def test_name_only_profile_saves_and_legacy_identity_is_not_returned(context):
    from app.routes.personal import pack, unpack
    c,h,w,_,_=context
    result=c.put('/api/v1/self/profile',json={'expected_version':0,'details':{'full_name':'বাংলা নাম','consent':True}})
    assert result.status_code==200,result.text
    with h['session_factory']() as db:
        profile=db.get(PersonalProfile,w['editor'].id)
        details=unpack(profile.details_encrypted)
        details.update(identity_type='NID',identity_number='1000000000')
        profile.details_encrypted=pack(details);db.commit()
    assert 'identity_number' not in c.get('/api/v1/self/profile').text
    reading=c.put('/api/v1/self/profile',json={'expected_version':1,'section':'reading','details':{'consent':True}})
    assert reading.status_code==200,reading.text
    with h['session_factory']() as db:
        assert 'identity_number' not in unpack(db.get(PersonalProfile,w['editor'].id).details_encrypted)


def test_daily_salah_limit_is_enforced_on_the_server(context):
    c,h,w,unit,_=context
    assert c.put('/api/v1/self/profile',json={'expected_version':0,'details':{'full_name':'Synthetic Salah boundary','consent':True}}).status_code==200
    base={'month':'2020-01-01','expected_version':0,'consent':True,'entries':[{'day':'2020-01-01','prayers':6}]}
    for invalid in [6,-1,1.5,100]:
        assert c.put('/api/v1/self/reports',json={**base,'entries':[{'day':'2020-01-01','prayers':invalid}]}).status_code==422
    for version,value in enumerate([None,0,5]):
        r=c.put('/api/v1/self/reports',json={**base,'expected_version':version,'entries':[{'day':'2020-01-01','prayers':value}]})
        assert r.status_code==200,r.text
        assert r.json()['entries'][0]['prayers']==value
