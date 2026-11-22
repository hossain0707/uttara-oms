"""Current consented-profile aggregates, separate from the official membership ledger."""
from datetime import datetime, timezone
from .models import AppUser, PersonalProfile, OrgNode
from .policies import personal_nodes, allowed_nodes
from .routes.personal import unpack


def registered_summary(db, actor):
    global_scope = any(role in {'THANA_ADMIN', 'THANA_VIEWER'} for role, _ in actor.grants)
    scopes = allowed_nodes(db, actor)
    query = db.query(PersonalProfile).join(AppUser, AppUser.id == PersonalProfile.user_id).filter(AppUser.active.is_(True))
    if not global_scope:
        from .models import Member
        query = query.join(Member, Member.id == PersonalProfile.member_id).filter(Member.org_node_id.in_(personal_nodes(db, actor)))
    categories = {k: 0 for k in ['RUKON', 'WORKER', 'ASSOCIATE', 'SUPPORTER', 'UNSPECIFIED']}
    total = linked = represented = 0
    for profile in query.yield_per(20):
        represented += 1
        details = unpack(profile.details_encrypted)
        if not details.get('consent') or not (details.get('full_name') or '').strip():
            continue
        total += 1
        linked += bool(profile.member_id)
        category = details.get('category')
        categories[category if category in categories else 'UNSPECIFIED'] += 1
    accounts = db.query(AppUser).filter(AppUser.active.is_(True)).count() if global_scope else represented
    nodes = {n.id: n for n in db.query(OrgNode).all()}
    def active(n):
        ward = nodes.get(n.parent_id)
        root = nodes.get(ward.parent_id) if ward else None
        return n.active and ward and ward.kind == 'WARD' and ward.active and root and root.kind == 'THANA' and root.active and root.parent_id is None
    return {'active_accounts': accounts, 'total_profiles': total, 'by_category': categories,
            'linked_profiles': linked, 'awaiting_confirmation': total - linked, 'profiles_missing': accounts - total,
            'active_units': sum(bool(active(n)) for n in nodes.values() if n.kind == 'UNIT' and n.id in scopes),
            'global_scope': global_scope, 'generated_at': datetime.now(timezone.utc).isoformat()}
