// Offline cache. Everything same-origin is served from cache and refreshed in the background,
// so a deploy shows up on the next launch. Bump CACHE only to drop old entries (renamed or removed files).
const CACHE = 'darija-v3';
const CORE = [
  './', 'index.html', 'verbs.html', 'match.html', 'nouns.html', 'prepositions.html', 'numbers.html',
  'words.html', 'questions.html', 'sentences.html', 'dictionary.html', 'rules.html', 'manifest.webmanifest', 'content/about.md', 'content/install.md',
  'assets/style.css', 'assets/common.js', 'assets/quiz.js', 'assets/verbs-data.js', 'assets/numbers-data.js',
  'assets/verbs.js', 'assets/match.js', 'assets/nouns.js', 'assets/prepositions.js', 'assets/numbers.js',
  'assets/words.js', 'assets/questions.js', 'assets/sentences.js', 'assets/dictionary.js', 'assets/rules.js',
  'assets/icons/icon-192.png', 'assets/icons/apple-touch-icon.png',
  'data/verbs.json', 'data/nouns.json', 'data/prepositions.json', 'data/words.json', 'data/questions.json', 'data/spelling.json', 'data/examples.json',
];
const FONTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || !(url.origin === location.origin || FONTS.includes(url.hostname))) return;
  e.respondWith(caches.open(CACHE).then(async cache => {
    const hit = await cache.match(req, { ignoreSearch: true });
    const fresh = fetch(req).then(res => {
      if (res.ok || res.type === 'opaque') cache.put(req, res.clone());
      return res;
    });
    if (hit) { fresh.catch(() => {}); return hit; }
    return fresh;
  }));
});
