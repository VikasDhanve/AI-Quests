"""Mirror public AI Quests build and its pinned CMS snapshot; no backend credentials."""
from pathlib import Path
from urllib.parse import urlsplit, urljoin, urldefrag, unquote
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip, hashlib, json, re, time, html, mimetypes
from urllib.error import HTTPError
ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
BASE = 'https://research.google/ai-quests/'
MEDIA = {'kstatic.googleusercontent.com','lh3.googleusercontent.com','fonts.gstatic.com','fonts.googleapis.com','www.gstatic.com'}
EXT = re.compile(r'\.(?:js|css|json|glb|gltf|webm|mp4|mp3|wav|ogg|svg|png|jpe?g|webp|gif|ico|woff2?|ttf|otf|vtt|srt|pdf|hdr|bin|wasm)(?:[?#].*)?$', re.I)
MANIFEST = ROOT / 'reports' / 'manifest.json'
records = json.loads(MANIFEST.read_text('utf-8')) if MANIFEST.exists() else {}
seen = set()
pending = set()
constants = {}

def fetch(url):
    for attempt in range(4):
        try:
            req = Request(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36','Accept-Encoding':'identity'})
            with urlopen(req, timeout=50) as res:
                b = res.read()
                if b[:2] == b'\x1f\x8b': b = gzip.decompress(b)
                return b, res.headers.get('Content-Type','application/octet-stream')
        except HTTPError as exc:
            if exc.code in (403,404) or attempt == 3: raise
            time.sleep(attempt + 1)
        except Exception:
            if attempt == 3: raise
            time.sleep(attempt + 1)

def canonical(url):
    u = urlsplit(html.unescape(url))
    if u.scheme not in ('https','http'): return None
    if u.hostname == 'research.google':
        if not u.path.startswith('/ai-quests/'): return None
        return 'https://research.google' + u.path
    if u.hostname in MEDIA:
        if u.hostname == 'www.gstatic.com' and not any(x in u.path for x in ('/glue/','/images/branding/')): return None
        return urldefrag(html.unescape(url))[0]
    return None

def local_path(url):
    u=urlsplit(url)
    if u.hostname=='research.google':
        p=unquote(u.path).lstrip('/')
        if '/intl/' in u.path and not EXT.search(u.path): p=p.rstrip('/')+'/index.html'
    else:
        suffix=Path(u.path).suffix
        if len(suffix)>8: suffix=''
        if u.hostname=='fonts.googleapis.com': suffix='.css'
        p='ai-quests/_external/'+u.hostname+'/'+hashlib.sha256(url.encode()).hexdigest()+suffix
    target=(PUBLIC/p).resolve()
    if not target.is_relative_to(PUBLIC.resolve()): raise ValueError('Path escapes public root')
    return target

def add(value, origin=BASE, bucket=False):
    value=html.unescape(value.strip()).replace('\\/','/')
    if not value or any(c in value for c in ('${','\n','\r','<','>')) or value.startswith(('data:','blob:','#')): return
    if value.startswith('/assets/'): value='/ai-quests'+value
    if bucket and not value.startswith(('http:','https:','/ai-quests/')):
        value=BASE+'assets/bucket/'+value.lstrip('/')
    url=canonical(urljoin(origin,value))
    if url and url not in seen and not ('404' in records.get(url,{}).get('error','')): pending.add(url)

def scan(url,b,ctype):
    if not any(x in ctype for x in ('text/','javascript','json','xml')) and not EXT.search(urlsplit(url).path) or urlsplit(url).path.endswith(('.webm','.mp4','.mp3','.woff2','.woff','.png','.jpg','.webp','.glb','.wasm','.bin','.ico','.hdr')): return
    try: s=b.decode('utf-8')
    except UnicodeDecodeError: return
    for value in re.findall(r'\./(?:chunk|main|styles)-[A-Z0-9]+\.(?:js|css)',s): add(value,BASE)
    for value in re.findall(r'/ai-quests/assets/[^\s"\x27<>`\\)]+',s):
        if EXT.search(value): add(value,BASE)
    for value in re.findall(r'"((?:global|flood|dunes|lab|map)/[^"\\]+\.webm)"',s): add(BASE+'assets/audio/'+value)
    # Resolve build-time template path constants without executing upstream code.
    literals=re.findall(r'(?<![\w$])([\w$]+)\s*=\s*(["`])([^"`\n]{1,240})\2',s)
    for _ in range(8):
        for key,_,value in literals:
            for k,v in constants.items(): value=value.replace('${'+k+'}',v)
            if '${' not in value and value.startswith(('/ai-quests/','assets/')): constants[key]=value
    for value in re.findall(r'`([^`\n]{1,300})`',s):
        for k,v in constants.items(): value=value.replace('${'+k+'}',v)
        if EXT.search(value) and value.startswith(('/ai-quests/','assets/')): add(value,BASE)
    for value in re.findall(r'https?://[^\s"\x27<>`\\)]+',s): add(value,url)
    for value in re.findall(r'(?:src|href)\s*=\s*["\x27]([^"\x27]+)',s):
        if EXT.search(value) or value.startswith('https://fonts.googleapis.com/'): add(value,BASE)
    for value in re.findall(r'url\(\s*["\x27]?([^\s)"\x27]+)',s): add(value,url)
    for value in re.findall(r'["\x27]([^"\x27\n]{1,350})["\x27]',s):
        if not EXT.search(value): continue
        if value.startswith(('/ai-quests/','/assets/','assets/','./chunk-','./main-','./styles-')): add(value,BASE)
        elif re.match(r'^(global|flood|dunes|lab|map)/.*\.webm$',value): add(BASE+'assets/audio/'+value)
    if 'json' in ctype or url.endswith('.json'):
        try: data=json.loads(s)
        except ValueError: return
        def walk(obj):
            if isinstance(obj,dict):
                for k,v in obj.items():
                    if isinstance(v,str) and (k in ('url','uri','src','href') or EXT.search(v) and '/' in v): add(v,url,bucket=not v.startswith(('http','/ai-quests/')))
                    elif isinstance(v,(list,dict)): walk(v)
            elif isinstance(obj,list):
                for v in obj: walk(v)
        walk(data)

def download(url):
    path=local_path(url)
    old=records.get(url)
    if old and old.get('status')=='ok' and path.exists():
        text_path=ROOT/'upstream-text'/path.relative_to(PUBLIC)
        b=text_path.read_bytes() if text_path.exists() else path.read_bytes()
        return url,b,old['content_type'],True
    b,ct=fetch(url)
    # Reject SPA fallback HTML for a file request.
    if EXT.search(urlsplit(url).path) and 'text/html' in ct: raise ValueError('HTML fallback returned for asset')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b)
    if any(x in ct for x in ('text/','javascript','json','xml')):
        original=ROOT/'upstream-text'/path.relative_to(PUBLIC)
        original.parent.mkdir(parents=True,exist_ok=True);original.write_bytes(b)
    return url,b,ct,False

def flush():
    temporary=MANIFEST.with_suffix('.tmp')
    temporary.write_text(json.dumps(records,ensure_ascii=False,indent=2),'utf-8')
    temporary.replace(MANIFEST)

if __name__=='__main__':
    add(BASE+'intl/en_us')
    archive_config=ROOT/'archive-config.json'
    if archive_config.exists(): sid=json.loads(archive_config.read_text('utf-8'))['snapshot_id']
    else: sid=json.loads(fetch(BASE+'content/api/current_snapshot_id')[0])['snapshot_id']
    add(BASE+'content/api/current_snapshot_id')
    config=json.loads(fetch(BASE+'content/api/snapshot/'+sid+'/site_config.json')[0])
    add(BASE+'content/api/snapshot/'+sid+'/site_config.json')
    # Types used by the published app; additional types discovered below are added dynamically.
    types={'sitewide','home_page','planet_page','flood_prediction'}
    locales=[x['site_locale'] for x in config['locales'] if x.get('enabled')]
    for loc in locales:
        add(BASE+'intl/'+loc)
        for page in ('about','faq','teacher-resources','privacy-notice','videos'): add(BASE+'intl/'+loc+'/'+page)
        for typ in types: add(BASE+'content/api/snapshot/'+sid+'/'+loc+'/'+typ+'.json')
    for name in ('draco_decoder.js','draco_wasm_wrapper.js','draco_decoder.wasm'):
        add(BASE+'assets/webgl/decoders/draco/'+name)
    print(json.dumps({'snapshot':sid,'locales':locales}),flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        round_no=0
        while pending:
            batch=sorted(pending-seen);pending.clear()
            if not batch: break
            seen.update(batch);round_no+=1
            print('ROUND',round_no,'queued',len(batch),'total',len(seen),flush=True)
            futures={pool.submit(download,u):u for u in batch}
            for ix,f in enumerate(as_completed(futures),1):
                u=futures[f]
                try:
                    u,b,ct,cached=f.result();p=local_path(u)
                    records[u]={'status':'ok','path':p.relative_to(PUBLIC).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'content_type':ct}
                    scan(u,b,ct)
                    if u.endswith('.js'):
                        s=b.decode('utf-8')
                        for typ in re.findall(r'\([^()]{0,70},"([a-z_]+)"\)\)\.subscribe',s):
                            if any(t in typ for t in ('prediction','detection','page','quest','research','brain','blindness','lab')):
                                for loc in locales: add(BASE+'content/api/snapshot/'+sid+'/'+loc+'/'+typ+'.json')
                except Exception as exc:
                    records[u]={'status':'error','error':str(exc)}
                    print('ERROR',u,str(exc),flush=True)
                if ix%100==0: flush();print('PROGRESS',ix,'/',len(batch),flush=True)
            flush()
    ok=[r for r in records.values() if r['status']=='ok'];err=[u for u,r in records.items() if r['status']!='ok']
    print(json.dumps({'files':len(ok),'bytes':sum(r['bytes'] for r in ok),'errors':len(err),'snapshot':sid}),flush=True)