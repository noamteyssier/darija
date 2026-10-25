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

// Example sentences from scripts/build_examples.py; the site still works without the file.
export const loadExamples = () => getJSON('data/examples.json').catch(() => ({}));

// The examples table, verb form in bold. first: tense to list first (the one just drilled).
export function exampleTable(v, examples, { script, first } = {}) {
  const ex = examples[v.id];
  if (!ex) return '';
  const mark = (s, f) => esc(s).replace(esc(f), '<strong>' + esc(f) + '</strong>');
  const rows = first ? [...ex].sort((a, b) => (b.t === first) - (a.t === first)) : ex;
  return '<div class="table"><h2>examples</h2>' + rows.map(e => {
    const f = v[e.t];
    const L = '<span class="lat">' + mark(e.lat, f.lat[e.p]) + '</span>';
    const A = '<span class="ar" lang="ar" dir="rtl">' + mark(e.ar, f.ar[e.p]) + '</span>';
    return '<div class="row ex"><span class="p">' + esc(TENSE[e.t].label.toLowerCase() + ' · ' + PRON[e.p].lat) + '</span>'
      + (script === 'latin' ? L : script === 'arabic' ? A : L + A)
      + '<span class="pen">' + esc(e.en) + '</span></div>';
  }).join('') + '</div>';
}
