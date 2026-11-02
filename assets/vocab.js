import { $, header, load, esc, getJSON, shuffle } from './common.js';
import { quiz } from './quiz.js';

header();
const st = load('vocab-set', { module: 'family', dir: 'ar-en' });
const { words: WORDS } = await getJSON('data/doda.json');

const BY = t => WORDS.filter(w => w.topic === t);

// Each word is asked both ways: Darija to English, and English to Darija.
function make(topic) {
  const words = BY(topic);
  return {
    pool: () => words.flatMap(w => ['ar-en', 'en-ar'].filter(d => st.dir === 'both' || st.dir === d).map(d => ({ w, d, key: w.id + '|' + d }))),
    render: ({ w, d }) => {
      const toAr = d === 'en-ar';
      const others = shuffle(words.filter(o => o.id !== w.id && o.en !== w.en)).slice(0, 6);
      return {
        chip: (toAr ? 'English → Darija' : 'Darija → English') + '',
        word: toAr ? null : { lat: w.lat, ar: w.ar },
        wordHtml: toAr ? '<span class="lat">' + esc(w.en) + '</span>' : undefined,
        small: toAr,
        ask: { lat: '' },
        plain: !toAr,
        answer: toAr ? { lat: w.lat, ar: w.ar } : { lat: w.en, ar: '' },
        options: others.map(o => (toAr ? { lat: o.lat, ar: o.ar } : { lat: o.en, ar: '' })),
      };
    },
  };
}

const TOPICS = {
  family: ['Family', '', 'Family words'],
  body: ['Body', '', 'Body parts'],
  health: ['Health', '', 'Health and medicine'],
  clothes: ['Clothes', '', 'Clothes'],
  food: ['Food', '', 'Food and drink'],
  nature: ['Nature', '', 'Animals, plants and the environment'],
  colors: ['Colors', '', 'Colors'],
  places: ['Places', '', 'Places, cities and countries'],
  work: ['Work and money', '', 'Jobs, business and money'],
  school: ['School', '', 'School and maths'],
  culture: ['Culture', '', 'Religion, art and sport'],
  feelings: ['Feelings', '', 'Feelings'],
};
const MODULES = Object.fromEntries(Object.entries(TOPICS).map(([id, [title, sub, intro]], i) => [id, {
  n: i + 1, title, sub: BY(id).slice(0, 3).map(w => w.lat).join(', ') + '...',
  intro: '<p>' + esc(intro) + ' from the DODa word list (' + BY(id).length + ' words). Each word is asked both ways, Darija to English and English to Darija.</p>',
  ...make(id),
}]));

let q = null, cache = null;
function progress(id) {
  const saved = load('vocab-' + id, { weights: {} });
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
  const m = MODULES[st.module] || MODULES.family;
  drawModules();
  drawDir();
  $('introText').innerHTML = m.intro + '<p class="note">These words come from <a href="https://github.com/darija-open-dataset/dataset">DODa</a> (CC BY-NC 4.0), not from the Peace Corps book, and are not all checked. Check them with a speaker.</p>';
  cache = null;
  q = quiz($('quiz'), {
    name: 'vocab-' + st.module,
    pool: () => (cache ||= m.pool()),
    render: m.render,
  });
  q.next();
}
$('dir').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { st.dir = b.dataset.val; st.save(); start(); }));
start();
