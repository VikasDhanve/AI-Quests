import assert from 'node:assert/strict';import {chromium} from 'playwright';import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const browser=await chromium.launch({headless:true,executablePath:'C:/Users/yamal/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe',args:['--enable-unsafe-swiftshader','--autoplay-policy=no-user-gesture-required']});
const context=await browser.newContext({viewport:{width:1440,height:960}});const page=await context.newPage();const failed=[],errors=[],external=[];
await context.route('**/*',r=>{const u=r.request().url();if(!u.startsWith('http')||new URL(u).hostname==='127.0.0.1')return r.continue();external.push(u);return r.abort('internetdisconnected');});
page.on('response',r=>{if(r.status()>=400)failed.push({url:r.url(),status:r.status()});});page.on('pageerror',e=>errors.push(e.stack));
const report={};
try{
 await page.goto('http://127.0.0.1:4192/ai-quests/intl/en_us');await page.getByRole('button',{name:'English (US)',exact:true}).click({timeout:20000});
 await page.getByRole('link',{name:'简体中文',exact:true}).click();await page.waitForURL(/\/intl\/zh_cn/);await page.getByRole('button',{name:'接受任务',exact:true}).waitFor({state:'visible',timeout:20000});
 assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');report.home=await page.locator('body').innerText();await page.screenshot({path:path.join(root,'reports/zh-home.png'),fullPage:true});
 await page.getByRole('button',{name:'接受任务',exact:true}).click();await page.waitForTimeout(1500);
 if(await page.getByRole('button',{name:'继续',exact:true}).isVisible().catch(()=>false))await page.getByRole('button',{name:'继续',exact:true}).click();
 await page.locator('video').waitFor({state:'visible',timeout:20000});await page.waitForTimeout(3500);
 report.media=await page.locator('video').evaluateAll(es=>es.map(v=>({ready:v.readyState,currentTime:v.currentTime,tracks:Array.from(v.textTracks,t=>({kind:t.kind,language:t.language,mode:t.mode,cues:Array.from(t.cues||[],c=>c.text)}))})));
 assert.ok(report.media.some(v=>v.ready>=3&&v.tracks.some(t=>t.mode==='showing'&&t.cues.some(s=>/[\u4e00-\u9fff]/.test(s)))),'中文开场字幕必须真实加载并显示');
 await page.screenshot({path:path.join(root,'reports/zh-intro-subtitles.png'),fullPage:true});
 await page.locator('video').evaluateAll(es=>es.forEach(v=>{if(Number.isFinite(v.duration)){v.currentTime=v.duration-.15;v.play().catch(()=>{});}}));
 await page.getByRole('button',{name:'开始任务',exact:true}).waitFor({state:'visible',timeout:25000});report.map=await page.locator('body').innerText();
 for(const title of ['集市沼泽','暮色沙丘','极地之巅'])assert.ok(report.map.replace(/\s/g,'').includes(title),'地图缺少中文任务名：'+title);
 await page.screenshot({path:path.join(root,'reports/zh-map.png'),fullPage:true});await context.storageState({path:path.join(root,'reports/browser-state-zh.json')});
 const english=await browser.newPage();await english.goto('http://127.0.0.1:4192/ai-quests/intl/en_us');await english.getByRole('button',{name:'Accept mission',exact:true}).waitFor({state:'visible',timeout:20000});assert.equal(await english.locator('html').getAttribute('lang'),'en');report.english=await english.locator('body').innerText();await english.close();
 assert.deepEqual(failed,[]);assert.deepEqual(errors,[]);assert.deepEqual(external,[]);report.passed=true;
}catch(e){report.passed=false;report.error=e.message;report.body=await page.locator('body').innerText().catch(()=>'');await page.screenshot({path:path.join(root,'reports/zh-flow-failure.png'),fullPage:true}).catch(()=>{});process.exitCode=1;}
finally{Object.assign(report,{failed,errors,external});fs.writeFileSync(path.join(root,'reports/zh-browser.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));await browser.close();}