"""

fastapi
cd src
uvicorn rag_api:app --reload

"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from search import getResults, RagResponse
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Models ────────────────────────────────────────────────────────────────────

class RequestText(BaseModel):
    prompt: str

class ResponseText(BaseModel):
    prompt: str
    chunks: list[str]

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    prompt: str

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Corpus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend at /
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("../frontend/index.html")

# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/query")
def query(request: RequestText) -> ResponseText:
    try:
        result = getResults(request.prompt)
        return ResponseText(prompt=request.prompt, chunks=result.retrieved_chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


SYSTEM_PROMPT = """You are Corpus, an expert AI assistant specializing in EU legal documents — \
in particular the General Data Protection Regulation (GDPR, Regulation (EU) 2016/679) and \
related EU regulations.

Your job is to answer questions accurately and clearly, drawing exclusively from the source \
excerpts provided. When relevant, cite the Article or Recital number. \
Write in a professional yet accessible tone. \
If the provided sources do not contain enough information to answer the question, say so honestly \
and explain what you do know from them."""


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    try:
        # Retrieve relevant chunks from Azure AI Search
        rag_result = getResults(request.prompt)
        chunks = rag_result.retrieved_chunks

        context = "\n\n---\n\n".join(
            f"[Source {i + 1}]\n{chunk}" for i, chunk in enumerate(chunks)
        )

        llm = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question: {request.prompt}\n\n"
                    f"Relevant excerpts from EU documents:\n\n{context}\n\n"
                    "Please provide a clear, accurate answer based only on the above sources."
                ),
            },
        ]

        completion = llm.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=messages,
            temperature=0.1,
            max_tokens=1200,
        )

        answer = completion.choices[0].message.content

        return ChatResponse(answer=answer, sources=chunks, prompt=request.prompt)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
