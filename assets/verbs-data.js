// Verb data: loads data/verbs.json (built by scripts/build_verbs.py) and adds the future.
import { getJSON, esc, PRON } from './common.js';

export const TENSE = {
  past: { label: 'Past', ar: 'ماضي' },
  pres: { label: 'Present', ar: 'مضارع' },
  fut: { label: 'Future', ar: 'مستقبل' },
};

export const KINDS = {
  sound: { name: 'regular', text: 'Every root letter is a consonant, so the stem keeps its shape. Before -at, -u and -i the schwa moves forward (kteb becomes ketbat, katketbi).' },
  initial: { name: 'starts with w', text: 'The first root letter is w. It conjugates like a regular verb (wsel, weslat, kanwsel).' },
  hollow: { name: 'hollow', text: 'A long vowel sits in the middle. It drops before the past endings -t, -ti, -na, -tu (shaf becomes shft) and comes back in the present (kanshuf).' },
  final: { name: 'ends in a vowel', text: 'The stem ends in a vowel. The past adds -i- before consonant endings (bgha becomes bghit). The present ends in -i or -a; -a verbs add -y for nti (katqray).' },
  doubled: { name: 'doubled', text: 'The stem ends in a doubled letter. The past adds -i- before consonant endings (shedd becomes sheddit); the present is regular (kanshedd).' },
  longa: { name: 'long a stem', text: 'The stem keeps a long a. The past adds -i- before consonant endings (khtar becomes khtarit).' },
  hamza: { name: 'dropped hamza', text: 'The first root letter was a hamza. The past works like a final-vowel verb (klit); the present starts with a- (kanakul, katakli).' },
  irregular: { name: 'irregular', text: 'The stem changes in a way the patterns above do not predict. Learn the table.' },
};

// Negation wraps the verb: ma + form + sh (ma ktebtsh). The future's ghadi takes the sh: ma ghadish nkteb.
const ma = x => ({ lat: 'ma ' + x.lat, ar: 'ما ' + x.ar });
const sh = (x, t) => (t === 'fut'
  ? { lat: x.lat.replace(/^ghadi /, 'ghadish '), ar: x.ar.replace(/^غادي /, 'غاديش ') }
  : { lat: x.lat + 'sh', ar: x.ar + 'ش' });
export const negate = (x, t) => ma(sh(x, t));
// The contracted future (ghankteb) is negated like any other verb: ma ghanktebsh.
// The two half-negations learners produce by mistake: ma without sh, and sh without ma.
export const halfNegations = (x, t) => [ma(x), sh(x, t)];

export const isStrong = v => v.kind === 'sound';

export async function loadVerbs() {
  const data = await getJSON('data/verbs.json');
  if (!data.ready) {
    for (const v of data.verbs) {
      v.fut = {
        lat: v.pres.lat.map(f => 'ghadi ' + f.replace(/^ka/, '')),
        ar: v.pres.ar.map(f => 'غادي ' + f.slice(1)),
      };
    }
    data.ready = true;
  }
  return data;
}

export function glossOf(v) {
  return 'to ' + v.en + (v.prep ? ' (+ ' + v.prep + ')' : '');
}

// Example sentences from scripts/build_examples.py, one file per verb. Fetch with loadExamples(id)
// (drill pages call it in render(), so the file has arrived by the time an answer is shown), then
// exampleTable reads the cache. The site still works without the files.
const examples = new Map();
export const loadExamples = id => examples.has(id)
  ? Promise.resolve(examples.get(id))
  : getJSON('data/examples/' + id + '.json').catch(() => []).then(ex => (examples.set(id, ex), ex));

// The examples table, verb form in bold. For a drilled slot ({ t, p, neg }) the rows are the
// drilled slot, then the same person and polarity in other tenses; only when the verb has none
// of those does it fall back to the same person in the other polarity, then the same tense, then
// the rest. Without a person (dictionary, match) a verb with the full set lists the positive
// sentences of tense t (default present). max caps the rows.
export function exampleTable(v, { script, t, p, neg = false, max = 8 } = {}) {
  let ex = examples.get(v.id) || [];
  if (!ex.length) return '';
  if (p !== undefined) {
    const same = e => e.p === p && !!e.neg === neg;
    const rank = e => (same(e) ? (e.t === t ? 0 : 1) : e.p === p ? 2 : e.t === t ? 3 : 4);
    ex = ex.map((e, i) => [rank(e), i, e]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (ex[0][0] <= 1) ex = ex.filter(x => x[0] <= 1);
    ex = ex.slice(0, max).map(x => x[2]);
  } else if (ex.length > 3) ex = ex.filter(e => e.t === (t || 'pres') && !e.neg).slice(0, max);
  const mark = (s, f) => esc(s).replace(esc(f), '<strong>' + esc(f) + '</strong>');
  return '<div class="table"><h2>examples</h2>' + ex.map(e => {
    const f = { lat: v[e.t].lat[e.p], ar: v[e.t].ar[e.p] };
    const g = e.neg ? negate(f, e.t) : f;
    const L = '<span class="lat">' + mark(e.lat, g.lat) + '</span>';
    const A = '<span class="ar" lang="ar" dir="rtl">' + mark(e.ar, g.ar) + '</span>';
    return '<div class="row ex"><span class="p">' + esc(TENSE[e.t].label.toLowerCase() + ' · ' + PRON[e.p].lat + (e.neg ? ' · negative' : '')) + '</span>'
      + (script === 'latin' ? L : script === 'arabic' ? A : L + A)
      + '<span class="pen">' + esc(e.en) + '</span></div>';
  }).join('') + '</div>';
}
