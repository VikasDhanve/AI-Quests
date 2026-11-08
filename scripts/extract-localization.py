from pathlib import Path
from html.parser import HTMLParser
import hashlib,html,json,re
ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT='20261023-141713'
EN=ROOT/'public/ai-quests/content/api/snapshot'/SNAPSHOT/'en_us'
ORDER=['sitewide.json','planet_page.json','home_page.json','not_found_page.json','flood_prediction.json','blindness_prevention.json','mapping_brain.json']
PROTECTED={'collection_id','document_id','id','url','uri','src','file_name','type','record_id','validity','patient_number','eye_color','diagnosis_severity','diagnosis_type','risk','mode','theme','color','iconId','icon_id','token_id'}
LANGUAGES={'English (US)','English (UK)','Bahasa Melayu','Español (ES)','Español (419)','Français','Italiano','Português (PT)','Português (BR)','Türkçe','עברית','العربية'}
def norm(s):return re.sub(r'\s+',' ',html.unescape(s)).strip()
def translatable(p,v):
 if not v or not re.search(r'[A-Za-z]',v):return False
 key=p.rsplit('/',1)[-1]
 if key in PROTECTED or '/key_concept_tags/' in p:return False
 if key in {'habitat','uv_rating','region','gender'} and re.fullmatch('[a-z_-]+',v):return False
 if re.match(r'^(?:https?://|data:|blob:|/ai-quests/|assets/)',v) or re.search(r'\.(?:webm|mp4|png|webp|svg|jpg|glb|js|css|woff2?)(?:[?#].*)?$',v):return False
 if not re.search('[A-Za-z]',re.sub(r'\{\{.*?\}\}','',v)):return False
 return True
catalog=[];by_source={}
def add(s,context):
 s=norm(s)
 if not s or not re.search('[A-Za-z]',s) or s in LANGUAGES:return
 if s not in by_source:
  entry={'id':f't{len(catalog)+1:04d}','source':s,'contexts':[]};catalog.append(entry);by_source[s]=entry
 by_source[s]['contexts'].append(context)
def walk(v,p=''):
 if isinstance(v,dict):
  for k,x in v.items():yield from walk(x,p+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from walk(x,p+'/'+str(i))
 elif isinstance(v,str):yield p,v
for name in ORDER:
 for p,v in walk(json.loads((EN/name).read_text('utf-8'))):
  if not translatable(p,v):continue
  if v.startswith('WEBVTT'):
   for line in html.unescape(v).splitlines():
    if line.strip() and line.strip()!='WEBVTT' and not re.match(r'^\d\d:\d\d:',line):add(line,name+p+'[subtitle]')
  else:add(v,name+p)
class TextCatalog(HTMLParser):
 def __init__(self,name):super().__init__(convert_charrefs=True);self.name=name;self.stack=[]
 def handle_starttag(self,tag,attrs):
  if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(tag)
  if not any(x in self.stack for x in ('svg','script','style')):
   for k,v in attrs:
    if k in {'aria-label','title','placeholder','alt'} and v and not re.fullmatch('[a-z0-9_-]+',v) and v not in LANGUAGES:add(v,'page:'+self.name+'@'+k)
 def handle_endtag(self,tag):
  if tag in self.stack:self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
 def handle_data(self,data):
  if any(x in self.stack for x in ('script','style','svg','noscript')):return
  s=norm(data)
  if not s or s in LANGUAGES or re.match('https?://',s) or '@' in s:return
  add(s,'page:'+self.name)
for name in ['about','faq','teacher-resources','privacy-notice','videos']:
 TextCatalog(name).feed((ROOT/'public/ai-quests/intl/en_us'/name/'index.html').read_text('utf-8'))
for s in ['This experience is designed to be heard','We recommend turning your sound on. You can easily mute it at any time once you begin.','Video Transmission','Transmission','Return to game','Objective','Task','Review','Next','Previous','Correct','Incorrect','Privacy','Healthy','Early signs','Moderate','Severe']:
 add(s,'compiled UI fallback')
path=ROOT/'localization/zh_cn/catalog.en.json';path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'catalog_entries':len(catalog),'words':sum(len(x['source'].split()) for x in catalog)},ensure_ascii=True))