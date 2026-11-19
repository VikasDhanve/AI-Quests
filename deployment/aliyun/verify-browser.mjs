import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const pkg=JSON.parse(fs.readFileSync(path.join(here,'artifacts/latest-package.json'),'utf8'));
const out=path.join(here,'artifacts',pkg.release);
const base=process.argv[2]||'http://182.92.231.54';
const report={base,release:pkg.release,failed:[],errors:[],external:[]};
const browser=await chromium.launch({headless:true,executablePath:'C:/Users/yamal/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe',args:['--enable-unsafe-swiftshader','--autoplay-policy=no-user-gesture-required']});
const context=await browser.newContext({viewport:{width:1440,height:960}});
const page=await context.newPage();
await context.route('**/*',route=>{
  const url=route.request().url();
  if(!url.startsWith('http')||new URL(url).origin===new URL(base).origin)return route.continue();
  report.external.push(url);return route.abort('internetdisconnected');
});
context.on('page',p=>{
  p.on('response',r=>{if(r.status()>=400)report.failed.push({url:r.url(),status:r.status()});});
  p.on('pageerror',e=>report.errors.push(e.message));
});
page.on('response',r=>{if(r.status()>=400)report.failed.push({url:r.url(),status:r.status()});});
page.on('pageerror',e=>report.errors.push(e.message));
try {
  await page.goto(base+'/',{waitUntil:'networkidle',timeout:60000});
  await page.getByRole('button',{name:'接受任务',exact:true}).waitFor({timeout:30000});
  assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');
  report.home=true;
  await page.screenshot({path:path.join(out,'cloud-home.png'),fullPage:true});
  await page.getByRole('button',{name:'接受任务',exact:true}).click();
  if(await page.getByRole('button',{name:'继续',exact:true}).isVisible().catch(()=>false))
    await page.getByRole('button',{name:'继续',exact:true}).click();
  await page.locator('video').first().waitFor({timeout:30000});
  await page.waitForFunction(()=>[...document.querySelectorAll('video')].some(v=>v.readyState>=3&&[...v.textTracks].some(t=>t.mode==='showing'&&t.cues?.length>0)),{},{timeout:45000});
  report.intro=await page.locator('video').evaluateAll(vs=>vs.map(v=>({ready:v.readyState,tracks:[...v.textTracks].map(t=>({language:t.language,mode:t.mode,cues:t.cues?.length||0}))})));
  assert.ok(report.intro.some(v=>v.tracks.some(t=>t.language==='zh-CN'&&t.cues>=20)));
  await page.screenshot({path:path.join(out,'cloud-subtitles.png'),fullPage:true});
  await page.locator('video').evaluateAll(vs=>vs.forEach(v=>{if(Number.isFinite(v.duration)){v.currentTime=v.duration-.15;v.play().catch(()=>{});}}));
  await page.getByRole('button',{name:'开始任务',exact:true}).waitFor({timeout:30000});
  const mapText=(await page.locator('body').innerText()).replace(/\s/g,'');
  for(const title of ['集市沼泽','暮色沙丘','极地之巅'])assert.ok(mapText.includes(title),title);
  report.map=true;
  await page.screenshot({path:path.join(out,'cloud-map.png'),fullPage:true});
  await page.goto(base+'/ai-quests/intl/zh_cn/quest/market-marshes');
  const resume=page.getByRole('button',{name:/^(继续|继续上次进度)$/,exact:true});
  try { await resume.first().click({timeout:15000}); report.resumeClicked=true; } catch(error) { if(!(await page.locator('video').count()))throw error; }
  await page.waitForFunction(()=>[...document.querySelectorAll('video')].some(v=>v.readyState>=3),{},{timeout:45000});
  await page.locator('video').evaluateAll(vs=>vs.forEach(v=>{if(Number.isFinite(v.duration)){v.currentTime=v.duration-.15;v.play().catch(()=>{});}}));
  await page.waitForTimeout(8000);
  assert.ok(await page.locator('canvas').count()>0);
  report.scene={canvases:await page.locator('canvas').count(),text:(await page.locator('body').innerText()).slice(0,1500)};
  await page.screenshot({path:path.join(out,'cloud-scene.png'),fullPage:true});
  const teacher=await context.newPage();
  await teacher.goto(base+'/ai-quests/intl/zh_cn/teacher-resources',{waitUntil:'networkidle',timeout:45000});
  assert.equal(await teacher.getByRole('link',{name:/^中文 PDF/}).count(),5);
  const video=teacher.locator('#trailer-tr');
  await video.evaluate(v=>{v.muted=true;});
  await teacher.locator('button[data-for="trailer-tr"]').click();
  await teacher.waitForFunction(()=>document.querySelector('#trailer-tr')?.textTracks[0]?.cues?.length===29,{},{timeout:30000});
  report.teacher={chinesePdfLinks:5,tracks:await video.evaluate(v=>[...v.textTracks].map(t=>({language:t.language,mode:t.mode,cues:t.cues.length})))};
  assert.equal(report.teacher.tracks[0].language,'zh-CN');
  assert.equal(report.teacher.tracks[0].mode,'showing');
  await teacher.screenshot({path:path.join(out,'cloud-teachers.png'),fullPage:true});
  assert.deepEqual(report.failed,[]);
  assert.deepEqual(report.errors,[]);
  assert.deepEqual(report.external,[]);
  report.passed=true;
}catch(error){
  report.passed=false;report.error=String(error.stack||error);
  report.body=await page.locator('body').innerText().catch(()=>'');
  await page.screenshot({path:path.join(out,'cloud-failure.png'),fullPage:true}).catch(()=>{});
  process.exitCode=1;
}finally{
  fs.writeFileSync(path.join(out,'browser-validation.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
  await browser.close();
}