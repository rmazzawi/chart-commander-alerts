"""Builds the Reya Office n8n workflows (JSON for import) from the JS sources below.

Run:  python3 reya-n8n/build.py
Output: reya-n8n/workflows/*.json
"""
import json, os, uuid

OUT = os.path.join(os.path.dirname(__file__), 'workflows')
SHEET_ID = '1jSeftb1cyc9YYg7zTRPDJFGgIDltvQLJKjF3LRB3zHI'
CRED_SHEETS = {'googleSheetsOAuth2Api': {'id': 'hGcn8iQaUPZNWaG9', 'name': 'Reya Google Sheets'}}
CRED_TG = {'telegramApi': {'id': 'USmj7xUTRbgSc4ZB', 'name': 'Reya B2B bot'}}
CRED_CLAUDE = {'httpHeaderAuth': {'id': 'qXwcfKXxR9EDHtIs', 'name': 'Anthropic API'}}
CRED_GMAIL = {'gmailOAuth2': {'id': '7uH7CFIkCzGQIsJq', 'name': 'Reya Gmail'}}

# ---------------------------------------------------------------- shared JS
COMMON = r"""
const TZ='Asia/Amman';
const SENT='أُرسلت إلى الجهة', READY='جاهزة للمراجعة', DENIED='مرفوض - انتهت المهلة', EXCL='مستبعد - صانع شموع';
const NP='غير منشور', NV='غير متحقق';
const APPROVERS=[8469419204, 1798976243];
const MODEL='claude-sonnet-5';
const APPROVAL_HOURS=6;
const s=v=>String(v==null?'':v).trim();
const today=()=>new Date().toLocaleDateString('en-CA',{timeZone:TZ});
const nd=v=>{v=s(v);if(!v)return '';if(/^\d{4}-\d{2}-\d{2}/.test(v))return v.slice(0,10);const m=v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);return m?`${m[3]}-${m[1].padStart(2,'0')}-${m[2].padStart(2,'0')}`:'';};
const addDays=(d,n)=>{const t=new Date(d+'T00:00:00Z');t.setUTCDate(t.getUTCDate()+n);return t.toISOString().slice(0,10);};
const avail=v=>{v=s(v);return v!==''&&!v.startsWith(NP)&&!v.startsWith(NV)&&!v.startsWith('غير متوفر');};
// Parses model JSON. If the answer was cut off mid-list, keeps every COMPLETE
// object it can find instead of failing the whole run.
const salvageObjects=t=>{const out=[];let depth=0,start=-1,inStr=false,esc2=false;
  for(let i=0;i<t.length;i++){const ch=t[i];
    if(inStr){if(esc2)esc2=false;else if(ch==='\\')esc2=true;else if(ch==='"')inStr=false;continue;}
    if(ch==='"'){inStr=true;continue;}
    if(ch==='{'){if(depth===1&&start<0)start=i;depth++;}
    else if(ch==='}'){depth--;if(depth===1&&start>=0){try{out.push(JSON.parse(t.slice(start,i+1)));}catch(e){}start=-1;}}
    else if(ch==='['&&depth===0)depth=1;}
  return out;};
const parseJson=t=>{t=String(t||'').replace(/```json|```/g,'');const a=t.search(/[\[{]/);if(a<0)throw new Error('no JSON in model output');const close=t[a]==='['?']':'}';const b=t.lastIndexOf(close);
  try{return JSON.parse(t.slice(a,b+1));}catch(e){if(t[a]==='['){const objs=salvageObjects(t.slice(a));if(objs.length)return objs;}throw e;}};
const claudeText=r=>(r.content||[]).filter(c=>c.type==='text').map(c=>c.text).join('\n');
const clean=v=>s(v).replace(/<\/?cite[^>]*>/g,'').replace(/\(?cite index="[^"]*">/g,'').trim();
const esc=x=>String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
// 6 approval hours counted only while awake (08:00-22:00 Amman, UTC+3): a card at 21:00 expires 13:00 next day
const deadlineIso=()=>{const OFF=3*3600e3,START=8,END=22;let t=Date.now(),left=APPROVAL_HOURS*3600e3;
  while(left>0){const l=new Date(t+OFF);const h=l.getUTCHours()+l.getUTCMinutes()/60+l.getUTCSeconds()/3600;
    if(h<START){t+=(START-h)*3600e3;continue;}if(h>=END){t+=(24-h+START)*3600e3;continue;}
    const step=Math.min(left,(END-h)*3600e3);t+=step;left-=step;}
  return new Date(t).toISOString();};
const fmtAmman=iso=>new Date(iso).toLocaleString('en-GB',{timeZone:TZ,weekday:'short',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
// Categories (ز flowers retired; ط spas and ح home decor added per CLAUDE.md)
const CATS=['أ — منظمو حفلات الزفاف','ب — متاجر هدايا المعمودية','ج — متاجر الشموع المميزة (بائعو تجزئة فقط)','هـ — محال الكيك والمناسبات','و — محال الهدايا في فنادق 5 نجوم','ط — سبا نسائي (سبا للسيدات)','ح — محال الديكور المنزلي والمفاهيم'];
const CODE={'أ':'A','ب':'B','ج':'C','ه':'H','و':'W','ط':'S','ح':'D','ز':'Z'};
// Hard rule: never contact candle makers / producers / own-brand candle shops
const MAKER_NAME=/candle|كاندل|شموع|شمع/i;
const MAKER_TXT=/(مصنع|تصنيع|يصنع|تصنع|صانع|منتج|مصبوب|يدوي)[^.؛،\n]{0,25}(شمع|شموع)|(شمع|شموع)[^.؛،\n]{0,15}(يدوي|مصبوب|صويا)|candle ?(maker|brand|studio|factory|shop)|hand-?poured/i;
const isCandleMaker=r=>MAKER_NAME.test(s(r.business_name)+' '+s(r.english_name))||MAKER_TXT.test([r.verification_notes,r.other_channels,r.relevance,r.description].map(s).join(' '));
"""

WRITER_GUIDE = r"""أنت موظف مراسلات B2B لدى Reya Candles & Soaps (علامة شموع معطرة مصبوبة يدويًا في عمّان، تأسست 2025).
الحقائق المؤكدة فقط: تصنع شموعًا معطرة مصبوبة يدويًا في الأردن؛ يذكر الكتالوج مزيج شمع الصويا العضوي وشمع النحل وزيوتًا عطرية من مكونات طبيعية؛ خطوط المنتجات: الشموع العصرية، المجسمة، الزجاجية، شمع الذوبان، وهدايا المناسبات.
قواعد التنسيق المهمة لعرض الرسالة على شاشة الجوال: (1) لا تكتب أي كلمة أو جملة إنجليزية داخل سطر عربي؛ أي نص إنجليزي (اسم إنجليزي أو رابط أو رقم هاتف) يوضع في سطر مستقل بمفرده. (2) اذكر اسم العلامة داخل الجمل العربية بالعربية «ريا كاندلز». (3) لا تكتب كلمة «واتساب» إطلاقًا؛ استخدم الرمز 📱 بدلًا منها. (4) لا تضف توقيعًا ولا أرقام تواصل في نهاية الرسالة؛ يضيفها النظام تلقائيًا للبريد.
ممنوع: ذكر أسعار أو خصومات أو حد أدنى للطلب أو مدة تجهيز أو قدرة تخصيص أو شروط توريد؛ ادعاءات مثل «الأفضل» أو «الأكثر مبيعًا» أو «عضوي بالكامل»؛ ضمان نجاح التعاون؛ ادعاء معرفة تفاصيل عن الجهة غير موجودة في البيانات المعطاة؛ الرموز التعبيرية الكثيرة؛ اقتراح «شراكة» أو «تبادل» مع صانعي شموع.
دليل التخصيص حسب الفئة (زاوية واحدة ومنتج أو خط واحد لكل رسالة):
أ — منظمو حفلات الزفاف: هدايا ضيوف ولمسة شخصية للمناسبات؛ الشموع الصغيرة مثل Little Paws وهدايا المناسبات؛ لا تدّعِ توفر تخصيص.
ب — متاجر هدايا المعمودية: شموع صغيرة تذكارية؛ Little Paws وLove You Beary Much؛ لا تصف أي منتج بأنه ديني.
ج — متاجر الشموع المميزة (بائعو تجزئة): تنوع بصري وعطري محلي الصنع لرفوف المتجر؛ الشموع المجسمة والزجاجية وشمع الذوبان.
هـ — محال الكيك والمناسبات: تصاميم مستوحاة من الحلويات لأعياد الميلاد؛ Strawberry Dream وBlueberry Cocoa Bliss وCoffee Combo وRaspberry Iced Coffee؛ وضّح أنها شموع ديكورية وليست طعامًا.
و — محال الهدايا في فنادق 5 نجوم: هدايا محلية الصنع من عمّان بحضور بصري؛ Cave ومجموعات الشخصيات والشموع الزجاجية؛ لا تصف الخامات بأنها «فاخرة».
ط — سبا نسائي: أجواء عطرية هادئة لغرف الاسترخاء أو رف بيع صغير؛ الشموع الزجاجية وشمع الذوبان؛ ممنوع أي ادعاء علاجي أو صحي.
ح — محال الديكور المنزلي والمفاهيم: قطع ديكور معطرة مصنوعة محليًا؛ الشموع المجسمة والزجاجية.
ز — محال الزهور: الجمع بين الباقات والشموع كهدايا؛ Blossom Float.
إذا كشفت بيانات الجهة تخصصًا أدق، خصّص الرسالة لنشاطها الفعلي."""

# ---------------------------------------------------------------- helpers
def node(name, typ, ver, pos, params, **extra):
    n = {'parameters': params, 'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'reya/' + name)), 'name': name,
         'type': typ, 'typeVersion': ver, 'position': pos}
    n.update(extra)
    return n

def code(name, pos, js, **extra):
    return node(name, 'n8n-nodes-base.code', 2, pos, {'jsCode': COMMON + js}, **extra)

def sheet_read(name, pos, **extra):
    return node(name, 'n8n-nodes-base.googleSheets', 4.5, pos, {
        'documentId': {'__rl': True, 'value': SHEET_ID, 'mode': 'id', 'cachedResultName': 'Reya_B2B_Master_Sheet'},
        'sheetName': {'__rl': True, 'value': 'Sheet1', 'mode': 'name'}, 'options': {}},
        credentials=CRED_SHEETS, alwaysOutputData=True, **extra)

def sheet_upsert(name, pos, **extra):
    return node(name, 'n8n-nodes-base.googleSheets', 4.5, pos, {
        'operation': 'appendOrUpdate',
        'documentId': {'__rl': True, 'value': SHEET_ID, 'mode': 'id', 'cachedResultName': 'Reya_B2B_Master_Sheet'},
        'sheetName': {'__rl': True, 'value': 'Sheet1', 'mode': 'name'},
        'columns': {'mappingMode': 'autoMapInputData', 'value': {}, 'matchingColumns': ['record_id'], 'schema': []},
        'options': {'cellFormat': 'RAW'}}, credentials=CRED_SHEETS, **extra)

def claude_call(name, pos, timeout=180000):
    return node(name, 'n8n-nodes-base.httpRequest', 4.2, pos, {
        'method': 'POST', 'url': 'https://api.anthropic.com/v1/messages',
        'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth',
        'sendHeaders': True, 'headerParameters': {'parameters': [
            {'name': 'anthropic-version', 'value': '2023-06-01'},
            {'name': 'content-type', 'value': 'application/json'}]},
        'sendBody': True, 'specifyBody': 'json', 'jsonBody': '={{ JSON.stringify($json.body) }}',
        'options': {'batching': {'batch': {'batchSize': 1, 'batchInterval': 2000}}, 'timeout': timeout}},
        credentials=CRED_CLAUDE, onError='continueRegularOutput')

def tg_text(name, pos, **extra):
    return node(name, 'n8n-nodes-base.telegram', 1.2, pos, {
        'chatId': '={{ $json.chat_id }}', 'text': '={{ $json.text }}',
        'additionalFields': {'appendAttribution': False}},
        credentials=CRED_TG, webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, 'reya/wh/' + name)),
        onError='continueRegularOutput', **extra)

def tg_approval(name, pos):
    btn = lambda i: {'text': '={{ $json.bt%d }}' % i, 'additionalFields': {'callback_data': '={{ $json.bc%d }}' % i}}
    return node(name, 'n8n-nodes-base.telegram', 1.2, pos, {
        'chatId': '={{ $json.chat_id }}', 'text': '={{ $json.text }}', 'replyMarkup': 'inlineKeyboard',
        'inlineKeyboard': {'rows': [{'row': {'buttons': [btn(1), btn(2)]}},
                                    {'row': {'buttons': [btn(3), btn(4)]}},
                                    {'row': {'buttons': [btn(5)]}}]},
        'additionalFields': {'appendAttribution': False, 'parse_mode': 'HTML', 'disable_web_page_preview': True}},
        credentials=CRED_TG, webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, 'reya/wh/' + name)),
        onError='continueRegularOutput')

def if_node(name, pos, expr):
    return node(name, 'n8n-nodes-base.if', 2.2, pos, {
        'conditions': {'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'loose', 'version': 2},
                       'conditions': [{'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'reya/if/' + name)),
                                       'leftValue': expr, 'rightValue': '',
                                       'operator': {'type': 'boolean', 'operation': 'true', 'singleValue': True}}],
                       'combinator': 'and'}, 'looseTypeValidation': True, 'options': {}})

def link(conns, a, b, out=0):
    outs = conns.setdefault(a, {'main': []})['main']
    while len(outs) <= out:
        outs.append([])
    outs[out].append({'node': b, 'type': 'main', 'index': 0})

def chain(conns, *names):
    for a, b in zip(names, names[1:]):
        link(conns, a, b)

def save(fname, name, nodes, conns):
    wf = {'name': name, 'nodes': nodes, 'connections': conns, 'pinData': {},
          'settings': {'executionOrder': 'v1', 'timezone': 'Asia/Amman', 'saveManualExecutions': True},
          'meta': {'instanceId': 'f3ebdc47079737fb41f9a77191b283344a56abf33f613d18c592413418d3cc73'}}
    with open(os.path.join(OUT, fname), 'w', encoding='utf-8') as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)

# Telegram approval card, shared by first messages and reminders
BUILD_MSG = r"""
function buildMsg(r,type){
  const first=type==='first';
  const clip=(x,n)=>{x=s(x);return x.length>n?x.slice(0,n)+'…':x;};
  const id=s(r.record_id);
  const L=['<b>'+esc(s(r.business_name))+'</b>'];
  if(avail(r.english_name))L.push(esc(s(r.english_name)));
  L.push('🏷 '+esc(s(r.category))+' | '+esc(s(r.area)));
  L.push('🆔 '+esc(id)+(first?' — NEW outreach':' — 7-day REMINDER'));
  if(r.approval_deadline)L.push('⏰ Approve before <b>'+esc(fmtAmman(r.approval_deadline))+'</b> (Amman). No tap = automatically DENIED.');
  L.push('');
  if(s(r.draft_email_body))L.push('📧 EMAIL to '+esc(s(r.email)),'Subject:',esc(clip(r.draft_email_subject,150)),'','<pre>'+esc(clip(r.draft_email_body,1100))+'</pre>','');
  if(s(r.draft_whatsapp)){const n=s(r.whatsapp_number).replace(/\D/g,'');
    L.push('📱 '+esc(s(r.whatsapp_number)),'<a href="'+esc('https://wa.me/'+n+'?text='+encodeURIComponent(clip(r.draft_whatsapp,600)))+'">Open chat with this draft</a>','','<pre>'+esc(clip(r.draft_whatsapp,600))+'</pre>','');}
  if(s(r.draft_messenger))L.push('💬 FACEBOOK — <a href="'+esc(s(r.facebook))+'">open page</a>, paste:','<pre>'+esc(clip(r.draft_messenger,500))+'</pre>','');
  if(s(r.draft_instagram))L.push('📸 INSTAGRAM — <a href="'+esc(s(r.instagram))+'">open profile</a>, paste:','<pre>'+esc(clip(r.draft_instagram,500))+'</pre>','');
  L.push(first?'Email button SENDS the email. Other channels: send by hand, then tap its button.':'Email button SENDS the reminder. Other channels by hand, tap their button, then tap “Reminder done”.');
  const has=k=>!!s(r[k]);
  const b=(ok,label,act)=>ok?[label,act+'|'+id]:['— not available','n|'+id];
  const b1=b(has('draft_email_body'),'📧 Send email now','e');
  const b2=b(has('draft_whatsapp'),'📱 WhatsApp sent','w');
  const b3=b(has('draft_messenger'),'💬 Messenger sent','m');
  const b4=b(has('draft_instagram'),'📸 Instagram sent','i');
  const b5=first?['❌ Skip (deny)','s|'+id]:['✔ Reminder done','d|'+id];
  return {text:L.join('\n'),bt1:b1[0],bc1:b1[1],bt2:b2[0],bc2:b2[1],bt3:b3[0],bc3:b3[1],bt4:b4[0],bc4:b4[1],bt5:b5[0],bc5:b5[1]};
}
"""

# ================================================================ 1. DAILY RUN
def daily_run():
    N, C = [], {}
    N.append(node('08:00 Sat–Thu', 'n8n-nodes-base.scheduleTrigger', 1.2, [0, 400],
                  {'rule': {'interval': [{'field': 'cronExpression', 'expression': '0 8 * * 6,0-4'}]}}))
    N.append(node('▶ Start the day (manual)', 'n8n-nodes-base.manualTrigger', 1, [0, 600], {}))

    # ---------- Stage A: research (top branch, runs first)
    y = 0
    N.append(sheet_read('A1 Read sheet', [250, y]))
    N.append(code('A2 Plan research', [480, y], r"""
const rows=$input.all().map(i=>i.json).filter(r=>r.record_id);
const t=today();
const LIMIT=20;
const need=Math.max(0,LIMIT-rows.filter(r=>nd(r.date_added)===t).length);
const focus=CATS[Math.floor(Date.now()/86400000)%CATS.length];
const known=[...new Set(rows.flatMap(r=>[r.business_name,r.english_name]).map(s).filter(x=>x&&x!==NP))].slice(0,700);
const SYSTEM=[
'أنت باحث تطوير أعمال لصالح Reya Candles & Soaps (شموع معطرة مصبوبة يدويًا في عمّان، الأردن).',
'مهمتك: العثور على جهات B2B جديدة داخل محافظة عمّان فقط، وجمع بيانات الاتصال التجارية المنشورة علنًا وحدها. عند العثور على موقع إلكتروني ابحث داخله (صفحة اتصل بنا، من نحن، التذييل) عن البريد والأرقام والحسابات.',
'الفئات: '+CATS.join(' | ')+'.',
'استبعاد مطلق: أي جهة تصنع أو تصب أو تنتج الشموع أو تبيع شموعًا من صنعها (علامات شموع، ورش، مصانع، متاجر شموع يدوية)، حتى لو للتعاون أو التوريد. المقبول فقط محلات تبيع منتجات جهات أخرى. أي جهة خارج عمّان مستبعدة. عند الشك تجاهل الجهة.',
'قواعد صارمة: لا تخمّن أي رقم أو بريد أو حساب؛ اكتب "غير منشور" عندما لا تجد المعلومة. لا تضع رقمًا في whatsapp_number إلا إذا كان موصوفًا كواتساب أو عليه رابط wa.me. وحّد أرقام الأردن إلى +962. لا بيانات شخصية لموظفين. لا تتجاوز صفحات تسجيل الدخول. أعطِ الأولوية لجهات لديها قناة تواصل منشورة واحدة على الأقل (بريد، واتساب، فيسبوك، إنستغرام).',
'صنّف كل جهة بدليل واضح من نشاطها. للفئة و: تحقق أن الفندق خمس نجوم وأن المتجر داخله.',
'verification_status: مؤكد (مصدر رسمي حديث أو مصدران متوافقان) | مرجح (مصدر واحد موثوق) | غير متحقق.',
'اجعل الـ JSON مضغوطًا في سطر واحد بدون مسافات زائدة، واختصر الملاحظات (verification_notes و popularity_reason و potential_fit) إلى جملة قصيرة واحدة.',
'لا تضع وسوم cite أو مراجع داخل النصوص. أعد JSON فقط: مصفوفة كائنات بالمفاتيح: category, business_name, english_name, branch, area, address, map_link, landline, mobile, whatsapp_number, whatsapp_link, email, website, facebook, instagram, other_channels, popularity_reason, activity_status, verification_status, main_source, extra_sources, verification_notes, potential_fit, priority. قيمة category تطابق إحدى الفئات أعلاه حرفيًا. activity_status: نشط | غير واضح | مغلق مؤقتًا | مغلق نهائيًا. priority: عالية | متوسطة | منخفضة.'
].join('\n');
const USER=`ابحث عن ${need} جهة جديدة. فئة اليوم: ${focus}. إن لم تجد العدد الكافي فأكمل من الفئات الأخرى (عدا صانعي الشموع). تجنّب هذه الجهات المسجلة مسبقًا: ${known.join(' ; ')||'(لا شيء)'}`;
return [{json:{need,focus,today:t,body:{model:MODEL,max_tokens:32000,system:SYSTEM,tools:[{type:'web_search_20250305',name:'web_search',max_uses:25}],messages:[{role:'user',content:USER}]}}}];
"""))
    N.append(if_node('A3 Need contacts?', [700, y], '={{ $json.need > 0 }}'))
    N.append(claude_call('A4 Claude research (web search)', [920, y - 100], timeout=900000))
    N.append(code('A5 Prepare rows', [1140, y], r"""
const plan=$('A2 Plan research').first().json;
if(plan.need<=0)return [{json:{_none:true,_dropped:0}}];
const existing=$('A1 Read sheet').all().map(i=>i.json).filter(r=>r.record_id);
let list=[];
const resp=$input.first().json;
if(resp.error)return [{json:{_none:true,_dropped:0,_error:'Research failed (Claude API): '+(resp.error.message||JSON.stringify(resp.error)).slice(0,300)}}];
try{list=parseJson(claudeText(resp));}catch(e){return [{json:{_none:true,_dropped:0,_error:'Research failed: '+e.message+' (stop_reason: '+(resp.stop_reason||'none')+')'}}];}
if(!Array.isArray(list))list=list.contacts||[];
const keyOf=x=>s(x).toLowerCase().replace(/\s+/g,' ');
const digits=x=>s(x).replace(/\D/g,'');
const seen=new Set();
existing.forEach(r=>[r.business_name,r.english_name,r.instagram,r.facebook,digits(r.mobile),digits(r.whatsapp_number)].forEach(v=>{const k=keyOf(v);if(k&&k!==keyOf(NP))seen.add(k);}));
const normPhone=p=>{const d=digits(p);if(!d)return NP;if(d.startsWith('962'))return '+'+d;if(d.startsWith('0'))return '+962'+d.slice(1);return s(p);};
const maxSeq={};
existing.forEach(r=>{const m=/^AMM-([A-Z])-(\d+)$/.exec(s(r.record_id));if(m)maxSeq[m[1]]=Math.max(maxSeq[m[1]]||0,+m[2]);});
const P=x=>clean(x)||NP;
const out=[];let dropped=0;
for(const c0 of list){
  if(out.length>=plan.need)break;
  const c={};for(const k in c0)c[k]=clean(c0[k]);
  if(!c.business_name&&!c.english_name)continue;
  if(isCandleMaker(c)){dropped++;continue;}
  const keys=[c.business_name,c.english_name,c.instagram,c.facebook,digits(c.mobile),digits(c.whatsapp_number)].map(keyOf).filter(k=>k&&k!==keyOf(NP));
  if(keys.some(k=>seen.has(k)))continue;
  keys.forEach(k=>seen.add(k));
  const first=s(c.category).charAt(0);
  const cat=CATS.find(x=>x.charAt(0)===first);
  if(!cat){dropped++;continue;}   // unknown category: skip instead of mislabelling
  const code=CODE[first];
  maxSeq[code]=(maxSeq[code]||0)+1;
  const wa=avail(c.whatsapp_number)?normPhone(c.whatsapp_number):NP;
  const row={record_id:`AMM-${code}-${String(maxSeq[code]).padStart(4,'0')}`,date_added:plan.today,category:cat,
    business_name:P(c.business_name),english_name:P(c.english_name),branch:P(c.branch),governorate:'عمّان',area:P(c.area),
    address:P(c.address),map_link:P(c.map_link),landline:avail(c.landline)?normPhone(c.landline):NP,
    mobile:avail(c.mobile)?normPhone(c.mobile):NP,whatsapp_number:wa,whatsapp_link:wa!==NP?'https://wa.me/'+digits(wa):NP,
    email:P(c.email),website:P(c.website),facebook:P(c.facebook),instagram:P(c.instagram),other_channels:P(c.other_channels),
    popularity_reason:P(c.popularity_reason),activity_status:P(c.activity_status),
    verification_status:['مؤكد','مرجح','غير متحقق'].includes(c.verification_status)?c.verification_status:NV,
    last_verified:plan.today,main_source:P(c.main_source),extra_sources:P(c.extra_sources),verification_notes:P(c.verification_notes),
    potential_fit:P(c.potential_fit),priority:['عالية','متوسطة','منخفضة'].includes(c.priority)?c.priority:'متوسطة'};
  const ch={email_status:avail(row.email),whatsapp_status:avail(row.whatsapp_number),messenger_status:avail(row.facebook),instagram_dm_status:avail(row.instagram)};
  let n=0;for(const k in ch){row[k]=ch[k]?'لم تبدأ':'غير متاح';if(ch[k])n++;}
  row.channels_available=n;row.channels_sent=0;row.overall_status=n?'لم تبدأ':'لا توجد قناة';
  out.push({json:row});
}
if(out.length)out[0].json._dropped=dropped;   // stripped before saving
return out.length?out:[{json:{_none:true,_dropped:dropped}}];
"""))
    N.append(code('A6 Strip helper fields', [1360, y - 100], r"""
return $input.all().filter(i=>!i.json._none).map(i=>{const j={...i.json};delete j._dropped;delete j._error;return {json:j};});
"""))
    N.append(sheet_upsert('A7 Save new contacts', [1580, y - 100]))
    N.append(code('A8 Research summary', [1800, y], r"""
let items=[],drop=0,err='';
try{const p=$('A5 Prepare rows').all().map(i=>i.json);items=p.filter(j=>j.record_id);drop=p.reduce((a,j)=>a+(j._dropped||0),0);err=(p.find(j=>j._error)||{})._error||'';}catch(e){}
const plan=$('A2 Plan research').first().json;
if(plan.need<=0)return APPROVERS.map(id=>({json:{chat_id:id,text:`🔎 Researcher — ${plan.today}\nDaily quota already reached, no new search.`}}));
const by={};items.forEach(j=>by[j.category]=(by[j.category]||0)+1);
const ch=items.filter(j=>j.channels_available>0).length;
const text=`🔎 Researcher — ${plan.today}\nAdded ${items.length} of ${plan.need} contacts (${ch} with at least one channel).\n`+
 Object.entries(by).map(([k,v])=>`• ${k}: ${v}`).join('\n')+
 (drop?`\n🚫 Dropped ${drop} (candle makers / unknown category).`:'')+(err?`\n⚠️ ${err}`:'');
return APPROVERS.map(id=>({json:{chat_id:id,text}}));
""", executeOnce=True))
    N.append(tg_text('A9 Telegram research summary', [2020, y]))
    chain(C, 'A1 Read sheet', 'A2 Plan research', 'A3 Need contacts?')
    link(C, 'A3 Need contacts?', 'A4 Claude research (web search)', 0)
    link(C, 'A3 Need contacts?', 'A5 Prepare rows', 1)
    chain(C, 'A4 Claude research (web search)', 'A5 Prepare rows', 'A6 Strip helper fields', 'A7 Save new contacts')
    chain(C, 'A5 Prepare rows', 'A8 Research summary', 'A9 Telegram research summary')

    # ---------- Stage B: writer (middle branch, runs after research)
    y = 600
    N.append(sheet_read('B1 Read sheet', [250, y]))
    N.append(code('B2 Select contacts', [480, y], r"""
const LIMIT=20;
const rows=$input.all().map(i=>i.json).filter(r=>r.record_id);
const t=today();
const left=Math.max(0,LIMIT-rows.filter(r=>nd(r.draft_date)===t).length);
const pr={'عالية':0,'متوسطة':1,'منخفضة':2};
const cand=rows.filter(r=>!nd(r.draft_date)&&!nd(r.first_send_date)&&!s(r.overall_status).startsWith('مستبعد')&&!isCandleMaker(r)
  &&['مؤكد','مرجح'].includes(s(r.verification_status))&&[r.email,r.whatsapp_number,r.facebook,r.instagram].some(avail));
cand.sort((a,b)=>((pr[s(a.priority)]??1)-(pr[s(b.priority)]??1))||nd(a.date_added).localeCompare(nd(b.date_added)));
return cand.slice(0,left).map(r=>({json:r}));
"""))
    N.append(code('B3 Build draft request', [700, y], r"""
const SYS=GUIDE+"\nالمهمة: اكتب رسالة تعريفية عربية قصيرة ومهنية ودافئة لجهة واحدة، لكل قناة مطلوبة.\nالبنية: تحية (مرحبًا فريق [اسم المنشأة])، تعريف موجز بريا كاندلز مع حقيقة واحدة ذات صلة، سبب واقعي واحد يجعل التعاون مناسبًا لنشاط الجهة، ودعوة بسيطة مثل طلب الإذن بإرسال الكتالوج.\nالطول: messenger وinstagram من 2 إلى 4 جمل؛ whatsapp من 3 إلى 5 جمل قصيرة تنتهي بسؤال واحد؛ email موضوع قصير + نص 70 إلى 120 كلمة بلا توقيع.\nأعد JSON فقط: {\"email\":{\"subject\":\"\",\"body\":\"\"},\"whatsapp\":\"\",\"messenger\":\"\",\"instagram\":\"\"} واترك القنوات غير المطلوبة فارغة.";
return $input.all().map(i=>{
  const r=i.json;const chans=[];
  if(avail(r.email))chans.push('email');
  if(avail(r.whatsapp_number))chans.push('whatsapp');
  if(avail(r.facebook))chans.push('messenger');
  if(avail(r.instagram))chans.push('instagram');
  const info={business_name:r.business_name,english_name:r.english_name,category:r.category,area:r.area,potential_fit:clean(r.potential_fit),why_listed:clean(r.popularity_reason),channels_requested:chans};
  return {json:{record_id:r.record_id,row:r,chans,body:{model:MODEL,max_tokens:4500,system:SYS,messages:[{role:'user',content:'اكتب المسودات لهذه الجهة وأعد JSON فقط:\n'+JSON.stringify(info)}]}}};
});
""".replace('GUIDE', json.dumps(WRITER_GUIDE, ensure_ascii=False))))
    N.append(claude_call('B4 Claude drafts', [920, y]))
    N.append(code('B5 Parse drafts', [1140, y], r"""
const src=$('B3 Build draft request').all();
const SIG='\n\nفريق ريا كاندلز\nReya Candles & Soaps\n📱 +962 77 913 2655\n📘 https://www.facebook.com/Reyacandles\n📸 https://www.instagram.com/reya_candles/';
const out=[];
$input.all().forEach((it,idx)=>{
  const ctx=src[idx].json;const r=ctx.row;const ch=ctx.chans;
  let d;try{d=parseJson(claudeText(it.json));}catch(e){return;}
  const u={record_id:r.record_id,draft_date:today(),draft_type:'first',draft_email_subject:'',draft_email_body:'',draft_whatsapp:'',draft_messenger:'',draft_instagram:''};
  if(ch.includes('email')&&d.email&&s(d.email.body)){u.draft_email_subject=s(d.email.subject);u.draft_email_body=s(d.email.body)+SIG;}
  if(ch.includes('whatsapp')&&s(d.whatsapp))u.draft_whatsapp=s(d.whatsapp);
  if(ch.includes('messenger')&&s(d.messenger))u.draft_messenger=s(d.messenger);
  if(ch.includes('instagram')&&s(d.instagram))u.draft_instagram=s(d.instagram);
  out.push({json:u});
});
return out;
"""))
    N.append(code('B6 Build manager review', [1360, y], r"""
const R={};for(const x of $('B3 Build draft request').all())R[x.json.record_id]=x.json.row||{};
const rules='You are the department manager reviewing one outbound B2B draft for Reya Candles (hand-poured candles from Amman, Jordan). Check the draft against the sheet row and fix it. Rules: 1) Arabic, respectful, short. 2) One main angle and one product line only. 3) No claims about custom orders, agreements, prices, awards or materials beyond: organic soy and beeswax blend, figurine candles, glass candles, melt candles. No therapeutic claims. 4) The word WhatsApp must never appear; use the phone icon instead. 5) Any English text sits on its own line. 6) Keep a channel draft only if that channel exists in the sheet row; never invent contact details. 7) BLOCK if the business itself makes, pours, produces, brands or wholesales candles (candle brands, workshops, factories, handmade-candle shops). We never contact candle makers, not even for partnership. Only retailers selling products made by others. 8) BLOCK if the row says unverified or needs verification before contact. 9) BLOCK if the row does not clearly place the business physically in Amman, Jordan. Return ONLY one JSON object: verdict (ok|fixed|block), note (one short English sentence), email_subject, email_body, whatsapp, messenger, instagram (corrected texts; unchanged fields as given).';
const out=[];
for(const i of $input.all()){const d=i.json;if(!(d.draft_email_body||d.draft_whatsapp||d.draft_messenger||d.draft_instagram))continue;
  out.push({json:{record_id:d.record_id,body:{model:MODEL,max_tokens:8000,system:rules,messages:[{role:'user',content:JSON.stringify({sheet_row:R[d.record_id]||{},draft:{email_subject:d.draft_email_subject,email_body:d.draft_email_body,whatsapp:d.draft_whatsapp,messenger:d.draft_messenger,instagram:d.draft_instagram}})}]}}});}
return out;
"""))
    N.append(claude_call('B7 Manager review Claude', [1580, y]))
    N.append(code('B8 Apply review + set 6h deadline', [1800, y], r"""
const ids=$('B6 Build manager review').all().map(x=>x.json.record_id);
const rows={};for(const x of $('B3 Build draft request').all())rows[x.json.record_id]=x.json.row;
const rev={};
$input.all().forEach((it,k)=>{const id=ids[k];if(!id)return;try{rev[id]=parseJson(claudeText(it.json));}catch(e){rev[id]={verdict:'block',note:'Manager review failed (API error) — draft held back.'};}});
const dl=deadlineIso();
const out=[];
for(const i of $('B5 Parse drafts').all()){
  const d={...i.json};const r=rows[d.record_id]||{};const v=rev[d.record_id];
  if(v&&v.verdict==='fixed'){d.draft_email_subject=s(v.email_subject);d.draft_email_body=s(v.email_body);d.draft_whatsapp=s(v.whatsapp);d.draft_messenger=s(v.messenger);d.draft_instagram=s(v.instagram);
    if(d.draft_email_body&&!d.draft_email_body.includes('Reya Candles & Soaps'))d.draft_email_body+='\n\nفريق ريا كاندلز\nReya Candles & Soaps\n📱 +962 77 913 2655\n📘 https://www.facebook.com/Reyacandles\n📸 https://www.instagram.com/reya_candles/';}
  const blocked=!v||v.verdict==='block';
  if(blocked){d.draft_email_subject='';d.draft_email_body='';d.draft_whatsapp='';d.draft_messenger='';d.draft_instagram='';}
  const st=(has,exists)=>has?READY:(exists?'لم تبدأ':'غير متاح');
  d.email_status=st(d.draft_email_body,avail(r.email));
  d.whatsapp_status=st(d.draft_whatsapp,avail(r.whatsapp_number));
  d.messenger_status=st(d.draft_messenger,avail(r.facebook));
  d.instagram_dm_status=st(d.draft_instagram,avail(r.instagram));
  d.channels_available=[r.email,r.whatsapp_number,r.facebook,r.instagram].filter(avail).length;d.channels_sent=0;
  if(blocked){d.draft_type='blocked';d.overall_status='محجوبة من المدير';d.writer_notes=[s(r.writer_notes),'Manager blocked: '+s(v&&v.note)].filter(Boolean).join(' | ');d.approval_deadline='';}
  else{d.overall_status='بانتظار الموافقة';d.approval_deadline=dl;}
  out.push({json:d});
}
return out;
"""))
    N.append(sheet_upsert('B9 Save drafts to sheet', [2020, y]))
    N.append(code('B10 Build Telegram cards', [2240, y], BUILD_MSG + r"""
const rows={};for(const x of $('B3 Build draft request').all())rows[x.json.record_id]=x.json.row;
return $('B8 Apply review + set 6h deadline').all().filter(p=>p.json.draft_type==='first').flatMap(p=>{
  const m=buildMsg({...rows[p.json.record_id],...p.json},'first');
  return APPROVERS.map(id=>({json:{chat_id:id,...m}}));
});
""", executeOnce=True))
    N.append(tg_approval('B11 Telegram approval', [2460, y]))
    N.append(code('B12 Manager notes', [2020, y + 220], r"""
const R={};for(const x of $('B3 Build draft request').all())R[x.json.record_id]=x.json.row||{};
const ids=$('B6 Build manager review').all().map(x=>x.json.record_id);
const lines=[];
$input.all().forEach((it,k)=>{const id=ids[k];if(!id)return;let v;try{v=parseJson(claudeText(it.json));}catch(e){lines.push('⚠️ '+id+': review failed, draft held back');return;}
  if(v.verdict==='ok')return;lines.push((v.verdict==='block'?'⛔ ':'✏️ ')+s((R[id]||{}).english_name||(R[id]||{}).business_name||id)+' ('+id+'): '+s(v.note));});
if(!lines.length)return [];
const text="📝 Manager notes on today's drafts:\n"+lines.join('\n')+'\n(⛔ blocked — not sent to you; ✏️ fixed before reaching you)';
return APPROVERS.map(c=>({json:{chat_id:c,text}}));
"""))
    N.append(tg_text('B13 Telegram manager notes', [2240, y + 220]))
    chain(C, 'B1 Read sheet', 'B2 Select contacts', 'B3 Build draft request', 'B4 Claude drafts', 'B5 Parse drafts',
          'B6 Build manager review', 'B7 Manager review Claude', 'B8 Apply review + set 6h deadline', 'B9 Save drafts to sheet',
          'B10 Build Telegram cards', 'B11 Telegram approval')
    chain(C, 'B7 Manager review Claude', 'B12 Manager notes', 'B13 Telegram manager notes')

    # ---------- Stage C: reminders (bottom branch, runs last)
    y = 1200
    N.append(sheet_read('C1 Read sheet', [250, y]))
    N.append(code('C2 Select due reminders', [480, y], r"""
const LIMIT=20;const t=today();
const F=['email_status','whatsapp_status','messenger_status','instagram_dm_status'];
const due=$input.all().map(i=>i.json).filter(r=>r.record_id&&nd(r.reminder_due)&&nd(r.reminder_due)<=t&&!nd(r.reminder_sent_date)
  &&!['reminder','done'].includes(s(r.draft_type))&&!s(r.reminder_status).startsWith('مرفوض')&&F.some(k=>s(r[k])===SENT));
due.sort((a,b)=>nd(a.reminder_due).localeCompare(nd(b.reminder_due)));
return due.slice(0,LIMIT).map(r=>({json:r}));
"""))
    N.append(code('C3 Build reminder request', [700, y], r"""
const SYS=GUIDE+"\nالمهمة: اكتب رسالة تذكير قصيرة (جملتان إلى 4 جمل) بعد أسبوع من رسالتنا الأولى، لكل قناة مطلوبة. مهذبة بلا ضغط، تشير لرسالتنا السابقة دون تكرارها، وتنتهي بسؤال بسيط واحد. للبريد: موضوع يبدأ بـ «تذكير:» ونص لا يتجاوز 70 كلمة بلا توقيع.\nأعد JSON فقط: {\"email\":{\"subject\":\"\",\"body\":\"\"},\"whatsapp\":\"\",\"messenger\":\"\",\"instagram\":\"\"}";
return $input.all().map(i=>{const r=i.json;const chans=[];
  if(s(r.email_status)===SENT)chans.push('email');if(s(r.whatsapp_status)===SENT)chans.push('whatsapp');
  if(s(r.messenger_status)===SENT)chans.push('messenger');if(s(r.instagram_dm_status)===SENT)chans.push('instagram');
  const info={business_name:r.business_name,english_name:r.english_name,category:r.category,first_message_sent:r.first_send_date,channels_requested:chans};
  return {json:{record_id:r.record_id,row:r,chans,body:{model:MODEL,max_tokens:3000,system:SYS,messages:[{role:'user',content:'اكتب رسائل التذكير لهذه الجهة وأعد JSON فقط:\n'+JSON.stringify(info)}]}}};});
""".replace('GUIDE', json.dumps(WRITER_GUIDE, ensure_ascii=False))))
    N.append(claude_call('C4 Claude reminders', [920, y]))
    N.append(code('C5 Parse reminders + set 6h deadline', [1140, y], r"""
const src=$('C3 Build reminder request').all();const t=today();const dl=deadlineIso();
const SIG='\n\nفريق ريا كاندلز\nReya Candles & Soaps\n📱 +962 77 913 2655\n📘 https://www.facebook.com/Reyacandles\n📸 https://www.instagram.com/reya_candles/';
const out=[];
$input.all().forEach((it,idx)=>{const ctx=src[idx].json;const r=ctx.row;const ch=ctx.chans;
  let d;try{d=parseJson(claudeText(it.json));}catch(e){return;}
  const u={record_id:r.record_id,draft_type:'reminder',draft_email_subject:'',draft_email_body:'',draft_whatsapp:'',draft_messenger:'',draft_instagram:'',
    reminder_status:nd(r.reminder_due)===t?'مستحق اليوم':'متأخر',approval_deadline:dl};
  if(ch.includes('email')&&d.email&&s(d.email.body)){u.draft_email_subject=s(d.email.subject);u.draft_email_body=s(d.email.body)+SIG;}
  if(ch.includes('whatsapp')&&s(d.whatsapp))u.draft_whatsapp=s(d.whatsapp);
  if(ch.includes('messenger')&&s(d.messenger))u.draft_messenger=s(d.messenger);
  if(ch.includes('instagram')&&s(d.instagram))u.draft_instagram=s(d.instagram);
  if(u.draft_email_body||u.draft_whatsapp||u.draft_messenger||u.draft_instagram)out.push({json:u});});
return out;
"""))
    N.append(sheet_upsert('C6 Save reminders to sheet', [1360, y]))
    N.append(code('C7 Build reminder cards', [1580, y], BUILD_MSG + r"""
const rows={};for(const x of $('C3 Build reminder request').all())rows[x.json.record_id]=x.json.row;
return $('C5 Parse reminders + set 6h deadline').all().flatMap(p=>{const m=buildMsg({...rows[p.json.record_id],...p.json},'reminder');return APPROVERS.map(id=>({json:{chat_id:id,...m}}));});
""", executeOnce=True))
    N.append(tg_approval('C8 Telegram reminder approval', [1800, y]))
    chain(C, 'C1 Read sheet', 'C2 Select due reminders', 'C3 Build reminder request', 'C4 Claude reminders',
          'C5 Parse reminders + set 6h deadline', 'C6 Save reminders to sheet', 'C7 Build reminder cards', 'C8 Telegram reminder approval')

    # triggers fan out; v1 execution order runs branches top → bottom (A, then B, then C)
    for t in ('08:00 Sat–Thu', '▶ Start the day (manual)'):
        for n in ('A1 Read sheet', 'B1 Read sheet', 'C1 Read sheet'):
            link(C, t, n)
    save('Reya_Office_1_Daily_Run.json', 'Reya Office – 1 Daily Run (research → drafts → reminders)', N, C)

# ================================================================ 2. APPROVALS + 6h EXPIRY
def approvals():
    N, C = [], {}
    N.append(node('Telegram button pressed', 'n8n-nodes-base.telegramTrigger', 1.1, [0, 0],
                  {'updates': ['callback_query'], 'additionalFields': {}}, credentials=CRED_TG,
                  webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, 'reya/wh/trigger'))))
    N.append(code('Parse tap', [220, 0], r"""
const cq=$input.first().json.callback_query;
if(!cq)return [];
const [act,record_id]=String(cq.data||'').split('|');
return [{json:{act,record_id,from_id:cq.from.id,who:cq.from.first_name||cq.from.username||String(cq.from.id),callback_query_id:cq.id}}];
"""))
    N.append(node('Read row', 'n8n-nodes-base.googleSheets', 4.5, [440, 0], {
        'documentId': {'__rl': True, 'value': SHEET_ID, 'mode': 'id', 'cachedResultName': 'Reya_B2B_Master_Sheet'},
        'sheetName': {'__rl': True, 'value': 'Sheet1', 'mode': 'name'},
        'filtersUI': {'values': [{'lookupColumn': 'record_id', 'lookupValue': '={{ $json.record_id }}'}]}, 'options': {}},
        credentials=CRED_SHEETS, alwaysOutputData=True))
    N.append(code('Decide', [660, 0], r"""
const p=$('Parse tap').first().json;
const row=($input.all()[0]||{json:{}}).json;
const out={callback_query_id:p.callback_query_id,send_email:false,has_update:false,reply:'',update:{record_id:row.record_id||p.record_id}};
const fin=text=>{out.reply=text.slice(0,190);return [{json:out}];};
if(!APPROVERS.includes(p.from_id))return fin('Not authorised to use this bot.');
if(p.act==='n')return fin('This channel is not available for this business.');
if(!row.record_id)return fin('Record not found: '+p.record_id);
const t=today();
const type=s(row.draft_type)||'first';
if(!['first','reminder'].includes(type))return fin('⛔ No open approval for this business ('+type+').');
if(s(row.approval_deadline)&&Date.now()>new Date(row.approval_deadline).getTime())
  return fin('⏰ Approval window ('+APPROVAL_HOURS+'h) closed — automatically DENIED. Nothing was sent.');
const note=(old,add)=>[s(old),add].filter(Boolean).join(' | ');
const CH={e:['email_status','Email'],w:['whatsapp_status','WhatsApp'],m:['messenger_status','Messenger'],i:['instagram_dm_status','Instagram']};
const chs=['email_status','whatsapp_status','messenger_status','instagram_dm_status'];
const availN=[row.email,row.whatsapp_number,row.facebook,row.instagram].filter(avail).length;
const U=out.update;
const prepEmail=()=>{const em=s(row.email);
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)||!s(row.draft_email_body))return false;
  out.send_email=true;out.email_to=em;out.email_subject=s(row.draft_email_subject);out.email_body=s(row.draft_email_body);return true;};
if(type==='first'){
  if(p.act==='s'){
    if(chs.some(k=>s(row[k])===SENT))return fin('Already partly sent — cannot skip.');
    chs.forEach(k=>{if(s(row[k])===READY)U[k]='مرفوض';});
    U.draft_type='skipped';U.overall_status='مرفوض';U.approval_deadline='';U.writer_notes=note(row.writer_notes,`Skipped by ${p.who} ${t}`);
    out.has_update=true;return fin('❌ Skipped (denied).');
  }
  const c=CH[p.act];if(!c)return fin('Unknown action.');
  const [f,label]=c;
  if(s(row[f])===SENT)return fin(`${label} was already sent to this business.`);
  if(![READY,'فشل الإرسال'].includes(s(row[f])))return fin(`${label} is not waiting for approval.`);
  if(p.act==='e'&&!prepEmail())return fin('Email address or draft is invalid.');
  const first=nd(row.first_send_date)||t;
  const sentN=chs.filter(k=>k===f||s(row[k])===SENT).length;
  U[f]=SENT;U.first_send_date=first;U.channels_sent=sentN;U.channels_available=availN;
  const stillReady=chs.some(k=>k!==f&&s(row[k])===READY);
  U.overall_status=stillReady?'جزئية':'اكتملت';
  if(!stillReady)U.approval_deadline='';
  U.reminder_due=addDays(first,7);U.reminder_status=s(row.reminder_status)||'لم يحن بعد';
  U.writer_notes=note(row.writer_notes,`${label} sent by ${p.who} ${t}`);
  out.has_update=true;
  return fin(p.act==='e'?`✅ Sending email to ${s(row.email)}…`:`✅ ${label} recorded as sent.`);
}
// reminder
const rn=s(row.reminder_notes);
if(p.act==='d'){U.reminder_sent_date=t;U.reminder_status='تم التذكير';U.draft_type='done';U.approval_deadline='';U.reminder_notes=note(rn,`Done by ${p.who} ${t}`);out.has_update=true;return fin('✅ Reminder marked as done.');}
const c=CH[p.act];if(!c)return fin('Unknown action.');
const label=c[1];
if(rn.includes(`${label} reminder sent`))return fin(`${label} reminder was already sent.`);
if(p.act==='e'&&!prepEmail())return fin('Email address or draft is invalid.');
U.reminder_notes=note(rn,`${label} reminder sent by ${p.who} ${t}`);out.has_update=true;
return fin(p.act==='e'?'✅ Sending reminder email… tap “Reminder done” when all channels are done.':'✅ Recorded. Tap “Reminder done” when all channels are done.');
"""))
    N.append(if_node('Send email?', [880, 0], '={{ $json.send_email }}'))
    N.append(node('Send Gmail', 'n8n-nodes-base.gmail', 2.1, [1100, -140], {
        'sendTo': '={{ $json.email_to }}', 'subject': '={{ $json.email_subject }}', 'emailType': 'text',
        'message': '={{ $json.email_body }}', 'options': {'appendAttribution': False, 'senderName': 'Reya Candles & Soaps'}},
        credentials=CRED_GMAIL, webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, 'reya/wh/gmail')), onError='continueErrorOutput'))
    N.append(if_node('Has update?', [1100, 120], '={{ $json.has_update }}'))
    N.append(code('Update payload', [1320, 0], "return [{json:$('Decide').first().json.update}];"))
    N.append(sheet_upsert('Update sheet', [1540, 0]))
    cb = lambda name, pos, text: node(name, 'n8n-nodes-base.telegram', 1.2, pos, {
        'resource': 'callback', 'queryId': "={{ $('Decide').first().json.callback_query_id }}",
        'additionalFields': {'text': text, 'show_alert': True}}, credentials=CRED_TG,
        webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, 'reya/wh/' + name)), onError='continueRegularOutput')
    N.append(cb('Answer tap', [1760, 60], "={{ $('Decide').first().json.reply }}"))
    N.append(cb('Answer email failed', [1320, -260], 'Email FAILED to send — sheet not changed. Try again.'))
    chain(C, 'Telegram button pressed', 'Parse tap', 'Read row', 'Decide', 'Send email?')
    link(C, 'Send email?', 'Send Gmail', 0)
    link(C, 'Send email?', 'Has update?', 1)
    link(C, 'Send Gmail', 'Update payload', 0)
    link(C, 'Send Gmail', 'Answer email failed', 1)
    link(C, 'Has update?', 'Update payload', 0)
    link(C, 'Has update?', 'Answer tap', 1)
    chain(C, 'Update payload', 'Update sheet', 'Answer tap')

    # ---- hourly sweep: anything not approved within 6h is denied by default
    y = 500
    N.append(node('Every 30 min', 'n8n-nodes-base.scheduleTrigger', 1.2, [0, y],
                  {'rule': {'interval': [{'field': 'minutes', 'minutesInterval': 30}]}}))
    N.append(sheet_read('Read sheet (expiry)', [220, y]))
    N.append(code('Expire unapproved', [440, y], r"""
const now=Date.now();const t=today();const out=[];
const chs=['email_status','whatsapp_status','messenger_status','instagram_dm_status'];
for(const i of $input.all()){const r=i.json;
  if(!r.record_id||!s(r.approval_deadline))continue;
  if(now<=new Date(r.approval_deadline).getTime())continue;
  const u={record_id:r.record_id,approval_deadline:'',_name:s(r.english_name)&&avail(r.english_name)?s(r.english_name):s(r.business_name)};
  if(s(r.draft_type)==='reminder'){
    const some=s(r.reminder_notes).includes('reminder sent');
    u.draft_type='done';u.reminder_status=some?'تم التذكير (جزئي)':DENIED;
    if(some)u.reminder_sent_date=t;
    u.reminder_notes=[s(r.reminder_notes),`Auto-denied after ${APPROVAL_HOURS}h ${t}`].filter(Boolean).join(' | ');u._kind='reminder';
  }else{
    chs.forEach(k=>{if(s(r[k])===READY)u[k]=DENIED;});
    const anySent=chs.some(k=>s(r[k])===SENT);
    u.overall_status=anySent?'جزئية':DENIED;if(!anySent)u.draft_type='expired';
    u.writer_notes=[s(r.writer_notes),`Unapproved channels auto-denied after ${APPROVAL_HOURS}h ${t}`].filter(Boolean).join(' | ');u._kind='first';
  }
  out.push({json:u});}
return out;
"""))
    N.append(code('Strip names', [660, y], "return $input.all().map(i=>{const j={...i.json};delete j._name;delete j._kind;return {json:j};});"))
    N.append(sheet_upsert('Save denials', [880, y]))
    N.append(code('Denial notice', [1100, y], r"""
const L=$('Expire unapproved').all().map(i=>`• ${i.json._name} (${i.json.record_id}) — ${i.json._kind==='reminder'?'reminder':'first message'}`);
if(!L.length)return [];
const text=`⏰ Not approved within ${APPROVAL_HOURS}h — automatically DENIED (nothing sent):\n`+L.join('\n');
return APPROVERS.map(id=>({json:{chat_id:id,text}}));
""", executeOnce=True))
    N.append(tg_text('Telegram denial notice', [1320, y]))
    chain(C, 'Every 30 min', 'Read sheet (expiry)', 'Expire unapproved', 'Strip names', 'Save denials', 'Denial notice', 'Telegram denial notice')
    save('Reya_Office_2_Telegram_Approvals.json', 'Reya Office – 2 Telegram approvals + 6h auto-deny', N, C)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    daily_run()
    approvals()
    print('written to', OUT)
