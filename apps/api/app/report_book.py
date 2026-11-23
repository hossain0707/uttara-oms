"""Offline, escaped PDF and formula-safe Excel personal report exports."""
from html import escape
from datetime import date
from io import BytesIO
from .report_fields import CHECKS, aggregate
METRICS=[('prayers','সালাত','ওয়াক্ত'),('quran','কুরআন অধ্যয়ন (পরিমাণ)','পৃষ্ঠা'),('hadith','হাদিস অধ্যয়ন','টি'),('literature','সাহিত্য অধ্যয়ন','পৃষ্ঠা'),('organization','সাংগঠনিক কাজ','মিনিট'),('congregational_prayers','জামাতে সালাত','ওয়াক্ত'),('quran_studied','কুরআন অধ্যয়ন','দিন'),('dawah_meetings','দাওয়াতি সাক্ষাৎ','বার'),('worker_meetings','কর্মী সাক্ষাৎ','বার'),('member_meetings','সদস্য সাক্ষাৎ','বার'),('worker_contacts','কর্মী যোগাযোগ','বার'),('books_distributed','বই বিতরণ','টি'),('family_meeting','পারিবারিক বৈঠক','দিন'),('social_work','সামাজিক কাজ','দিন'),('donated_hours','সময় দান','ঘণ্টা'),('visits','সফর','বার'),('report_kept','রিপোর্ট রাখা','দিন'),('self_evaluation','আত্মসমালোচনা','দিন')]
REFLECTION_LABELS=[('achievements','মাসের অর্জন'),('incomplete_work','অসম্পূর্ণ কাজ'),('next_plan','আগামী মাসের পরিকল্পনা'),('summary','অতিরিক্ত মাসিক মন্তব্য'),('review_note','দায়িত্বশীলের মন্তব্য')]
STATUS={'DRAFT':'খসড়া','RETURNED':'সংশোধনের জন্য ফেরত','SUBMITTED':'পর্যালোচনাধীন','REVIEWED':'পর্যালোচিত'}
def bn(value):
    return str(value).translate(str.maketrans('0123456789','০১২৩৪৫৬৭৮৯'))
def cell(entry,key):
    value=entry.get(key)
    return '—' if value is None else ('হ্যাঁ' if value else 'না') if key in CHECKS else bn(value)
def reporting_book_html(data, full_name=''):
    month=date.fromisoformat(data['month'])
    months=['জানুয়ারি','ফেব্রুয়ারি','মার্চ','এপ্রিল','মে','জুন','জুলাই','আগস্ট','সেপ্টেম্বর','অক্টোবর','নভেম্বর','ডিসেম্বর']
    caption=months[month.month-1]+' '+bn(month.year)
    totals,reported=aggregate(data['entries'])
    rows=''.join(f'<tr><th>{label}<small>{unit}</small></th><td>{bn(totals[key])}</td><td>{bn(reported[key])}</td></tr>' for key,label,unit in METRICS)
    reflections=''.join(f'<h2>{label}</h2><div class="summary">{escape(data.get(key) or "কোনো মন্তব্য লেখা হয়নি।")}</div>' for key,label in REFLECTION_LABELS)
    goals={g['metric']:g['target'] for g in data.get('goals',[]) if g['metric']!='prayers'}
    goal_rows=''.join(f'<tr><th>{label} ({unit})</th><td>{bn(goals[key])}</td><td>{bn(totals[key])}</td></tr>' for key,label,unit in METRICS if key in goals)
    goal_section=f'<h2>নির্ধারিত অধ্যয়নের লক্ষ্য</h2><table><thead><tr><th>কার্যক্রম</th><th>লক্ষ্য</th><th>অর্জন</th></tr></thead><tbody>{goal_rows}</tbody></table>' if goal_rows else ''
    ledger=''
    for start in range(0,len(METRICS),5):
        group=METRICS[start:start+5]
        header='<tr><th>তারিখ</th>'+''.join(f'<th>{label}<small>{unit}</small></th>' for _,label,unit in group)+'</tr>'
        days=''.join('<tr><th>'+escape(bn(e['day']))+'</th>'+''.join('<td>'+cell(e,k)+'</td>' for k,_,_ in group)+'</tr>' for e in sorted(data['entries'],key=lambda e:e['day']))
        ledger+=f'<section class="ledger-section"><h2>দিনভিত্তিক হিসাব · {caption}</h2><table><thead>{header}</thead><tbody>{days}</tbody></table></section>'
    notes=''.join(f'<tr><th>{escape(bn(e["day"]))}</th><td class="summary">{escape(e.get("notes", ""))}</td></tr>' for e in data['entries'] if e.get('notes'))
    css='''@page{size:A4;margin:15mm;@bottom-left{content:"Uttara OMS • ব্যক্তিগত রিপোর্ট";font-family:"Noto Sans Bengali",sans-serif;font-size:8pt}@bottom-right{content:counter(page);font-size:8pt}}body{font-family:"Noto Sans Bengali",sans-serif;color:#193e2e;font-size:9pt;line-height:1.6}h1{font-size:23pt;margin:6px 0}h2{font-size:13pt;margin:18px 0 8px}.hero{background:#173f2d;color:#fff9e7;padding:18px;border-bottom:3px solid #bea354;border-radius:10px}.brand{font-size:9pt;letter-spacing:2px;color:#e5ce8b}table{width:100%;border-collapse:collapse;margin:12px 0}th,td{border:1px solid #d5d8c4;padding:6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}thead th{background:#ece6c6}tbody th{font-weight:400}small{display:block;color:#62735c;font-size:8pt}thead{display:table-header-group}tr{break-inside:avoid}.summary{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid #d1d6bd;background:#fffdf2;padding:12px;min-height:30px}.ledger-section{break-before:page}.ledger-section table{font-size:8pt}.ledger-section th,.ledger-section td{padding:3px 5px}.muted{font-size:8pt;color:#62735c}'''
    return f'''<!doctype html><html lang="bn"><meta charset="utf-8"><title>Uttara OMS - ব্যক্তিগত রিপোর্ট</title><style>{css}</style><body><header class="hero"><div class="brand">UTTARA OMS / PERSONAL REPORT BOOK</div><h1>আমার রিপোর্ট বই</h1><p>{escape(full_name)} · {caption} · {escape(STATUS.get(data['status'],data['status']))}</p></header><h2>মাসিক হিসাব</h2><p class="muted">ফাঁকা = তথ্য দেওয়া হয়নি; ০ / না = তথ্য দেওয়া হয়েছে। টিক চিহ্নের মোট = কাজটি করা দিনের সংখ্যা।</p><table><thead><tr><th>কার্যক্রম</th><th>মোট</th><th>তথ্য দেওয়া দিন</th></tr></thead><tbody>{rows}</tbody></table>{goal_section}{reflections}{ledger}<h2>দিনের মন্তব্য</h2><table>{notes}</table><p class="muted">এটি সর্বশেষ সংরক্ষিত রিপোর্ট। কেবল নির্ধারিত দায়িত্বশীল জমা দেওয়া রিপোর্ট পর্যালোচনা করেন।</p></body></html>'''
def reporting_book_xlsx(data):
    import xlsxwriter
    out=BytesIO()
    workbook=xlsxwriter.Workbook(out,{'in_memory':True,'strings_to_formulas':False,'strings_to_urls':False})
    heading=workbook.add_format({'bold':True,'bg_color':'#194C35','font_color':'white','text_wrap':True})
    wrap=workbook.add_format({'text_wrap':True,'valign':'top'})
    ledger=workbook.add_worksheet('Daily report')
    columns=[('day','Date')]+[(k,f'{label} ({unit})') for k,label,unit in sorted(METRICS[:5],key=lambda m:['prayers','literature','organization','quran','hadith'].index(m[0]))]+[('notes','Notes')]+[(k,f'{label} ({unit})') for k,label,unit in METRICS[5:]]
    ledger.write_row(0,0,[label for _,label in columns],heading)
    for row,entry in enumerate(data['entries'],1):
        ledger.write_row(row,0,[('Yes' if entry[k] else 'No') if k in CHECKS and entry.get(k) is not None else entry.get(k) for k,_ in columns],wrap)
    ledger.freeze_panes(1,1);ledger.autofilter(0,0,len(data['entries']),len(columns)-1)
    ledger.set_column(0,0,14);ledger.set_column(1,len(columns)-1,22);ledger.set_column(6,6,50);ledger.set_row(0,42)
    summary=workbook.add_worksheet('Monthly summary')
    summary.write_row(0,0,['Month',data['month'],'Status',data['status']],heading)
    summary.write_row(2,0,['Activity','Unit','Total','Reported days'],heading)
    totals,reported=aggregate(data['entries'])
    for row,(key,label,unit) in enumerate(METRICS,3):
        summary.write_row(row,0,[label,unit,totals[key],reported[key]])
    row=len(METRICS)+5
    for key,label in REFLECTION_LABELS:
        summary.write(row,0,label,heading);summary.merge_range(row,1,row+2,3,data.get(key) or '',wrap);row+=4
    summary.set_column(0,0,34);summary.set_column(1,3,23);summary.freeze_panes(3,0)
    workbook.close()
    return out.getvalue()
