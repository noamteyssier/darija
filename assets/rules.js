import { $, PRON, OWNER, header, both, esc, getJSON } from './common.js';
import { loadVerbs, KINDS, TENSE, negate } from './verbs-data.js';

header();
const [{ verbs }, { nouns }] = await Promise.all([loadVerbs(), getJSON('data/nouns.json')]);
const V = Object.fromEntries(verbs.map(v => [v.id, v]));
const ktab = nouns.find(n => n.id === 'ktab');

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

$('possTable').innerHTML = '<h2>ktab · book</h2>' + OWNER.map((o, i) =>
  '<div class="row"><span class="p">' + esc(o.en) + ' book</span><span class="f">' + both(ktab.mine.lat[i], ktab.mine.ar[i]) + '</span></div>').join('');
