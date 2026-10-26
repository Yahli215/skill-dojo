// Content script — polls the presence bridge via background service worker
// and writes the result to localStorage for Skill Dojo to read.
// This bypasses Chrome's Private Network Access restriction: the page itself
// cannot fetch from 127.0.0.1, but the extension's background worker can.
(function poll() {
  chrome.runtime.sendMessage({ action: 'getPresence' }, resp => {
    if (resp && resp.ok) {
      try {
        localStorage.setItem('__sdpres__', JSON.stringify(resp.data));
      } catch (e) { /* storage full / private mode */ }
    }
    // If not ok, leave the existing localStorage value in place;
    // the page's stale-age check will eventually mark it offline.
  });
  setTimeout(poll, 9000); // slightly faster than the page's 10 s poll
})();
