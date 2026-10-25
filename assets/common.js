// Shared helpers for every page: header, saved state, script display, answer matching.

export const PRON = [
  { lat: 'ana', ar: 'أنا', en: 'I' },
  { lat: 'nta', ar: 'نتا', en: 'you (m.)' },
  { lat: 'nti', ar: 'نتي', en: 'you (f.)' },
  { lat: 'huwa', ar: 'هو', en: 'he' },
  { lat: 'hiya', ar: 'هي', en: 'she' },
  { lat: '7na', ar: 'حنا', en: 'we' },
  { lat: 'ntuma', ar: 'نتوما', en: 'you (pl.)' },
  { lat: 'huma', ar: 'هوما', en: 'they' },
];

// Possessive endings have one "your" for nta and nti.
export const OWNER = [
  { lat: 'ana', ar: 'أنا', en: 'my' },
  { lat: 'nta / nti', ar: 'نتا / نتي', en: 'your' },
  { lat: 'huwa', ar: 'هو', en: 'his' },
  { lat: 'hiya', ar: 'هي', en: 'her' },
  { lat: '7na', ar: 'حنا', en: 'our' },
  { lat: 'ntuma', ar: 'نتوما', en: 'your (pl.)' },
  { lat: 'huma', ar: 'هوما', en: 'their' },
];

export function $(id) { return document.getElementById(id); }

export function load(name, defaults) {
  const key = 'darija:' + name;
  let data = structuredClone(defaults);
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const p = JSON.parse(raw);
      if (p && typeof p === 'object') data = Object.assign(data, p);
    }
  } catch (e) { /* private mode or blocked storage: start fresh */ }
  data.save = () => {
    try { localStorage.setItem(key, JSON.stringify(data)); } catch (e) { /* ignore */ }
  };
  return data;
}

// Display preference shared by all pages.
export const prefs = load('prefs', { script: 'both', mode: 'choose', stars: [] });

export function esc(s) {
  return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

export function disp(lat, ar, script = prefs.script) {
  const L = '<span class="lat">' + esc(lat) + '</span>';
  const A = '<span class="ar" lang="ar" dir="rtl">' + esc(ar) + '</span>';
  return script === 'latin' ? L : script === 'arabic' ? A : L + A;
}
export function both(lat, ar) { return disp(lat, ar, 'both'); }

// Answer matching ignores schwa (e), doubled letters, hyphens, apostrophes and spaces,
// and accepts the book's letters (š x ġ ع н) alongside arabizi.
export function norm(s) {
  return String(s).toLowerCase().normalize('NFC')
    .replace(/š/g, 'sh').replace(/x/g, 'kh').replace(/ġ/g, 'gh').replace(/[нḥ]/g, '7')
    .replace(/ع(?=[a-z])/g, '3').replace(/(?<=[a-z0-9])ع/g, '3')
    .normalize('NFD').replace(/[̀-ًͯ-ٰٟ]/g, '')
    .replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ا').replace(/ڭ|گ/g, 'ك')
    .replace(/ch/g, 'sh').replace(/ou/g, 'u').replace(/9/g, 'q')
    .replace(/e/g, '')
    .replace(/[^a-z0-9؀-ۿ]/g, '')
    .replace(/(.)\1+/g, '$1');
}

export function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const cache = {};
export function getJSON(path) {
  cache[path] ||= fetch(path).then(r => {
    if (!r.ok) throw new Error(path + ': ' + r.status);
    return r.json();
  });
  return cache[path];
}

const PAGES = [
  ['verbs.html', 'Verbs'],
  ['match.html', 'Match'],
  ['nouns.html', 'Nouns'],
  ['dictionary.html', 'Dictionary'],
  ['rules.html', 'Rules'],
];
const LOGO = '<svg width="34" height="34" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="22" height="22"/><rect x="9" y="9" width="22" height="22" transform="rotate(45 20 20)"/><circle cx="20" cy="20" r="3.2" fill="currentColor" stroke="none"/></svg>';

export function header() {
  const here = location.pathname.split('/').pop() || 'index.html';
  const el = $('top');
  el.className = 'top';
  el.innerHTML = '<a class="brand" href="./">' + LOGO + '<h1>Darija Drills</h1></a>'
    + '<nav class="tabs" aria-label="Pages">'
    + PAGES.map(([href, name]) => '<a href="' + href + '"' + (href === here ? ' aria-current="page"' : '') + '>' + name + '</a>').join('')
    + '</nav>';
}

// Segmented buttons: <div class="seg" data-group="x"><button data-val="...">
export function bindSeg(root, state, onChange) {
  root.querySelectorAll('.seg[data-group]').forEach(g => {
    const k = g.dataset.group;
    const sync = () => g.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.val === state[k])));
    g.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
      state[k] = b.dataset.val;
      sync();
      onChange(k);
    }));
    sync();
  });
}

export function scriptSeg() {
  return '<div class="seg" role="group" aria-label="Script" data-group="script">'
    + '<button type="button" data-val="latin">Latin</button>'
    + '<button type="button" data-val="arabic">عربي</button>'
    + '<button type="button" data-val="both">Both</button></div>';
}

export function toggleStar(id) {
  const i = prefs.stars.indexOf(id);
  if (i >= 0) prefs.stars.splice(i, 1); else prefs.stars.push(id);
  prefs.save();
  return i < 0;
}
