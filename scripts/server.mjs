import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public');
const manifestPath = path.resolve(root, '../reports/manifest.json');
const types = {'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.html':'text/html; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.glb':'model/gltf-binary','.wasm':'application/wasm','.webm':'video/webm','.mp4':'video/mp4','.woff2':'font/woff2','.woff':'font/woff','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg','.jpeg':'image/jpeg','.ico':'image/x-icon','.pdf':'application/pdf','.vtt':'text/vtt'};
const extraTypes = new Map();
if(fs.existsSync(manifestPath)) for(const r of Object.values(JSON.parse(fs.readFileSync(manifestPath,'utf8')))) if(r.status==='ok') extraTypes.set(r.path,r.content_type);
const server = http.createServer((req,res)=>{
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('X-Frame-Options','SAMEORIGIN');
  res.setHeader('Content-Security-Policy',"default-src 'none'; base-uri 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; media-src 'self' blob: data:; connect-src 'self' blob:; worker-src 'self' blob:; frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com; object-src 'none'; form-action 'none'; frame-ancestors 'self'");
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,{'Allow':'GET, HEAD'});return res.end();}
  let requested;
  try { requested = decodeURIComponent(new URL(req.url,'http://localhost').pathname); } catch {res.writeHead(400);return res.end();}
  if(requested.includes('\0') || requested.includes('\\')) {res.writeHead(400);return res.end();}
  if(requested==='/'){res.writeHead(302,{Location:'/ai-quests/intl/en_us'});return res.end();}
  const relative=requested.replace(/^\/+/, '');
  let file=path.resolve(root,relative);
  if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
  if(fs.existsSync(file) && fs.statSync(file).isDirectory()) file=path.join(file,'index.html');
  const localeRoute=/^\/ai-quests\/intl\/([a-zA-Z_-]+)(?:\/.*)?$/.exec(requested);
  if(!fs.existsSync(file) && localeRoute && !path.extname(requested)){
    const localeIndex=path.join(root,'ai-quests/intl',localeRoute[1],'index.html');
    file=fs.existsSync(localeIndex)?localeIndex:path.join(root,'ai-quests/intl/en_us/index.html');
  }
  if(!fs.existsSync(file) || !fs.statSync(file).isFile()){res.writeHead(404);return res.end('Missing local resource');}
  const stat=fs.statSync(file);
  const key=path.relative(root,file).split(path.sep).join('/');
  res.setHeader('Content-Type',types[path.extname(file)] || extraTypes.get(key) || 'application/octet-stream');
  res.setHeader('Accept-Ranges','bytes');
  res.setHeader('Cache-Control','no-cache');
  let start=0,end=stat.size-1,status=200;
  if(req.headers.range){
    const m=/^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
    if(!m || (!m[1]&&!m[2])){res.writeHead(416,{'Content-Range':`bytes */${stat.size}`});return res.end();}
    if(!m[1])start=Math.max(0,stat.size-Number(m[2]));
    else{start=Number(m[1]);if(m[2])end=Math.min(Number(m[2]),end);}
    if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>end||start>=stat.size){res.writeHead(416,{'Content-Range':`bytes */${stat.size}`});return res.end();}
    status=206;res.setHeader('Content-Range',`bytes ${start}-${end}/${stat.size}`);
  }
  res.setHeader('Content-Length',Math.max(0,end-start+1));res.writeHead(status);
  if(req.method==='HEAD'||!stat.size)return res.end();
  const stream=fs.createReadStream(file,{start,end});
  stream.on('error',()=>res.destroy());res.on('close',()=>stream.destroy());stream.pipe(res);
});
server.on('error',error=>{console.error(error.message);process.exitCode=1;});
server.listen({port:4192,host:'127.0.0.1',exclusive:true},()=>console.log('AI Quests: http://127.0.0.1:4192/ai-quests/intl/en_us'));