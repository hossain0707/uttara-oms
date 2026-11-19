"""Offline provisioning CLI: run only by trusted operator, never from an HTTP route."""
import argparse
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import AppUser, OrgNode, RoleGrant


def init_org(db: Session):
    root = db.query(OrgNode).filter(OrgNode.kind == "THANA").first()
    if root is None:
        root = OrgNode(kind="THANA", name="Uttara Model Thana", code="uttara-model")
        db.add(root)
        db.flush()
    for i in range(1, 13):
        code = f"ward-{i:02d}"
        if not db.query(OrgNode).filter(OrgNode.parent_id == root.id, OrgNode.code == code).first():
            db.add(OrgNode(parent_id=root.id, kind="WARD", code=code, name=f"Ward {i:02d}"))
    db.commit()
    print("Organizational structure initialized; no member data inserted.")


def provision_admin(db: Session, sub: str, email: str):
    # User must already have completed Supabase Google auth with this exact sub.
    user = db.query(AppUser).filter(AppUser.auth_sub == sub).first()
    if user is None:
        user = AppUser(auth_sub=sub, email=email, active=True)
        db.add(user); db.flush()
    else:
        user.active = True
    if not db.query(RoleGrant).filter(RoleGrant.user_id == user.id, RoleGrant.role == "THANA_ADMIN").first():
        db.add(RoleGrant(user_id=user.id, role="THANA_ADMIN", scope_node_id=None))
    db.commit()
    print("Admin assigned. Ensure MFA is enabled; review offline provisioning log.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_subparsers(dest="command", required=True)
    group.add_parser("init-org")
    admin = group.add_parser("admin")
    admin.add_argument("--sub", required=True)
    admin.add_argument("--email", required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == "init-org":
            init_org(db)
        elif args.command == "admin":
            provision_admin(db, args.sub, args.email)
