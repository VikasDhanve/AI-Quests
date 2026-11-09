from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import hashlib,html,json,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];APP=ROOT/'public/ai-quests';LOC=ROOT/'localization/zh_cn';SNAPSHOT='20261023-141713';API=APP/'content/api/snapshot'/SNAPSHOT
catalog=json.loads((LOC/'catalog.en.json').read_text('utf-8'));by_source={e['source']:e for e in catalog}
targets=json.loads((LOC/'translations.json').read_text('utf-8'));overrides=json.loads((LOC/'reference-overrides.json').read_text('utf-8'));terms=json.loads((LOC/'inline-terms.json').read_text('utf-8'))
RESERVED={'count','total','number','google_logo','partner_logo'}
PROTECTED={'collection_id','document_id','id','url','uri','src','file_name','type','record_id','validity','patient_number','eye_color','diagnosis_severity','diagnosis_type','risk','mode','theme','color','iconId','icon_id','token_id'}
def norm(s):return re.sub(r'\s+',' ',html.unescape(s)).strip()
def can_translate(p,v):
 if not v or not re.search('[A-Za-z]',v):return False
 k=p.rsplit('/',1)[-1]
 if k in PROTECTED or '/key_concept_tags/' in p:return False
 if k in {'habitat','uv_rating','region','gender'} and re.fullmatch('[a-z_-]+',v):return False
 if re.match(r'^(?:https?://|data:|blob:|/ai-quests/|assets/)',v) or re.search(r'\.(?:webm|mp4|png|webp|svg|jpg|glb|js|css|woff2?)(?:[?#].*)?$',v):return False
 return bool(re.search('[A-Za-z]',re.sub(r'\{\{.*?\}\}','',v)))
def inline(s):
 def replace(m):
  k=m[1].strip()
  return m[0] if k in RESERVED else '{{ '+terms.get(k,k)+' }}'
 return re.sub(r'\{\{(.*?)\}\}',replace,s).replace('AI Quests · 中文伴读','AI Quests · 简体中文')
class SafeText(HTMLParser):
 def handle_starttag(self,tag,attrs):
  if tag not in {'b','strong','em','i','u','s','br','p','span','ul','ol','li','a','sup','sub'}:raise ValueError('Unexpected translated HTML tag: '+tag)
  for k,v in attrs:
   if k.lower().startswith('on') or k.lower() in {'srcdoc','style'}:raise ValueError('Unsafe translated attribute')
   if k in {'href','src'} and not (v or '').startswith(('https://','http://','/','#')):raise ValueError('Unsafe translated URL')
def translate(s,where):
 e=by_source.get(norm(s));t=targets.get(e['id']) if e else None
 if t is None:raise ValueError('Missing translation: '+where+' '+s[:90])
 return inline(t)
def cue_lines(s):return [line.strip() for line in html.unescape(s).splitlines() if re.match(r'^(?:\d\d:)?\d\d:\d\d\.\d+\s+-->',line.strip())]
def subtitle(s,where):
 out=[]
 for line in s.splitlines():
  u=html.unescape(line).strip()
  if u=='```':continue
  if not u or u=='WEBVTT' or re.match(r'^(?:\d\d:)?\d\d:\d\d\.\d+\s+-->',u) or u.isdigit():out.append(line)
  else:out.append(translate(line,where))
 return '\n'.join(out)
translated_leaves=0;preserved_leaves=0;tracks=0

def convert(v,p='',name=''):
 global translated_leaves,preserved_leaves,tracks
 if isinstance(v,dict):return {k:convert(x,p+'/'+k,name) for k,x in v.items()}
 if isinstance(v,list):return [convert(x,p+'/'+str(i),name) for i,x in enumerate(v)]
 if not isinstance(v,str) or not can_translate(p,v):preserved_leaves+=1;return v
 t=overrides.get(name,{}).get(p)
 if t is None:t=subtitle(v,name+p) if v.startswith('WEBVTT') else translate(v,name+p)
 t=inline(t)
 source_vars=Counter(x.strip() for x in re.findall(r'\{\{(.*?)\}\}',v) if x.strip() in RESERVED)
 target_vars=Counter(x.strip() for x in re.findall(r'\{\{(.*?)\}\}',t) if x.strip() in RESERVED)
 if source_vars!=target_vars:raise ValueError('Template variables changed: '+name+p)
 if v.startswith('WEBVTT'):
  if cue_lines(v)!=cue_lines(t):raise ValueError('Subtitle timing changed: '+name+p)
  tracks+=1
 else:SafeText(convert_charrefs=True).feed(html.unescape(t))
 translated_leaves+=1
 return t

(API/'zh_cn').mkdir(parents=True,exist_ok=True)
for name in ['sitewide.json','planet_page.json','home_page.json','not_found_page.json','flood_prediction.json','blindness_prevention.json','mapping_brain.json']:
 original=json.loads((API/'en_us'/name).read_text('utf-8'));translated=convert(original,name=name)
 if name=='sitewide.json':translated['seo']['title']='AI Quests · 简体中文'
 (API/'zh_cn'/name).write_text(json.dumps(translated,ensure_ascii=False,indent=2)+'\n','utf-8')
config_path=API/'site_config.json';config=json.loads(config_path.read_text('utf-8'))
config['locales']=[x for x in config['locales'] if x['site_locale']!='zh_cn']
zh=dict(next(x for x in config['locales'] if x['site_locale']=='en_us'))
zh.update(text='简体中文',site_locale='zh_cn',kintaro_locale='zh_cn',html_lang='zh-CN',country_codes='CN,CHN',sitemap_hreflangs='zh-CN',lang_dir_rtl=False,enabled=True,enabled_quests=['quest-flood','quest-blindness','quest-brain'],additional_resources_enabled=True)
config['locales'].append(zh);config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n','utf-8')

def add_option(s,page,selected=False):
 def replace(m):
  body=re.sub(r'<option\b[^>]*value="/ai-quests/intl/zh_cn[^>]*>.*?</option>','',m[0],flags=re.S)
  if selected:body=re.sub(r'\sselected(?:="[^"]*")?','',body)
  option='<option value="/ai-quests/intl/zh_cn/'+page+'"'+(' selected' if selected else '')+'>简体中文</option>'
  return body.replace('</select>',option+'</select>')
 return re.sub(r'<select\b[^>]*id="lang-selector"[^>]*>.*?</select>',replace,s,flags=re.S)

# Translate static documents at build time; no extension, interception or DOM replacement.
LANGUAGES={'English (US)','English (UK)','Bahasa Melayu','Español (ES)','Español (419)','Français','Italiano','Português (PT)','Português (BR)','Türkçe','עברית','العربية'}
class ChinesePage(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.attrs=[];self.out=[]
 def handle_starttag(self,tag,attrs):
  raw=self.get_starttag_text();attr=dict(attrs);in_select=any(x=='option' or x=='select' for x in self.stack)
  if tag=='html':raw=re.sub(r'lang="[^"]*"','lang="zh-CN"',raw);raw=re.sub(r'dir="[^"]*"','dir="ltr"',raw)
  for k,v in attrs:
   if not v:continue
   nv=v
   if k in {'href','value'} and tag!='option' and not in_select:nv=nv.replace('/ai-quests/intl/en_us','/ai-quests/intl/zh_cn')
   if k in {'aria-label','title','placeholder','alt'} and norm(v) in by_source and norm(v) not in LANGUAGES:nv=translate(v,'static attribute')
   if nv!=v:
    raw=re.sub(r'(\b'+re.escape(k)+r'\s*=\s*)(["\x27])(.*?)\2',lambda m:m[1]+m[2]+html.escape(nv,quote=True)+m[2],raw,flags=re.I|re.S)
  self.out.append(raw)
  if tag not in self.VOID:self.stack.append(tag);self.attrs.append(attr)
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in self.VOID:self.handle_endtag(tag,False)
 def handle_endtag(self,tag,emit=True):
  if emit:self.out.append('</'+tag+'>')
  if tag in self.stack:
   n=len(self.stack)-1-self.stack[::-1].index(tag);self.stack=self.stack[:n];self.attrs=self.attrs[:n]
 def handle_data(self,s):
  if any(x in self.stack for x in ('script','style','svg')):self.out.append(s);return
  n=norm(s)
  if not n or n in LANGUAGES or n=='简体中文' or '@' in n or re.match('https?://',n) or not re.search('[A-Za-z]',n):self.out.append(html.escape(s,quote=False));return
  t=translate(n,'static page')
  if n=='Google Drive' and any(a.get('href','').endswith('.pdf') for a in self.attrs):t='英文 PDF'
  self.out.append(html.escape(re.match(r'^\s*',s)[0]+t+re.search(r'\s*$',s)[0],quote=False))
 def handle_comment(self,s):self.out.append('<!--'+s+'-->')
 def handle_decl(self,s):self.out.append('<!'+s+'>')

html_dir=APP/'intl/zh_cn';html_dir.mkdir(parents=True,exist_ok=True)
shutil.copytree(ROOT/'local-features/sponsor',APP/'local-support',dirs_exist_ok=True)
subprocess.run([sys.executable,str(ROOT/'scripts/build-teacher-pdfs.py')],cwd=ROOT,check=True)
teacher_pdfs=json.loads((ROOT/'reports/teacher-resources-zh.json').read_text('utf-8'))
teacher_pdf_map={f'/ai-quests/assets/teacher-resources/{r["source_id"]}.pdf':r for r in teacher_pdfs}
def teacher_resources(s):
 def add_pdf(m):
  a=m[0];href=re.search(r'\bhref="([^"]+)"',a)[1];r=teacher_pdf_map[href]
  zh=a.replace('href="'+href+'"','href="'+r['local']+'"',1).replace('英文 PDF','中文 PDF')
  if zh==a:raise ValueError('Chinese PDF link not generated')
  zh=zh.replace('<a ','<a aria-label="中文 PDF：'+html.escape(r['title'],quote=True)+'" ',1)
  return a+'\n'+zh
 s,count=re.subn(r'<a\b[^>]*class="[^"]*\baiq-card__doc-btn\b[^"]*"[^>]*>.*?</a>',add_pdf,s,flags=re.S)
 if count!=5:raise ValueError('Expected five teacher PDF buttons')
 track=re.search(r'<track\b[^>]*src="data:text/vtt;base64,([^"]+)"[^>]*>',s)
 if not track:raise ValueError('Expected teacher overview caption track')
 import base64
 en_vtt=base64.b64decode(track[1]).decode('utf-8');zh_vtt=(LOC/'teacher-resources/teacher-video.zh.vtt').read_text('utf-8')
 if cue_lines(en_vtt)!=cue_lines(zh_vtt):raise ValueError('Teacher video subtitle timing changed')
 dest=APP/'assets/teacher-resources/zh_cn/teacher-overview.zh.vtt';dest.write_text(zh_vtt,'utf-8')
 replacement='<track default kind="captions" srclang="zh-CN" label="简体中文" src="/ai-quests/assets/teacher-resources/zh_cn/teacher-overview.zh.vtt">'
 return s[:track.start()]+replacement+s[track.end():]
home=(APP/'intl/en_us/index.html').read_text('utf-8');home=re.sub(r'<html lang="[^"]*"','<html lang="zh-CN"',home);home=home.replace('/intl/en_us','/intl/zh_cn');home=re.sub(r'<title>.*?</title>','<title>AI Quests · 简体中文</title>',home)
home=home.replace('</head>','<link rel="stylesheet" href="/ai-quests/zh-cn.css"><script src="/ai-quests/zh-cn-runtime.js" type="module"></script><link rel="stylesheet" href="/ai-quests/local-support/sponsor.css"><script src="/ai-quests/local-support/sponsor.js" type="module"></script></head>')
(html_dir/'index.html').write_text(home,'utf-8')
for page in ['about','faq','teacher-resources','privacy-notice','videos']:
 en=(APP/'intl/en_us'/page/'index.html').read_text('utf-8');parser=ChinesePage();parser.feed(en);out=''.join(parser.out);out=add_option(out,page,True);out=out.replace('</head>','<link rel="stylesheet" href="/ai-quests/zh-cn.css"></head>')
 if page=='teacher-resources':out=teacher_resources(out)
 target=html_dir/page/'index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(out,'utf-8')
 for lang in config['locales']:
  if lang['site_locale']=='zh_cn':continue
  p=APP/'intl'/lang['site_locale']/page/'index.html'
  if p.exists():p.write_text(add_option(p.read_text('utf-8'),page),'utf-8')

# Display names also form three legacy image filenames; keep the model's type keys stable.
for name,en in [('毛细血管','capillary'),('神经元','neuron'),('星形胶质细胞','astrocytes')]:
 src=APP/'assets/mock/lab/04/note'/(en+'.png');dst=src.with_name(name+'.png');shutil.copyfile(src,dst)
(APP/'zh-cn.css').write_text('''html[lang="zh-CN"] :is(body,button,input,textarea,select){font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif}html[lang="zh-CN"] video::cue{font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;font-size:clamp(28px,3vw,36px);line-height:1.5}html[lang="zh-CN"] .aiq-typesystem-h2{line-height:1.35}html[lang="zh-CN"] .aiq-video-card__title{overflow-wrap:anywhere}\n''','utf-8')
with (APP/'zh-cn.css').open('a',encoding='utf-8') as css:
 css.write('html[lang="zh-CN"] .aiq-teacher-resource__links{display:flex;flex-wrap:wrap;align-items:center;gap:12px}html[lang="zh-CN"] .aiq-teacher-resource__links .aiq-card__doc-btn{margin:0}\n')
(APP/'zh-cn-runtime.js').write_text('''if(/\\/intl\\/zh_cn(?:\\/|$)/.test(location.pathname)){
const show=(video)=>{for(const track of video.querySelectorAll('track')){if(!['subtitles','captions'].includes(track.kind))continue;track.srclang='zh-CN';track.label='简体中文';track.default=true;track.track.mode='showing';}};
document.addEventListener('loadedmetadata',e=>{if(e.target instanceof HTMLVideoElement)show(e.target);},true);
document.addEventListener('load',e=>{if(e.target instanceof HTMLTrackElement&&e.target.parentElement instanceof HTMLVideoElement)show(e.target.parentElement);},true);
}\n''','utf-8')
# A compact source/target map is also used for legacy UI defaults embedded in the build.
ui={}
for e in catalog:
 if e['id'] in targets:ui[e['source']]=inline(targets[e['id']])
for name,values in overrides.items():
 for p,t in values.items():
  if not t.startswith('WEBVTT'):
   original=json.loads((API/'en_us'/name).read_text('utf-8'));v=original
   for part in p.strip('/').split('/'):v=v[int(part)] if isinstance(v,list) else v[part]
   ui.setdefault(norm(v),inline(t))
ui.update({f'Scan {i}':f'扫描图 {i}' for i in range(1,4)});ui.update({f'Token {i}':f'样本 {i}' for i in range(1,4)});ui['AI Quests']='AI Quests';(LOC/'ui-map.json').write_text(json.dumps(ui,ensure_ascii=False,indent=2)+'\n','utf-8')
subprocess.run(['node',str(ROOT/'scripts/patch-zh-ui.mjs')],cwd=ROOT,check=True)
# Update local hashes, preserving the independently stored upstream hashes.
manifest=json.loads((ROOT/'reports/manifest.json').read_text('utf-8'));changes=[]
for u,r in manifest.items():
 if r['status']!='ok':continue
 p=ROOT/'public'/r['path'];h=hashlib.sha256(p.read_bytes()).hexdigest()
 if h!=r['sha256']:changes.append({'path':r['path'],'original_sha256':r['sha256'],'local_sha256':h})
(ROOT/'reports/local-modifications.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),'utf-8')
report={'locale':'zh_cn','language':'简体中文','reference_repository':'https://github.com/notwin/coopa-study','reference_revision':'9ea4b867ce4857779d3cf84bfb423d12c7136049','translated_json_leaves':translated_leaves,'preserved_data_leaves':preserved_leaves,'subtitle_tracks':tracks,'generated_files':[]}
for p in list(html_dir.rglob('*'))+list((API/'zh_cn').rglob('*'))+list((APP/'assets/teacher-resources/zh_cn').glob('*'))+list((APP/'local-support').glob('*'))+[APP/'zh-cn.css',APP/'zh-cn-runtime.js']:
 if p.is_file():report['generated_files'].append({'path':p.relative_to(ROOT/'public').as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'reports/zh-cn-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='generated_files'},ensure_ascii=True))
