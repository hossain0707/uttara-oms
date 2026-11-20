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
    assert len(c.get("/api/v1/reviews").json()["items"]) == 1
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
                "details": {"full_name": "Synthetic", "consent": True},
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
