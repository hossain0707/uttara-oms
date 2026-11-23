from app.report_book import reporting_book_html


def test_book_escapes_private_text_and_keeps_real_units():
    data={'month':'2026-11-01','status':'DRAFT','entries':[{'day':'2026-11-01','prayers':0,'quran':None,'literature':20,'organization':45,'notes':'<script>bad()</script>'}], 'totals':{'prayers':0,'quran':0,'hadith':0,'literature':20,'organization':45},'goals':[{'metric':'literature','target':30}], 'summary':'<img src="https://invalid.example/">','review_note':'<b>Private review</b>'}
    html=reporting_book_html(data,'<owner>')
    assert '<script>' not in html and '<img src=' not in html and '<owner>' not in html
    assert '&lt;script&gt;' in html and '&lt;owner&gt;' in html
    assert 'পৃষ্ঠা' in html and 'মিনিট' in html and 'আমার রিপোর্ট বই' in html
    assert 'data:image' not in html and '@import' not in html
    assert '২০' in html and '৪৫' in html and 'নভেম্বর ২০২৬' in html


def test_activity_totals_distinguish_unreported_no_and_zero():
    from app.report_fields import aggregate
    totals,reported=aggregate([{'prayers':0,'quran_studied':True,'donated_hours':1.25},{'prayers':None,'quran_studied':False,'donated_hours':0.5},{}])
    assert totals['prayers']==0 and reported['prayers']==1
    assert totals['quran_studied']==1 and reported['quran_studied']==2
    assert totals['donated_hours']==1.75
    assert reported['organization']==0


def test_exports_include_extended_fields_without_ceiling_and_formula_execution():
    from app.report_book import reporting_book_xlsx
    import zipfile
    from io import BytesIO
    data={'month':'2026-11-01','status':'DRAFT','entries':[{'day':'2026-11-01','prayers':5,'congregational_prayers':4,'quran_studied':False,'donated_hours':1.25,'notes':'=1+1'}], 'achievements':'<script>example</script>', 'next_plan':'=1+1'}
    html=reporting_book_html(data)
    assert 'জামাতে সালাত' in html and 'সময় দান' in html and 'না' in html
    assert 'মাসিক সর্বোচ্চ' not in html and 'দৈনিক সর্বোচ্চ' not in html
    assert '&lt;script&gt;' in html and '<script>' not in html
    with zipfile.ZipFile(BytesIO(reporting_book_xlsx(data))) as z:
        assert b'<f>' not in z.read('xl/worksheets/sheet1.xml')
        assert b'<f>' not in z.read('xl/worksheets/sheet2.xml')
        assert b'No' in z.read('xl/sharedStrings.xml')
