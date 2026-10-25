"""Extract the Peace Corps 'Glossary of Verbs' (pp. 163-192) into a TSV.

usage: uv run --with pypdf python scripts/extract_glossary.py <cherif.pdf> > data/raw/pc_glossary.tsv
Columns: page, english, pc (book transcription), pres1 (I, present), past1 (I, past)
"""
import re
import sys
import unicodedata

import pypdf

FIRST, LAST = 167, 196  # 0-based pdf page indices of the glossary


def main(path):
    reader = pypdf.PdfReader(path)
    rows: list[dict] = []
    for i in range(FIRST, LAST + 1):
        page = i - 4  # printed page number
        text = unicodedata.normalize("NFC", reader.pages[i].extract_text(extraction_mode="layout"))
        for line in text.splitlines():
            if not line.strip() or "Moroccan Arabic" in line or "Peace Corps" in line:
                continue
            if re.search(r"English|Present Tense|Glossary of Verbs|This glossary|possible for you", line):
                continue
            cols = re.split(r"\s{2,}", line.strip())
            kan = [j for j, c in enumerate(cols) if re.match(r"(ma-)?ka[nyt][- ]|عndi", c)]
            if not kan:
                # wrapped english text, belongs to the previous row's english
                if rows and rows[-1]["page"] == page:
                    rows[-1]["english"] += " " + line.strip()
                continue
            # a wrapped english line can share a physical line with the next rows
            j = kan[0]
            head, pres, past = cols[:j], cols[j], cols[j + 1] if j + 1 < len(cols) else ""
            # A long english column can collide with the transcription column (single space)
            if len(head) == 2:
                english, pc = head
            elif len(head) == 1:
                english, pc = ("", head[0]) if line.startswith("    ") else (None, head[0])
            else:
                english, pc = " ".join(head[:-1]), head[-1]
            if english is None:
                english, pc = split_single(head[0])
            rows.append({"page": page, "english": english, "pc": pc, "pres1": pres, "past1": past})
    for r in rows:
        for k in ("pc", "pres1", "past1"):
            r[k] = fix_rtl(r[k])
    english = ""
    print("page\tenglish\tpc\tpres1\tpast1")
    for r in rows:
        english = r["english"].strip() or english  # blank english = alternate verb for the previous gloss
        print(f'{r["page"]}\t{english}\t{r["pc"]}\t{r["pres1"]}\t{r["past1"]}')


def fix_rtl(s):
    """Undo glyph-order damage around the Arabic letter ع inside latin words:
    a doubled ع splits off (b ععd = bععd) and the dot of ṭ lands after ع (qtع̣ t = qṭعt)."""
    s = unicodedata.normalize("NFD", s)
    s = re.sub("t(ع+)\u0323", "t\u0323\\1", s)
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"(\S) (عع)", r"\1\2", s)
    s = re.sub(r"(ع) t$", r"\1t", s)
    return s


def split_single(s):
    """'acquaint with sth tعarf' -> english, transcription, when columns merged."""
    words = s.split()
    for k in range(len(words) - 1, 0, -1):
        if not all(w.isascii() for w in words[k:]):
            continue
        break
    return " ".join(words[:-1]), words[-1]


if __name__ == "__main__":
    main(sys.argv[1])
