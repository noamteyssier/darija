import { $, PRON, prefs, header, load, bindSeg, esc, shuffle } from './common.js';
import { quiz, formTable } from './quiz.js';
import { loadVerbs, loadExamples, exampleTable, TENSE, isStrong, glossOf, negate, halfNegations } from './verbs-data.js';

header();
const set = load('verbs-set', { tense: 'all', polarity: 'all', levels: ['1'], topics: [], vtype: 'all', starred: false, prons: PRON.map((_, i) => i) });
const data = await loadVerbs();
const VERBS = data.verbs;

function verbsInSet() {
  return VERBS.filter(v => {
    const inLevel = set.levels.includes(String(v.level)) || (set.starred && prefs.stars.includes(v.id));
    if (!inLevel) return false;
    if (set.topics.length && !v.topics.some(t => set.topics.includes(t))) return false;
    if (set.vtype !== 'all' && (set.vtype === 'strong') !== isStrong(v)) return false;
    return true;
  });
}

let poolCache = null;
function pool() {
  if (poolCache) return poolCache;
  const ts = set.tense === 'all' ? ['past', 'pres', 'fut'] : [set.tense];
  const ns = set.polarity === 'all' ? [false, true] : [set.polarity === 'neg'];
  const out = [];
  for (const v of verbsInSet()) for (const t of ts) for (const i of set.prons) for (const neg of ns) out.push({ v, t, i, neg, key: v.id + '|' + t + '|' + i + (neg ? '|neg' : '') });
  return (poolCache = out);
}

function render({ v, t, i, neg }) {
  loadExamples(v.id);
  const f = v[t];
  const other = t === 'pres' ? 'past' : 'pres';
  const forms = (x, tt) => x.lat.map((lat, j) => ({ lat, ar: x.ar[j] })).map(o => (neg ? negate(o, tt) : o));
  let options = [...shuffle(forms(f, t)), ...shuffle(forms(v[other], other))];
  const full = neg ? forms(f, t) : null;
  const answer = neg ? full[i] : { lat: f.lat[i], ar: f.ar[i] };
  // Contracted future (ghankteb): the same slot, with or without negation.
  const accept = t === 'fut' ? [{ lat: f.lat[i].replace(/^ghadi /, 'gha'), ar: f.ar[i].replace(/^غادي /, 'غا') }] : [];
  const accepted = neg ? accept.map(a => negate(a, 'pres')) : accept;
  // Negative drills lead with the half-negations, the likeliest mix-ups.
  if (neg) options = [...halfNegations({ lat: f.lat[i], ar: f.ar[i] }, t), ...options];
  const tag = neg ? ' · negative' : '';
  return {
    chipCls: 'tense-' + t,
    chip: TENSE[t].label + tag + '<span class="ar" lang="ar" dir="rtl">' + TENSE[t].ar + (neg ? ' منفي' : '') + '</span>',
    gloss: glossOf(v),
    word: { lat: v.lat, ar: v.ar },
    ask: { lat: PRON[i].lat, ar: PRON[i].ar, en: PRON[i].en },
    answer,
    options: options.filter(o => o.lat !== answer.lat),
    accept: accepted.flatMap(a => [a.lat, a.ar]),
    why: v.note,
    after: good => {
      const conj = neg
        ? formTable(v.lat + ' · ' + TENSE[t].label.toLowerCase() + ' · negative', PRON.map(p => p.lat), full.map(o => o.lat), full.map(o => o.ar), i)
        : formTable(v.lat + ' · ' + TENSE[t].label.toLowerCase(), PRON.map(p => p.lat), f.lat, f.ar, i);
      const ex = exampleTable(v, { script: prefs.script, t, p: i, neg, max: 4 });
      return ex ? [{ label: 'Conjugation', html: conj, open: !good }, { label: 'Examples', html: ex, open: good }] : conj;
    },
  };
}

const q = quiz($('quiz'), { name: 'verbs', pool, render, traits: c => ['p' + c.i, 't' + c.t, 'k' + c.v.kind, 'n' + (c.neg ? 1 : 0)] });

function counts(pred) { return VERBS.filter(pred).length; }
function chip(label, n, on, onClick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.innerHTML = esc(label) + '<small>' + n + '</small>';
  b.setAttribute('aria-pressed', String(on));
  b.addEventListener('click', () => { onClick(); b.setAttribute('aria-pressed', String(!on)); on = !on; changed(); });
  return b;
}
function changed() {
  set.save();
  poolCache = null;
  const n = set.topics.length + (set.vtype !== 'all' ? 1 : 0);
  $('moreSummary').textContent = n ? 'More filters (' + n + ' on)' : 'More filters';
  $('pronSummary').textContent = 'Pronouns (' + set.prons.length + ' of 8)';
  q.next();
}
function toggle(arr, x) { const k = arr.indexOf(x); if (k >= 0) arr.splice(k, 1); else arr.push(x); }

for (const [lv, name] of Object.entries(data.levels)) {
  $('levels').appendChild(chip(name, counts(v => String(v.level) === lv), set.levels.includes(lv), () => toggle(set.levels, lv)));
}
$('levels').appendChild(chip('★ Starred', prefs.stars.length, set.starred, () => { set.starred = !set.starred; }));
for (const [tp, name] of Object.entries(data.topics)) {
  $('topics').appendChild(chip(name, counts(v => v.topics.includes(tp)), set.topics.includes(tp), () => toggle(set.topics, tp)));
}
function syncProns() {
  $('prons').querySelectorAll('button').forEach((b, i) => b.setAttribute('aria-pressed', String(set.prons.includes(i))));
}
PRON.forEach((p, i) => {
  const b = document.createElement('button');
  b.type = 'button';
  b.innerHTML = esc(p.lat) + '<small>' + esc(p.en) + '</small>';
  b.addEventListener('click', () => {
    if (set.prons.includes(i) && set.prons.length === 1) return; // keep at least one
    toggle(set.prons, i);
    set.prons.sort((a, b) => a - b);
    syncProns(); changed();
  });
  $('prons').appendChild(b);
});
$('pronAll').addEventListener('click', () => { set.prons = PRON.map((_, i) => i); syncProns(); changed(); });
syncProns();
bindSeg($('verbSettings'), set, () => changed());
changed();
