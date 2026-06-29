const CACHE     = 'grittrack-v1';
const APP_SHELL = ['/', '/static/manifest.json'];

// Install: cache the app shell
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Timer notification scheduling
let timerTimeout = null;
self.addEventListener('message', e => {
  if (!e.data) return;
  if (e.data.type === 'SCHEDULE_TIMER') {
    if (timerTimeout) { clearTimeout(timerTimeout); timerTimeout = null; }
    timerTimeout = setTimeout(() => {
      timerTimeout = null;
      self.registration.showNotification(e.data.title || 'GritTrack', {
        body: e.data.body || 'REST COMPLETE — GET BACK ON IT 💪',
        icon: '/static/icon-192.png',
        badge: '/static/icon-192.png',
        tag: 'rest-timer',
        renotify: true,
      });
    }, e.data.delay);
  } else if (e.data.type === 'CANCEL_TIMER') {
    if (timerTimeout) { clearTimeout(timerTimeout); timerTimeout = null; }
  }
});

// Fetch strategy:
//   /api/*  → network first (fresh data), fall back to offline response
//   static  → cache first, fall back to network
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  if (url.pathname.startsWith('/api/')) {
    // Network first for all API calls
    e.respondWith(
      fetch(e.request).catch(() =>
        new Response(
          JSON.stringify({ error: 'offline' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        )
      )
    );
    return;
  }

  // Cache first for everything else
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      // Cache successful GET responses
      if (e.request.method === 'GET' && res.status === 200) {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return res;
    }))
  );
});
