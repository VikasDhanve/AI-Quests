from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import hashlib,json,re,concurrent.futures
ROOT=Path(__file__).resolve().parents[1];PUBLIC=ROOT/'public';BASE='http://127.0.0.1:4192'
m=json.loads((ROOT/'reports/manifest.json').read_text('utf-8'));mods={r['path']:r for r in json.loads((ROOT/'reports/local-modifications.json').read_text('utf-8'))}
fail=[];total=0;count=0
for url,r in m.items():
 if r['status']!='ok':continue
 p=PUBLIC/r['path'];count+=1;total+=r['bytes']
 if not p.is_file():fail.append({'file':r['path'],'error':'missing'});continue
 original=ROOT/'upstream-text'/r['path'];b=original.read_bytes() if original.exists() else p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=r['sha256']:fail.append({'file':r['path'],'error':'upstream hash mismatch'})
 if r['path'] in mods and hashlib.sha256(p.read_bytes()).hexdigest()!=mods[r['path']]['local_sha256']:fail.append({'file':r['path'],'error':'local build hash mismatch'})
# Assert all media referenced by the requested English snapshot has been captured.
missing=[];refs=[];placeholders=[]
def walk(v,where):
 if isinstance(v,dict):
  for k,x in v.items():
   if k in ('url','src','uri') and x=='tbd':
    placeholders.append({'source':where,'value':x,'reason':'Official CMS placeholder; training renderer uses its bundled neuron-right/neuron-wrong media instead'})
   elif k in ('url','src','uri') and isinstance(x,str) and x and (not x.startswith('http') or 'googleusercontent.com/' in x):
    if x.startswith('/ai-quests/'):u='https://research.google'+x
    elif x.startswith('http'):u=x
    else:u='https://research.google/ai-quests/assets/bucket/'+x.lstrip('/')
    refs.append((where,u))
    if m.get(u,{}).get('status')!='ok':missing.append({'source':where,'url':u})
   elif isinstance(x,(dict,list)):walk(x,where)
 elif isinstance(v,list):
  for x in v:walk(x,where)
for p in (ROOT/'upstream-text/ai-quests/content/api/snapshot/20261023-141713/en_us').glob('*.json'):walk(json.loads(p.read_text('utf-8')),p.name)
checks=[]
def request(p,method='GET',headers=None):
 try:
  with urlopen(Request(BASE+p,method=method,headers=headers or {}),timeout=20) as r:return r.status,r.headers,r.read() if method!='HEAD' else b''
 except HTTPError as r:return r.code,r.headers,r.read()
for p in ['/reports/manifest.json','/scripts/server.mjs','/upstream-text/','/%2e%2e/README.md','/ai-quests/%5c..%5cREADME.md']:
 code,_,b=request(p);checks.append({'path':p,'status':code,'pass':code in (400,403,404)})
code,h,_=request('/ai-quests/intl/en_us',method='POST');checks.append({'check':'write methods rejected','pass':code==405,'status':code})
media=[r for r in m.values() if r['status']=='ok' and r['path'].endswith(('.webm','.mp4'))]
def check_media(r):
 code,h,b=request('/'+r['path'],headers={'Range':'bytes=0-127'})
 return {'path':r['path'],'pass':code==206 and len(b)==128 and h.get('Content-Range')==f"bytes 0-127/{r['bytes']}"}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:media_checks=list(pool.map(check_media,media))
code,h,_=request('/'+media[0]['path'],headers={'Range':'bytes=999999999999-'})
checks.append({'check':'invalid range rejected','status':code,'pass':code==416})
code,h,_=request('/ai-quests/intl/en_us',method='HEAD');checks.append({'check':'security headers','pass':h.get('X-Content-Type-Options')=='nosniff' and "object-src 'none'" in h.get('Content-Security-Policy','') and h.get('X-Frame-Options')=='SAMEORIGIN'})
report={'snapshot':'20261023-141713','verified_files':count,'upstream_bytes':total,'hash_failures':fail,'official_cms_placeholders':placeholders,'english_media_references':len(refs),'english_missing_media':missing,'media_range_checks':len(media_checks),'failed_media_ranges':[x for x in media_checks if not x['pass']],'http_security_checks':checks,'upstream_failed_candidates':[{'url':u,**r} for u,r in m.items() if r['status']!='ok']}
(ROOT/'reports/integrity-security.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('upstream_failed_candidates','official_cms_placeholders')},ensure_ascii=True))
assert not fail and not missing and all(x['pass'] for x in checks) and all(x['pass'] for x in media_checks)