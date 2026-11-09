// Local, voluntary support for the Chinese adaptation; no payment API or tracking.
const homeRoute = /^\/ai-quests\/intl\/zh_cn(?:\/index\.html)?\/?$/;
const assetBase = '/ai-quests/local-support/';
const heart = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.8 4.6a5.4 5.4 0 0 0-7.6 0L12 5.8l-1.2-1.2a5.4 5.4 0 0 0-7.6 7.6L12 21l8.8-8.8a5.4 5.4 0 0 0 0-7.6Z"/></svg>';
const template = document.createElement('template');
// The template contains only authored constants, never URL, storage or form data.
template.innerHTML = `
<dialog id="aiq-support-dialog" class="aiq-support" aria-labelledby="aiq-support-title" aria-describedby="aiq-support-subtitle">
  <button type="button" class="aiq-support__close" aria-label="关闭赞助窗口" autofocus>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>
  </button>
  <header class="aiq-support__header">
    <h2 id="aiq-support-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 4c3-2 7-2 7-2s0 4-2 7l-6 6-5-5 6-6Z"/><circle cx="15.5" cy="6.5" r="1.5"/><path d="m7 10-4 1-1 5 5-1m5 0-1 5 5-1 1-4M7 17l-3 3m4-1-1 2m-2-5-2 1"/></svg>为 AI 探索加点能量</h2>
    <p id="aiq-support-subtitle">让更多孩子轻松接触 AI，让每一份好奇心都有机会被点亮。</p>
  </header>
  <fieldset class="aiq-support__amounts">
    <legend class="aiq-support__sr-only">选择赞助金额</legend>
    <label class="aiq-support__amount">
      <input type="radio" name="support-amount" value="9.9">
      ${heart}<span class="aiq-support__price">¥9.9</span><span>一份鼓励</span>
    </label>
    <label class="aiq-support__amount">
      <input type="radio" name="support-amount" value="19.9" checked>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m13 2-9 12h7l-1 8 10-13h-8l1-7Z"/></svg>
      <span class="aiq-support__price">¥19.9</span><span>加点能量</span>
    </label>
    <label class="aiq-support__amount">
      <input type="radio" name="support-amount" value="29.9">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 11h16v10H4zM3 7h18v4H3zM12 7v14"/><path d="M12 7H8a3 3 0 1 1 3-3l1 3Zm0 0h4a3 3 0 1 0-3-3l-1 3Z"/></svg>
      <span class="aiq-support__price">¥29.9</span><span>大力支持</span>
    </label>
  </fieldset>
  <div class="aiq-support__content">
    <figure class="aiq-support__payment">
      <img class="aiq-support__qr" src="${assetBase}alipay-19.9.jpg" alt="支付宝 ¥19.9 赞助二维码" width="1139" height="1139">
      <p class="aiq-support__image-status" role="status" hidden>二维码暂时无法显示，请刷新后再试。</p>
      <figcaption><strong class="aiq-support__payment-label">支付宝 ¥19.9</strong><span>扫码自愿支持</span></figcaption>
    </figure>
    <div class="aiq-support__copy">
      <p class="aiq-support__credit"><strong class="aiq-support__brand">AI Quests</strong> 是 <strong class="aiq-support__source">Google Research</strong> 与<strong class="aiq-support__source">斯坦福大学学习促进中心</strong>共同推出的面向中学生（11-14岁）的AI游戏化学习体验。</p>
      <p>本站进行了中文化与适配，希望让国内的孩子也能轻松接触这些优质内容。</p>
      <p>希望小朋友们能在探索和互动中激发好奇心、培养创造力，发现人工智能带来的更多可能。</p>
      <p>网站为国内镜像站点，持续更新，站点<strong class="aiq-support__free">始终免费开放，不以盈利为目的</strong>。能力范围内可赞助一下带宽。</p>
      <p>如果这些内容对你或孩子有所帮助，欢迎自愿支持一点维护费用，让这份小小的分享能够陪伴更多孩子的 AI 探索。</p>
      <p class="aiq-support__promise">赞助完全自愿，不赞助也没关系。希望每一份好奇心都能被点亮，每一个孩子都能快乐探索 AI 的世界！</p>
      <p class="aiq-support__official">官方站点：<a href="https://research.google/ai-quests" target="_blank" rel="noopener noreferrer" aria-label="AI Quests 官方站点（新窗口打开）">https://research.google/ai-quests</a></p>
    </div>
  </div>
  <p class="aiq-support__footer">完全自愿 · 不影响免费使用 ${heart}</p>
</dialog>`;

const dialog = template.content.querySelector('dialog');
const trigger = document.createElement('button');
trigger.type = 'button';
trigger.className = 'aiq-support-trigger';
trigger.setAttribute('aria-label', '赞助支持');
trigger.setAttribute('aria-haspopup', 'dialog');
trigger.setAttribute('aria-controls', dialog.id);
trigger.setAttribute('aria-expanded', 'false');
trigger.title = '赞助支持';
trigger.innerHTML = `${heart}<span>赞助</span>`;

const qr = dialog.querySelector('.aiq-support__qr');
const status = dialog.querySelector('.aiq-support__image-status');
trigger.addEventListener('click', () => {
  dialog.showModal();
  dialog.scrollTop = 0;
  trigger.setAttribute('aria-expanded', 'true');
  document.documentElement.classList.add('aiq-support-open');
});
dialog.querySelector('.aiq-support__close').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => {
  document.documentElement.classList.remove('aiq-support-open');
  trigger.setAttribute('aria-expanded', 'false');
  if (trigger.isConnected) trigger.focus({ preventScroll: true });
});
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const rect = dialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
});
dialog.addEventListener('keydown', event => {
  event.stopPropagation();
  if (event.key !== 'Tab') return;
  const first = dialog.querySelector('.aiq-support__close');
  const last = dialog.querySelector('.aiq-support__official a');
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
});
dialog.addEventListener('change', event => {
  const amount = event.target.value;
  if (!['9.9', '19.9', '29.9'].includes(amount)) return;
  qr.hidden = false;
  status.hidden = true;
  qr.alt = `支付宝 ¥${amount} 赞助二维码`;
  dialog.querySelector('.aiq-support__payment-label').textContent = `支付宝 ¥${amount}`;
  qr.src = `${assetBase}alipay-${amount}.jpg`;
});
qr.addEventListener('error', () => { qr.hidden = true; status.hidden = false; });

function syncEntry() {
  const isHome = homeRoute.test(location.pathname);
  const sound = isHome && document.querySelector('.global-ui__mute-button');
  if (!sound) {
    trigger.remove();
    if (!isHome && dialog.open) dialog.close();
    return;
  }
  if (!dialog.isConnected) document.body.append(dialog);
  if (sound.nextElementSibling !== trigger) sound.after(trigger);
}
// Angular can replace the header when the route or viewport changes.
new MutationObserver(syncEntry).observe(document.body, { childList: true, subtree: true });
syncEntry();
