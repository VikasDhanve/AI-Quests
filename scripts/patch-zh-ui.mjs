import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createRequire} from 'node:module';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const require=createRequire(import.meta.url);const {babelParse,traverse}=require(path.join(root,'node_modules/playwright/lib/transform/babelBundle.js'));
const app=path.join(root,'public/ai-quests');const map=JSON.parse(fs.readFileSync(path.join(root,'localization/zh_cn/ui-map.json'),'utf8'));const norm=s=>s.replace(/\s+/g,' ').trim();const report=[];
for(const name of fs.readdirSync(app).filter(x=>/^(chunk-|main-).*\.js$/.test(x))){
 let s=fs.readFileSync(path.join(app,name),'utf8');if(s.includes('const __aiqZhLocale='))continue;
 const ast=babelParse(s,name,true);const edits=[],used={};
 traverse(ast,{StringLiteral(p){
  const v=p.node.value,k=norm(v),aria=p.parent.type==='ArrayExpression'&&p.parent.elements[Number(p.key)-1]?.value==='ariaLabel',t=(aria?({next:'下一步',previous:'上一步',close:'关闭',back:'返回'}[k]):null)||map[k];if(['High','Medium','Low'].includes(k)||!t||t===k||/^(?:https?:|\/|\.)/.test(v)||/^[A-Z0-9_-]+$/.test(k)||(!aria&&/^[a-z0-9_-]+$/.test(k)))return;
  const a=p.parent;if((a.type==='ObjectProperty'||a.type==='ObjectMethod'||a.type==='ClassProperty'||a.type==='ClassMethod')&&p.key==='key')return;
  if(a.type.startsWith('Import')||a.type.startsWith('Export')||a.type==='SwitchCase'||(a.type==='MemberExpression'&&p.key==='property'))return;
  const target=(v.match(/^\s*/)?.[0]||'')+t+(v.match(/\s*$/)?.[0]||'');used[v]=target;edits.push({start:p.node.start,end:p.node.end,value:'__aiqT('+JSON.stringify(v)+')'});
 }});
 for(const e of edits.sort((a,b)=>b.start-a.start))s=s.slice(0,e.start)+e.value+s.slice(e.end);
 if(edits.length)s='const __aiqZhLocale=/\\/intl\\/zh_cn(?:\\/|$)/.test(location.pathname);const __aiqZhText='+JSON.stringify(used)+';const __aiqT=s=>__aiqZhLocale?(__aiqZhText[s]??s):s;\n'+s;
 if(name==='chunk-5XHC44OL.js'){
  if(!s.includes('var kne=["en_gb","en_us"]'))throw Error('Expected language menu whitelist not found');s=s.replace('var kne=["en_gb","en_us"]','var kne=["en_gb","en_us","zh_cn"]');
  const save='function Js(i){let e=btoa(JSON.stringify(i));localStorage.setItem(W_,e)}';if(!s.includes(save))throw Error('Expected progress save function not found');s=s.replace(save,'function Js(i){let e=btoa(Array.from(new TextEncoder().encode(JSON.stringify(i)),b=>String.fromCharCode(b)).join(""));localStorage.setItem(W_,e)}');
  const load='let e=JSON.parse(atob(i));';if(!s.includes(load))throw Error('Expected progress load function not found');s=s.replace(load,'let e=__aiqDecodeProgress(i);');s='function __aiqDecodeProgress(v){const b=atob(v);try{return JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(Uint8Array.from(b,c=>c.charCodeAt(0))))}catch{return JSON.parse(b)}}\n'+s;
 }
 if(name==='chunk-ZOE2GR7R.js'){
  s=s.split('e.name.toLowerCase().includes(t.activePen().toLowerCase())').join('e.type===t.activePen()');
  for(const [en,zh] of [['capillary','毛细血管'],['neuron','神经元'],['astrocyte','星形胶质细胞']]){
   const needle='t.includes("'+en+'")&&(a="'+en+'")';if(!s.includes(needle))throw Error('Expected lab label type mapping not found: '+en);s=s.split(needle).join('(t.includes("'+en+'")||t.includes("'+zh+'"))&&(a="'+en+'")');
  }
 }
 babelParse(s,name,true);fs.writeFileSync(path.join(app,name),s);report.push({file:name,translated_literals:edits.length});
}
fs.writeFileSync(path.join(root,'reports/zh-cn-ui-patches.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({patched_ui_files:report.filter(x=>x.translated_literals).length,translated_ui_literals:report.reduce((a,x)=>a+x.translated_literals,0)}));