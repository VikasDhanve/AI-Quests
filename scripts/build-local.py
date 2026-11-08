from pathlib import Path
import json,re,html,hashlib
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'reports/manifest.json').read_text('utf-8'))
lookup={url:'/'+r['path'] for url,r in manifest.items() if r['status']=='ok'}
extra=ROOT/'reports/teacher-resources.json'
if extra.exists():
    for r in json.loads(extra.read_text('utf-8')):
        if r['status']=='ok': lookup[html.unescape(r['original_link'])]=r['local']
changed=[]
for url,r in manifest.items():
    if r['status']!='ok':continue
    original=ROOT/'upstream-text'/r['path']
    if not original.exists():continue
    s=original.read_text('utf-8')
    if r['path'].endswith('.html'):
        # Analytics and cookie notices are unnecessary for a private offline copy.
        def script_tag(m):
            attrs,body=m[1],m[2]
            if 'speculationrules' in attrs: return ''
            if any(x in attrs+body for x in ('googletagmanager','google-analytics','partytown','cookienotificationbar','dataLayer')): return ''
            if 'src=' in attrs or 'application/ld+json' in attrs: return m[0]
            if not body.strip(): return ''
            name='offline-inline-'+hashlib.sha256(body.encode()).hexdigest()[:16]+'.js'
            (ROOT/'public/ai-quests'/name).write_text(body,'utf-8')
            return '<script src="/ai-quests/'+name+'"'+attrs+'></script>'
        s=re.sub(r'<script\b([^>]*)>(.*?)</script>',script_tag,s,flags=re.S)
        s=re.sub(r'<noscript\b[^>]*>.*?</noscript>','',s,flags=re.S)
        s=re.sub(r'<link\b[^>]*rel="preconnect"[^>]*>','',s)
    s=re.sub(r'https?://[^\s"\x27<>`\\)]+',lambda m:lookup.get(html.unescape(m[0]),m[0]),s)
    # The upstream asset helper must recognize localized CDN URLs as complete paths.
    s=s.replace('function l5(i){return o5.some','function l5(i){return i.startsWith("/ai-quests/_external/")||o5.some')
    target=ROOT/'public'/r['path'];target.write_text(s,'utf-8')
    h=hashlib.sha256(target.read_bytes()).hexdigest()
    if h!=r['sha256']:changed.append({'path':r['path'],'original_sha256':r['sha256'],'local_sha256':h})
(ROOT/'reports/local-modifications.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'localized_text_files':len(changed),'preserved_originals':len(list((ROOT/'upstream-text').rglob('*.*')))}))