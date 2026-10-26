import { $, prefs, header, load, bindSeg, esc, shuffle } from './common.js';
import { quiz } from './quiz.js';
import { loadVerbs, loadExamples, exampleTable, glossOf } from './verbs-data.js';

header();
const set = load('match-set', { dir: 'en-ar', choices: '4', levels: ['1'], topics: [], starred: false });
const data = await loadVerbs();
const VERBS = data.verbs;

let poolCache = null;
function pool() {
  return (poolCache ||= VERBS.filter(v => {
    const inLevel = set.levels.includes(String(v.level)) || (set.starred && prefs.stars.includes(v.id));
    return inLevel && (!set.topics.length || v.topics.some(t => set.topics.includes(t)));
  }).map(v => ({ v, key: v.id + '|' + set.dir })));
}

function render({ v }) {
  loadExamples(v.id);
  const toAr = set.dir === 'en-ar';
  const gloss = glossOf(v);
  // Wrong choices come from the whole set (all verbs if it is tiny), never sharing the answer's meaning or spelling.
  const src = pool().length > 3 ? pool().map(c => c.v) : VERBS;
  const others = shuffle(src.filter(o => o.id !== v.id && o.lat !== v.lat && glossOf(o) !== gloss)).slice(0, 6);
  return {
    chip: toAr ? 'English → Arabic' : 'Arabic → English',
    word: toAr ? null : { lat: v.lat, ar: v.ar },
    wordHtml: toAr ? '<span class="lat">' + esc(gloss) + '</span>' : undefined,
    small: toAr,
    ask: { lat: '' },
    plain: !toAr,
    answer: toAr ? { lat: v.lat, ar: v.ar } : { lat: gloss, ar: '' },
    options: others.map(o => (toAr ? { lat: o.lat, ar: o.ar } : { lat: glossOf(o), ar: '' })),
    max: Number(set.choices),
    after: () => exampleTable(v, { script: prefs.script, max: 3 }),
  };
}

const q = quiz($('quiz'), { name: 'match', pool, render, noMode: true });

function chip(label, n, on, onClick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.innerHTML = esc(label) + '<small>' + n + '</small>';
  b.setAttribute('aria-pressed', String(on));
  b.addEventListener('click', () => { onClick(); on = !on; b.setAttribute('aria-pressed', String(on)); changed(); });
  return b;
}
function changed() {
  set.save();
  poolCache = null;
  $('moreSummary').textContent = set.topics.length ? 'More filters (' + set.topics.length + ' on)' : 'More filters';
  q.next();
}
const toggle = (arr, x) => { const k = arr.indexOf(x); if (k >= 0) arr.splice(k, 1); else arr.push(x); };

for (const [lv, name] of Object.entries(data.levels)) {
  $('levels').appendChild(chip(name, VERBS.filter(v => String(v.level) === lv).length, set.levels.includes(lv), () => toggle(set.levels, lv)));
}
$('levels').appendChild(chip('★ Starred', prefs.stars.length, set.starred, () => { set.starred = !set.starred; }));
for (const [tp, name] of Object.entries(data.topics)) {
  $('topics').appendChild(chip(name, VERBS.filter(v => v.topics.includes(tp)).length, set.topics.includes(tp), () => toggle(set.topics, tp)));
}
bindSeg($('matchSettings'), set, changed);
changed();
