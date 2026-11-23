from app.report_book import reporting_book_html


def test_book_escapes_private_text_and_keeps_real_units():
    data={'month':'2026-11-01','status':'DRAFT','entries':[{'day':'2026-11-01','prayers':0,'quran':None,'notes':'<script>bad()</script>'}], 'totals':{'prayers':0,'quran':0,'hadith':0,'literature':20,'organization':45},'goals':[{'metric':'literature','target':30}], 'summary':'<img src="https://invalid.example/">','review_note':'<b>Private review</b>'}
    html=reporting_book_html(data,'<owner>')
    assert '<script>' not in html and '<img src=' not in html and '<owner>' not in html
    assert '&lt;script&gt;' in html and '&lt;owner&gt;' in html
    assert 'পৃষ্ঠা' in html and 'মিনিট' in html and 'আমার রিপোর্ট বই' in html
    assert 'data:image' not in html and '@import' not in html
    assert '২০' in html and '৪৫' in html and 'নভেম্বর ২০২৬' in html


def test_salah_month_lengths_and_unreported_days():
    from app.report_book import salah_summary
    for month,days in [('2026-11-01',30),('2026-01-01',31),('2025-02-01',28),('2024-02-01',29)]:
        s=salah_summary({'month':month,'entries':[{'prayers':5},{'prayers':0},{'prayers':None}]})
        assert s==dict(days=days,maximum=days*5,reported_days=2,unreported_days=days-2,total=5,invalid=False)
    s=salah_summary({'month':'2026-11-01','entries':[{'prayers':6}]})
    assert s['invalid'] and s['total']==6  # never silently alter old saved data
