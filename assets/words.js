import { $, header, load, esc, getJSON, shuffle } from './common.js';
import { quiz } from './quiz.js';
import { clock } from './numbers-data.js';

header();
const st = load('words-set', { module: 'time', dir: 'ar-en' });
const { words: WORDS } = await getJSON('data/words.json');

// Round times only (on the hour, half past, quarters), every hour of the day.
const TIMES = Array.from({ length: 24 }, (_, h) => [0, 30, 15, 45].map(m => ({ m, ...clock(h, m) }))).flat();

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
    n: 1, title: 'Today, yesterday, tomorrow', sub: 'l-yum, l-bare7, ghedda, daba, dima, imta...',
    intro: '<p>Time words do not change: <strong>l-yum</strong> today, <strong>l-bare7</strong> yesterday, <strong>ghedda</strong> tomorrow, <strong>daba</strong> now. Put them at the end of the sentence: mchit l-bare7, I went yesterday. The past or future comes from the verb, not from the time word.</p>',
    ...make('time'),
  },
  calendar: {
    n: 2, title: 'Week, month, year', sub: 's-semmana, ch-chher, l-3am, l-khmis, had l-3am...',
    intro: '<p>This is <strong>had</strong> plus the noun with <strong>the</strong>: had s-semmana, this week. Next and last follow the noun after it: <strong>jay / jaya</strong> for next and <strong>lli fat / lli fatet</strong> for last. Feminine nouns (semmana) take the -a and -et forms: s-semmana jaya, s-semmana lli fatet. Masculine ones (chher, 3am) do not: ch-chher jay.</p><p>The days are used with the article: l-khmis, j-jem3a. Add <strong>nhar</strong> if you want to be clear: nhar l-khmis.</p>',
    ...make('calendar'),
  },
  direction: {
    n: 3, title: 'Left, right, north, south', sub: 'limen, liser, nichan, chmal, hna, tmma...',
    intro: '<p>To a place, use <strong>3la</strong>: 3la limen to the right, 3la liser to the left. Straight on is <strong>nichan</strong>. A few short commands cover most directions: dewer 3la limen, mchi nichan, 7bes hna.</p><p>The compass words are <strong>chmal</strong>, <strong>janub</strong>, <strong>charq</strong> and <strong>gharb</strong>. People mostly use left and right in the street.</p>',
    ...make('direction'),
  },
  clock: {
    n: 4, title: 'Telling the time', sub: 's-sa3a juj, tlata w nus, setta ila rub3, z-zwal...',
    intro: '<p>The hour comes after <strong>s-sa3a</strong> (the hour): s-sa3a tlata, three o\'clock. Add <strong>w nus</strong> for half past, <strong>w rub3</strong> for a quarter past, and <strong>ila rub3</strong> for a quarter to the next hour: s-sa3a juj w nus, 2:30; s-sa3a tlata ila rub3, 2:45. One o\'clock is feminine, <strong>wa7da</strong>. To say am or pm, add <strong>d s-sba7</strong> (morning), <strong>d z-zwal</strong> (early afternoon), <strong>d l-3chiya</strong> (late afternoon and evening) or <strong>d l-lil</strong> (night). Noon is <strong>z-zwal</strong> and midnight is <strong>nus l-lil</strong>.</p>',
    pool: () => TIMES.flatMap(t => ['ar-en', 'en-ar'].filter(d => st.dir === 'both' || st.dir === d).map(d => ({ t, d, key: 'clock|' + t.en + '|' + d }))),
    render: ({ t, d }) => {
      const toAr = d === 'en-ar';
      // Same minutes first: the hour and the part of the day are what the learner has to tell apart.
      const near = TIMES.filter(o => o.en !== t.en);
      const others = [...shuffle(near.filter(o => o.m === t.m)), ...shuffle(near.filter(o => o.m !== t.m))].slice(0, 6);
      return {
        chip: (toAr ? 'English → Darija' : 'Darija → English') + ' · time',
        word: toAr ? null : { lat: t.lat, ar: t.ar },
        wordHtml: toAr ? '<span class="lat">' + esc(t.en) + '</span>' : undefined,
        small: true,
        ask: { lat: '' },
        plain: !toAr,
        answer: toAr ? { lat: t.lat, ar: t.ar } : { lat: t.en, ar: '' },
        options: others.map(o => (toAr ? { lat: o.lat, ar: o.ar } : { lat: o.en, ar: '' })),
      };
    },
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
