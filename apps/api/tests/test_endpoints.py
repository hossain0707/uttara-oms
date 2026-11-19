"""End-to-end route tests using entirely synthetic records and two independent actors."""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.auth import Actor, current_actor
from app.database import Base, get_db
from app.main import app
from app.models import AppUser, OrgNode, RoleGrant


@pytest.fixture
def context():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
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
        "admin": Actor(uuid.uuid4(), "admin@example.invalid", [("THANA_ADMIN", None)], True),
    }
    with Local() as db:
        for a in who.values():
            db.add(AppUser(id=a.id, auth_sub=str(a.id), email=a.email, active=True))
        db.commit()
    holder = {"actor": who["editor"]}

    def override_db():
        with Local() as db:
            yield db

    def override_actor():
        return holder["actor"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[current_actor] = override_actor
    try:
        with TestClient(app) as client:
            yield client, holder, who, unit1, unit2
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


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
    reviewer = Actor(uuid.uuid4(), "independent-admin@example.invalid", [("THANA_ADMIN", None)], True)
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
