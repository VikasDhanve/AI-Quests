from pathlib import Path, PurePosixPath
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
import json, sys, gzip

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=sys.argv[1] if len(sys.argv)>1 else "http://182.92.231.54"
package=json.loads((HERE/"artifacts/latest-package.json").read_text("utf-8"))
OUT=HERE/"artifacts"/package["release"]
manifest=json.loads((ROOT/"reports/manifest.json").read_text("utf-8"))
checks=[]
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl): return None
def request(path, method="GET", headers=None):
    opener=build_opener(ProxyHandler({}),NoRedirect())
    try:
        with opener.open(Request(BASE+path,method=method,headers=headers or {}),timeout=20) as response:
            return response.status,response.headers,response.read()
    except HTTPError as response:
        return response.code,response.headers,response.read()
def check(name, passed, **details):
    checks.append(dict(check=name,passed=bool(passed),**details))
code,h,b=request("/")
check("Chinese root redirect",code==302 and h.get("Location")=="/ai-quests/intl/zh_cn",status=code)
code,h,b=request("/ai-quests/intl/zh_cn/")
check("Chinese HTML and headers",code==200 and b'lang="zh-CN"' in b and h.get("X-Content-Type-Options")=="nosniff" and "object-src 'none'" in h.get("Content-Security-Policy","") and h.get("Cache-Control")=="no-cache",status=code)
for locale in sorted((ROOT/"public/ai-quests/intl").iterdir()):
    if locale.is_dir() and (locale/"index.html").is_file():
        code,h,b=request("/ai-quests/intl/"+locale.name+"/",method="HEAD")
        check("Language "+locale.name,code==200 and h.get_content_type()=="text/html",status=code)
for slug in ["market-marshes","dusky-dunes","polar-peaks"]:
    code,h,b=request("/ai-quests/intl/zh_cn/quest/"+slug,method="HEAD")
    check("Deep route "+slug,code==200 and h.get_content_type()=="text/html",status=code)
for path in ["/.git/config","/.env","/reports/manifest.json","/scripts/server.mjs","/deployment/aliyun/nginx.conf","/upstream-text/","/%2e%2e/README.md","/ai-quests/%5c..%5cREADME.md","/ai-quests/%00","/ai-quests/intl/zh_cn/missing-script.js"]:
    code,h,b=request(path)
    check("Private/missing "+path,code in (400,403,404),status=code)
for method in ["POST","PUT","DELETE"]:
    code,h,b=request("/ai-quests/intl/zh_cn/",method=method)
    check("Reject "+method,code==405,status=code)
extensionless=[row for row in manifest.values() if row.get("status")=="ok" and not PurePosixPath(row["path"]).suffix]
def check_mime(row):
    path="/"+quote(row["path"],safe="/")
    code,h,b=request(path,method="HEAD")
    expected=row["content_type"].split(";")[0].strip()
    actual=h.get_content_type()
    return {"path":row["path"],"passed":code==200 and actual==expected,"expected":expected,"actual":actual,"status":code}
with ThreadPoolExecutor(max_workers=8) as pool:
    mime_checks=list(pool.map(check_mime,extensionless))
media=[row for row in manifest.values() if row.get("status")=="ok" and row["path"].endswith((".webm",".mp4"))]
def check_range(row):
    code,h,b=request("/"+quote(row["path"],safe="/"),headers={"Range":"bytes=0-127"})
    return {"path":row["path"],"passed":code==206 and len(b)==128 and h.get("Content-Range")=="bytes 0-127/"+str(row["bytes"]),"status":code}
with ThreadPoolExecutor(max_workers=8) as pool:
    ranges=list(pool.map(check_range,media))
code,h,b=request("/"+media[0]["path"],headers={"Range":"bytes=999999999999-"})
check("Invalid range",code==416,status=code)
resources=json.loads((ROOT/"reports/teacher-resources-zh.json").read_text("utf-8"))
for row in resources:
    code,h,b=request(row["local"],headers={"Range":"bytes=0-4"})
    check("Chinese PDF "+row["local"],code==206 and b==b"%PDF-" and h.get_content_type()=="application/pdf",status=code)
for suffix,mime in [(".wasm","application/wasm"),(".vtt","text/vtt"),(".glb","model/gltf-binary")]:
    candidates=list((ROOT/"public").rglob("*"+suffix))
    assert candidates
    code,h,b=request("/"+quote(candidates[0].relative_to(ROOT/"public").as_posix(),safe="/"),method="HEAD")
    check("MIME "+suffix,code==200 and h.get_content_type()==mime,actual=h.get_content_type())
js=next((ROOT/"public").rglob("*.js"))
code,h,b=request("/"+quote(js.relative_to(ROOT/"public").as_posix(),safe="/"),headers={"Accept-Encoding":"gzip"})
check("JavaScript readable",code==200 and ("javascript" in h.get_content_type()),encoding=h.get("Content-Encoding","identity"))
report={"base":BASE,"release":package["release"],"checks":checks,"extensionless_mime_count":len(mime_checks),"mime_failures":[r for r in mime_checks if not r["passed"]],"media_range_count":len(ranges),"range_failures":[r for r in ranges if not r["passed"]]}
report["passed"]=all(r["passed"] for r in checks) and not report["mime_failures"] and not report["range_failures"]
(OUT/"http-validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="checks"}))
assert report["passed"],json.dumps([r for r in checks if not r["passed"]])