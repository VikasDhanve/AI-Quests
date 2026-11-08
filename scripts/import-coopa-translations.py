from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
import json,hashlib,re,html,collections
from importlib.util import spec_from_file_location,module_from_spec
ROOT=Path(__file__).resolve().parents[1];REV='9ea4b867ce4857779d3cf84bfb423d12c7136049'
REF=ROOT/'localization/reference/coopa-study';REF.mkdir(parents=True,exist_ok=True)
FILES=['LICENSE','README.md','content-source/SNAPSHOT.txt']+[prefix+name for prefix in ['content-source/en_us/','public/content-zh/en_us/'] for name in ['sitewide.json','planet_page.json','home_page.json','flood_prediction.json','blindness_prevention.json']]
def download(p):
 u='https://raw.githubusercontent.com/notwin/coopa-study/'+REV+'/'+p
 with urlopen(u,timeout=40) as r:b=r.read()
 if p.endswith('.json'):json.loads(b)
 target=REF/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
 return {'path':p,'url':u,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
with ThreadPoolExecutor(max_workers=6) as pool:records=list(pool.map(download,FILES))
(REF/'provenance.json').write_text(json.dumps({'repository':'https://github.com/notwin/coopa-study','revision':REV,'files':records},indent=2),'utf-8')
spec=spec_from_file_location('extract',ROOT/'scripts/extract-localization.py');mod=module_from_spec(spec);spec.loader.exec_module(mod)
current=ROOT/'public/ai-quests/content/api/snapshot/20261023-141713/en_us'
accepted={};changes=[];invalid=[];pairs=collections.defaultdict(list)
def at(v,p):
 for x in p.strip('/').split('/'):
  v=v[int(x)] if isinstance(v,list) else v[x]
 return v
def marks(s):return re.findall(r'\{\{.*?\}\}|(?<!\{)\{[A-Za-z_][\w ]*\}(?!\})',s)
def times(s):return re.findall(r'\d\d:\d\d:\d\d\.\d+\s+-->\s+\d\d:\d\d:\d\d\.\d+[^\n]*',html.unescape(s))
for name in ['sitewide.json','planet_page.json','home_page.json','flood_prediction.json','blindness_prevention.json']:
 en=json.loads((REF/'content-source/en_us'/name).read_text('utf-8'));zh=json.loads((REF/'public/content-zh/en_us'/name).read_text('utf-8'));local=json.loads((current/name).read_text('utf-8'));out={}
 for p,v in mod.walk(local):
  if not mod.translatable(p,v):continue
  try:old=at(en,p);translated=at(zh,p)
  except (KeyError,IndexError,ValueError):changes.append({'file':name,'path':p,'reason':'new field','source':v});continue
  if not isinstance(translated,str) or mod.norm(old)!=mod.norm(v):changes.append({'file':name,'path':p,'reason':'source changed','source':v});continue
  if sorted(marks(v))!=sorted(marks(translated)) or (v.startswith('WEBVTT') and times(v)!=times(translated)):
   invalid.append({'file':name,'path':p,'source':v,'translation':translated});continue
  out[p]=translated
  if not v.startswith('WEBVTT'):pairs[mod.norm(v)].append(translated)
 accepted[name]=out
(ROOT/'localization/zh_cn/reference-overrides.json').write_text(json.dumps(accepted,ensure_ascii=False,indent=2),'utf-8')
p=ROOT/'localization/zh_cn/translations.json';mapping=json.loads(p.read_text('utf-8')) if p.exists() else {};catalog=json.loads((ROOT/'localization/zh_cn/catalog.en.json').read_text('utf-8'))
for e in catalog:
 if e['source'] in pairs:mapping[e['id']]=collections.Counter(pairs[e['source']]).most_common(1)[0][0]
p.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n','utf-8')
report={'revision':REV,'accepted_by_file':{k:len(v) for k,v in accepted.items()},'changed_fields':changes,'rejected_placeholder_or_timing_changes':invalid,'catalog_translations':len(mapping)}
(ROOT/'reports/coopa-reference-import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'accepted_by_file':report['accepted_by_file'],'changed_fields':len(changes),'rejected':len(invalid),'catalog_translations':len(mapping)},ensure_ascii=True))
for text in ['AI Quests','Market Marshes','Dusky Dunes','Professor Skye','Luna','Training','Testing']:
 print(text,json.dumps(pairs.get(text,[])[:4],ensure_ascii=False))
covered=[];missing=[]
for e in catalog:
 contexts=e['contexts'];covered_contexts=[c for c in contexts if c.split('/',1)[0] in accepted and ('/'+c.split('/',1)[1].replace('[subtitle]','')) in accepted[c.split('/',1)[0]]]
 if e['id'] not in mapping and len(covered_contexts)<len(contexts):missing.append(e)
(ROOT/'reports/zh-missing-translations.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2),'utf-8')
print('REMAINING_CATALOG_ENTRIES',len(missing))
for e in missing[:80]:print(e['id']+'\t'+e['source'])