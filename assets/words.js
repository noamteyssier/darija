import { $, header, load, esc, getJSON, shuffle } from './common.js';
import { quiz } from './quiz.js';

header();
const st = load('words-set', { module: 'time', dir: 'ar-en' });
const { words: WORDS } = await getJSON('data/words.json');

const BY = g => WORDS.filter(w => w.group === g);
const first = en => en.split(' / ')[0];
const exHtml = w => (w.ex ? '<div class="ex"><strong>Example:</strong> ' + esc(w.ex.lat) + ' <em>(' + esc(w.ex.en) + ')</em></div>' : '');

// Each word is asked both ways: Darija to English, and English to Darija.
function make(group) {
  const words = BY(group);
  return {
    pool: () => words.flatMap(w => ['ar-en', 'en-ar'].filter(d => st.dir === 'both' || st.dir === d).map(d => ({ w, d, key: w.id + '|' + d }))),
    render: ({ w, d }) => {
      const toAr = d === 'en-ar';
      // Same kind first (a phrase is not offered next to a one-word answer), never the same meaning.
      const near = words.filter(o => o.id !== w.id && o.en !== w.en);
      const same = shuffle(near.filter(o => o.kind === w.kind)), rest = shuffle(near.filter(o => o.kind !== w.kind));
      const others = [...same, ...rest].slice(0, 6);
      return {
        chip: (toAr ? 'English → Darija' : 'Darija → English') + (w.kind === 'phrase' ? ' · phrase' : ''),
        word: toAr ? null : { lat: w.lat, ar: w.ar },
        wordHtml: toAr ? '<span class="lat">' + esc(w.en) + '</span>' : undefined,
        small: toAr || w.kind === 'phrase',
        ask: { lat: '' },
        plain: !toAr,
        answer: toAr ? { lat: w.lat, ar: w.ar } : { lat: w.en, ar: '' },
        options: others.map(o => (toAr ? { lat: o.lat, ar: o.ar } : { lat: o.en, ar: '' })),
        whyHtml: esc(w.note || '') + exHtml(w),
      };
    },
  };
}

const MODULES = {
  time: {
    n: 1, title: 'Today, yesterday, tomorrow', sub: 'lyum, lbare7, ghedda, daba, dima, imta...',
    intro: '<p>Time words do not change: <strong>lyum</strong> today, <strong>lbare7</strong> yesterday, <strong>ghedda</strong> tomorrow, <strong>daba</strong> now. Put them first in the sentence: lbare7 mshit, yesterday I went. The past or future comes from the verb, not from the time word.</p>',
    ...make('time'),
  },
  calendar: {
    n: 2, title: 'Week, month, year', sub: 's-semmana, sh-shher, l-3am, l-khmis, had l-3am...',
    intro: '<p>This is <strong>had</strong> plus the noun with <strong>the</strong>: had s-semmana, this week. Next and last follow the noun after it: <strong>jay / jaya</strong> for next and <strong>lli fat / lli fatet</strong> for last. Feminine nouns (semmana) take the -a and -et forms: s-semmana jaya, s-semmana lli fatet. Masculine ones (shher, 3am) do not: sh-shher jay.</p><p>The days are used with the article: l-khmis, j-jem3a. Add <strong>nhar</strong> if you want to be clear: nhar l-khmis.</p>',
    ...make('calendar'),
  },
  direction: {
    n: 3, title: 'Left, right, north, south', sub: 'limen, liser, nishan, shmal, hna, temma...',
    intro: '<p>To a place, use <strong>3la</strong>: 3la limen to the right, 3la liser to the left. Straight on is <strong>nishan</strong>. A few short commands cover most directions: dwer 3la limen, mshi nishan, 7bes hna.</p><p>The compass words are <strong>shmal</strong>, <strong>janub</strong>, <strong>sharq</strong> and <strong>gharb</strong>. People mostly use left and right in the street.</p>',
    ...make('direction'),
  },
};

let q = null, cache = null;
function progress(id) {
  const saved = load('words-' + id, { weights: {} });
  const items = MODULES[id].pool();
  const learned = items.filter(c => saved.weights[c.key] < 1).length;
  return Math.round(100 * learned / items.length);
}
function drawModules() {
  $('modules').innerHTML = Object.entries(MODULES).map(([id, m]) =>
    '<button type="button" class="module" data-id="' + id + '" aria-pressed="' + (st.module === id) + '"><span class="n">' + m.n + '</span><span class="t"><b>' + esc(m.title) + '</b><span>' + esc(m.sub) + '</span></span><span class="pct">' + progress(id) + '%</span></button>').join('');
  $('modules').querySelectorAll('.module').forEach(b => b.addEventListener('click', () => { st.module = b.dataset.id; st.save(); start(); }));
}
function drawDir() {
  $('dir').querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.val === st.dir)));
}
function start() {
  const m = MODULES[st.module] || MODULES.time;
  drawModules();
  drawDir();
  $('introText').innerHTML = m.intro + '<p class="note">These words are not from the Peace Corps book. Check them with a speaker.</p>';
  cache = null;
  q = quiz($('quiz'), {
    name: 'words-' + st.module,
    pool: () => (cache ||= m.pool()),
    render: m.render,
  });
  q.next();
}
$('dir').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { st.dir = b.dataset.val; st.save(); start(); }));
start();
