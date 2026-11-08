import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const browser=await chromium.launch({headless:true,executablePath:'C:/Users/yamal/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe',args:['--enable-unsafe-swiftshader','--autoplay-policy=no-user-gesture-required']});
const results=[];
for(const slug of ['market-marshes','dusky-dunes','polar-peaks']){
 const context=await browser.newContext({viewport:{width:1440,height:960},storageState:path.join(root,'reports/browser-state-zh.json')});
 const page=await context.newPage();const failures=[],errors=[],requests=[],external=[];
 await context.route('**/*',r=>{const u=r.request().url();if(!u.startsWith('http')||new URL(u).hostname==='127.0.0.1')return r.continue();external.push(u);return r.abort('internetdisconnected');});
 page.on('request',r=>requests.push(r.url()));page.on('response',r=>{if(r.status()>=400)failures.push({url:r.url(),status:r.status()});});page.on('pageerror',e=>errors.push(e.stack));
 await page.goto('http://127.0.0.1:4192/ai-quests/intl/zh_cn/quest/'+slug);
 try { await page.getByRole('button',{name:/^(继续|继续上次进度)$/,exact:true}).click({timeout:15000}); } catch(e) { console.log('RESUME_NOT_SHOWN',slug,page.url(),(await page.locator('body').innerText()).slice(0,2000),JSON.stringify({failures,errors})); }
 await page.waitForTimeout(12000);
 const body=(await page.locator('body').innerText()).slice(0,5000);
 const buttons=await page.getByRole('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label')})));
 const videos=await page.locator('video').evaluateAll(es=>es.map(e=>({src:e.currentSrc,ready:e.readyState,duration:e.duration,time:e.currentTime,paused:e.paused})));
 await page.locator('video').evaluateAll(es=>es.forEach(e=>{if(Number.isFinite(e.duration)&&e.duration>0){e.currentTime=e.duration-.15;e.play().catch(()=>{});}}));
 await page.waitForTimeout(8000);
 const sceneText=(await page.locator('body').innerText()).slice(0,5000);
 const canvases=await page.locator('canvas').count();
 const result={slug,url:page.url(),body,buttons,videos,sceneText,canvases,failures,errors,external,requests};results.push(result);
 console.log(JSON.stringify({...result,requests:requests.length}));
 await page.screenshot({path:path.join(root,'reports/zh-quest-'+slug+'.png'),fullPage:true});await context.close();
}
fs.writeFileSync(path.join(root,'reports/quests-zh-offline.json'),JSON.stringify(results,null,2));await browser.close();
if(results.some(r=>r.failures.length||r.errors.length||r.external.length||!r.canvases||!r.videos.some(v=>v.ready>=3&&v.time>0)))process.exitCode=1;