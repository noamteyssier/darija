import { $, header, load, esc, getJSON, shuffle } from './common.js';
import { quiz } from './quiz.js';

header();
const st = load('questions-set', { module: 'meanings', dir: 'both' });
const { words: QW } = await getJSON('data/questions.json');
const BY = Object.fromEntries(QW.map(w => [w.id, w]));

// Sentences mark the answer as {word}. m3ach, waqtach and imta all mean when, so a word's twins ("like") are never offered as wrong options and are accepted when typed.
const blank = t => t.replace(/\{[^}]*\}/, '___');
const full = t => t.replace(/[{}]/g, '');
const twin = w => (w.like || []).flatMap(id => [BY[id].lat, BY[id].ar]);
const others = w => shuffle(QW.filter(o => o.id !== w.id && !(w.like || []).includes(o.id)));

const MODULES = {
  meanings: {
    n: 1, title: 'Meanings', sub: 'fin, m3ach, waqtach, imta, kifach, 3lach, achnu, chkun, chhal',
    intro: '<p><strong>fin</strong> where, <strong>imta</strong> / <strong>waqtach</strong> / <strong>m3ach</strong> when, <strong>kifach</strong> how, <strong>3lach</strong> why, <strong>achnu</strong> what, <strong>chkun</strong> who, <strong>chhal</strong> how much. In Darija the question word usually stays in place at the start of the sentence, and the answer does not change the word order.</p>',
    pool: () => QW.flatMap(w => ['ar-en', 'en-ar'].filter(d => st.dir === 'both' || st.dir === d).map(d => ({ w, d, key: w.id + '|' + d }))),
    render: ({ w, d }) => {
      const toAr = d === 'en-ar';
      const ex = w.s[Math.floor(Math.random() * w.s.length)];
      return {
        chip: toAr ? 'English → Darija' : 'Darija → English',
        word: toAr ? null : { lat: w.lat, ar: w.ar },
        wordHtml: toAr ? '<span class="lat">' + esc(w.en) + '</span>' : undefined,
        small: toAr,
        ask: { lat: '' },
        plain: !toAr,
        answer: toAr ? { lat: w.lat, ar: w.ar } : { lat: w.en, ar: '' },
        options: others(w).slice(0, 6).map(o => (toAr ? { lat: o.lat, ar: o.ar } : { lat: o.en, ar: '' })),
        accept: toAr ? twin(w) : [],
        whyHtml: esc(w.note) + '<div class="ex"><strong>Example:</strong> ' + esc(full(ex.lat)) + ' <em>(' + esc(ex.en) + ')</em></div>',
      };
    },
  },
  blank: {
    n: 2, title: 'Fill in the blank', sub: 'Which question word completes the sentence?',
    intro: '<p>Read the English, then pick the question word that fits the gap. Careful with <strong>achnu</strong> (what) and <strong>chkun</strong> (who), and remember that <strong>imta</strong>, <strong>waqtach</strong> and <strong>m3ach</strong> all mean when.</p>',
    pool: () => QW.flatMap(w => w.s.map((s, i) => ({ w, s, key: w.id + '|' + i }))),
    render: ({ w, s }) => ({
      chip: 'Fill in the blank',
      gloss: w.en,
      word: null,
      wordHtml: '',
      ask: { lat: blank(s.lat), ar: blank(s.ar), en: s.en, stack: true },
      answer: { lat: w.lat, ar: w.ar },
      options: others(w).slice(0, 6).map(o => ({ lat: o.lat, ar: o.ar })),
      accept: twin(w),
      whyHtml: esc(full(s.lat)) + ' <em>(' + esc(s.en) + ')</em><div class="ex">' + esc(w.note) + '</div>',
    }),
  },
};

let q = null, cache = null;
function progress(id) {
  const saved = load('questions-' + id, { weights: {} });
  const items = MODULES[id].pool();
  return Math.round(100 * items.filter(c => saved.weights[c.key] < 1).length / items.length);
}
function drawModules() {
  $('modules').innerHTML = Object.entries(MODULES).map(([id, m]) =>
    '<button type="button" class="module" data-id="' + id + '" aria-pressed="' + (st.module === id) + '"><span class="n">' + m.n + '</span><span class="t"><b>' + esc(m.title) + '</b><span>' + esc(m.sub) + '</span></span><span class="pct">' + progress(id) + '%</span></button>').join('');
  $('modules').querySelectorAll('.module').forEach(b => b.addEventListener('click', () => { st.module = b.dataset.id; st.save(); start(); }));
}
function start() {
  const m = MODULES[st.module] || MODULES.meanings;
  drawModules();
  $('dir').hidden = st.module !== 'meanings';
  $('dir').querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.val === st.dir)));
  $('introText').innerHTML = m.intro;
  cache = null;
  q = quiz($('quiz'), { name: 'questions-' + st.module, pool: () => (cache ||= m.pool()), render: m.render });
  q.next();
}
$('dir').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { st.dir = b.dataset.val; st.save(); start(); }));
start();
