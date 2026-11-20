"""End-to-end route tests using entirely synthetic records and two independent actors."""
import uuid
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.auth import Actor, account_actor, current_actor
from app.database import Base, get_db
from app.main import app
from app.models import AppUser, OrgNode, RoleGrant


@pytest.fixture
def context():
    test_url = os.environ.get("TEST_DATABASE_URL")
    schema = "oms_test_" + uuid.uuid4().hex
    if test_url:
        admin_engine = create_engine(test_url)
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(test_url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    Local = sessionmaker(bind=engine, expire_on_commit=False)
    with Local() as db:
        root = OrgNode(kind="THANA", code="test-root", name="Test root")
        db.add(root); db.flush()
        ward1 = OrgNode(kind="WARD", code="test-ward-1", name="Test Ward 1", parent_id=root.id)
        ward2 = OrgNode(kind="WARD", code="test-ward-2", name="Test Ward 2", parent_id=root.id)
        db.add_all([ward1, ward2]); db.flush()
        unit1 = OrgNode(kind="UNIT", code="test-unit-1", name="Test Unit 1", parent_id=ward1.id)
        unit2 = OrgNode(kind="UNIT", code="test-unit-2", name="Test Unit 2", parent_id=ward2.id)
        db.add_all([unit1, unit2]); db.flush()
        db.commit()
    who = {
        "editor": Actor(uuid.uuid4(), "editor@example.invalid", [("UNIT_EDITOR", unit1.id)], False),
        "viewer": Actor(uuid.uuid4(), "viewer@example.invalid", [("THANA_VIEWER", None)], False),
        "outsider": Actor(uuid.uuid4(), "outsider@example.invalid", [("UNIT_EDITOR", unit2.id)], False),
        "reviewer": Actor(uuid.uuid4(), "reviewer@example.invalid", [("WARD_ADMIN", ward1.id)], True),
        "admin2": Actor(uuid.uuid4(), "admin2@example.invalid", [("THANA_ADMIN", None)], True),
        "admin": Actor(uuid.uuid4(), "admin@example.invalid", [("THANA_ADMIN", None)], True),
    }
    with Local() as db:
        for a in who.values():
            db.add(AppUser(id=a.id, auth_sub=str(a.id), email=a.email, active=True))
        db.commit()
    holder = {"actor": who["editor"], "session_factory": Local}

    def override_db():
        with Local() as db:
            yield db

    def override_actor():
        return holder["actor"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[current_actor] = override_actor
    app.dependency_overrides[account_actor] = override_actor
    try:
        with TestClient(app) as client:
            yield client, holder, who, unit1, unit2
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
        if test_url:
            with admin_engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin_engine.dispose()


def make_body(unit_id, number="TEST-0001", phone="01700000001", consent=True):
    return {
        "member_number": number, "full_name": "Synthetic Test Profile",
        "phone": phone, "category": "SUPPORTER", "org_node_id": str(unit_id),
        "consent_attested": consent, "consent_version": "v1",
    }


def test_consent_duplicate_and_scope(context):
    client, holder, who, unit1, unit2 = context
    bad = client.post("/api/v1/members", json=make_body(unit1.id, consent=False))
    assert bad.status_code == 422
    saved = client.post("/api/v1/members", json=make_body(unit1.id))
    assert saved.status_code == 201, saved.text
    member_id = saved.json()["id"]
    assert client.post("/api/v1/members", json=make_body(unit1.id, "TEST-0002", "+8801700000001")).status_code == 409
    assert client.get("/api/v1/members?q=01700000001").json()["total"] == 1
    holder["actor"] = who["outsider"]
    assert client.get("/api/v1/members").json()["total"] == 0
    assert client.get("/api/v1/members/"+member_id).status_code == 403
    assert client.post("/api/v1/members", json=make_body(unit1.id, "TEST-0003", "01700000003")).status_code == 403
    assert client.get("/api/v1/reports/export.xlsx?include_personal=true").status_code == 403


def test_sensitive_change_requires_independent_approval(context):
    client, holder, who, unit1, unit2 = context
    saved = client.post("/api/v1/members", json=make_body(unit1.id))
    assert saved.status_code == 201
    item = saved.json()
    assert client.patch("/api/v1/members/"+item["id"], json={
        "expected_version": item["version"], "category": "RUKON"}).status_code == 422
    request = client.post("/api/v1/approvals/members/"+item["id"],
                          json={"kind":"CATEGORY","proposed_value":"RUKON"})
    assert request.status_code == 201, request.text
    approval_id = request.json()["id"]
    assert client.post("/api/v1/approvals/"+approval_id+"/decision", json={"approve":True}).status_code == 403
    holder["actor"] = who["reviewer"]
    done = client.post("/api/v1/approvals/"+approval_id+"/decision", json={"approve":True})
    assert done.status_code == 200, done.text
    assert client.get("/api/v1/members/"+item["id"]).json()["category"] == "RUKON"
    dashboard = client.get("/api/v1/reports/dashboard").json()
    assert dashboard["total_active"] == 1
    assert dashboard["by_ward"][0]["count"] == 1
    history = client.get("/api/v1/members/"+item["id"]+"/history")
    assert history.status_code == 200
    assert {row["action"] for row in history.json()["items"]} == {"CREATED", "CATEGORY"}
    assert dashboard["by_category"]["RUKON"] == 1
    assert dashboard["this_month"]["increase"] == 1


def test_cross_ward_transfer_needs_thana_admin(context):
    client, holder, who, unit1, unit2 = context
    member = client.post("/api/v1/members", json=make_body(unit1.id)).json()
    request = client.post("/api/v1/approvals/members/"+member["id"],
                          json={"kind":"TRANSFER","proposed_value":str(unit2.id)})
    assert request.status_code == 201
    rid = request.json()["id"]
    holder["actor"] = who["reviewer"]
    assert client.post("/api/v1/approvals/"+rid+"/decision", json={"approve":True}).status_code == 403
    holder["actor"] = who["admin"]
    accepted = client.post("/api/v1/approvals/"+rid+"/decision", json={"approve":True})
    assert accepted.status_code == 200, accepted.text
    holder["actor"] = who["outsider"]
    assert client.get("/api/v1/members/"+member["id"]).status_code == 200



def test_access_grant_requires_second_admin(context):
    client, holder, who, unit1, unit2 = context
    from app.auth import Actor
    import uuid
    target = uuid.uuid4()
    holder["actor"] = who["admin"]
    response = client.post("/api/v1/access/requests", json={
        "auth_sub": str(target), "email": "synthetic-user@example.invalid",
        "role": "UNIT_EDITOR", "scope_node_id": str(unit1.id), "operation": "GRANT",
    })
    assert response.status_code == 201, response.text
    rid = response.json()["id"]
    assert client.post("/api/v1/access/requests/"+rid+"/decision",json={"approve":True}).status_code == 403
    reviewer = who["admin2"]
    holder["actor"] = reviewer
    approved = client.post("/api/v1/access/requests/"+rid+"/decision",json={"approve":True})
    assert approved.status_code == 200, approved.text
    people = client.get("/api/v1/access/users").json()["items"]
    assert any(p["auth_sub"] == str(target) and p["roles"][0]["role"] == "UNIT_EDITOR" for p in people)
    holder["actor"] = who["outsider"]
    assert client.get("/api/v1/access/users").status_code == 403



def test_report_only_role_cannot_read_sensitive_profiles(context):
    client, holder, who, unit1, unit2 = context
    member = client.post("/api/v1/members", json=make_body(unit1.id)).json()
    holder["actor"] = who["viewer"]
    assert client.get("/api/v1/reports/dashboard").status_code == 200
    assert client.get("/api/v1/members").status_code == 403
    assert client.get("/api/v1/members/"+member["id"]).status_code == 403
    assert client.get("/api/v1/approvals").status_code == 403


def test_invalid_patches_and_stale_versions(context):
    client, holder, who, unit1, unit2 = context
    member = client.post("/api/v1/members", json=make_body(unit1.id)).json()
    url = "/api/v1/members/" + member["id"]
    for value in (None, "  "):
        response = client.patch(url, json={"expected_version": 1, "full_name": value})
        assert response.status_code == 422
        assert all("input" not in error for error in response.json()["detail"])
    assert client.patch(url, json={"expected_version": 1, "occupation": "Teacher"}).status_code == 200
    assert client.patch(url, json={"expected_version": 1, "occupation": "Doctor"}).status_code == 409
    assert client.get(url).json()["occupation"] == "Teacher"
    bad = make_body(unit1.id, "TEST-2", "01700000002")
    bad["full_name"] = "  "
    assert client.post("/api/v1/members", json=bad).status_code == 422
    bad["full_name"] = "Valid Name"
    bad["status"] = "INACTIVE"
    assert client.post("/api/v1/members", json=bad).status_code == 422
    assert client.get(url).headers["cache-control"] == "no-store"


def test_inactive_unit_reactivation_is_blocked(context):
    client, holder, who, unit1, unit2 = context
    member = client.post("/api/v1/members", json=make_body(unit1.id)).json()
    def propose(kind, value):
        return client.post("/api/v1/approvals/members/"+member["id"], json={"kind":kind,"proposed_value":value}).json()["id"]
    rid = propose("DEACTIVATE", "INACTIVE")
    holder["actor"] = who["admin"]
    assert client.post(f"/api/v1/approvals/{rid}/decision", json={"approve":True}).status_code == 200
    assert client.patch(f"/api/v1/organization/nodes/{unit1.id}", json={"active":False}).status_code == 200
    holder["actor"] = who["editor"]
    rid = propose("REACTIVATE", "ACTIVE")
    holder["actor"] = who["admin"]
    assert client.post(f"/api/v1/approvals/{rid}/decision", json={"approve":True}).status_code == 409
    assert client.get("/api/v1/members/"+member["id"]).json()["status"] == "INACTIVE"
    assert client.patch(f"/api/v1/organization/nodes/{unit1.parent_id}", json={"active":False}).status_code == 200
    assert client.patch(f"/api/v1/organization/nodes/{unit1.id}", json={"active":True}).status_code == 409
    assert client.patch(f"/api/v1/organization/nodes/{unit1.id}", json={"name":None}).status_code == 422
    assert client.patch(f"/api/v1/organization/nodes/{unit1.id}", json={}).status_code == 422


def test_ledger_transfers_conserve_global_totals(context):
    client, holder, who, unit1, unit2 = context
    member = client.post("/api/v1/members", json=make_body(unit1.id)).json()
    rid = client.post("/api/v1/approvals/members/"+member["id"],
        json={"kind":"TRANSFER","proposed_value":str(unit2.id)}).json()["id"]
    holder["actor"] = who["admin"]
    assert client.post(f"/api/v1/approvals/{rid}/decision", json={"approve":True}).status_code == 200
    report = client.get("/api/v1/reports/dashboard").json()
    assert report["period"]["increase"] == 1
    assert report["period"]["decrease"] == 0
    assert report["total_active"] == 1
    holder["actor"] = who["editor"]
    report = client.get("/api/v1/reports/dashboard").json()
    assert report["period"]["increase"] == 1  # creation stays in original scope
    assert report["period"]["decrease"] == 1
    assert report["total_active"] == 0
    holder["actor"] = who["outsider"]
    report = client.get("/api/v1/reports/dashboard").json()
    assert report["period"]["increase"] == 1  # one transfer-in, not historical creation
    assert report["total_active"] == 1


def test_date_filters_and_exports(context):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from zipfile import ZipFile
    from io import BytesIO
    client, holder, who, unit1, unit2 = context
    client.post("/api/v1/members", json=make_body(unit1.id))
    today = datetime.now(ZoneInfo("Asia/Dhaka")).date()
    past = today - timedelta(days=1)
    result = client.get(f"/api/v1/reports/dashboard?start_date={past}&end_date={past}")
    assert result.status_code == 200
    assert result.json()["total_active"] == 0
    assert result.json()["period"]["increase"] == 0
    assert client.get(f"/api/v1/reports/dashboard?start_date={today}&end_date={past}").status_code == 422
    assert client.get(f"/api/v1/reports/dashboard?end_date={today+timedelta(days=1)}").status_code == 422
    assert client.get(f"/api/v1/reports/dashboard?start_date={today-timedelta(days=400)}").status_code == 422
    excel = client.get("/api/v1/reports/export.xlsx")
    assert excel.status_code == 200
    with ZipFile(BytesIO(excel.content)) as archive:
        assert "xl/workbook.xml" in archive.namelist()
        assert b"Current personal records" not in archive.read("xl/workbook.xml")
    pdf = client.get("/api/v1/reports/export.pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")


def test_access_scope_must_still_be_active(context):
    client, holder, who, unit1, unit2 = context
    holder["actor"] = who["admin"]
    rid = client.post("/api/v1/access/requests", json={
        "auth_sub":str(uuid.uuid4()), "email":"synthetic@example.invalid",
        "role":"UNIT_EDITOR", "scope_node_id":str(unit1.id),
    }).json()["id"]
    assert client.patch(f"/api/v1/organization/nodes/{unit1.id}", json={"active":False}).status_code == 200
    holder["actor"] = who["admin2"]
    assert client.post(f"/api/v1/access/requests/{rid}/decision", json={"approve":True}).status_code == 409
    assert client.post(f"/api/v1/access/requests/{rid}/decision", json={"approve":False}).status_code == 200


def test_postgres_concurrent_routine_edits(context):
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("PostgreSQL row locking requires TEST_DATABASE_URL")
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi import HTTPException
    from app.routes.members import update_routine
    from app.schemas import MemberRoutineUpdate
    client, holder, who, unit1, unit2 = context
    member = client.post("/api/v1/members", json=make_body(unit1.id)).json()
    barrier = Barrier(2)
    def change(occupation):
        with holder["session_factory"]() as db:
            barrier.wait(timeout=5)
            try:
                update_routine(uuid.UUID(member["id"]), MemberRoutineUpdate(expected_version=1, occupation=occupation), who["editor"], db)
                return 200
            except HTTPException as exc:
                return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(change, ("Teacher", "Doctor")))
    assert sorted(outcomes) == [200, 409]
    assert client.get("/api/v1/members/"+member["id"]).json()["version"] == 2


def test_historical_category_status_and_month_boundaries(context):
    from datetime import datetime, timezone
    from app.analytics import record_movement
    from app.models import Member, MemberEvent
    client, holder, who, unit1, unit2 = context
    member = client.post("/api/v1/members", json=make_body(unit1.id)).json()
    # Separate synthetic member with a known old timeline. Current data is deliberately
    # different from every historical snapshot under test.
    with holder["session_factory"]() as db:
        m = Member(member_number="OLD-01", full_name="Historical Synthetic Person", category="RUKON", status="INACTIVE", org_node_id=unit2.id, consent_at=datetime(2020,1,1,tzinfo=timezone.utc), consent_version="test")
        db.add(m);db.flush()
        states = [None, (unit1.id,"SUPPORTER","ACTIVE"), (unit1.id,"RUKON","ACTIVE"), (unit2.id,"RUKON","ACTIVE"), (unit2.id,"RUKON","INACTIVE")]
        # Jan 31 18:00 UTC is Feb 1 00:00 Dhaka: this transfer belongs to February.
        dates = [datetime(2020,1,1,tzinfo=timezone.utc), datetime(2020,1,20,tzinfo=timezone.utc), datetime(2020,1,31,18,tzinfo=timezone.utc), datetime(2020,2,5,tzinfo=timezone.utc)]
        for i, action in enumerate(("CREATED","CATEGORY","TRANSFER","DEACTIVATE")):
            event = MemberEvent(member_id=m.id, action=action, actor_id=who["editor"].id, created_at=dates[i])
            db.add(event);db.flush();record_movement(db,event,states[i],states[i+1])
        db.commit()
    holder["actor"] = who["admin"]
    january = client.get("/api/v1/reports/dashboard?start_date=2020-01-01&end_date=2020-01-31").json()
    assert january["total_active"] == 1
    assert january["by_category"]["RUKON"] == 1
    assert january["period"]["increase"] == 1
    assert january["period"]["decrease"] == 0
    assert next(u for u in january["by_unit"] if u["id"] == str(unit1.id))["count"] == 1
    february = client.get("/api/v1/reports/dashboard?start_date=2020-02-01&end_date=2020-02-29").json()
    assert february["total_active"] == 0
    assert february["period"]["increase"] == 0
    assert february["period"]["decrease"] == 1
    holder["actor"] = who["editor"]
    outgoing = client.get("/api/v1/reports/dashboard?start_date=2020-02-01&end_date=2020-02-29").json()
    assert outgoing["period"]["decrease"] == 1
    holder["actor"] = who["outsider"]
    incoming = client.get("/api/v1/reports/dashboard?start_date=2020-02-01&end_date=2020-02-29").json()
    assert incoming["period"]["increase"] == 1
    assert incoming["period"]["decrease"] == 1


def test_health_and_production_headers(context):
    client, holder, who, unit1, unit2 = context
    assert client.get("/health/live").json() == {"status":"ok"}
    # metadata-created test DB intentionally has no Alembic revision.
    assert client.get("/health/ready").status_code == 503
    response = client.get("/api/v1/me")
    assert response.json()["id"] == str(who["editor"].id)
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_stale_approval_rolls_back_and_remains_rejectable(context):
    client, holder, who, unit1, unit2 = context
    member = client.post("/api/v1/members", json=make_body(unit1.id)).json()
    url = "/api/v1/members/"+member["id"]
    rid = client.post("/api/v1/approvals/members/"+member["id"],json={"kind":"CATEGORY","proposed_value":"RUKON"}).json()["id"]
    assert client.patch(url,json={"expected_version":1,"occupation":"Updated"}).status_code == 200
    holder["actor"] = who["reviewer"]
    assert client.post(f"/api/v1/approvals/{rid}/decision",json={"approve":True}).status_code == 409
    assert client.get(url).json()["category"] == "SUPPORTER"
    assert client.post(f"/api/v1/approvals/{rid}/decision",json={"approve":False}).status_code == 200
    assert client.post(f"/api/v1/approvals/{rid}/decision",json={"approve":True}).status_code == 409


def test_postgres_reporting_uses_read_only_snapshot(context):
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("PostgreSQL snapshot isolation requires TEST_DATABASE_URL")
    from unittest.mock import patch
    from app import analytics
    client, holder, who, unit1, unit2 = context
    original = analytics._report_data
    def verify_snapshot(db, actor, start, end):
        assert db.execute(text("SHOW transaction_isolation")).scalar_one() == "repeatable read"
        assert db.execute(text("SHOW transaction_read_only")).scalar_one() == "on"
        return original(db, actor, start, end)
    with patch("app.analytics._report_data", side_effect=verify_snapshot) as check:
        assert client.get("/api/v1/reports/dashboard").status_code == 200
        check.assert_called_once()


def registration_claims(subject=None):
    return {"sub":str(subject or uuid.uuid4()),"email":"normal@example.invalid",
            "app_metadata":{"provider":"google"},"aal":"aal1",
            "user_metadata":{"role":"THANA_ADMIN","scope_node_id":"all"}}


def real_auth(context, monkeypatch, claims):
    client, holder, *_ = context
    app.dependency_overrides.pop(current_actor, None)
    app.dependency_overrides.pop(account_actor, None)
    monkeypatch.setattr("app.auth.jwt_claims", lambda _: claims)
    monkeypatch.setattr("app.main.jwt_claims", lambda _: claims)
    return client, holder, {"Authorization":"Bearer synthetic-token"}


def test_google_registration_is_idempotent_and_self_only(context, monkeypatch):
    from app.models import AuditLog, Member
    claims = registration_claims()
    client, holder, headers = real_auth(context, monkeypatch, claims)
    assert client.post("/api/v1/account/register", headers=headers).status_code == 200
    assert client.post("/api/v1/account/register", headers=headers).status_code == 200
    profile = client.get("/api/v1/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["email"] == claims["email"]
    assert profile.json()["roles"] == []
    for path in ("/members", "/organization/nodes", "/reports/dashboard", "/access/users", "/approvals"):
        assert client.get("/api/v1"+path, headers=headers).status_code == 403
    with holder["session_factory"]() as db:
        user = db.query(AppUser).filter(AppUser.auth_sub == claims["sub"]).one()
        assert db.query(RoleGrant).filter(RoleGrant.user_id == user.id).count() == 0
        assert db.query(Member).count() == 0
        assert db.query(AuditLog).filter(AuditLog.actor_id == user.id, AuditLog.action == "ACCOUNT_REGISTERED").count() == 1


def test_registration_does_not_reactivate_disabled_account(context, monkeypatch):
    claims = registration_claims()
    client, holder, headers = real_auth(context, monkeypatch, claims)
    with holder["session_factory"]() as db:
        db.add(AppUser(auth_sub=claims["sub"],email=claims["email"],active=False)); db.commit()
    assert client.post("/api/v1/account/register", headers=headers).status_code == 403
    assert client.get("/api/v1/me", headers=headers).status_code == 403
    with holder["session_factory"]() as db:
        assert not db.query(AppUser).filter(AppUser.auth_sub == claims["sub"]).one().active


@pytest.mark.parametrize("change",[{"app_metadata":{"provider":"phone"}}, {"is_anonymous":True}, {"sub":"invalid"}, {"email":None}])
def test_registration_rejects_ineligible_identity(context, monkeypatch, change):
    claims = {**registration_claims(), **change}
    client, _, headers = real_auth(context, monkeypatch, claims)
    assert client.post("/api/v1/account/register", headers=headers).status_code in {401,403}


def test_basic_account_flow_preserves_administrator_mfa(context, monkeypatch):
    claims = registration_claims()
    client, holder, headers = real_auth(context, monkeypatch, claims)
    assert client.post("/api/v1/account/register", headers=headers).status_code == 200
    with holder["session_factory"]() as db:
        user = db.query(AppUser).filter(AppUser.auth_sub == claims["sub"]).one()
        db.add(RoleGrant(user_id=user.id,role="THANA_ADMIN",scope_node_id=None)); db.commit()
    assert client.get("/api/v1/me", headers=headers).json()["detail"] == "Administrator MFA required"
    assert client.get("/api/v1/access/users", headers=headers).status_code == 403
    claims["aal"] = "aal2"
    assert client.get("/api/v1/me", headers=headers).status_code == 200


def test_concurrent_registration_creates_one_basic_account(context, monkeypatch):
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("Independent concurrent transactions require PostgreSQL")
    from concurrent.futures import ThreadPoolExecutor
    from types import SimpleNamespace
    from app.main import register_account
    claims = registration_claims()
    _, holder, _ = real_auth(context, monkeypatch, claims)
    def register():
        with holder["session_factory"]() as db:
            return register_account(SimpleNamespace(credentials="synthetic"), db)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert all(result["registered"] for result in pool.map(lambda _: register(), range(2)))
    with holder["session_factory"]() as db:
        assert db.query(AppUser).filter(AppUser.auth_sub==claims["sub"]).count() == 1
