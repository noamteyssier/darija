// Verb data: loads data/verbs.json (built by scripts/build_verbs.py) and adds the future.
import { getJSON } from './common.js';

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
