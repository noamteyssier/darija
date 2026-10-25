import { $, PRON, OWNER, prefs, header, load, bindSeg, both, norm, esc, getJSON, toggleStar } from './common.js';
import { loadVerbs, loadExamples, exampleTable, TENSE, KINDS, isStrong, glossOf } from './verbs-data.js';

header();
const st = load('dict', { what: 'verbs', level: 'all', tense: 'pres' });
const [vdata, ndata, examples] = await Promise.all([loadVerbs(), getJSON('data/nouns.json'), loadExamples()]);
const PAGE = 60;
let shown = PAGE, open = null, q = '';

// 0 a whole gloss matches, 1 a word matches, 2 a word starts with the query, 3 contains it,
// -1 no match. So "go" puts msha before tle3 (go up), and "house" puts dar before husband.
function score(texts) {
  const n = norm(q);
  if (!n) return 0;
  let best = -1;
  const keep = s => { if (s >= 0 && (best < 0 || s < best)) best = s; };
  for (const t of texts) {
    for (const g of String(t).split(' / ')) if (norm(g) === n) keep(0);
    for (const w of String(t).split(/[\s/(),]+/)) {
      const x = norm(w);
      keep(x === n ? 1 : x.startsWith(n) ? 2 : x.includes(n) ? 3 : -1);
    }
  }
  return best;
}
function ranked(list, texts) {
  return list.map(x => [score(texts(x)), x]).filter(([s]) => s >= 0).sort((a, b) => a[0] - b[0]).map(([, x]) => x);
}

function table(title, labels, lat, ar) {
  return '<div class="table"><h2>' + esc(title) + '</h2>' + labels.map((p, i) =>
    '<div class="row"><span class="p"><span>' + esc(p.lat) + '</span><span class="par" lang="ar" dir="rtl">' + esc(p.ar) + '</span><span class="pen">' + esc(p.en) + '</span></span><span class="f">' + both(lat[i], ar[i]) + '</span></div>').join('') + '</div>';
}

function verbItems() {
  return ranked(vdata.verbs.filter(v => st.level === 'star' ? prefs.stars.includes(v.id) : st.level === 'all' || String(v.level) === st.level),
    v => [v.lat, v.ar, v.en, v.id]).map(v => ({
    id: v.id, lat: v.lat, ar: v.ar, en: v.en, star: true,
    badges: [[isStrong(v) ? 'strong' : 'weak', KINDS[v.kind].name], ['l' + v.level, vdata.levels[v.level]]],
    body: () => {
      const k = KINDS[v.kind];
      let h = '<p class="kind"><strong>' + esc(k.name[0].toUpperCase() + k.name.slice(1)) + '.</strong> ' + esc(k.text) + '</p>';
      if (v.prep) h += '<p class="kind">Used with <strong>' + esc(v.prep) + '</strong>.</p>';
      if (v.note) h += '<p class="kind">' + esc(v.note) + '</p>';
      if (v.verify) h += '<p class="kind">Check: ' + esc(v.verify) + '</p>';
      h += '<div class="seg" role="group" aria-label="Tense">' + Object.entries(TENSE).map(([t, x]) =>
        '<button type="button" data-tense="' + t + '" aria-pressed="' + (st.tense === t) + '">' + x.label + '</button>').join('') + '</div>';
      const f = v[st.tense];
      h += table(v.lat + ' · ' + TENSE[st.tense].label.toLowerCase(), PRON, f.lat, f.ar);
      h += exampleTable(v, examples);
      h += '<p class="note">' + esc(glossOf(v)) + ' · source: ' + esc(v.src) + ' (book spelling: ' + esc(v.pc) + ')</p>';
      return h;
    },
  }));
}

function nounItems() {
  return ranked(ndata.nouns, n => [n.lat, n.ar, n.en, n.pl ? n.pl.lat : '']).map(n => ({
    id: n.id, lat: n.lat, ar: n.ar, en: n.en,
    badges: [[n.g === 'f' ? 'weak' : 'strong', n.g === 'f' ? 'feminine' : 'masculine']],
    body: () => {
      let h = '<div class="table"><h2>forms</h2>'
        + '<div class="row"><span class="p">the</span><span class="f">' + both(n.def.lat, n.def.ar) + '</span></div>'
        + (n.pl ? '<div class="row"><span class="p">plural' + (n.plSrc ? ' (' + esc(n.plSrc) + ')' : '') + '</span><span class="f">' + both(n.pl.lat, n.pl.ar) + '</span></div>' : '')
        + '</div>';
      if (n.mine) h += table('with endings', OWNER, n.mine.lat, n.mine.ar);
      if (n.dyal) h += table('with dyal', OWNER, n.dyal.lat, n.dyal.ar);
      if (n.note) h += '<p class="note">' + esc(n.note) + '</p>';
      if (n.src) h += '<p class="note">Source: ' + esc(n.src) + '</p>';
      return h;
    },
  }));
}

function adjItems() {
  return ranked(ndata.adjectives, a => [...a.lat, ...a.ar, a.en]).map(a => ({
    id: a.id, lat: a.lat[0], ar: a.ar[0], en: a.en, badges: [],
    body: () => table('forms', [{ lat: 'masculine', ar: '', en: '' }, { lat: 'feminine', ar: '', en: '' }, { lat: 'plural', ar: '', en: '' }], a.lat, a.ar)
      + '<p class="note">Source: ' + esc(a.src) + '</p>',
  }));
}

function render(focusId) {
  const items = st.what === 'verbs' ? verbItems() : st.what === 'nouns' ? nounItems() : adjItems();
  const total = st.what === 'verbs' ? vdata.verbs.length : st.what === 'nouns' ? ndata.nouns.length : ndata.adjectives.length;
  $('verbFilters').hidden = st.what !== 'verbs';
  $('count').textContent = items.length + ' of ' + total;
  const box = $('list');
  box.innerHTML = '';
  if (!items.length) { box.innerHTML = '<p class="note">Nothing matches. Try another spelling.</p>'; $('more').hidden = true; return; }
  let toFocus = null;
  for (const it of items.slice(0, shown)) {
    const isOpen = open === it.id;
    const el = document.createElement('div');
    el.className = 'vitem' + (isOpen ? ' open' : '');
    el.innerHTML = '<div class="vrow"><button type="button" class="vhead" aria-expanded="' + isOpen + '"><span class="vmain">' + both(it.lat, it.ar) + '</span>'
      + '<span class="vside"><span class="en">' + esc(it.en) + '</span><span class="badges">' + it.badges.map(([c, t]) => '<span class="badge ' + c + '">' + esc(t) + '</span>').join('') + '</span></span></button>'
      + (it.star ? '<button type="button" class="star" aria-label="Star ' + esc(it.lat) + '" aria-pressed="' + prefs.stars.includes(it.id) + '">★</button>' : '') + '</div>';
    el.querySelector('.vhead').addEventListener('click', () => { open = isOpen ? null : it.id; render(it.id); });
    const star = el.querySelector('.star');
    if (star) star.addEventListener('click', () => star.setAttribute('aria-pressed', String(toggleStar(it.id))));
    if (isOpen) {
      const b = document.createElement('div');
      b.className = 'vbody';
      b.innerHTML = it.body();
      b.querySelectorAll('[data-tense]').forEach(t => t.addEventListener('click', () => { st.tense = t.dataset.tense; st.save(); render(it.id); }));
      el.appendChild(b);
    }
    if (focusId === it.id) toFocus = el.querySelector('.vhead');
    box.appendChild(el);
  }
  $('more').hidden = items.length <= shown;
  if (toFocus) try { toFocus.focus({ preventScroll: true }); } catch (e) { /* ignore */ }
}

bindSeg($('filters'), st, () => { st.save(); shown = PAGE; open = null; render(); });
$('search').addEventListener('input', e => { q = e.target.value; shown = PAGE; render(); });
$('more').addEventListener('click', () => { shown += PAGE; render(); });
render();
