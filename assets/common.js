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

// Ids renamed since progress was saved, old -> new. Add a line per rename (collocations use the whole key).
const RENAMED = {
  // verbs
  'shreb': 'chreb',
  'shref': 'chref',
  'neshshet': 'nechchet',
  'shedd': 'chedd',
  'tshetter': 'tchetter',
  'mshet': 'mchet',
  'shra': 'chra',
  'nqesh': 'nqech',
  'gheshsh': 'ghechch',
  'shmet': 'chmet',
  'shre7': 'chre7',
  'tshekka': 'tchekka',
  'tshawer': 'tchawer',
  'khsha': 'khcha',
  'shte7': 'chte7',
  't3eshsha': 't3echcha',
  'ktashef': 'ktachef',
  'naqesh': 'naqech',
  'sherreb': 'cherreb',
  'nshef': 'nchef',
  'neshshef': 'nechchef',
  '7eshshem': '7echchem',
  '7shem': '7chem',
  'shejje3': 'chejje3',
  'shbe3': 'chbe3',
  'nshet': 'nchet',
  'msha': 'mcha',
  'shwa': 'chwa',
  'nsher': 'ncher',
  'sherref': 'cherref',
  'shedd-2': 'chedd-2',
  'fettesh': 'fettech',
  'hemmesh': 'hemmech',
  'shat': 'chat',
  'sh3el': 'ch3el',
  'shaf': 'chaf',
  'tshabeh': 'tchabeh',
  'shbeh': 'chbeh',
  'rshem': 'rchem',
  'reshshe7': 'rechche7',
  'sharek': 'charek',
  'qeshsher': 'qechcher',
  'tqeshsher': 'tqechcher',
  'riyesh': 'riyech',
  'shellel': 'chellel',
  'tshawef': 'tchawef',
  'duwesh': 'duwech',
  'terresh': 'terrech',
  'shemm': 'chemm',
  'reshsh': 'rechch',
  'feshshesh': 'fechchech',
  "s'her": 'sher',
  'sheffer': 'cheffer',
  'tmeshsha': 'tmechcha',
  'tshemmesh': 'tchemmech',
  '3ash': '3ach',
  'shetteb': 'chetteb',
  'qeshsheb': 'qechcheb',
  'shiyer': 'chiyer',
  'shhed': 'chhed',
  'teshten': 'techten',
  // nouns and adjectives
  'wjjeh': 'wjeh',
  'fumm': 'fum',
  'khedma': 'khdma',
  'sh3er': 'ch3er',
  'kersh': 'kerch',
  'tebla': 'tbla',
  'tebsil': 'tbsil',
  'tlfaza': 'telfaza',
  'medrasa': 'mdrasa',
  'meshsh': 'mechch',
  'shher': 'chher', // also a word
  'shems': 'chems',
  'sukkar': 'sukar',
  'shurba': 'churba',
  'sandwish': 'sandwich',
  '3sha': '3cha',
  'matisha': 'maticha',
  'furshita': 'furchita',
  'salun': 'salon',
  'shebbak': 'chebbak',
  'meshghul': 'mchghul',
  // words
  'b3d-ghda': 'b3d-ghedda',
  'men-b3d': 'mn-b3d',
  'bekri': 'bkri',
  'l-3shiya': 'l-3chiya',
  'sh-shta': 'ch-chta',
  'had-sh-shher': 'had-ch-chher',
  'sh-shher-jay': 'ch-chher-jay',
  'sh-shher-lli-fat': 'ch-chher-lli-fat',
  'nishan': 'nichan',
  'shmal': 'chmal',
  'sharq': 'charq',
  'temma': 'tmma',
  'tma': 'tmma',
  'dwer-3la-limen': 'dewer-3la-limen',
  'dwer-3la-liser': 'dewer-3la-liser',
  'mshi-nishan': 'mchi-nichan',
  // collocations
  'c|2|d7k|3la': 'c|2|de7k|3la',
  'c|3|d7k|m3a': 'c|3|de7k|m3a',
  'c|8|khaf|men': 'c|8|khaf|mn',
  'c|9|thlla|f': 'c|9|thla|f',
  'c|21|shark|f': 'c|21|chark|f',
  'c|30|tleb|men': 'c|30|tleb|mn',
};

// Saved weights are keyed by drill keys that embed ids ('mine|khu|0', 'shaf|pres|1'); stars hold bare ids.
function renameKey(k) {
  return RENAMED[k] ?? k.split('|').map(s => RENAMED[s] ?? s).join('|');
}

function migrate(p) {
  if (Array.isArray(p.stars)) p.stars = [...new Set(p.stars.map(id => RENAMED[id] ?? id))];
  if (p.weights && typeof p.weights === 'object') {
    const w = {};
    for (const k of Object.keys(p.weights)) { const n = renameKey(k); if (!(n in p.weights) || n === k) w[n] = p.weights[k]; }
    p.weights = w;
  }
}

export function load(name, defaults) {
  const key = 'darija:' + name;
  let data = structuredClone(defaults);
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const p = JSON.parse(raw);
      if (p && typeof p === 'object') { migrate(p); data = Object.assign(data, p); }
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
  ['prepositions.html', 'Prepositions'],
  ['numbers.html', 'Numbers'],
  ['words.html', 'Time &amp; place'],
  ['vocab.html', 'Vocabulary'],
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
  const cur = el.querySelector('nav.tabs a[aria-current="page"]');
  if (cur && cur.offsetLeft > 0) {
    const nav = el.querySelector('nav.tabs');
    nav.scrollLeft = cur.offsetLeft - (nav.clientWidth - cur.clientWidth) / 2;
  }
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
