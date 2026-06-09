"""
03. savesToIndex

saves to index
"""
from embedding import createEmbedding


from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv


import os

load_dotenv()


def saveToSearchIndex(
        indexName: str,
        doc_id:str,
        chunk:str,
        embedding:list[float]
        )->None:

    search_client = SearchClient(
        endpoint=os.getenv("AI_SEARCH_ENDPOINT"),
        index_name="team06_test",
        credential=AzureKeyCredential(os.getenv("AI_SEARCH_API_KEY"))
    )

    document = {
    "chunk_id": doc_id,
    "chunk_text": chunk,
    "embedding": embedding
    }
 

    result = search_client.upload_documents(
    documents=[document]
    )

 
if __name__=="__main__":
   text = "hello"
   saveToSearchIndex("team06_test", 
                     "2",
                     text, 
                     createEmbedding(text)) 