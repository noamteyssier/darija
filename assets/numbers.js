import { $, header, load, esc, shuffle, bindSeg } from './common.js';
import { quiz } from './quiz.js';
import { say, FRACTIONS } from './numbers-data.js';

header();
const set = load('numbers-set', { dir: 'en-ar', kind: 'whole', min: 1, max: 100 });

let cache = null;
const pool = () => (cache ||= set.kind === 'fractions'
  ? FRACTIONS.map(f => ({ f, key: 'f|' + f.sym + '|' + set.dir }))
  : Array.from({ length: set.max - set.min + 1 }, (_, i) => ({ n: set.min + i, key: (set.min + i) + '|' + set.dir })));

function renderFraction({ f }) {
  const toAr = set.dir === 'en-ar';
  const label = x => x.sym + ' (' + x.en + ')';
  const others = shuffle(FRACTIONS.filter(o => o !== f)).slice(0, 3);
  return {
    chip: toAr ? 'English → Darija' : 'Darija → English',
    word: toAr ? null : { lat: f.lat, ar: f.ar },
    wordHtml: toAr ? '<span class="lat">' + esc(label(f)) + '</span>' : undefined,
    small: !toAr,
    ask: { lat: '' },
    plain: !toAr,
    answer: toAr ? { lat: f.lat, ar: f.ar } : { lat: label(f), ar: '' },
    options: others.map(o => (toAr ? { lat: o.lat, ar: o.ar } : { lat: label(o), ar: '' })),
  };
}

function render({ n, f }) {
  if (f) return renderFraction({ f });
  const toAr = set.dir === 'en-ar';
  // Wrong choices are the closest numbers, the likeliest mix-ups.
  const around = Array.from({ length: 20 }, (_, i) => n + (i < 10 ? i + 1 : 9 - i));
  let near = around.filter(m => m >= set.min && m <= set.max);
  if (near.length < 3) near = around.filter(m => m >= 0 && m <= 10000); // a tiny range: borrow from outside it
  near = shuffle(near);
  const a = say(n);
  return {
    chip: toAr ? 'English → Darija' : 'Darija → English',
    word: toAr ? null : a,
    wordHtml: toAr ? '<span class="lat">' + n + '</span>' : undefined,
    small: !toAr,
    ask: { lat: '' },
    plain: !toAr,
    exact: !toAr,
    accept: n === 2 ? ['tnin', 'تنين'] : [],
    answer: toAr ? a : { lat: String(n), ar: '' },
    options: near.map(m => (toAr ? say(m) : { lat: String(m), ar: '' })),
  };
}

const q = quiz($('quiz'), { name: 'numbers', pool, render, noMode: true });
bindSeg($('numSettings'), set, () => { set.save(); cache = null; $('rangeBox').hidden = set.kind === 'fractions'; q.next(); });

// Sliders are logarithmic (with 0 at the far left) so 10-20 is as easy to set as 100-5000; the boxes take exact values.
const toPos = v => (v ? 1 + Math.round(Math.log10(v) * 100) : 0), fromPos = p => (p > 0 ? Math.round(10 ** ((p - 1) / 100)) : 0);
const clamp = v => Math.min(10000, Math.max(0, Math.round(v) || 0));
function show() {
  $('loN').value = set.min; $('hiN').value = set.max;
  $('loS').value = toPos(set.min); $('hiS').value = toPos(set.max);
}
// A box or slider moves its own end; the other end is pushed along if they would cross.
function setRange(end, v, commit) {
  v = clamp(v);
  if (end === 'min') { set.min = v; if (set.max < v) set.max = v; } else { set.max = v; if (set.min > v) set.min = v; }
  show();
  if (commit) { set.save(); cache = null; q.next(); }
}
for (const [end, id] of [['min', 'lo'], ['max', 'hi']]) {
  $(id + 'S').addEventListener('input', e => setRange(end, fromPos(e.target.value), false));
  $(id + 'S').addEventListener('change', e => setRange(end, fromPos(e.target.value), true));
  $(id + 'N').addEventListener('change', e => setRange(end, e.target.value, true));
}
set.min = clamp(set.min); set.max = Math.max(set.min, clamp(set.max));
show();
$('rangeBox').hidden = set.kind === 'fractions';
q.next();
