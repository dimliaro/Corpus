"""
file:2.embedding


"""

from dotenv import load_dotenv
import os

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("EMBEDDING_MODEL_NAME")
deployment = os.getenv("EMBEDDING_MODEL_NAME")
api_key =  os.getenv("AZURE_OPENAI_API_KEY")
api_version=os.getenv("AZURE_OPENAI_API_VERSION")


from openai import AzureOpenAI

def createEmbedding(text: str)->list:

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version
    )

    response = client.embeddings.create(
        model=deployment,
        input=text
    )
    embedding = response.data[0].embedding
    return embedding


if __name__=="__main__":
    text = "hello"
    embed = createEmbedding(text)
    print(embed)