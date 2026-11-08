from pathlib import Path
import json,sys
root=Path(sys.argv[1]);p=root/'localization/zh_cn/translations.json'
d=json.loads(p.read_text('utf-8')) if p.exists() else {}
for line in sys.stdin.read().splitlines():
 if not line.strip():continue
 i,text=line.split('\t',1);d['t'+i]=text.replace('\\n','\n')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')
print('Saved translations:',len(d))