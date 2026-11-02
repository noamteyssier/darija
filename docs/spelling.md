# Spelling

Darija has no standard spelling. On this site every word is spelled one way, everywhere: data,
example sentences, page text and generators. Where people really do disagree, the site follows
what Moroccans write most often. Where counting would give the wrong answer, a fixed rule decides,
and each such rule is listed below with its reason.

Typed answers are forgiving either way: `norm()` in `assets/common.js` accepts `sh` / `ch`, `9` / `q`,
`ou` / `u`, extra or missing `e` and doubled letters. This page is about what the site displays.

## Where the counts come from

`scripts/spelling.py` counts every Latin-script word in two collections of Darija written by people:

| Source | What | Size |
|---|---|---|
| [DODa](https://github.com/darija-open-dataset/dataset) (MIT) | the human-written rows only: `sentences/sentences.csv`, `ongoing/*.csv`, `x-tra/shorts.csv` (not the model-written DODa-500K) | about 147k rows, 439k words |
| [atlasia/Atlaset](https://huggingface.co/datasets/atlasia/Atlaset) (gated) | Latin-script rows from real sources, almost all Facebook comments | about 6k rows, 44k words |

The counts are stored in `data/raw/spelling_counts.json` (words seen at least 3 times), so the map can
be rebuilt without the downloads. To recount:

```sh
python3 scripts/spelling.py --doda path/to/dataset --atlaset atlaset_latin.tsv
```

## Letters: fixed rules

Before counting, every corpus word is rewritten in the site's letters, so these choices are never
a vote between spellings.

| Sound | Site | Also written | Why |
|---|---|---|---|
| ش | **ch** | sh | The counts: 96% of DODa words with this sound use `ch` (`wach` 3,839 vs `wash` 197, `ma ... ch` 9,489 vs `ma ... sh` 251). It also frees `sh` for a real s + h (`sher`, stay up late), which used to need an apostrophe. |
| ق | **q** | 9 | Kept against the counts (DODa writes `9` 98% of the time). A digit inside a word is noise for a learner, and `q` is unambiguous. |
| /u/ | **u** | o, ou | Kept against the counts (DODa writes `ou` or `o` most of the time). `o` and `ou` come from French spelling, not from a different sound: one Arabic letter, و, and no Darija word changes meaning between them. Counting word by word gives a patchwork (`kol` but `mul`, `yom` but `yumayn`) that a learner cannot predict. |
| خ | **kh** | 5 | The counts agree (75%). |
| ع ح | **3 7** | | Universal. |
| غ | **gh** | | Universal. |

**French loanwords keep `o`**: `t-tobis`, `s-salon`, `l-otil`, `stilo`. They are listed under `keep`
in `data/raw/spelling.json`, which `canon()` leaves alone.

French habits are not counted as variants: `ss` written to keep an `s` from sounding like `z`
(`madrassa`) counts as `s`, and a final `e` (`tajine`) never wins.

## Vowels and doubled letters: counted

Spellings that differ only in schwa (`e`) or in doubled letters are one word. The spelling written
most often wins when it has at least 20 hits and at least 1.5 times the next one. When two are close,
the one that writes more schwa wins (it is easier to read aloud).

| Word | Site | Counts |
|---|---|---|
| good | mzyan | mzyan 548, mezian 28, mezyan 24 |
| early | bkri | bkri 149, bekri 72 |
| until | 7ta | 7ta 265, 7tta 39, 7etta 4 |
| when | mli | mli 555, mlli 27, meli 8 |
| tomorrow | ghda | ghda 331, gheda 125, ghdda 35, ghedda 17 |
| after | b3d | b3d 78, be3d 36 |
| work | khedma | khedma 323, khdma 316 (close: more schwa wins) |
| coffee | qehwa | qehwa 45, qhwa 45 (close: more schwa wins) |

A doubled first letter is never treated as optional: `mmi` (my mother) and `mi`, `bba` (my father)
and `ba` are different words. Neither are stretched vowels (`bzaaaf`) or text-message abbreviations
(`bzf`): they never win.

## Words

- **and** is `w`, its own word: `khuya w sa7bu`, `tnin w 3achrin`. This is a choice against the
  counts (`u` 3,421, written `ou` or `o`, vs `w` 723), kept for now because `w` is the site's
  long-standing spelling and reads as one letter, و.
- **The article** takes a hyphen and copies a sun letter: `l-ktab`, `d-dar`, `ch-chems`, `t-tumubil`.
  This is grammar, not a count (corpus writers rarely mark it), so the site keeps it.
- **f, l, b, mn, 3la** are separate words before a noun: `f d-dar`, `l s-suq`, `b t-tobis`.
- **dyal** and pronoun endings follow the counts per word: `dyalk` (508 vs `dyalek` 19), `3ndk`, but
  `rasek` (close: more schwa wins). The same goes for nouns and prepositions with endings, which
  `scripts/build_nouns.py` and `scripts/build_prepositions.py` build and then pass through `canon()`.
- **Negation** wraps the verb with `ma ... ch`: `ma ktebtch`, `ma ghadich nkteb`.

## Arabic script

Arabic letters only, no diacritics. The article is always ال. f, l, b join the next word the way
Moroccans write them (فالدار, للسوق, بالطوبيس). The future marker is غادي. The Arabic does not
change with the Latin spelling: schwa and doubled letters are not written in it.

## Hand-made choices

`data/raw/spelling.json`:

- `keep`: words left as they are, mostly the French loanwords above.
- `force`: a spelling chosen by hand, with the variants it replaces. Used where the model wrote a
  word the corpus spells differently (`bzzef`, `hed` for `bezzaf`, `had`), for loanwords
  (`otel` → `otil`), and for **and** (`u` → `w`).
- `distinct`: spellings that look like variants of each other but are different words (`merra` once,
  `mra` woman; `sirr` secret, `sir` go; `qllb` look for, `qelb` heart).

## How it is applied

1. `scripts/spelling.py` turns the counts and `data/raw/spelling.json` into `data/spelling.json`:
   for each word, the site's spelling, how it was chosen (`corpus`, `schwa`, `manual`) and the counts.
2. `canon()` rewrites arabizi text to those spellings. `build_nouns.py`, `build_prepositions.py`,
   `build_words.py` and `build_examples.py` run it on everything they write.
3. `tests/test_spelling.py` fails if any generated data uses a spelling the map rewrites, uses `9`, or
   uses `o` outside the `keep` list.
4. The example prompts (`STYLE` in `scripts/build_examples.py`, shared with `gemini_batch.py` and
   `review_examples.py`) state the letter rules and list the words the model has misspelled before.

Not covered: conjugated verb forms keep the spelling `scripts/build_verbs.py` gives them, and
`canon()` never rewrites them. Page text in `assets/*.js` and `*.html` mixes English and arabizi, so
it was fixed by hand and is not tested.
