"""
01. chunking.py

"""

import fitz

def getPagesFromPdf(filename: str) -> str:
    doc = fitz.open(filename)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text:
            pages.append(text.strip())
    doc.close()
    return "\n\n".join(pages)


def getChunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[str]:

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (
            chunk_size -
            chunk_overlap
        )

    return chunks





"""
01. chunking.py

"""

import fitz

 
def getPagesFromPdf(filename: str) -> str:
    doc = fitz.open(filename)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text:
            pages.append(text.strip())
    doc.close()
    return "\n\n".join(pages)


def getChunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[str]:

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (
            chunk_size -
            chunk_overlap
        )

    return chunks





 