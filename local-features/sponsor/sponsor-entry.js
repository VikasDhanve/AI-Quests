// A failed or invalid configuration hides this optional feature only.
async function startSponsor() {
  let settings;
  try {
    const response = await fetch('/ai-quests/site-config.json', { cache: 'no-store' });
    if (!response.ok) return;
    settings = await response.json();
  } catch {
    return;
  }
  if (settings?.showSponsor === true) await import('./sponsor.js');
}

startSponsor();
