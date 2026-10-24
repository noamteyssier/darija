import { $, OWNER, prefs, header, load, esc, getJSON, shuffle } from './common.js';
import { quiz, formTable } from './quiz.js';

header();
const st = load('nouns-set', { module: 'mine' });
const { nouns: NOUNS, adjectives: ADJS } = await getJSON('data/nouns.json');
const A = Object.fromEntries(ADJS.map(a => [a.id, a]));

// Which noun topics each adjective makes sense with.
const ALL = ['family', 'body', 'home', 'clothes', 'things', 'places', 'animal'];
const STUFF = ['home', 'clothes', 'things'];
const ADJ_FOR = {
  kbir: ALL, sghir: ALL, zwin: [...ALL, 'abstract'], mzyan: [...ALL, 'abstract', 'time'], khayb: [...ALL, 'abstract', 'time'],
  twil: ['family', 'clothes', 'time'], qsir: ['family', 'clothes', 'time'],
  jdid: [...STUFF, 'places', 'time'], qdim: [...STUFF, 'places'],
  nqi: ['body', ...STUFF, 'places', 'animal'], mussekh: ['body', ...STUFF, 'places', 'animal'],
  ghali: STUFF, rkhis: STUFF, b3id: ['places'], qrib: ['places'], '7lu': ['family'], bsit: ['abstract'],
  fer7an: ['family'], meskin: ['family', 'animal'], '3iyan': ['family', 'animal'], ji3an: ['family', 'animal'], meshghul: ['family'], mrid: ['family', 'animal'],
  byed: [...STUFF, 'animal'], k7el: [...STUFF, 'animal'], '7mer': STUFF, zreq: STUFF, khder: STUFF, sfer: STUFF,
};
const NO_AGREE = new Set(['bba', 'mmi', 'khu', 'khet', 'shems', 'sh3er']);
const adjsFor = n => ADJS.filter(a => (ADJ_FOR[a.id] || []).includes(n.topic));

const first = en => en.split(' / ')[0];
function enPlural(en) {
  const m = first(en).match(/^([^(]*?)\s*(\(.*\))?$/);
  const w = m[1], tail = m[2] ? ' ' + m[2] : '';
  const irr = { man: 'men', woman: 'women', foot: 'feet', knife: 'knives', shoes: 'shoes', pants: 'pants', 'small shop': 'small shops', 'sheet of paper': 'sheets of paper' };
  const p = irr[w] || (/[^aeiou]y$/.test(w) ? w.slice(0, -1) + 'ies' : /(s|sh|ch|x)$/.test(w) ? w + 'es' : w + 's');
  return p + tail;
}
const article = w => (/^[aeiou]/.test(w) ? 'an ' : 'a ') + w;
const G = { m: { lat: 'masculine', ar: 'مذكر' }, f: { lat: 'feminine', ar: 'مؤنث' } };

function genderWhy(n) {
  if (n.g === 'f' && /a$/.test(n.lat)) return n.lat + ' ends in -a, the usual sign of a feminine noun.';
  if (n.g === 'f') return n.lat + ' is feminine without -a. Body parts that come in pairs, dar and shems are feminine anyway.';
  if (/a$/.test(n.lat)) return n.lat + ' ends in -a but is masculine. Watch for these.';
  return n.lat + ' ends in a consonant or another vowel, so it is masculine.';
}

// An article mistake (l-dar instead of d-dar) as a distractor; same Arabic, so Latin only.
function articleSlip(defLat, rest) {
  const m = defLat.match(/^(\w+)-(.*)$/);
  if (!m || prefs.script === 'arabic') return [];
  const word = m[2];
  const wrong = m[1] === 'l' ? word.match(/^(sh|kh|gh|.)/)[1] + '-' + word : 'l-' + word;
  return [{ lat: wrong + rest, ar: '' }];
}

const MODULES = {
  mine: {
    n: 1, title: 'My book', sub: 'Possessive endings: ktabi, ktabek, ktabu',
    intro: '<p>Add an ending to the noun: <strong>-i</strong> my, <strong>-ek</strong> your, <strong>-u</strong> his, <strong>-ha</strong> her, <strong>-na</strong> our, <strong>-kum</strong> your (pl.), <strong>-hum</strong> their.</p><p>Feminine nouns ending in <strong>-a</strong> turn it into <strong>-t-</strong>: magana, maganti. After a vowel, my is <strong>-ya</strong> and his is <strong>-h</strong>: khuya, khuh. Endings sound natural on family, body parts and a few everyday things.</p>',
    pool: () => NOUNS.filter(n => n.mine).flatMap(n => OWNER.map((_, i) => ({ n, i, key: 'mine|' + n.id + '|' + i }))),
    render: ({ n, i }) => ({
      chip: 'Ending', gloss: n.en,
      word: { lat: n.lat, ar: n.ar },
      ask: { lat: OWNER[i].lat, ar: OWNER[i].ar, en: OWNER[i].en + ' ' + first(n.en) },
      answer: { lat: n.mine.lat[i], ar: n.mine.ar[i] },
      options: shuffle(n.mine.lat.map((lat, j) => ({ lat, ar: n.mine.ar[j] })).filter((_, j) => j !== i)),
      why: n.note,
      after: () => formTable(n.lat + ' · with endings', OWNER.map(o => o.en), n.mine.lat, n.mine.ar, i),
    }),
  },
  dyal: {
    n: 2, title: 'The book of mine', sub: 'dyal: l-ktab dyali, d-dar dyalha',
    intro: '<p>Put <strong>the</strong> on the noun and follow it with <strong>dyal</strong> plus an ending: l-ktab dyali, my book. dyal works with almost any noun, and it is the usual choice for things you own.</p><p><strong>the</strong> is l- before most letters but copies the first letter before t d r z s sh n l j and their emphatic forms: d-dar, s-sarut, t-tumubil.</p>',
    pool: () => NOUNS.filter(n => n.dyal).flatMap(n => OWNER.map((_, i) => ({ n, i, key: 'dyal|' + n.id + '|' + i }))),
    render: ({ n, i }) => ({
      chip: 'dyal', gloss: n.en,
      word: { lat: n.lat, ar: n.ar },
      ask: { lat: OWNER[i].lat, ar: OWNER[i].ar, en: OWNER[i].en + ' ' + first(n.en) },
      answer: { lat: n.dyal.lat[i], ar: n.dyal.ar[i] },
      options: [...articleSlip(n.def.lat, ' ' + n.dyal.lat[i].split(' ')[1]), ...shuffle(n.dyal.lat.map((lat, j) => ({ lat, ar: n.dyal.ar[j] })).filter((_, j) => j !== i))],
      after: () => formTable('with dyal', OWNER.map(o => o.en), n.dyal.lat, n.dyal.ar, i),
    }),
  },
  gender: {
    n: 3, title: 'Gender and agreement', sub: 'dar is feminine: dar kbira, d-dar l-kbira',
    intro: '<p>Most nouns ending in <strong>-a</strong> are feminine; the rest are masculine. Exceptions: body parts that come in pairs (yedd, 3in, rjel, wden), dar and shems are feminine.</p><p>Adjectives come after the noun and add <strong>-a</strong> for a feminine noun: dar kbira, a big house. With <strong>the</strong>, both words take it: d-dar l-kbira. Without it on the adjective, d-dar kbira is a sentence: the house is big.</p>',
    pool: () => [
      ...NOUNS.map(n => ({ n, kind: 'g', key: 'g|' + n.id })),
      ...NOUNS.filter(n => !NO_AGREE.has(n.id)).flatMap(n => adjsFor(n).flatMap(a => [0, 1].map(d => ({ n, a, d, kind: 'a', key: 'a|' + n.id + '|' + a.id + '|' + d })))),
    ],
    render: it => {
      const { n } = it;
      if (it.kind === 'g') {
        return {
          chip: 'Gender', gloss: n.en, word: { lat: n.lat, ar: n.ar },
          ask: { lat: 'masculine or feminine?', ar: 'مذكر ولا مؤنث؟' },
          answer: G[n.g], options: [G[n.g === 'm' ? 'f' : 'm']], chooseOnly: true, keepOrder: true, order: ['masculine', 'feminine'],
          why: genderWhy(n),
        };
      }
      const { a, d } = it, gi = n.g === 'f' ? 1 : 0, wi = 1 - gi;
      const phrase = (k, def) => def ? { lat: n.def.lat + ' ' + a.def.lat[k], ar: n.def.ar + ' ' + a.def.ar[k] } : { lat: n.lat + ' ' + a.lat[k], ar: n.ar + ' ' + a.ar[k] };
      const en = (d ? 'the ' + a.en.split(' / ')[0] + ' ' + first(n.en) : article(a.en.split(' / ')[0] + ' ' + first(n.en)));
      const options = [phrase(wi, d)];
      options.push(d ? { lat: n.def.lat + ' ' + a.lat[gi], ar: n.def.ar + ' ' + a.ar[gi] } : phrase(gi, 1));
      options.push(phrase(wi, !d));
      return {
        chip: 'Agreement', gloss: n.en + ' (' + G[n.g].lat + ') + ' + a.en,
        word: { lat: n.lat + ' + ' + a.lat[0], ar: n.ar + ' + ' + a.ar[0] }, small: true,
        ask: { lat: en, ar: '' },
        answer: phrase(gi, d), options,
        why: n.lat + ' is ' + G[n.g].lat + (n.g === 'f' ? ', so the adjective takes -a.' : ', so the adjective stays as it is.') + (d ? ' With the, both words take the article.' : ''),
      };
    },
  },
  plural: {
    n: 4, title: 'Plurals', sub: 'ktab → ktub, kbir → kbar, dyur kbar',
    intro: '<p>Many plurals change the vowels inside the word (ktab, ktub; dar, dyur; weld, wlad); learn them with the noun. Others add <strong>-at</strong> (tilifun, tilifunat) or <strong>-in</strong>.</p><p>Adjectives add <strong>-in</strong> (mzyan, mzyanin) or change their middle vowel (kbir, kbar). A plural noun takes a plural adjective: dyur kbar, big houses.</p>',
    pool: () => [
      ...NOUNS.filter(n => n.pl).map(n => ({ n, kind: 'n', key: 'pn|' + n.id })),
      ...ADJS.map(a => ({ a, kind: 'adj', key: 'pa|' + a.id })),
      ...NOUNS.filter(n => n.pl && !NO_AGREE.has(n.id)).flatMap(n => adjsFor(n).map(a => ({ n, a, kind: 'p', key: 'pp|' + n.id + '|' + a.id }))),
    ],
    render: it => {
      if (it.kind === 'n') {
        const { n } = it;
        const stem = n.lat.replace(/a$/, ''), stemAr = n.ar.replace(/ة$/, '');
        const fakes = [{ lat: stem + 'at', ar: stemAr + 'ات' }, { lat: n.lat + 'in', ar: n.ar + 'ين' }];
        const others = shuffle(NOUNS.filter(m => m.pl && m.id !== n.id)).slice(0, 3).map(m => ({ lat: m.pl.lat, ar: m.pl.ar }));
        return {
          chip: 'Plural', gloss: n.en + ' → ' + enPlural(n.en), word: { lat: n.lat, ar: n.ar },
          ask: { lat: 'plural', ar: 'الجمع' },
          answer: { lat: n.pl.lat, ar: n.pl.ar }, options: [...shuffle(fakes).slice(0, 1), ...others],
          why: n.plSrc ? 'This plural is not in the book; check it with a speaker.' : '',
        };
      }
      if (it.kind === 'adj') {
        const { a } = it;
        const fake = /in$/.test(a.lat[2]) ? { lat: a.lat[1] + 't', ar: a.ar[1].replace(/ة$/, 'ات') } : { lat: a.lat[0] + 'in', ar: a.ar[0] + 'ين' };
        return {
          chip: 'Plural', gloss: a.en, word: { lat: a.lat[0], ar: a.ar[0] },
          ask: { lat: 'plural', ar: 'الجمع' },
          answer: { lat: a.lat[2], ar: a.ar[2] }, options: [fake, { lat: a.lat[1], ar: a.ar[1] }],
          after: () => formTable(a.lat[0], ['masculine', 'feminine', 'plural'], a.lat, a.ar, 2),
        };
      }
      const { n, a } = it, gi = n.g === 'f' ? 1 : 0;
      return {
        chip: 'Plural agreement', gloss: n.en + ' + ' + a.en,
        word: { lat: n.lat + ' + ' + a.lat[0], ar: n.ar + ' + ' + a.ar[0] }, small: true,
        ask: { lat: a.en.split(' / ')[0] + ' ' + enPlural(n.en), ar: '' },
        answer: { lat: n.pl.lat + ' ' + a.lat[2], ar: n.pl.ar + ' ' + a.ar[2] },
        options: [
          { lat: n.pl.lat + ' ' + a.lat[gi], ar: n.pl.ar + ' ' + a.ar[gi] },
          { lat: n.lat + ' ' + a.lat[2], ar: n.ar + ' ' + a.ar[2] },
          { lat: n.pl.lat + ' ' + a.lat[1 - gi], ar: n.pl.ar + ' ' + a.ar[1 - gi] },
        ],
        why: 'A plural noun takes the plural adjective: ' + a.lat[2] + '.',
      };
    },
  },
};

let q = null;
function progress(id) {
  const saved = load('nouns-' + id, { weights: {} });
  const items = MODULES[id].pool();
  const learned = items.filter(c => saved.weights[c.key] < 1).length;
  return Math.round(100 * learned / items.length);
}
function drawModules() {
  $('modules').innerHTML = Object.entries(MODULES).map(([id, m]) =>
    '<button type="button" class="module" data-id="' + id + '" aria-pressed="' + (st.module === id) + '"><span class="n">' + m.n + '</span><span class="t"><b>' + esc(m.title) + '</b><span>' + esc(m.sub) + '</span></span><span class="pct">' + progress(id) + '%</span></button>').join('');
  $('modules').querySelectorAll('.module').forEach(b => b.addEventListener('click', () => { st.module = b.dataset.id; st.save(); start(); }));
}
function start() {
  const m = MODULES[st.module] || MODULES.mine;
  drawModules();
  $('introText').innerHTML = m.intro + '<p><a href="rules.html#nouns">All noun rules</a></p>';
  let cache = null;
  q = quiz($('quiz'), {
    name: 'nouns-' + st.module,
    pool: () => (cache ||= m.pool()),
    render: m.render,
  });
  q.next();
}
start();
