from pathlib import Path
import sys,re,json,html
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tooling'))
from yt_dlp import YoutubeDL
s=(ROOT/'upstream-text/ai-quests/intl/en_us/videos/index.html').read_text('utf-8')
links=[html.unescape(html.unescape(x.strip())) for x in re.findall(r'data-link="([^"]+)"',s)]
ids=[]
for u in links:
 m=re.search(r'(?:youtu\.be/|[?&]v=)([\w-]{11})',u)
 if m and m[1] not in ids:ids.append(m[1])
print('PUBLIC_SHOWCASE_VIDEOS',len(ids),flush=True)
options={'format':'best[ext=mp4]/best','outtmpl':str(ROOT/'public/ai-quests/assets/showcase/%(id)s.%(ext)s'),'noplaylist':True,'quiet':False,'retries':1,'extractor_retries':1,'socket_timeout':20,'js_runtimes':{'node':{}},'cachedir':str(ROOT/'tooling/cache')}
results=[]
# Probe one public video first; no account, cookies or access-control bypass.
for id in ids:
 try:
  with YoutubeDL(options) as dl:
   info=dl.extract_info('https://www.youtube.com/watch?v='+id,download=True)
   results.append({'id':id,'status':'ok','path':dl.prepare_filename(info),'title':info.get('title')})
 except Exception as e:
  results.append({'id':id,'status':'unavailable','error':str(e)})
  if len(results)==1:break
(ROOT/'reports/showcase-videos.json').write_text(json.dumps({'ids':ids,'results':results},ensure_ascii=False,indent=2),'utf-8')