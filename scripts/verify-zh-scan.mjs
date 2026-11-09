import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Users/yamal/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe',
  args: ['--enable-unsafe-swiftshader'],
});
const report = { results: [] };
let activePage;
try {
  for (const locale of ['zh_cn', 'en_us']) {
    const chinese = locale === 'zh_cn';
    const state = JSON.parse(fs.readFileSync('reports/browser-state-zh.json', 'utf8'));
    const storage = state.origins[0].localStorage.find(item => item.name === 'quests');
    const data = JSON.parse(Buffer.from(storage.value, 'base64').toString('utf8'));
    data.quests.lab.completedStages = ['INTRO', 'EXPLORE_LAB'];
    data.quests.lab.visitedStages = [...data.quests.lab.completedStages];
    data.redirectTo = `/intl/${locale}/quest/polar-peaks`;
    storage.value = Buffer.from(JSON.stringify(data)).toString('base64');
    const context = await browser.newContext({ storageState: state, viewport: { width: 1440, height: 960 } });
    await context.route('**/*', route => {
      const url = route.request().url();
      return !url.startsWith('http') || new URL(url).hostname === '127.0.0.1'
        ? route.continue() : route.abort('internetdisconnected');
    });
    const page = await context.newPage();
    activePage = page;
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:4192/ai-quests/intl/${locale}/quest/polar-peaks`);
    await page.getByRole('button', { name: chinese ? /^(继续|继续上次进度)$/ : /^(Continue|Resume)$/ }).click({ timeout: 20000 });
    const next = page.getByRole('button', { name: chinese ? '下一步' : 'next', exact: true });
    await next.click({ timeout: 20000 });
    await page.waitForTimeout(1500);
    await next.click({ timeout: 20000 });
    await page.locator('aiq-lab-brain-lights button.active:not([disabled])').first().click({ timeout: 20000 });
    await page.waitForTimeout(2500);
    const label = page.getByText(/DRAG TO SCAN|拖动以扫描/);
    await label.waitFor({ state: 'visible', timeout: 15000 });
    await page.screenshot({ path: `reports/${locale}-scan-slider.png` });
    const text = (await label.innerText()).trim();
    const result = { locale, text, errors };
    report.results.push(result);
    assert.equal(text, chinese ? '拖动以扫描' : 'DRAG TO SCAN');
    const scanner = page.locator('aiq-lab-card-stacker-modal');
    const title = scanner.locator('.lab-stacker__meta__upper__title');
    assert.equal((await title.innerText()).trim(), chinese ? '可以开始扫描' : 'Ready to scan');
    assert.match(await scanner.innerText(), chinese ? /扫描图：\s*001/ : /SCAN:\s*001/);
    // The original arrow pulses continuously, so its bounding box never becomes stable.
    await scanner.locator('.progress-slider__button button').click({ force: true });
    await scanner.getByText(chinese ? '正在扫描' : 'SCANNING IN PROGRESS', { exact: true }).waitFor({ timeout: 10000 });
    result.scanningLabel = true;
    result.scanningTitle = (await title.innerText()).trim();
    assert.equal(result.scanningTitle, chinese ? '正在扫描…' : 'Scanning...');
    if (chinese) assert.doesNotMatch(await scanner.innerText(), /[A-Za-z]/, '扫描进行中面板仍含英文');
    await page.screenshot({ path: `reports/${locale}-scan-in-progress.png` });
    const save = scanner.getByText(chinese ? '保存数据集' : 'Save Dataset', { exact: true });
    await save.waitFor({ state: 'visible', timeout: 25000 });
    const completeText = await scanner.innerText();
    assert.equal((await title.innerText()).trim(), chinese ? '扫描完成' : 'Scanning complete');
    result.completeText = completeText;
    assert.match(completeText, chinese ? /扫描图总数[：:]\s*1500/ : /TOTAL SCANS:\s*1500/);
    if (chinese) assert.doesNotMatch(completeText, /[A-Za-z]/, '扫描完成面板仍含英文');
    await page.waitForTimeout(1500); // Let the original total-count entrance animation finish.
    await page.screenshot({ path: `reports/${locale}-scan-complete.png` });
    await save.click();
    await page.getByText(chinese ? /数据集\s*1\s*已保存/ : /Dataset\s*1\s*saved/i).waitFor({ state: 'visible', timeout: 20000 });
    result.firstDatasetSaved = true;
    assert.deepEqual(errors, []);
    await context.close();
  }
  report.passed = true;
} catch (error) {
  report.passed = false;
  report.error = error.message;
  report.body = await activePage?.locator('body').innerText().catch(() => '');
  await activePage?.screenshot({ path: 'reports/scan-localization-failure.png' }).catch(() => {});
  process.exitCode = 1;
} finally {
  fs.writeFileSync('reports/scan-localization.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
  await browser.close();
}
