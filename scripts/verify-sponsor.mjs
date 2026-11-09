import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true,
  executablePath: 'C:/Users/yamal/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe',
  args: ['--enable-unsafe-swiftshader'] });
const report = { failures: [], errors: [], external: [] };
fs.mkdirSync('.impeccable/review', { recursive: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  await page.route('**/*', route => {
    const url = route.request().url();
    if (!url.startsWith('http') || new URL(url).hostname === '127.0.0.1') return route.continue();
    report.external.push(url);
    return route.abort('internetdisconnected');
  });
  page.on('response', r => { if (r.status() >= 400) report.failures.push(r.url()); });
  page.on('pageerror', e => report.errors.push(e.message));
  await page.goto('http://127.0.0.1:4192/ai-quests/intl/zh_cn');
  await page.getByRole('button', { name: '接受任务', exact: true }).waitFor({ timeout: 25000 });
  await page.waitForTimeout(3500);
  const trigger = page.getByRole('button', { name: '赞助支持', exact: true });
  assert.equal(await trigger.count(), 1, '首页应提供赞助支持按钮');
  const sound = await page.getByRole('button', { name: '开关声音', exact: true }).boundingBox();
  const support = await trigger.boundingBox();
  assert.ok(support.y > sound.y + sound.height && Math.abs(support.x - sound.x) < 2);
  await trigger.click();
  const dialog = page.getByRole('dialog', { name: '为 AI 探索加点能量', exact: true });
  assert.ok(await dialog.isVisible());
  const copy = dialog.locator('.aiq-support__copy');
  assert.equal(await copy.locator('.aiq-support__credit').innerText(), 'AI Quests 是 Google Research 与斯坦福大学学习促进中心共同推出的面向中学生（11-14岁）的AI游戏化学习体验。');
  assert.ok((await copy.innerText()).includes('网站为国内镜像站点，持续更新，站点始终免费开放，不以盈利为目的。能力范围内可赞助一下带宽。'));
  const brandBox = await copy.getByText('AI Quests', { exact: true }).boundingBox();
  const stanfordBox = await copy.getByText('斯坦福大学学习促进中心', { exact: true }).boundingBox();
  assert.ok(Math.abs(brandBox.y - stanfordBox.y) < 2, '桌面介绍中的官方名称应连续排列在同一行');
  assert.equal((await copy.innerText()).includes('个人维护仍需要承担服务器'), false);
  const official = dialog.getByRole('link', { name: 'AI Quests 官方站点（新窗口打开）', exact: true });
  assert.equal(await official.getAttribute('href'), 'https://research.google/ai-quests');
  assert.equal(await official.getAttribute('target'), '_blank');
  assert.match(await official.getAttribute('rel'), /noopener/);
  assert.match(await official.getAttribute('rel'), /noreferrer/);
  assert.equal(await dialog.getByRole('radio', { checked: true }).inputValue(), '19.9');
  await dialog.getByRole('img').evaluate(img => img.decode());
  await page.screenshot({ path: '.impeccable/review/desktop.png' });
  for (const amount of ['9.9', '19.9', '29.9']) {
    await dialog.getByText(`¥${amount}`, { exact: true }).click();
    assert.equal(await dialog.getByRole('radio', { checked: true }).inputValue(), amount);
    const image = dialog.getByRole('img', { name: `支付宝 ¥${amount} 赞助二维码`, exact: true });
    await image.evaluate(img => img.decode());
    const url = await image.getAttribute('src');
    const response = await fetch(new URL(url, page.url()));
    assert.equal(response.status, 200);
    const actual = crypto.createHash('sha256').update(Buffer.from(await response.arrayBuffer())).digest('hex');
    const original = crypto.createHash('sha256').update(fs.readFileSync(`local-features/sponsor/alipay-${amount}.jpg`)).digest('hex');
    assert.equal(actual, original, `¥${amount}必须对应用户提供的原图`);
    if (amount !== '19.9') await dialog.screenshot({ path: `.impeccable/review/amount-${amount}.png` });
  }
  await dialog.getByText('¥19.9', { exact: true }).click();
  await dialog.getByRole('radio', { checked: true }).focus();
  await page.keyboard.press('ArrowRight');
  assert.equal(await dialog.getByRole('radio', { checked: true }).inputValue(), '29.9');
  await page.keyboard.press('Tab');
  assert.ok(await official.evaluate(el => el === document.activeElement), '官方站点链接应可通过Tab访问');
  for (let n = 0; n < 5; n++) {
    await page.keyboard.press('Tab');
    assert.ok(await dialog.evaluate(el => el.contains(document.activeElement)), '键盘焦点不能离开弹窗');
  }
  await dialog.getByText('¥19.9', { exact: true }).click();
  report.viewports = [];
  for (const width of [1024, 375]) {
    await page.setViewportSize({ width, height: width === 375 ? 812 : 768 });
    await page.waitForTimeout(450);
    assert.ok(await dialog.isVisible(), '调整窗口后弹窗应保持可见');
    for (const name of ['Google Research', '斯坦福大学学习促进中心']) {
      assert.equal(await dialog.getByText(name, { exact: true }).evaluate(el => el.getClientRects().length), 1, '官方机构名称不得拆行');
    }
    assert.ok(await dialog.evaluate(el => el.scrollWidth <= el.clientWidth + 1), '弹窗不得横向溢出');
    const box = await dialog.boundingBox();
    assert.ok(box.x >= 0 && box.x + box.width <= width + 1);
    await page.screenshot({ path: `.impeccable/review/${width === 375 ? 'mobile' : 'tablet'}.png` });
    if (width === 375) {
      await dialog.getByText('完全自愿 · 不影响免费使用', { exact: true }).scrollIntoViewIfNeeded();
      await page.screenshot({ path: '.impeccable/review/mobile-bottom.png' });
    }
    report.viewports.push(width);
  }
  await page.setViewportSize({ width: 1440, height: 960 });
  await page.waitForTimeout(450);
  await page.keyboard.press('Escape');
  assert.equal(await dialog.isVisible(), false);
  assert.ok(await trigger.evaluate(el => el === document.activeElement));
  await page.screenshot({ path: '.impeccable/review/home.png' });
  await trigger.click();
  await dialog.getByRole('button', { name: '关闭赞助窗口', exact: true }).click();
  assert.equal(await dialog.isVisible(), false);
  await trigger.click();
  await page.mouse.click(5, 5);
  assert.equal(await dialog.isVisible(), false);
  // A fresh context avoids previously decoded image data masking a network failure.
  const errorPage = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  await errorPage.route('**/local-support/alipay-9.9.jpg', route => route.abort('failed'));
  await errorPage.goto('http://127.0.0.1:4192/ai-quests/intl/zh_cn');
  await errorPage.getByRole('button', { name: '赞助支持', exact: true }).click();
  const errorDialog = errorPage.getByRole('dialog');
  await errorDialog.getByText('¥9.9', { exact: true }).click();
  await errorDialog.getByRole('status').waitFor({ state: 'visible', timeout: 10000 });
  await errorDialog.screenshot({ path: '.impeccable/review/image-error.png' });
  await errorDialog.getByText('¥19.9', { exact: true }).click();
  await errorDialog.getByRole('img').evaluate(img => img.decode());
  assert.equal(await errorDialog.getByRole('status').isVisible(), false);
  report.imageFailureRecovery = true;
  await errorPage.close();
  const state = await page.evaluate(() => JSON.stringify(localStorage));
  await trigger.click();
  await page.keyboard.press('Escape');
  assert.equal(await page.evaluate(() => JSON.stringify(localStorage)), state, '赞助不改写游戏进度');
  await page.goto('http://127.0.0.1:4192/ai-quests/intl/zh_cn/quest/market-marshes');
  await page.waitForURL(/\/quest\//, { timeout: 20000 });
  assert.equal(await trigger.count(), 0, '进入关卡后不显示首页赞助入口');
  for (const route of ['en_us', 'zh_cn/teacher-resources']) {
    const other = await browser.newPage();
    await other.goto('http://127.0.0.1:4192/ai-quests/intl/' + route);
    assert.equal(await other.locator('script[src*="local-support"]').count(), 0);
    assert.equal(await other.getByRole('button', { name: '赞助支持', exact: true }).count(), 0);
    await other.close();
  }
  assert.deepEqual(report.failures, []);
  assert.deepEqual(report.errors, []);
  assert.deepEqual(report.external, []);
  report.passed = true;
} catch (error) {
  report.passed = false;
  report.error = error.stack;
  process.exitCode = 1;
} finally {
  fs.writeFileSync('reports/sponsor-validation.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
  await browser.close();
}
