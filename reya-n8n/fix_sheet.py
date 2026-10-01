"""Clean the live sheet (exported CSV) into an .xlsx for File > Import > Replace current sheet.
Usage: python3 fix_sheet.py live.csv out.xlsx"""
import csv,io,re,sys,openpyxl
csv.field_size_limit(10**9)
from openpyxl.styles import Font
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8')))
h=list(rows[0].keys())
if 'approval_deadline' not in h: h.append('approval_deadline')
SENT='أُرسلت إلى الجهة';READY='جاهزة للمراجعة';DEN='مرفوض - انتهت المهلة'
CH=['email_status','whatsapp_status','messenger_status','instagram_dm_status']
DR=['draft_date','draft_type','draft_email_subject','draft_email_body','draft_whatsapp','draft_messenger','draft_instagram']
MN=re.compile(r'candle|كاندل|شموع|شمع',re.I)
MT=re.compile(r'(مصنع|تصنيع|يصنع|تصنع|صانع|منتج|مصبوب|يدوي)[^.؛،\n]{0,25}(شمع|شموع)|(شمع|شموع)[^.؛،\n]{0,15}(يدوي|مصبوب|صويا)|candle ?(maker|brand|studio|factory|shop)|hand-?poured|#شموع',re.I)
cite=lambda v: re.sub(r'\(?cite index="[^"]*">','',re.sub(r'</?cite[^>]*>','',v)).strip()
note=lambda r,k,a: ' | '.join(x for x in [r.get(k,''),a] if x)
log={}
add=lambda k,v: log.setdefault(k,[]).append(v)
dseq=max([int(r['record_id'][-4:]) for r in rows if r['record_id'].startswith('AMM-D-')]+[0])
for r in rows:
  for k in r:
    if isinstance(r[k],str) and 'cite' in r[k]: r[k]=cite(r[k])
  rid=r['record_id']
  if not rid: continue
  if r['draft_type']=='excluded': continue
  if MN.search(r['business_name']+' '+r['english_name']) or MT.search(r['verification_notes']+' '+r['other_channels']):
    for k in CH:
      if r[k] not in(SENT,'غير متاح'): r[k]='مستبعد'
    for k in DR[2:]: r[k]=''
    r['draft_type']='excluded';r['overall_status']='مستبعد - صانع شموع';r['approval_deadline']=''
    r['writer_notes']=note(r,'writer_notes','Excluded: candle maker');add('excluded',rid);continue
  if rid.startswith('AMM-A-') and int(rid[-4:])>=24 and r['date_added']=='2026-09-30':
    dseq+=1;new=f'AMM-D-{dseq:04d}';r['record_id']=new;r['category']='ح — محال الديكور المنزلي والمفاهيم'
    for k in DR: r[k]=''
    for k in CH:
      if r[k]==READY: r[k]='لم تبدأ'
    if r['overall_status']!='لا توجد قناة': r['overall_status']='لم تبدأ'
    r['approval_deadline']='';r['writer_notes']=note(r,'writer_notes',f'Re-categorised from {rid}');add('recat',f'{rid}->{new}');continue
  # never-approved first drafts (Telegram step was crashing) -> redraft
  if r['draft_type']=='first' and not r['approval_deadline'] and any(r[k]==READY for k in CH):
    sent=any(r[k]==SENT for k in CH)
    for k in CH:
      if r[k]==READY: r[k]='لم تبدأ'
    if not sent:
      for k in DR: r[k]=''
    r['overall_status']='جزئية' if sent else 'لم تبدأ'
    r['writer_notes']=note(r,'writer_notes','Stuck draft reset — will be redrafted');add('redraft',rid)
  # reminders denied overnight during the first test, or stuck -> re-queue
  if (r['draft_type']=='done' and r['reminder_status']==DEN) or (r['draft_type']=='reminder' and not r['reminder_sent_date']):
    r['draft_type']='first';r['reminder_status']='لم يحن بعد';r['approval_deadline']=''
    for k in DR[2:]: r[k]=''
    r['reminder_notes']=note(r,'reminder_notes','Reminder re-queued (was denied overnight during setup test)');add('reminder requeued',rid)
wb=openpyxl.Workbook();ws=wb.active;ws.title='Sheet1';ws.append(h)
for r in rows: ws.append([r.get(k,'') for k in h])
for c in ws[1]: c.font=Font(bold=True)
ws.freeze_panes='B2';wb.save(sys.argv[2])
for k,v in log.items(): print(k,len(v),v)
