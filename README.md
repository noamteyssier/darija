# Darija Drills

Static site for drilling Moroccan Arabic (Casablanca / Rabat Darija): verb conjugation, possessives,
gender and plurals, in arabizi and Arabic script. No build step for the site itself; GitHub Pages
serves the repo root as is (Settings → Pages → Deploy from branch → `main` / root).

## Run locally

Pages load JSON with `fetch`, so open them through a server, not `file://`:

```sh
python3 -m http.server 8765
```

## Layout

```
index.html verbs.html nouns.html dictionary.html rules.html
assets/                shared CSS and ES modules (common.js, quiz.js, one module per page)
data/verbs.json        706 verbs with full past and present paradigms (generated)
data/nouns.json        nouns and adjectives with possessive, dyal, definite and plural forms (generated)
data/raw/              hand-edited inputs
scripts/               generators
tests/                 python3 -m unittest discover tests
```

## Data

Verbs come from the Peace Corps Morocco *Moroccan Arabic* (2011) verb glossary (pp. 163–192),
which lists each verb with its "I" present and past form.

1. `scripts/extract_glossary.py <pdf>` pulls the glossary into `data/raw/pc_glossary.tsv`
   (needs `pypdf`: `uv run --with pypdf python scripts/extract_glossary.py ...`).
2. `scripts/build_verbs.py` sorts each verb into a type (regular, hollow, ends in a vowel,
   doubled, hamza...), places the schwa the book leaves out, converts to arabizi, spells the
   Arabic, and writes all 8 persons for past and present to `data/verbs.json`.
   The future is built in the browser (ghadi + present without ka-).
   - `data/raw/verb_notes.json`: corrections, exclusions and better glosses, keyed by the book's spelling.
   - `data/raw/verb_tags.json`: levels (Starter, Everyday; everything else is Extended) and topics.
3. `scripts/build_nouns.py` turns `data/raw/nouns.json` into `data/nouns.json`.

After editing anything in `data/raw/`, rebuild and test:

```sh
python3 scripts/build_verbs.py && python3 scripts/build_nouns.py && python3 -m unittest discover tests
```

Spelling: arabizi with 3 = ع, 7 = ح, gh = غ, kh = خ, q = ق, sh = ش; `e` is the short schwa.
Typed answers ignore schwa, doubled letters and spaces, and also accept the book's letters
(š x ġ ع н).
