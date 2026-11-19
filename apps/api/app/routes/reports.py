from datetime import datetime, timezone
from html import escape
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AuditLog, Member, MemberEvent, OrgNode
from ..policies import CATEGORIES, allowed_nodes, is_thana_admin

router = APIRouter(prefix="/reports", tags=["reports"])


def report_data(db: Session, actor: Actor):
    ids = allowed_nodes(db, actor)
    data = {key: 0 for key in ["RUKON", "WORKER", "ASSOCIATE", "SUPPORTER"]}
    active = db.query(Member.category, func.count(Member.id)).filter(
        Member.org_node_id.in_(ids), Member.status == "ACTIVE").group_by(Member.category).all()
    for category, count in active:
        data[category] = count
    units = db.query(OrgNode).filter(OrgNode.kind == "UNIT", OrgNode.id.in_(ids)).all()
    rows = db.query(Member.org_node_id, func.count(Member.id)).filter(
        Member.org_node_id.in_(ids), Member.status == "ACTIVE").group_by(Member.org_node_id).all()
    counts = dict(rows)
    by_unit = [{"id": str(n.id), "name": n.name, "code": n.code, "count": counts.get(n.id, 0)} for n in units]
    ward_totals = {}
    for unit in units:
        if unit.parent_id:
            ward_totals[unit.parent_id] = ward_totals.get(unit.parent_id, 0) + counts.get(unit.id, 0)
    ward_ids = set(ward_totals) | {n for n in ids if db.get(OrgNode, n).kind == "WARD"}
    wards = db.query(OrgNode).filter(OrgNode.kind == "WARD", OrgNode.id.in_(ward_ids)).all()
    by_ward = [{"id": str(w.id), "name": w.name, "code": w.code,
                "count": ward_totals.get(w.id, 0)} for w in sorted(wards, key=lambda v: v.code)]
    # Events are scoped to the member's current assigned unit.
    start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    events = (db.query(MemberEvent.action, MemberEvent.after, func.count(MemberEvent.id))
              .join(Member, Member.id == MemberEvent.member_id)
              .filter(Member.org_node_id.in_(ids), MemberEvent.created_at >= start)
              .group_by(MemberEvent.action, MemberEvent.after).all())
    increased = sum(n for action, after, n in events if action == "CREATED" or (action == "REACTIVATE" and after == "ACTIVE"))
    decreased = sum(n for action, after, n in events if action == "DEACTIVATE" and after == "INACTIVE")
    return {"total_active": sum(data.values()), "by_category": data,
            "by_unit": by_unit, "by_ward": by_ward, "this_month": {"increase": increased, "decrease": decreased, "net": increased - decreased},
            "generated_at": datetime.now(timezone.utc).isoformat()}


@router.get("/dashboard")
def dashboard(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    return report_data(db, actor)


@router.get("/export.xlsx")
def export_xlsx(include_personal: bool = False, actor: Actor = Depends(current_actor),
                db: Session = Depends(get_db)):
    import xlsxwriter
    from ..security import decrypt
    if include_personal and not is_thana_admin(actor):
        raise HTTPException(403, "Personal-data export restricted to Thana Admin")
    data = report_data(db, actor)
    output = BytesIO()
    book = xlsxwriter.Workbook(output, {"in_memory": True, "strings_to_formulas": False, "strings_to_urls": False})
    sheet = book.add_worksheet("Overview")
    title = book.add_format({"bold": True, "font_size": 16, "font_color": "#153F37"})
    header = book.add_format({"bold": True, "bg_color": "#D9EDE5", "border": 1})
    sheet.set_column("A:A", 27); sheet.set_column("B:B", 19)
    sheet.write("A1", "UTTARA OMS - Authorized Report", title)
    sheet.write_row("A3", ["Category", "Active"], header)
    for idx, (k, v) in enumerate(data["by_category"].items(), 3):
        sheet.write_row(idx, 0, [k, v])
    sheet.write_row("A10", ["Month", "Increase", "Decrease", "Net"], header)
    sheet.write_row("A11", ["Current", data["this_month"]["increase"],
                              data["this_month"]["decrease"], data["this_month"]["net"]])
    units = book.add_worksheet("Unit counts")
    units.write_row(0, 0, ["Unit", "Code", "Active"], header)
    for idx, unit in enumerate(data["by_unit"], 1):
        units.write_row(idx, 0, [unit["name"], unit["code"], unit["count"]])
    units.set_column("A:A", 35)
    wards_sheet = book.add_worksheet("Ward counts")
    wards_sheet.write_row(0, 0, ["Ward", "Code", "Active"], header)
    for idx, ward in enumerate(data["by_ward"], 1):
        wards_sheet.write_row(idx, 0, [ward["name"], ward["code"], ward["count"]])
    wards_sheet.set_column("A:A", 35)
    if include_personal:
        people = book.add_worksheet("Restricted personal records")
        fields = ["Member number", "Name", "Phone", "Category", "Status", "Unit ID"]
        people.write_row(0, 0, fields, header)
        scopes = allowed_nodes(db, actor)
        for i, m in enumerate(db.query(Member).filter(Member.org_node_id.in_(scopes)).order_by(Member.member_number).all(), 1):
            values = [m.member_number, m.full_name, decrypt(m.phone_encrypted) or "",
                      m.category, m.status, str(m.org_node_id)]
            # Explicitly treat strings as text to avoid spreadsheet formula injection.
            for j, val in enumerate(values):
                people.write_string(i, j, str(val))
        people.set_column("A:F", 22)
    book.close()
    db.add(AuditLog(actor_id=actor.id, action="REPORT_EXPORTED", target_id="XLSX",
                    detail="personal" if include_personal else "aggregate"))
    db.commit()
    return Response(output.getvalue(),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment; filename=uttara-oms-report.xlsx",
                             "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/export.pdf")
def export_pdf(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    from weasyprint import HTML
    data = report_data(db, actor)
    rows = "".join("<tr><td>" + escape(key) + "</td><td>" + str(value) + "</td></tr>"
                   for key, value in data["by_category"].items())
    html = ('<html><meta charset="utf-8"><style>body{font-family:sans-serif;color:#18392f;padding:35px}'
            'h1{color:#0f5d46}table{border-collapse:collapse;width:100%}td,th{border:1px solid #b8ccc2;'
            'padding:12px;text-align:left}</style><h1>Uttara OMS</h1>'
            '<p>Confidential organizational summary. Authorized use only.</p>'
            '<h2>Active records: ' + str(data["total_active"]) + '</h2><table><tr><th>Category</th>'
            '<th>Count</th></tr>' + rows + '</table><p>Current month: +'
            + str(data["this_month"]["increase"]) + ' / -' + str(data["this_month"]["decrease"]) + '</p></html>')
    output = HTML(string=html).write_pdf()
    db.add(AuditLog(actor_id=actor.id, action="REPORT_EXPORTED", target_id="PDF", detail="aggregate"))
    db.commit()
    return Response(output, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=uttara-oms-report.pdf",
                             "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
