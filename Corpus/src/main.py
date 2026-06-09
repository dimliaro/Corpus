# #Code for correct chunking
# if __name__ == "__main__":
#     chunks = getPagesFromPdf("data/32016R0679_EN.pdf")
#     recitals = [c for c in chunks if c.type == "recital"]
#     articles = [c for c in chunks if c.type == "article"]
#     print(f"Total chunks: {len(chunks)}  ({len(recitals)} recitals, {len(articles)} articles)\n")
#     for c in chunks:
#         header = f"[{c.type.upper()} {c.number}]"
#         if c.title:
#             header += f" {c.title}"
#         if c.chapter:
#             header += f"  |  {c.chapter}"
#         header += f"  (p.{c.page})"
#         print(header)
#         print(c.text[:300].replace("\n", " ").strip())
#         print()
#     print(len(chunks))
# #

"""
04.
main.py
creates the embeddings and saves them in AI Search

"""

from embedding import createEmbedding
from chunk_iracleous import (getPagesFromPdf, getChunks)
from saveToIndex import saveToSearchIndex

pdf_file = "data/32016R0679_EN.pdf"
index = "team06_test"


if __name__=="__main__":
    text = getPagesFromPdf(pdf_file)
    chunks = getChunks(text)

    for index, chunk in enumerate(chunks):
        embedding = createEmbedding(chunk)
        saveToSearchIndex(
            index, 
            str(index),
            chunk,
            embedding
        )

