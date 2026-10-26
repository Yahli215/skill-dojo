// Background service worker — fetches presence data from localhost.
// Chrome extensions bypass Private Network Access restrictions, so this works
// even though the Skill Dojo page itself (github.io) cannot fetch from localhost.
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action !== 'getPresence') return;
  fetch('http://127.0.0.1:8765/presence', { cache: 'no-store' })
    .then(r => r.json())
    .then(data => sendResponse({ ok: true, data }))
    .catch(() => sendResponse({ ok: false }));
  return true; // keeps channel open for async sendResponse
});
