import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const runtime = 'public/ai-quests/site-config.json';
const report = { cases: [], errors: [] };
const browser = await chromium.launch({ headless: true,
  executablePath: 'C:/Users/yamal/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe',
  args: ['--enable-unsafe-swiftshader'] });
let original;
try {
  const response = await fetch('http://127.0.0.1:9091/ai-quests/site-config.json');
  assert.equal(response.status, 200, '发布目录应提供可直接修改的站点配置');
  original = fs.readFileSync(runtime);
  assert.equal(typeof JSON.parse(original.toString('utf8').replace(/^\uFEFF/, '')).showSponsor, 'boolean');
  const pages = await Promise.all([4192, 9091].map(async port => {
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    page.on('pageerror', e => report.errors.push(e.message));
    return { page, port, config: `http://127.0.0.1:${port}/ai-quests/site-config.json` };
  }));
  async function verify({ page, port, config }, enabled, label) {
    const requests = [];
    const listener = request => requests.push(request.url());
    page.on('request', listener);
    const settingResponse = page.waitForResponse(r => r.url() === config);
    // Each test context is isolated from the user's browser and progress.
    await page.evaluate(() => localStorage.clear()).catch(() => {});
    await page.goto(`http://127.0.0.1:${port}/ai-quests/intl/zh_cn`);
    await settingResponse;
    await page.getByRole('button', { name: '接受任务', exact: true }).waitFor({ timeout: 25000 });
    const entry = page.getByRole('button', { name: '赞助支持', exact: true });
    if (enabled) {
      await entry.waitFor();
      await entry.click();
      assert.ok(await page.getByRole('dialog').isVisible());
      await page.keyboard.press('Escape');
    } else {
      assert.equal(await entry.count(), 0);
      assert.equal(await page.locator('#aiq-support-dialog').count(), 0);
      assert.ok(!requests.some(url => /\/local-support\/(?:sponsor\.js|alipay-)/.test(url)), '关闭时不加载赞助模块和二维码');
    }
    page.off('request', listener);
    report.cases.push({ port, label, shown: enabled });
  }
  for (const enabled of [false, true, false]) {
    fs.writeFileSync(runtime, JSON.stringify({ showSponsor: enabled }, null, 2) + '\n');
    await Promise.all(pages.map(p => verify(p, enabled, `real file ${enabled}`)));
  }
  const main = pages.find(p => p.port === 9091);
  for (const [label, body, status] of [
    ['string false', '{"showSponsor":"false"}', 200],
    ['string true', '{"showSponsor":"true"}', 200],
    ['missing key', '{}', 200],
    ['invalid JSON', '{invalid', 200],
    ['missing file', '{}', 404],
  ]) {
    await main.page.route(main.config, route => route.fulfill({ status, contentType: 'application/json', body }));
    await verify(main, false, label);
    await main.page.unroute(main.config);
  }
  assert.deepEqual(report.errors, []);
  report.passed = true;
} catch (error) {
  report.passed = false;
  report.error = error.stack;
  process.exitCode = 1;
} finally {
  if (original) fs.writeFileSync(runtime, original);
  fs.writeFileSync('reports/sponsor-config-validation.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
  await browser.close();
}
