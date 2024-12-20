from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
import uuid
from typing import List, Optional
import anthropic
import os
import sys
sys.path.append("../../")
from utils.message_batching import MessageBatcher

app = FastAPI()
client = chromadb.Client()
collection = client.create_collection("documents")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
message_batcher = MessageBatcher(api_key=ANTHROPIC_API_KEY)
message_batcher.start()

class Document(BaseModel):
    text: str
    metadata: Optional[dict] = None

class Query(BaseModel):
    question: str
    n_results: int = 3

@app.post("/add_document")
async def add_document(document: Document):
    doc_id = str(uuid.uuid4())
    collection.add(
        documents=[document.text],
        metadatas=[document.metadata or {}],
        ids=[doc_id]
    )
    return {"document_id": doc_id}

@app.post("/query")
async def query_documents(query: Query):
    results = collection.query(
        query_texts=[query.question],
        n_results=query.n_results
    )
    
    context = "\n".join(results["documents"][0])
    system = "You are a helpful AI assistant that answers questions based on the provided context."
    prompt = f"""Context: {context}\n\nQuestion: {query.question}\n\nPlease answer the question based on the context provided."""
    
    answer = await message_batcher.add_message(system, prompt)
    
    return {
        "answer": answer,
        "source_documents": results["documents"][0],
        "metadata": results["metadatas"][0]
    }