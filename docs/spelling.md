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
| [DODa](https://github.com/darija-open-dataset/dataset) (CC BY-NC 4.0) | the human-written rows only: `sentences/sentences.csv`, `ongoing/*.csv`, `x-tra/shorts.csv` (not the model-written DODa-500K) | about 147k rows, 439k words |
| [atlasia/Atlaset](https://huggingface.co/datasets/atlasia/Atlaset) (gated) | Latin-script rows from real sources, almost all Facebook comments | about 6k rows, 44k words |

Atlaset is gated: accept its terms on Hugging Face while logged in, then download the five train
shards, `data/train-00000-of-00005.parquet` to `data/train-00004-of-00005.parquet` (about 1.1 GB), into
one folder. Leave out the test shard: the script reads every `*.parquet` in the folder. For example,
`hf download atlasia/Atlaset --repo-type dataset --include "data/train-*.parquet" --local-dir atlaset`
puts them in `atlaset/data`. A row is kept when:

- its `dataset_source` starts with `atlasia/Social_Media_Darija_DS`, `atlasia/facebook_darija_dataset`,
  `MTCD`, `MAC Corpus`, `common-crawl`, `bourbouh/moroccan-darija-youtube-subtitles` or
  `darija_youtube_subtitles`: written by people, not translated or model-written (the other sources
  are instruction sets, Wikipedia, summaries and the like);
- it has at least 6 Latin letters and Arabic letters (U+0600 to U+06FF) are under a quarter of the
  letters. Most Atlaset text is Arabic script, and this leaves 6,052 of its rows. Arabic
  presentation forms (the Arabic seen in some `common-crawl` rows) are not counted as Arabic here.

The counts are stored in `data/raw/spelling_counts.json` (words seen at least 3 times), so the map can
be rebuilt without the downloads. To recount (pyarrow is only needed for `--atlaset`, and is not a
dependency of the site scripts; it takes about 30 seconds):

```sh
uv run --with pyarrow python3 scripts/spelling.py --doda path/to/dataset --atlaset path/to/atlaset/data
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
| after | b3d | b3d 78, be3d 36 |
| coffee | qehwa | qehwa 45, qhwa 45 (close: more schwa wins) |

**Exception: a short list of words keeps its doubled letter**, against the counts. Native writers often
drop doubling (`mli` 555, `mlli` 27), but these words are pronounced doubled and learners should see that:

| Word | Site | Counts |
|---|---|---|
| until | 7tta | 7ta 265, 7tta 39 |
| when | mlli | mli 555, mlli 27 |
| there | tmma | tma 220, tmma 22 |
| working | khddam, khddama | khdam 143, khddam 27 |
| like this | hakka | haka 221, hakka 33 |
| shoes | sebbat | sbat 24, sbbat 8 |
| tomorrow | ghedda | ghda 331, ghedda 17 |

The list is in `force` in `data/raw/spelling.json`. DODa's Arabic can't settle this per word: its shadda
marks follow the same writer's Latin (64% of doubled Latin rows have one, 0.8% of undoubled rows), and
the common words never reach a useful share (`7ta` 4%, `mli` 2%). `ghedda` also keeps tomorrow apart
from lunch, which stays `ghda` / `l-ghda`.

A doubled first letter is never treated as optional: `mmi` (my mother) and `mi`, `bba` (my father)
and `ba` are different words. Neither are stretched vowels (`bzaaaf`) or text-message abbreviations
(`bzf`): they never win.

## Words

- **and** is `w`, its own word: `khuya w sa7bu`, `tnin w 3achrin`. This is a choice against the
  counts (`u` 3,421, written `ou` or `o`, vs `w` 723), kept for now because `w` is the site's
  long-standing spelling and reads as one letter, و.
- **The article** takes a hyphen and copies a sun letter: `l-ktab`, `d-dar`, `ch-chems`, `t-tumubil`.
  This is grammar, not a count (corpus writers rarely mark it), so the site keeps it. The sun letters
  are the ones in `SUN` in `scripts/build_nouns.py`: `t d r z s ch n l j`. The article is that letter before
  a stem that starts with it (`j-jar`, `l-lila`) and `l-` before any other letter (`l-jornal` is
  `j-jornal`, `l-bab` stays). `canon()` fixes a wrong one (`l-dar`, `s-chems`), also on `keep` words.
  When the article is written glued to a stem the site uses with it (`lbare7`, `jjay`), `canon()` adds the
  hyphen, using the `glued` table in `data/spelling.json`: stems seen at least 3 times with the article.
  A word that is itself a stem (`lila`, `l7em`, `lun`) or a verb form is left alone.
- **f, l, b, mn, 3la** are separate words before a noun: `f d-dar`, `l s-suq`, `b t-tobis`.
- **Pronoun tables** are chosen as a whole, so a table never mixes spellings: `mn` gives `mni, mnek, mnu,
  mnha, mna, mnkum, mnhum`, and `qdam` gives `qdami, qdamek, ...`. `table_force()` in `scripts/spelling.py`
  tries the table with and without schwa, doubled letters and the `-ek` of "your". A version replaces the
  table as written only if the forms it changes have at least 20 hits and 1.5 times the hits of the forms
  they replace. That's how `dyalk` (508 vs `dyalek` 19) and `3ndk` come out, while `rasek` stays. The
  headword follows its table, which is how `3nd` beats `3end` and work becomes `khdma` (`khdmti` 23 vs
  `khedmti` 3). Tables keep the regular change before an ending (`rajel`, `rajli`; `wjeh`, `wejhi`).
- **Negation** wraps the verb with `ma ... ch`: `ma ktebtch`, `ma ghadich nkteb`.

## Arabic script

Arabic letters only, no diacritics. The article is always ال. f, l, b join the next word the way
Moroccans write them (فالدار, للسوق, بالطوبيس). The future marker is غادي. The Arabic does not
change with the Latin spelling: schwa and doubled letters are not written in it.

The one exception to "no diacritics" is the shadda in the possessives of `bba` and `mmi` (`مّي`,
`بّا`), which `data/nouns.json` keeps on purpose. A lone ف, ل or ب is only the preposition itself
(its own entry in `data/prepositions.json`); inside a phrase it is joined. `ل` + `ال` drops the alef
(`للسوق`, `لليل`). `clean_ar()` in `scripts/spelling.py` applies the diacritic and joining rules, and
`build_examples.py` runs it on every sentence's Arabic.

Not enforced: that the Arabic has the same number of words as the Latin. Once f, l, b and w are
joined the two sides agree everywhere, but the check needs a hyphen-aware tokenizer to be worth a test.

## Hand-made choices

`data/raw/spelling.json`:

- `keep`: words left as they are, mostly the French loanwords above.
- `force`: a spelling chosen by hand, with the variants it replaces. Used where the model wrote a
  word the corpus spells differently (`bzzef`, `hed` for `bezzaf`, `had`), for loanwords
  (`otel` → `otil`), for **and** (`u` → `w`), and for the doubled words above.
- `tokens`: whole-word rewrites where the article decides the word (`l-gheda` → `l-ghda`, lunch).
- `distinct`: spellings that look like variants of each other but are different words (`merra` once,
  `mra` woman; `sirr` secret, `sir` go; `qllb` look for, `qelb` heart).

## How it is applied

1. `scripts/spelling.py` turns the counts and `data/raw/spelling.json` into `data/spelling.json`:
   for each word, the site's spelling, how it was chosen (`corpus`, `schwa`, `table`, `manual`) and the counts.
2. `canon()` rewrites arabizi text to those spellings. `build_nouns.py`, `build_prepositions.py`,
   `build_words.py` and `build_examples.py` run it on everything they write.
3. `tests/test_spelling.py` fails if any generated data uses a spelling the map rewrites, uses `9`, or
   uses `o` outside the `keep` list, or if an article does not copy its sun letter. It also checks page text and notes (below).
4. `tests/test_arabic.py` fails on Latin letters or digits in any Arabic string, diacritics (other than
   the shadda above), a lone ال, a lone ف / ل / ب inside a phrase, and a future sentence without غادي.
5. The example prompts (`STYLE` in `scripts/build_examples.py`, shared with `gemini_batch.py` and
   `review_examples.py`) state the letter rules and list the words the model has misspelled before.

**Verbs follow rules, not counts.** Conjugated forms keep the spelling `scripts/build_verbs.py` gives them,
and `canon()` never rewrites them. Only 3.7% of forms have enough data to decide, and following the
counts would make tables uneven (`wselt wslti wslti wsel weslat wslna`) and merge different verbs
(`qder` can, `qedder` estimate). The one exception is the particle `bli` (`bli` 294, `blli` 8), which
`build_verbs.py` writes to match the rest of the site.

Page text is checked in part: the test takes the static `<strong>` / `<em>` text in `assets/*.js` and
`*.html` and the `note` fields of `data/raw/*.json`, and checks only words that must be arabizi: a digit
(`d7k`), an article hyphen (`t-tebla`), or a variant in the map (`menni`, `qddam`, `u`). English cannot be
told apart reliably (`canon()` turns `for` into `fur`), so the test does not check the rest.

Not covered: plain arabizi words with no digit, hyphen or map entry (`sokkar`, `mor`), words in notes
whose only difference is a letter rule (`o`), the Peace Corps `x` (the test rejects it, `canon()` does not rewrite it), and
any other page text (`<code>`, headings, paragraphs).
