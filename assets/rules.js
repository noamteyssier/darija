import { $, PRON, OWNER, header, both, esc, getJSON } from './common.js';
import { say } from './numbers-data.js';
import { loadVerbs, KINDS, TENSE, negate } from './verbs-data.js';

header();
const [{ verbs }, { nouns }, { prepositions }] = await Promise.all([
  loadVerbs(),
  getJSON('data/nouns.json'),
  getJSON('data/prepositions.json'),
]);
const V = Object.fromEntries(verbs.map(v => [v.id, v]));
const N = Object.fromEntries(nouns.map(n => [n.id, n]));
const ktab = N.ktab, magana = N.magana;

const RULES = {
  past: {
    formula: 'stem + ending', marker: '–',
    pre: ['–', '–', '–', '–', '–', '–', '–', '–'],
    suf: ['-t', '-ti', '-ti', '–', '-at', '-na', '-tu', '-u'],
    note: 'nta and nti are the same in the past. Before -at and -u the schwa moves forward: kteb, ketbat, ketbu.',
  },
  pres: {
    formula: 'ka- + prefix + stem + ending', marker: 'ka-',
    pre: ['n-', 't-', 't-', 'y-', 't-', 'n-', 't-', 'y-'],
    suf: ['–', '–', '-i', '–', '–', '-u', '-u', '-u'],
    note: 'ka- marks an ongoing or habitual action. Drop it to get the bare form used after bgha, qder and similar verbs: bghit nkteb, I want to write. Before -i and -u the schwa moves forward: katkteb, katketbi.',
  },
  fut: {
    formula: 'ghadi + prefix + stem + ending', marker: 'ghadi',
    pre: ['n-', 't-', 't-', 'y-', 't-', 'n-', 't-', 'y-'],
    suf: ['–', '–', '-i', '–', '–', '-u', '-u', '-u'],
    note: 'Same prefixes and endings as the present; only the marker changes from ka- to ghadi. In speech ghadi often shortens and attaches: ghankteb.',
  },
};
let tense = 'past';
function renderTense() {
  const r = RULES[tense], f = V.kteb[tense];
  document.querySelectorAll('#rulesSeg button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.val === tense)));
  let h = '<h2>' + r.formula + '</h2><div class="scroll"><table class="rt"><thead><tr><th>Pronoun</th><th>Marker</th><th>Prefix</th><th>Ending</th><th>kteb</th></tr></thead><tbody>';
  PRON.forEach((p, i) => {
    h += '<tr><td><span class="lat">' + p.lat + '</span><span class="par2" lang="ar" dir="rtl">' + p.ar + '</span><span class="pen">' + p.en + '</span></td>'
      + '<td class="pt">' + r.marker + '</td><td class="pt">' + r.pre[i] + '</td><td class="pt">' + r.suf[i] + '</td><td>' + both(f.lat[i], f.ar[i]) + '</td></tr>';
  });
  $('rulesTable').innerHTML = h + '</tbody></table></div>';
  $('rulesNote').textContent = r.note;
}
document.querySelectorAll('#rulesSeg button').forEach(b => b.addEventListener('click', () => { tense = b.dataset.val; renderTense(); }));
renderTense();

const NEG = [['past', 'kteb', 3], ['pres', 'kteb', 3], ['fut', 'kteb', 3]];
$('negTable').innerHTML = '<h2>kteb · ma … sh</h2>' + NEG.map(([t, id, i]) => {
  const x = V[id][t];
  const n = negate({ lat: x.lat[i], ar: x.ar[i] }, t);
  return '<div class="row"><span class="p">' + esc(TENSE[t].label.toLowerCase()) + '</span><span class="f">' + both(x.lat[i], x.ar[i]) + '</span><span class="f">' + both(n.lat, n.ar) + '</span></div>';
}).join('');

const EXAMPLES = { sound: 'fhem', initial: 'wsel', hollow: 'shaf', final: 'bgha', doubled: 'shedd', longa: 'khtar', hamza: 'kla', irregular: 'kan' };
$('kinds').innerHTML = Object.entries(KINDS).map(([k, x]) => {
  const v = V[EXAMPLES[k]];
  const n = verbs.filter(w => w.kind === k).length;
  const ex = v ? ' <strong>' + esc(v.lat) + '</strong>: ' + [v.past.lat[0], v.past.lat[4], v.pres.lat[0], v.pres.lat[2]].map(esc).join(', ') + '.' : '';
  return '<p><strong>' + esc(x.name[0].toUpperCase() + x.name.slice(1)) + '</strong> (' + n + ' verbs). ' + esc(x.text) + ex + '</p>';
}).join('');

const POSS_END = ['-i', '-ek', '-u', '-ha', '-na', '-kum', '-hum'];
let possView = 'endings';
function renderPoss() {
  document.querySelectorAll('#possSeg button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.val === possView)));
  const ex = possView === 'examples';
  const head = ex
    ? [ktab, magana].map(n => '<th>' + esc(n.lat) + '<br><span class="pen">' + esc(n.en) + '</span></th>').join('')
    : '<th>Masculine</th><th>Feminine</th>';
  const cell = i => ex
    ? [ktab, magana].map(n => '<td>' + both(n.mine.lat[i], n.mine.ar[i]) + '</td>').join('')
    : '<td class="pt">' + POSS_END[i] + '</td><td class="pt">-t' + POSS_END[i].slice(1) + '</td>';
  $('possTable').innerHTML = '<div class="scroll"><table class="rt"><thead><tr><th>Pronoun</th>' + head + '</tr></thead><tbody>'
    + OWNER.map((o, i) => '<tr><td><span class="lat">' + o.lat + '</span><span class="par2" lang="ar" dir="rtl">' + o.ar + '</span><span class="pen">' + esc(o.en) + '</span></td>' + cell(i) + '</tr>').join('')
    + '</tbody></table></div>';
}
document.querySelectorAll('#possSeg button').forEach(b => b.addEventListener('click', () => { possView = b.dataset.val; renderPoss(); }));
renderPoss();

const P = Object.fromEntries(prepositions.map(p => [p.id, p]));
const SAMPLE_PREPS = ['l', 'f', 'm3a', '3la', 'men', '3nd'];
const PREP_PRON_EN = ['me', 'you', 'him', 'her', 'us', 'you (pl.)', 'them'];
let ph = '<div class="scroll"><table class="rt prep"><thead><tr><th></th>'
  + SAMPLE_PREPS.map(id => '<th>' + esc(P[id].lat) + '<br><span class="pen">' + esc(P[id].en.split(' / ')[0]) + '</span></th>').join('')
  + '</tr></thead><tbody>';
OWNER.forEach((o, i) => {
  ph += '<tr><td><span class="lat">' + o.lat + '</span><span class="pen">' + PREP_PRON_EN[i] + '</span></td>'
    + SAMPLE_PREPS.map(id => '<td>' + both(P[id].pronouns.lat[i], P[id].pronouns.ar[i]) + '</td>').join('')
    + '</tr>';
});
$('prepTable').innerHTML = ph + '</tbody></table></div>';

// Numbers: every example is built by say(), so the page cannot drift from the dictionary and the drill.
const nm = n => '<strong>' + esc(say(n).lat) + '</strong>';
$('numRules').innerHTML = [
  '<p><strong>1 to 10:</strong> ' + [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(nm).join(', ') + '.</p>',
  '<p><strong>11 to 19</strong> end in <strong>-ash</strong>: ' + [11, 12, 13, 14, 15, 19].map(nm).join(', ') + '. Learn them as their own words.</p>',
  '<p><strong>Tens</strong> end in <strong>-in</strong>: ' + [20, 30, 40, 50, 90].map(nm).join(', ') + '.</p>',
  '<p><strong>Putting them together:</strong> the small number comes first, joined with <strong>w</strong> (and): ' + nm(21) + ' (21), ' + nm(35) + ' (35). Beside a ten, 2 is <strong>tnin</strong>, not juj: ' + nm(22) + ' (22). Bigger numbers go in order, biggest first, with a <strong>w</strong> between each part: ' + nm(347) + ' (347).</p>',
  '<p><strong>Hundreds:</strong> ' + nm(100) + ' and ' + nm(200) + ' are their own words. From 300 the count is shortened and put before <strong>mya</strong>: ' + [300, 400, 500, 900].map(nm).join(', ') + '.</p>',
  '<p><strong>Thousands:</strong> ' + nm(1000) + ' and ' + nm(2000) + ' are their own words. From 3 thousand the shortened count goes before <strong>alaf</strong>, the same way as the hundreds: ' + [3000, 4000, 10000].map(nm).join(', ') + '.</p>',
].join('');
