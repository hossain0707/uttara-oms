"""Personal daily activity fields and units; aggregate counts only, no named target lists."""
CORE={'prayers':'prayers','literature':'pages','organization':'minutes','quran':'pages','hadith':'items'}
NUMERIC={**CORE,'congregational_prayers':'prayers','dawah_meetings':'times','worker_meetings':'times','member_meetings':'times','worker_contacts':'times','books_distributed':'books','donated_hours':'hours','visits':'times'}
CHECKS={'quran_studied':'days','family_meeting':'days','social_work':'days','report_kept':'days','self_evaluation':'days'}
EXTRA=set(NUMERIC).difference(CORE)|set(CHECKS)
METRICS={**NUMERIC,**CHECKS}
REFLECTIONS=('achievements','incomplete_work','next_plan')

def aggregate(entries):
    totals={k:round(sum(e.get(k) or 0 for e in entries),2) for k in NUMERIC}
    totals.update({k:sum(e.get(k) is True for e in entries) for k in CHECKS})
    reported={k:sum(e.get(k) is not None for e in entries) for k in METRICS}
    return totals,reported
