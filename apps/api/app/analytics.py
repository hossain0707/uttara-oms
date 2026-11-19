"""Membership accounting: category changes and in-scope transfers conserve total people."""
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from .auth import Actor
from .models import MembershipDelta, MemberEvent, OrgNode
from .policies import allowed_nodes

REPORT_ZONE = ZoneInfo("Asia/Dhaka")
State = tuple[UUID, str, str]


def record_movement(db: Session, event: MemberEvent, before: State | None, after: State):
    values: Counter = Counter()
    if before and before[2] == "ACTIVE":
        values[(before[0], before[1])] -= 1
    if after[2] == "ACTIVE":
        values[(after[0], after[1])] += 1
    for (unit, category), delta in values.items():
        if delta:
            db.add(MembershipDelta(event_id=event.id, org_node_id=unit, category=category,
                                   delta=delta, occurred_at=event.created_at))


def boundary(day: date) -> datetime:
    return datetime.combine(day, time.min, REPORT_ZONE).astimezone(timezone.utc)


def date_window(start: date | None, end: date | None):
    today = datetime.now(REPORT_ZONE).date()
    end = end or today
    start = start or end.replace(day=1)
    if start > end or end > today or (end - start).days > 366:
        raise HTTPException(422, "Use an ordered date range of at most 367 days ending no later than today (Asia/Dhaka)")
    return start, end


def _totals(db: Session, ids: set[UUID], end: datetime):
    return (db.query(MembershipDelta.org_node_id, MembershipDelta.category,
                     func.sum(MembershipDelta.delta))
            .filter(MembershipDelta.org_node_id.in_(ids), MembershipDelta.occurred_at < end)
            .group_by(MembershipDelta.org_node_id, MembershipDelta.category).all())


def _movement(db: Session, ids: set[UUID], start: datetime, end: datetime):
    # Group AFTER scoping: internal transfers and category changes sum to zero;
    # cross-boundary transfers count once in each affected scope.
    events = (db.query(func.sum(MembershipDelta.delta).label("net"))
              .filter(MembershipDelta.org_node_id.in_(ids), MembershipDelta.occurred_at >= start,
                      MembershipDelta.occurred_at < end)
              .group_by(MembershipDelta.event_id).subquery())
    from sqlalchemy import case
    inc, dec = db.query(
        func.coalesce(func.sum(case((events.c.net > 0, events.c.net), else_=0)), 0),
        func.coalesce(func.sum(case((events.c.net < 0, -events.c.net), else_=0)), 0),
    ).one()
    return {"increase": int(inc), "decrease": int(dec), "net": int(inc - dec)}


def report_data(db: Session, actor: Actor, start: date | None = None, end: date | None = None):
    # Auth uses the request session. Reporting uses one separate, read-only snapshot
    # so counts, comparison and movement cannot observe different commits.
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        with bind.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            with Session(bind=connection) as snapshot:
                return _report_data(snapshot, actor, start, end)
    return _report_data(db, actor, start, end)


def _report_data(db: Session, actor: Actor, start: date | None = None, end: date | None = None):
    start, end = date_window(start, end)
    stop = boundary(end + timedelta(days=1))
    ids = allowed_nodes(db, actor)
    categories = {key: 0 for key in ("RUKON", "WORKER", "ASSOCIATE", "SUPPORTER")}
    counts: Counter = Counter()
    for unit, category, count in _totals(db, ids, stop):
        categories[category] += int(count)
        counts[unit] += int(count)
    all_nodes = db.query(OrgNode).all()
    units = sorted((n for n in all_nodes if n.kind == "UNIT" and n.id in ids), key=lambda n: (n.code, str(n.id)))
    ward_totals: Counter = Counter()
    for unit in units:
        ward_totals[unit.parent_id] += counts[unit.id]
    def row(n, count):
        return {"id": str(n.id), "name": n.name, "code": n.code, "active": n.active, "count": count}
    wards = sorted((n for n in all_nodes if n.kind == "WARD" and (n.id in ids or n.id in ward_totals)), key=lambda n: (n.code, str(n.id)))
    length = (end - start).days + 1
    comparison_start = start - timedelta(days=length)
    previous_end = boundary(start)
    previous_total = sum(int(r[2]) for r in _totals(db, ids, previous_end))
    movement = _movement(db, ids, boundary(start), stop)
    summaries = []
    month = start.replace(day=1)
    while month <= end:
        next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        first, last = max(start, month), min(end, next_month - timedelta(days=1))
        summaries.append({"month": month.strftime("%Y-%m"), "start_date": first.isoformat(),
                          "end_date": last.isoformat(),
                          **_movement(db, ids, boundary(first), boundary(last + timedelta(days=1)))})
        month = next_month
    today = datetime.now(REPORT_ZONE).date()
    return {
        "total_active": sum(categories.values()), "by_category": categories,
        "by_unit": [row(n, counts[n.id]) for n in units],
        "by_ward": [row(n, ward_totals[n.id]) for n in wards],
        "this_month": _movement(db, ids, boundary(today.replace(day=1)), boundary(today + timedelta(days=1))),
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat(), **movement},
        "comparison": {"start_date": comparison_start.isoformat(),
                       "end_date": (start - timedelta(days=1)).isoformat(),
                       "total_active": previous_total,
                       **_movement(db, ids, boundary(comparison_start), previous_end)},
        "monthly_history": summaries,
        "timezone": "Asia/Dhaka", "as_of": end.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
