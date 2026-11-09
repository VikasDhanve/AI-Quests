import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true,
  executablePath: 'C:/Users/yamal/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe',
  args: ['--autoplay-policy=no-user-gesture-required'] });
const report = { failures: [], errors: [], external: [], layouts: [] };
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  page.on('response', r => { if (r.status() >= 400) report.failures.push(r.url()); });
  page.on('pageerror', e => report.errors.push(e.message));
  await page.route('**/*', route => {
    const url = route.request().url();
    if (!url.startsWith('http') || new URL(url).hostname === '127.0.0.1') return route.continue();
    report.external.push(url);
    return route.abort('internetdisconnected');
  });
  await page.goto('http://127.0.0.1:4192/ai-quests/intl/zh_cn/teacher-resources');
  const rows = page.locator('.aiq-teacher-resource__links');
  assert.equal(await rows.count(), 5);
  assert.equal(await page.getByRole('link', { name: /^中文 PDF/ }).count(), 5);
  const resources = JSON.parse(fs.readFileSync('reports/teacher-resources-zh.json', 'utf8'));
  for (const item of resources) {
    const link = page.locator(`a[href="${item.local}"]`);
    assert.equal(await link.count(), 1);
    const response = await fetch('http://127.0.0.1:4192' + item.local);
    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /application\/pdf/);
    assert.equal(Buffer.from(await response.arrayBuffer()).subarray(0, 5).toString(), '%PDF-');
  }
  for (const width of [1440, 768, 375]) {
    await page.setViewportSize({ width, height: 960 });
    for (let i = 0; i < 5; i++) {
      const row = rows.nth(i);
      await row.scrollIntoViewIfNeeded();
      const links = row.locator('a');
      assert.equal(await links.count(), 2);
      const [english, chinese] = await Promise.all([links.nth(0).boundingBox(), links.nth(1).boundingBox()]);
      assert.ok(chinese.x > english.x && Math.abs(chinese.y - english.y) < 4, `PDF buttons must be side by side at ${width}px`);
    }
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    report.layouts.push({ width, pairedPdfButtons: 5 });
  }
  await page.setViewportSize({ width: 1440, height: 960 });
  await page.evaluate(() => scrollTo(0, 0));
  const video = page.locator('#trailer-tr');
  await video.evaluate(v => { v.muted = true; });
  await page.locator('button[data-for="trailer-tr"]').click();
  await page.waitForFunction(() => document.querySelector('#trailer-tr')?.textTracks[0]?.cues?.length === 29);
  report.tracks = await video.evaluate(v => Array.from(v.textTracks, t => ({ language: t.language, mode: t.mode, cues: t.cues.length })));
  assert.equal(report.tracks[0].language, 'zh-CN');
  assert.equal(report.tracks[0].mode, 'showing');
  assert.ok(await video.evaluate(v => Array.from(v.textTracks[0].cues).every(c => /[\u4e00-\u9fff]/.test(c.text))));
  await video.evaluate(v => { v.currentTime = 35; });
  await page.waitForTimeout(400);
  assert.ok(await video.evaluate(v => /[\u4e00-\u9fff]/.test(v.textTracks[0].activeCues?.[0]?.text || '')));
  await video.screenshot({ path: 'reports/zh-teachers-subtitles.png' });
  await video.evaluate(v => v.pause());
  await rows.first().scrollIntoViewIfNeeded();
  await page.screenshot({ path: 'reports/zh-teachers-buttons.png' });
  const english = await browser.newPage();
  await english.goto('http://127.0.0.1:4192/ai-quests/intl/en_us/teacher-resources');
  assert.equal(await english.locator('a[href*="/teacher-resources/zh_cn/"]').count(), 0);
  assert.equal(await english.locator('.aiq-card__doc-btn').count(), 5);
  assert.equal(await english.locator('track[srclang="zh-CN"]').count(), 0);
  assert.deepEqual(report.failures, []);
  assert.deepEqual(report.errors, []);
  assert.deepEqual(report.external, []);
  report.passed = true;
} catch (error) {
  report.passed = false;
  report.error = error.stack;
  process.exitCode = 1;
} finally {
  fs.writeFileSync('reports/zh-teachers-validation.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
  await browser.close();
}
