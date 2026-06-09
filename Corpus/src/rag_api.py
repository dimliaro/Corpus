"""

fastapi
cd src
uvicorn rag_api:app --reload

"""

import os
import json
import fitz  # pymupdf
from fastapi import FastAPI, HTTPException, UploadFile, File
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
    document_context: str | None = None

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    prompt: str

class DocumentUploadResponse(BaseModel):
    valid: bool
    reason: str
    text: str
    filename: str

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


VALIDATION_PROMPT = """\
You are a document classifier for a legal AI system. \
Determine if the provided text excerpt is from an EU regulatory document. \
EU regulatory documents include: EU Regulations, EU Directives, EU Decisions, \
GDPR (Regulation 2016/679), AI Act, NIS2 Directive, eIDAS, Digital Services Act, \
Data Governance Act, or any other official EU legislative act. \
Respond with JSON only — no other text: {"valid": true or false, "reason": "one sentence"}"""

SYSTEM_PROMPT = """You are Corpus, an expert AI assistant specializing in EU legal documents — \
in particular the General Data Protection Regulation (GDPR, Regulation (EU) 2016/679) and \
related EU regulations.

Your job is to answer questions accurately and clearly, drawing exclusively from the source \
excerpts provided. When relevant, cite the Article or Recital number. \
Write in a professional yet accessible tone. \
If the provided sources do not contain enough information to answer the question, say so honestly \
and explain what you do know from them."""


@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")

    content = await file.read()

    if file.filename.lower().endswith('.pdf'):
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
        except Exception:
            raise HTTPException(status_code=400, detail="Could not read PDF file.")
    else:
        text = content.decode("utf-8", errors="replace")

    if len(text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable.")

    llm = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    try:
        validation = llm.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": VALIDATION_PROMPT},
                {"role": "user", "content": f"Document excerpt:\n\n{text[:2000]}"},
            ],
            temperature=0,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        result = json.loads(validation.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Validation service unavailable.")

    if not result.get("valid"):
        raise HTTPException(
            status_code=422,
            detail=result.get("reason", "This does not appear to be an EU regulatory document."),
        )

    return DocumentUploadResponse(
        valid=True,
        reason=result.get("reason", "Validated EU regulatory document."),
        text=text,
        filename=file.filename,
    )


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    try:
        # Retrieve relevant chunks from Azure AI Search
        rag_result = getResults(request.prompt)
        chunks = rag_result.retrieved_chunks

        rag_context = "\n\n---\n\n".join(
            f"[Indexed Source {i + 1}]\n{chunk}" for i, chunk in enumerate(chunks)
        )

        if request.document_context:
            context = f"[Uploaded Document]\n{request.document_context[:6000]}\n\n---\n\n{rag_context}"
        else:
            context = rag_context

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
