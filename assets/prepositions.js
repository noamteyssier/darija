import { $, prefs, header, load, esc, getJSON, shuffle } from './common.js';
import { quiz, formTable } from './quiz.js';

export const PREP_PRONS = [
  { lat: 'ana', ar: 'أنا', en: 'me' },
  { lat: 'nta / nti', ar: 'نتا / نتي', en: 'you' },
  { lat: 'huwa', ar: 'هو', en: 'him' },
  { lat: 'hiya', ar: 'هي', en: 'her' },
  { lat: '7na', ar: 'حنا', en: 'us' },
  { lat: 'ntuma', ar: 'نتوما', en: 'you (pl.)' },
  { lat: 'huma', ar: 'هوما', en: 'them' },
];

header();
const st = load('prepositions-set', { module: 'meanings', prons: PREP_PRONS.map((_, i) => i) });
const { prepositions: PREPS, collocations: COLLOCS, idioms: IDIOMS } = await getJSON('data/prepositions.json');
const PREP_MAP = Object.fromEntries(PREPS.map(p => [p.id, p]));

const first = en => en.split(' / ')[0];

const MODULES = {
  meanings: {
    n: 1, title: 'Meanings & Direction', sub: 'fuq, te7t, qddam, mura, 7da, bin, bla, men, 3la...',
    intro: '<p>Master what each preposition means in Moroccan Darija: spatial positions (<strong>fuq</strong> above, <strong>te7t</strong> under, <strong>qddam</strong> in front of, <strong>mura</strong> behind, <strong>7da</strong> next to, <strong>bin</strong> between), direction, and core relations (<strong>m3a</strong> with, <strong>bla</strong> without, <strong>men</strong> from, <strong>3la</strong> on/about, <strong>l</strong> to/for, <strong>f</strong> in/at).</p>',
    pool: () => PREPS.map(p => ({ p, key: 'm|' + p.id })),
    render: ({ p }) => {
      const distractors = shuffle(PREPS.filter(o => o.id !== p.id)).slice(0, 3);
      const ex = p.examples && p.examples[0];
      return {
        chip: 'Preposition · ' + p.type,
        gloss: p.type,
        word: { lat: p.lat, ar: p.ar },
        ask: { lat: 'meaning in English', ar: 'المعنى' },
        answer: { lat: p.en, ar: '' },
        options: distractors.map(d => ({ lat: d.en, ar: '' })),
        plain: true,
        whyHtml: esc(p.note) + (ex ? '<div class="ex"><strong>Example:</strong> ' + esc(ex.lat) + ' <em>(' + esc(ex.en) + ')</em></div>' : ''),
      };
    },
  },
  endings: {
    n: 2, title: 'Pronoun endings', sub: 'm3aya, lih, fiha, menna, 3ndkum, blak...',
    intro: '<p>Prepositions attach pronoun suffixes, but with distinct sound changes: <strong>l</strong> becomes <em>liya, lik, lih...</em>; <strong>f</strong> becomes <em>fiya, fik...</em>; <strong>men</strong> doubles the n: <em>menni, mennek, menna...</em>; <strong>3la</strong> becomes <em>3liya, 3lik...</em>; <strong>bin</strong> adds -at- in the plural: <em>binatna, binatkum, binathum</em>.</p>',
    pool: () => PREPS.filter(p => p.with_pronouns).flatMap(p => st.prons.map(i => ({ p, i, key: 'e|' + p.id + '|' + i }))),
    render: ({ p, i }) => {
      const pron = PREP_PRONS[i];
      const correctLat = p.pronouns.lat[i];
      const correctAr = p.pronouns.ar[i];
      const alts = [
        ...(p.pronouns.altLat && p.pronouns.altLat[i] ? [p.pronouns.altLat[i]] : []),
        ...(p.pronouns.altAr && p.pronouns.altAr[i] ? [p.pronouns.altAr[i]] : []),
      ];

      // Distractors: other persons of the same preposition
      const otherPersons = p.pronouns.lat
        .map((lat, j) => ({ lat, ar: p.pronouns.ar[j] }))
        .filter((_, j) => j !== i);

      return {
        chip: 'Pronoun ending',
        gloss: p.en,
        word: { lat: p.lat, ar: p.ar },
        ask: { lat: pron.lat, ar: pron.ar, en: pron.en },
        answer: { lat: correctLat, ar: correctAr },
        options: shuffle(otherPersons).slice(0, 3),
        accept: [correctLat, correctAr, ...alts],
        whyHtml: esc(p.note),
        after: () => formTable(p.lat + ' · with pronoun endings', PREP_PRONS.map(pr => pr.lat + ' (' + pr.en + ')'), p.pronouns.lat, p.pronouns.ar, i),
      };
    },
  },
  collocations: {
    n: 3, title: 'Verb collocations', sub: 'fkkr f, qllb 3la, tlaqa m3a, khaf men, sm7 l...',
    intro: '<p>Many Darija verbs require a specific preposition: you think <em>in</em> something (<strong>fkkr f</strong>), look <em>on</em> something (<strong>qllb 3la</strong>), and joke <em>with</em> someone (<strong>d7k m3a</strong>) but mock / laugh <em>at</em> someone with <strong>d7k 3la</strong>.</p>',
    pool: () => COLLOCS.map((c, idx) => ({ c, key: 'c|' + idx + '|' + c.verb + '|' + c.prep })),
    render: ({ c }) => {
      const verbObj = { lat: c.verb, ar: c.verbAr };
      const prepChoice = PREP_MAP[c.prep] || { lat: c.prep, ar: c.prepAr };
      const distractors = shuffle(['f', '3la', 'm3a', 'men', 'l', 'b'].filter(p => p !== c.prep)).slice(0, 3)
        .map(p => PREP_MAP[p] || { lat: p, ar: p });

      return {
        chip: 'Verb collocation',
        gloss: c.verb + ' (' + c.en + ') → ' + c.meaning,
        word: verbObj,
        ask: { lat: c.exampleBlank, en: c.exampleEn },
        answer: { lat: prepChoice.lat, ar: prepChoice.ar },
        options: distractors,
        accept: [c.prep, c.prepAr, prepChoice.lat, prepChoice.ar],
        whyHtml: '<strong>' + esc(c.verb) + '</strong> takes <strong>' + esc(c.prep) + '</strong> to mean &ldquo;' + esc(c.meaning) + '&rdquo;.<div class="ex"><strong>Example:</strong> ' + esc(c.exampleLat) + ' <em>(' + esc(c.exampleEn) + ')</em></div>',
      };
    },
  },
  idioms: {
    n: 4, title: 'Idioms & States', sub: 'fiya j-ju3, 3ndi flus, thlla f rask...',
    intro: '<p>Prepositions power everyday Darija phrases: <strong>f</strong> expresses sensations and illnesses (<em>fiya j-ju3</em> = I am hungry, <em>fih s-skhana</em> = he has a fever); <strong>3nd</strong> expresses possession (<em>3ndi flus</em>); <strong>3la</strong> expresses obligation (<em>3liya n-mshi</em>); and polite greetings use <em>sm7 liya</em> and <em>bla jmil</em>.</p>',
    pool: () => IDIOMS.map(im => ({ im, key: 'i|' + im.id })),
    render: ({ im }) => {
      const distractors = shuffle(IDIOMS.filter(o => o.id !== im.id)).slice(0, 3).map(o => ({ lat: o.lat, ar: o.ar }));
      return {
        chip: 'Idiom · ' + im.pattern,
        gloss: im.note,
        word: { lat: im.prompt, ar: '' },
        ask: { lat: im.prompt, en: im.en },
        answer: { lat: im.lat, ar: im.ar },
        options: distractors,
        accept: [im.lat, im.ar],
        why: im.note + (im.src ? ' (' + im.src + ')' : ''),
      };
    },
  },
};

let q = null, cache = null;
const hasPronFilter = () => st.module === 'endings';

function syncProns() {
  $('pronBox').hidden = !hasPronFilter();
  $('prons').querySelectorAll('button').forEach((b, i) => b.setAttribute('aria-pressed', String(st.prons.includes(i))));
  $('pronSummary').textContent = 'Pronouns (' + st.prons.length + ' of ' + PREP_PRONS.length + ')';
}

function toggle(arr, x) {
  const k = arr.indexOf(x);
  if (k >= 0) arr.splice(k, 1);
  else arr.push(x);
}

function pronsChanged() {
  st.prons.sort((a, b) => a - b);
  st.save();
  cache = null;
  syncProns();
  q.next();
}

PREP_PRONS.forEach((pr, i) => {
  const b = document.createElement('button');
  b.type = 'button';
  b.innerHTML = esc(pr.lat) + '<small>' + esc(pr.en) + '</small>';
  b.addEventListener('click', () => {
    if (st.prons.includes(i) && st.prons.length === 1) return;
    toggle(st.prons, i);
    pronsChanged();
  });
  $('prons').appendChild(b);
});

$('pronAll').addEventListener('click', () => {
  st.prons = PREP_PRONS.map((_, i) => i);
  pronsChanged();
});

function progress(id) {
  const saved = load('preps-' + id, { weights: {} });
  const items = MODULES[id].pool();
  if (!items.length) return 0;
  const learned = items.filter(c => saved.weights[c.key] < 1).length;
  return Math.round(100 * learned / items.length);
}

function drawModules() {
  $('modules').innerHTML = Object.entries(MODULES).map(([id, m]) =>
    '<button type="button" class="module" data-id="' + id + '" aria-pressed="' + (st.module === id) + '"><span class="n">' + m.n + '</span><span class="t"><b>' + esc(m.title) + '</b><span>' + esc(m.sub) + '</span></span><span class="pct">' + progress(id) + '%</span></button>'
  ).join('');

  $('modules').querySelectorAll('.module').forEach(b => b.addEventListener('click', () => {
    st.module = b.dataset.id;
    st.save();
    start();
  }));
}

function start() {
  const m = MODULES[st.module] || MODULES.meanings;
  drawModules();
  $('introText').innerHTML = m.intro + '<p><a href="rules.html#prepositions">All preposition rules</a></p>';
  cache = null;
  syncProns();
  q = quiz($('quiz'), {
    name: 'preps-' + st.module,
    pool: () => (cache ||= m.pool()),
    render: m.render,
  });
  q.next();
}

start();
