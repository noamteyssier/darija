import { $, PRON, prefs, header, load, bindSeg, esc, shuffle } from './common.js';
import { quiz, formTable } from './quiz.js';
import { loadVerbs, TENSE, isStrong, glossOf } from './verbs-data.js';

header();
const set = load('verbs-set', { tense: 'all', levels: ['1'], topics: [], vtype: 'all', starred: false });
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
  const out = [];
  for (const v of verbsInSet()) for (const t of ts) for (let i = 0; i < 8; i++) out.push({ v, t, i, key: v.id + '|' + t + '|' + i });
  return (poolCache = out);
}

function render({ v, t, i }) {
  const f = v[t];
  const other = t === 'pres' ? 'past' : 'pres';
  const forms = x => x.lat.map((lat, j) => ({ lat, ar: x.ar[j] }));
  const options = [...shuffle(forms(f)), ...shuffle(forms(v[other]))];
  const accept = t === 'fut' ? [f.lat[i].replace(/^ghadi /, 'gha'), f.ar[i].replace(/^غادي /, 'غا')] : [];
  return {
    chip: TENSE[t].label + '<span class="ar" lang="ar" dir="rtl">' + TENSE[t].ar + '</span>',
    gloss: glossOf(v),
    word: { lat: v.lat, ar: v.ar },
    ask: { lat: PRON[i].lat, ar: PRON[i].ar, en: PRON[i].en },
    answer: { lat: f.lat[i], ar: f.ar[i] },
    options: options.filter(o => o.lat !== f.lat[i]),
    accept,
    why: v.note,
    after: () => formTable(v.lat + ' · ' + TENSE[t].label.toLowerCase(), PRON.map(p => p.lat), f.lat, f.ar, i),
  };
}

const q = quiz($('quiz'), { name: 'verbs', pool, render });

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
bindSeg($('verbSettings'), set, () => changed());
changed();
