"""Personal reporting-book PDF. All user text is escaped; no remote resources."""
from html import escape
from datetime import date
import calendar

METRICS=[('prayers','সালাত','ওয়াক্ত'),('quran','কুরআন অধ্যয়ন','পৃষ্ঠা'),('hadith','হাদিস অধ্যয়ন','টি'),('literature','সাহিত্য অধ্যয়ন','পৃষ্ঠা'),('organization','সাংগঠনিক কাজ','মিনিট')]
STATUS={'DRAFT':'খসড়া','RETURNED':'সংশোধনের জন্য ফেরত','SUBMITTED':'পর্যালোচনাধীন','REVIEWED':'পর্যালোচিত'}
MONTHS=['জানুয়ারি','ফেব্রুয়ারি','মার্চ','এপ্রিল','মে','জুন','জুলাই','আগস্ট','সেপ্টেম্বর','অক্টোবর','নভেম্বর','ডিসেম্বর']
def bn(value):
    return str(value).translate(str.maketrans('0123456789','০১২৩৪৫৬৭৮৯'))


def salah_summary(data):
    month=date.fromisoformat(data['month'])
    days=calendar.monthrange(month.year,month.month)[1]
    reported=[e for e in data['entries'] if e.get('prayers') is not None]
    return dict(days=days,maximum=days*5,reported_days=len(reported),unreported_days=days-len(reported),total=sum(e['prayers'] for e in reported),invalid=any(not isinstance(e['prayers'],int) or not 0<=e['prayers']<=5 for e in reported))

def reporting_book_html(data, full_name=''):
    month=date.fromisoformat(data['month'])
    caption=MONTHS[month.month-1]+' '+bn(month.year)
    goals={g['metric']:g['target'] for g in data.get('goals',[])}
    totals=data['totals']
    salah=salah_summary(data)
    rows=''
    for key,label,unit in METRICS:
        goal=goals.get(key)
        rows+=f'<tr><th>{label}<small>{unit}</small></th><td>{bn(goal) if goal is not None else "—"}</td><td>{bn(totals.get(key,0))}</td><td>{bn(max(0,goal-totals.get(key,0))) if goal is not None else "—"}</td></tr>'
    ledger=''
    for entry in sorted(data['entries'],key=lambda e:e['day']):
        ledger+='<tr><th>'+escape(bn(entry['day']))+'</th>'+''.join('<td>'+(bn(entry.get(k)) if entry.get(k) is not None else '—')+'</td>' for k,_,_ in METRICS)+'<td class="notes">'+escape(entry.get('notes',''))+'</td></tr>'
    css='''@page{size:A4;margin:15mm;@bottom-left{content:"Uttara OMS • ব্যক্তিগত রিপোর্ট";font-family:"Noto Sans Bengali",sans-serif;font-size:8pt;color:#60745d}@bottom-right{content:counter(page);font-size:8pt;color:#60745d}}body{font-family:"Noto Sans Bengali",sans-serif;color:#193e2e;font-size:9.5pt;line-height:1.5}*{box-sizing:border-box}h1{font-size:23pt;margin:5px 0}h2{font-size:15pt;margin:13px 0 8px}h3{font-size:11pt;margin:0 0 7px}p{margin:5px 0}.hero{background:#173f2d;color:#fff9e7;padding:15px;border-bottom:3px solid #bea354;border-radius:10px}.brand{font-size:9pt;letter-spacing:2px;color:#e5ce8b}.meta{display:flex;justify-content:space-between;gap:15px}.stats{display:flex;gap:10px;margin:12px 0}.stats>div{width:33%;background:#faf4df;border:1px solid #d9d3b1;border-radius:7px;padding:9px}.stats span{font-size:9pt;display:block}.stats strong{font-size:18pt}.stats small{font-size:9pt}.muted{color:#62735c;font-size:8pt}.book-table{width:100%;border-collapse:collapse;margin:10px 0 18px}th,td{border:1px solid #d5d8c4;padding:6px 9px;text-align:left;vertical-align:top;overflow-wrap:anywhere}thead th{background:#ece6c6;font-weight:600}tbody th{font-weight:400}th small{display:block;font-size:8pt;color:#62735c}thead{display:table-header-group}tr{break-inside:avoid}.summary{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid #d1d6bd;background:#fffdf2;padding:14px;min-height:55px;line-height:1.8}.review{border-left:3px solid #bd9f45;padding:10px 15px;background:#f8f3df;margin-top:15px;white-space:pre-wrap;overflow-wrap:anywhere}.ledger{font-size:8pt}.ledger th,.ledger td{padding:4px 5px}.ledger .notes{white-space:pre-wrap;max-width:150px}.ledger-section{break-before:page}.footnote{font-size:8pt;color:#62735c;margin-top:14px}'''
    cards=f'<div class="stats"><div><span>লেখা হয়েছে</span><strong>{bn(len(data["entries"]))}</strong> <small>দিন</small></div><div><span>সাহিত্য অধ্যয়ন</span><strong>{bn(totals.get("literature",0))}</strong> <small>পৃষ্ঠা</small></div><div><span>সাংগঠনিক কাজ</span><strong>{bn(totals.get("organization",0))}</strong> <small>মিনিট</small></div></div>'
    salah_card=f'<h2>মাসিক সালাতের হিসাব</h2><table class="book-table"><tr><th>দৈনিক সর্বোচ্চ</th><td>৫ ওয়াক্ত</td><th>মাসের দিন</th><td>{bn(salah["days"])} দিন</td></tr><tr><th>মাসিক সর্বোচ্চ</th><td>{bn(salah["maximum"])} ওয়াক্ত</td><th>তথ্য দেওয়া হয়েছে</th><td>{bn(salah["reported_days"])} দিন</td></tr><tr><th>রিপোর্ট করা মোট</th><td>{bn(salah["total"])} ওয়াক্ত</td><th>তথ্য দেওয়া হয়নি</th><td>{bn(salah["unreported_days"])} দিন</td></tr></table><p class="muted">মাসিক সর্বোচ্চ = মাসের দিন × ৫; এটি নির্ধারিত লক্ষ্য নয়। ফাঁকা ঘর শূন্য নয়।</p>'
    if salah['invalid']:
        salah_card+='<p class="review">পুরোনো কোনো দিনের সালাতের সংখ্যা ০–৫-এর বাইরে। মূল তথ্য অপরিবর্তিত আছে; সংশোধন প্রয়োজন।</p>'
    header='<tr><th>তারিখ</th>'+''.join('<th>'+label+'<small>'+unit+'</small></th>' for _,label,unit in METRICS)+'<th>মন্তব্য</th></tr>'
    review='<div class="review"><h3>দায়িত্বশীলের মন্তব্য</h3>'+escape(data['review_note'])+'</div>' if data.get('review_note') else ''
    return f'''<!doctype html><html lang="bn"><meta charset="utf-8"><title>Uttara OMS - ব্যক্তিগত রিপোর্ট</title><style>{css}</style><body><header class="hero"><div class="brand">UTTARA OMS / PERSONAL REPORT BOOK</div><h1>আমার রিপোর্ট বই</h1><div class="meta"><span>{escape(full_name)}</span><span>{caption} · {escape(STATUS.get(data['status'],data['status']))}</span></div></header>{cards}{salah_card}<h2>মাসিক হিসাব ও লক্ষ্য</h2><table class="book-table"><thead><tr><th>কার্যক্রম</th><th>লক্ষ্য</th><th>অর্জন</th><th>বাকি</th></tr></thead><tbody>{rows}</tbody></table><p class="muted">লক্ষ্য দায়িত্বশীল প্রশাসক নির্ধারণ করেন। লক্ষ্য অর্জন স্বয়ংক্রিয়ভাবে সদস্যের শ্রেণি বা অনুমতি পরিবর্তন করে না।</p><h2>মাসের মূল্যায়ন ও আগামী মাসের পরিকল্পনা</h2><div class="summary">{escape(data.get('summary','')) or 'কোনো মন্তব্য লেখা হয়নি।'}</div>{review}<p class="footnote">এটি সর্বশেষ সংরক্ষিত রিপোর্ট। খসড়া ও পর্যালোচিত রিপোর্টের অবস্থা আলাদাভাবে দেখানো হয়েছে।</p><section class="ledger-section"><h2>দিনভিত্তিক হিসাব · {caption}</h2><p class="muted">ফাঁকা = তথ্য দেওয়া হয়নি; ০ = পরিমাণ শূন্য। কেবল সংরক্ষিত দিনের তথ্য এখানে রয়েছে।</p><table class="book-table ledger"><thead>{header}</thead><tbody>{ledger or '<tr><td colspan="7">কোনো দিন লেখা হয়নি।</td></tr>'}</tbody></table></section></body></html>'''
