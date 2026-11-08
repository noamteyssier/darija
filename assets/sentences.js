import { $, header, load, bindSeg, norm, esc, getJSON } from './common.js';

header();
const st = load('sentences', { kind: 'all' });
const [{ s: ROWS }, ndata, pdata, wdata, qdata] = await Promise.all([getJSON('data/sentences.json'), getJSON('data/nouns.json'), getJSON('data/prepositions.json'), getJSON('data/words.json'), getJSON('data/questions.json')]);
const PAGE = 40;
const WHAT = { v: 'verbs', p: 'preps', w: 'words', q: 'words' };
const TAG = { v: 'verb', p: 'preposition', w: 'word', q: 'question word' };
let shown = PAGE, q = '';

// Single words that have a dictionary entry: nouns, prepositions, time and place words. Short ones (l, f, b) are skipped.
const LINK = new Map();
const link = (lat, what, id) => { const k = norm(lat); if (k.length >= 3 && !lat.includes(' ') && !LINK.has(k)) LINK.set(k, [what, id]); };
for (const n of ndata.nouns) link(n.lat, 'nouns', n.id);
for (const p of pdata.prepositions) link(p.lat, 'preps', p.id);
for (const w of wdata.words) link(w.lat, 'words', w.id);
for (const w of qdata.words) link(w.lat, 'words', 'q-' + w.id);

const href = (what, id) => 'dictionary.html#' + what + '/' + encodeURIComponent(id);
const words = s => s.split(/\s+/);
const latHtml = (lat, own) => words(lat).map(t => {
  const hit = LINK.get(norm(t));
  return hit && hit.join('/') !== own ? '<a class="wl" href="' + href(hit[0], hit[1]) + '">' + esc(t) + '</a>' : esc(t);
}).join(' ');

// 0 a whole word matches, 1 the text contains the query. -1 no match.
const prepared = ROWS.map(r => ({ r, f: [r[0], r[1], r[2]].map(t => ({ n: norm(t), w: words(t).map(norm) })) }));
function score(row) {
  const n = norm(q);
  if (!n) return 0;
  let best = -1;
  for (const f of row.f) {
    if (f.w.includes(n)) return 0;
    if (f.n.includes(n)) best = 1;
  }
  return best;
}

function render() {
  const pool = prepared.filter(x => st.kind === 'all' || x.r[3] === st.kind);
  const hits = q ? pool.map(x => [score(x), x]).filter(([s]) => s >= 0).sort((a, b) => a[0] - b[0]).map(([, x]) => x) : pool;
  $('count').textContent = hits.length + ' of ' + ROWS.length + ' sentences';
  $('list').innerHTML = hits.length ? hits.slice(0, shown).map(({ r: [lat, ar, en, kind, id] }) =>
    '<div class="vitem"><div class="vbody"><div class="row ex"><span class="lat">' + latHtml(lat, WHAT[kind] + '/' + id) + '</span>'
    + '<span class="ar" lang="ar" dir="rtl">' + esc(ar) + '</span><span class="pen">' + esc(en) + '</span>'
    + '<a class="badge strong" href="' + href(WHAT[kind], id) + '">' + TAG[kind] + ' · ' + esc(id) + '</a></div></div></div>').join('')
    : '<p class="note">Nothing matches. Try another spelling.</p>';
  $('more').hidden = hits.length <= shown;
}

bindSeg($('filters'), st, () => { st.save(); shown = PAGE; render(); });
$('search').addEventListener('input', e => { q = e.target.value; shown = PAGE; render(); });
$('more').addEventListener('click', () => { shown += PAGE; render(); });
render();
