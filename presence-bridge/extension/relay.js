// Content script — runs on yahli215.github.io at document_start (before page JS).
// Injects a fetch override into the page so calls to 127.0.0.1:8765 are
// transparently routed through the extension background worker.
(function () {
  const s = document.createElement('script');
  s.textContent = `
(function () {
  const _orig = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    if (typeof url === 'string' && /127\\.0\\.0\\.1:8765/.test(url)) {
      return new Promise((resolve, reject) => {
        const id = Math.random().toString(36).slice(2);
        function h(e) {
          if (!e.data || e.data.type !== '__SDPRES_RES__' || e.data.id !== id) return;
          window.removeEventListener('message', h);
          if (e.data.ok) {
            resolve(new Response(JSON.stringify(e.data.data), {
              status: 200,
              headers: { 'Content-Type': 'application/json' }
            }));
          } else {
            reject(new TypeError('Presence bridge unavailable'));
          }
        }
        window.addEventListener('message', h);
        window.postMessage({ type: '__SDPRES_REQ__', id }, '*');
        // Safety timeout — if no response in 5s, reject
        setTimeout(() => {
          window.removeEventListener('message', h);
          reject(new TypeError('Presence bridge timeout'));
        }, 5000);
      });
    }
    return _orig(url, opts);
  };
})();
  `;
  (document.head || document.documentElement).prepend(s);
  s.remove();

  // Forward intercepted fetch requests to the background service worker
  window.addEventListener('message', e => {
    if (!e.data || e.data.type !== '__SDPRES_REQ__') return;
    const id = e.data.id;
    chrome.runtime.sendMessage({ action: 'getPresence' }, resp => {
      window.postMessage(
        { type: '__SDPRES_RES__', id, ...(resp || { ok: false }) },
        '*'
      );
    });
  });
})();
