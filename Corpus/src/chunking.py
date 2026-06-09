import re
from dataclasses import dataclass
from typing import Optional

import pymupdf as fitz


pdf_files = "/data/32016R0679"


@dataclass
class Chunk:
    text: str
    type: str          # "recital" | "article"
    number: str        # e.g. "42" or "173"
    title: Optional[str]   # article title; None for recitals
    chapter: Optional[str] # e.g. "CHAPTER III — Rights of the data subject"
    page: int


def getPagesFromPdf(filename: str) -> list[Chunk]:
    """
    Parse a EU regulation PDF and return one Chunk per recital and per article.

    EU regulations follow a fixed structure:
      • Preamble/recitals  — numbered "(1)  text…" lines before HAVE ADOPTED
      • Normative body     — CHAPTER [Roman] > Article [N] > paragraphs
    """
    doc = fitz.open(filename)

    # Build concatenated full text and record where each page starts.
    full_text = ""
    page_offsets: list[int] = []
    for page in doc:
        page_offsets.append(len(full_text))
        full_text += page.get_text("text")

    def offset_to_page(offset: int) -> int:
        for i in range(len(page_offsets) - 1, -1, -1):
            if offset >= page_offsets[i]:
                return i + 1
        return 1

    # Locate the boundary between recitals and normative text.
    adopt_marker = "HAVE ADOPTED THIS REGULATION"
    adopt_idx = full_text.find(adopt_marker)
    if adopt_idx == -1:
        raise ValueError(f"Marker '{adopt_marker}' not found in {filename}")

    recital_text = full_text[:adopt_idx]
    normative_text = full_text[adopt_idx:]
    normative_offset = adopt_idx

    chunks: list[Chunk] = []

    # ── Recitals ──────────────────────────────────────────────────────────────
    # Format: "(1)  \nText…"  or  "(100)  Text…"  — always 2+ spaces after ')'
    recital_re = re.compile(r"^\((\d+)\) {2,}", re.MULTILINE)
    recital_markers = list(recital_re.finditer(recital_text))

    for i, m in enumerate(recital_markers):
        end = recital_markers[i + 1].start() if i + 1 < len(recital_markers) else len(recital_text)
        text = recital_text[m.start():end].strip()
        chunks.append(Chunk(
            text=text,
            type="recital",
            number=m.group(1),
            title=None,
            chapter=None,
            page=offset_to_page(m.start()),
        ))

    # ── Normative articles ────────────────────────────────────────────────────
    # Each line in the PDF ends with a trailing space before \n.
    # Chapters:  "\nCHAPTER I \nGeneral provisions \n"
    # Articles:  "\nArticle 1 \nSubject-matter and objectives \n"
    chapter_re = re.compile(r"\nCHAPTER ([IVXLCDM]+) \n(.*?) \n")
    article_re = re.compile(r"\nArticle (\d+) \n(.*?) \n")

    markers: list[tuple[str, int, str, str]] = []
    for m in chapter_re.finditer(normative_text):
        markers.append(("chapter", m.start(), m.group(1), m.group(2).strip()))
    for m in article_re.finditer(normative_text):
        markers.append(("article", m.start(), m.group(1), m.group(2).strip()))

    markers.sort(key=lambda x: x[1])

    current_chapter: Optional[str] = None

    for i, (mtype, pos, num, title) in enumerate(markers):
        if mtype == "chapter":
            current_chapter = f"CHAPTER {num} — {title}"
            continue

        # Article text spans from this marker to the next chapter/article marker.
        end = markers[i + 1][1] if i + 1 < len(markers) else len(normative_text)
        text = normative_text[pos:end].strip()

        chunks.append(Chunk(
            text=text,
            type="article",
            number=num,
            title=title,
            chapter=current_chapter,
            page=offset_to_page(normative_offset + pos),
        ))

    return chunks


if __name__ == "__main__":
    chunks = getPagesFromPdf("data/32016R0679_EN.pdf")
    recitals = [c for c in chunks if c.type == "recital"]
    articles = [c for c in chunks if c.type == "article"]
    print(f"Total chunks: {len(chunks)}  ({len(recitals)} recitals, {len(articles)} articles)\n")
    for c in chunks:
        header = f"[{c.type.upper()} {c.number}]"
        if c.title:
            header += f" {c.title}"
        if c.chapter:
            header += f"  |  {c.chapter}"
        header += f"  (p.{c.page})"
        print(header)
        print(c.text[:300].replace("\n", " ").strip())
        print()
    print(len(chunks))