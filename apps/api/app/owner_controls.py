"""Owner authority is derived from durable configuration, never a client flag."""
import hashlib
import json
from . import security_policy as policy


def direct_owner(db, actor):
    return bool(actor.mfa and any(role == 'THANA_ADMIN' and scope is None for role, scope in actor.grants)
                and policy.is_owner(db, actor.id))


def roles_version(grants):
    rows = sorted((str(g.id), g.role, str(g.scope_node_id) if g.scope_node_id else None) for g in grants)
    return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()


def deleted(db, user_id):
    from .models import AuditLog
    return db.query(AuditLog.id).filter(AuditLog.action == 'MASTER_ACCOUNT_DELETED',
                                      AuditLog.target_id == str(user_id)).first() is not None
