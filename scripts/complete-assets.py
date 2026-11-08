import mirror as m
from pathlib import Path
import json,re,hashlib
from urllib.parse import quote
root=m.ROOT
extras=[]
base=m.BASE
paths=['assets/graphics/dunes/privacy/patient/record-%02d.webp'%i for i in range(1,6)]
paths += ['assets/ui/inventory-bar-%d.svg'%i for i in range(1,6)]
snapshot='20261023-141713'
def keys(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if k in ('capillary','neuron','astrocytes') and isinstance(x,str):yield x
   elif isinstance(x,(dict,list)):yield from keys(x)
 elif isinstance(v,list):
  for x in v:yield from keys(x)
for p in (root/'upstream-text/ai-quests/content/api/snapshot'/snapshot).glob('*/mapping_brain.json'):
 for x in keys(json.loads(p.read_text('utf-8'))):
  if '<' not in x and len(x)<60:paths.append('assets/mock/lab/04/note/'+x.lower()+'.png')
for p in sorted(set(paths)):
 u=base+quote(p,safe='/')
 try:
  u,b,ct,_=m.download(u);target=m.local_path(u);m.records[u]={'status':'ok','path':target.relative_to(m.PUBLIC).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'content_type':ct};print('OK',p,flush=True)
 except Exception as e:m.records[u]={'status':'error','error':str(e)};print('ERROR',p,str(e),flush=True)
# Save publicly exportable teacher handouts; retain original links as provenance.
s=(root/'upstream-text/ai-quests/intl/en_us/teacher-resources/index.html').read_text('utf-8')
links=sorted(set(re.findall(r'https://docs.google.com/document/d/[^"<>\s]+',s)))
for link in links:
 id=re.search(r'/d/([^/]+)',link)[1];u='https://docs.google.com/document/d/'+id+'/export?format=pdf'
 try:
  b,ct=m.fetch(u)
  if not b.startswith(b'%PDF'):raise ValueError('Public PDF export was not returned')
  p='ai-quests/assets/teacher-resources/'+id+'.pdf';out=m.PUBLIC/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
  m.records[u]={'status':'ok','path':p,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'content_type':'application/pdf'}
  extras.append({'original_link':link,'export_url':u,'local':'/'+p,'status':'ok'});print('PDF',id,len(b),flush=True)
 except Exception as e:extras.append({'original_link':link,'export_url':u,'status':'unavailable','error':str(e)});print('PDF unavailable',id,str(e),flush=True)
(root/'reports/teacher-resources.json').write_text(json.dumps(extras,indent=2),'utf-8');m.flush()