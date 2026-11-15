import { $, PRON, prefs, header, load, bindSeg, esc, shuffle } from './common.js';
import { quiz, formTable } from './quiz.js';
import { loadVerbs, loadExamples, TENSE, isStrong, negate, halfNegations } from './verbs-data.js';

header();
const set = load('blank-set', { tense: 'all', polarity: 'all', levels: ['1'], topics: [], vtype: 'all', starred: false });
const data = await loadVerbs();
const VERBS = data.verbs;

const verbsInSet = () => VERBS.filter(v => {
  if (!(set.levels.includes(String(v.level)) || (set.starred && prefs.stars.includes(v.id)))) return false;
  if (set.topics.length && !v.topics.some(t => set.topics.includes(t))) return false;
  return set.vtype === 'all' || (set.vtype === 'strong') === isStrong(v);
});

const slot = (v, e) => { const f = { lat: v[e.t].lat[e.p], ar: v[e.t].ar[e.p] }; return e.neg ? negate(f, e.t) : f; };
// The contracted future (ghankteb) is also written in sentences; the form found in the sentence is the answer.
const forms = (v, e) => {
  const f = { lat: v[e.t].lat[e.p], ar: v[e.t].ar[e.p] };
  const c = e.t === 'fut' ? [{ lat: f.lat.replace(/^ghadi /, 'gha'), ar: f.ar.replace(/^غادي /, 'غا') }] : [];
  return [f, ...c].map(x => (e.neg ? negate(x, e.t) : x));
};

let poolCache = [];
async function build() {
  const ts = set.tense === 'all' ? ['past', 'pres', 'fut'] : [set.tense];
  const vs = verbsInSet();
  const exs = await Promise.all(vs.map(v => loadExamples(v.id)));
  poolCache = vs.flatMap((v, k) => exs[k].map((e, i) => {
    if (!ts.includes(e.t) || (set.polarity !== 'all' && (set.polarity === 'neg') !== !!e.neg)) return null;
    const a = forms(v, e).find(f => e.lat.includes(f.lat) && e.ar.includes(f.ar));
    return a ? { v, e, a, key: v.id + '|' + i } : null;
  }).filter(Boolean));
}

const blank = (s, f) => s.replace(f, '___');

function render({ v, e, a }) {
  const f = v[e.t];
  const own = forms(v, e)[0];
  // Likeliest mix-ups first: other persons of this verb, then other tenses, then the same slot of other verbs.
  const mine = shuffle(PRON.map((_, j) => ({ t: e.t, p: j, neg: e.neg })).filter(x => x.p !== e.p));
  const tense = shuffle(['past', 'pres', 'fut'].filter(t => t !== e.t).map(t => ({ t, p: e.p, neg: e.neg })));
  const same = [...mine.slice(0, 3), ...tense].map(x => slot(v, x));
  const half = e.neg ? halfNegations({ lat: f.lat[e.p], ar: f.ar[e.p] }, e.t) : [];
  const verbs = shuffle(verbsInSet().filter(o => o.id !== v.id)).slice(0, 4).map(o => slot(o, e));
  return {
    chipCls: 'tense-' + e.t,
    chip: TENSE[e.t].label + (e.neg ? ' · negative' : '') + '<span class="ar" lang="ar" dir="rtl">' + TENSE[e.t].ar + (e.neg ? ' منفي' : '') + '</span>',
    word: null, wordHtml: '',
    ask: { lat: blank(e.lat, a.lat), ar: blank(e.ar, a.ar), en: e.en, stack: true },
    answer: a,
    options: [...half, ...same.slice(0, 2), ...verbs.slice(0, 2), ...same.slice(2), ...verbs.slice(2)].filter(o => o.lat !== a.lat),
    accept: [own.lat, own.ar],
    whyHtml: esc(e.lat) + ' <em>(' + esc(e.en) + ')</em>',
    after: () => formTable(v.lat + ' · ' + TENSE[e.t].label.toLowerCase() + (e.neg ? ' · negative' : ''),
      PRON.map(p => p.lat), PRON.map((_, j) => slot(v, { ...e, p: j }).lat), PRON.map((_, j) => slot(v, { ...e, p: j }).ar), e.p),
  };
}

const q = quiz($('quiz'), { name: 'blank', pool: () => poolCache, render, traits: c => ['p' + c.e.p, 't' + c.e.t, 'k' + c.v.kind, 'n' + (c.e.neg ? 1 : 0)] });

const counts = pred => VERBS.filter(pred).length;
function chip(label, n, on, onClick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.innerHTML = esc(label) + '<small>' + n + '</small>';
  b.setAttribute('aria-pressed', String(on));
  b.addEventListener('click', () => { onClick(); b.setAttribute('aria-pressed', String(!on)); on = !on; changed(); });
  return b;
}
async function changed() {
  set.save();
  const n = set.topics.length + (set.vtype !== 'all' ? 1 : 0);
  $('moreSummary').textContent = n ? 'More filters (' + n + ' on)' : 'More filters';
  await build();
  q.next();
}
const toggle = (arr, x) => { const k = arr.indexOf(x); if (k >= 0) arr.splice(k, 1); else arr.push(x); };

for (const [lv, name] of Object.entries(data.levels)) {
  $('levels').appendChild(chip(name, counts(v => String(v.level) === lv), set.levels.includes(lv), () => toggle(set.levels, lv)));
}
$('levels').appendChild(chip('★ Starred', prefs.stars.length, set.starred, () => { set.starred = !set.starred; }));
for (const [tp, name] of Object.entries(data.topics)) {
  $('topics').appendChild(chip(name, counts(v => v.topics.includes(tp)), set.topics.includes(tp), () => toggle(set.topics, tp)));
}
bindSeg($('blankSettings'), set, () => changed());
await changed();
