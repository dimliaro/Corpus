"""
05
search tool

"""


from pydantic import BaseModel

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from embedding import createEmbedding

import os

load_dotenv()



client = SearchClient(
        endpoint=os.getenv("AI_SEARCH_ENDPOINT"),
        index_name="team06_test",
        credential=AzureKeyCredential(os.getenv("AI_SEARCH_API_KEY"))
    )

class RagResponse(BaseModel):
    question: str
    retrieved_chunks: list[str]

def getResults(text:str)->RagResponse:
    query_vector =  createEmbedding(text)
    results = client.search(
    search_text=None,
    vector_queries=[
        VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=3,
            fields="embedding"
        )
    ],

    select=[
        "chunk_id",
        "chunk_text"
    ]
    )
    retrieved_chunks=[]
    for row in results:
       retrieved_chunks.append(row["chunk_text"])

    return  RagResponse(
        question=text, 
        retrieved_chunks=retrieved_chunks
   )
   
if __name__=="__main__":
    prompt = "What are my rights as consumer"
    results = getResults(prompt)

    for chunk in results.retrieved_chunks:
        print(chunk)