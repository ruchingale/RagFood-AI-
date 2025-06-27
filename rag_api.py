import os

if "HOME" not in os.environ and "USERPROFILE" in os.environ:
    os.environ["HOME"] = os.environ["USERPROFILE"]

import json

import chromadb
import requests
from clarifai.client.model import Model
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Load Clarifai PAT from .env
load_dotenv()
CLARIFAI_PAT = os.getenv("CLARIFAI_PAT")
if not CLARIFAI_PAT:
    raise ValueError("CLARIFAI_PAT is missing in your .env file!")

EMBED_MODEL_URL = "https://clarifai.com/mixedbread-ai/embed/models/mxbai-embed-large-v1"
embed_model = Model(url=EMBED_MODEL_URL, pat=CLARIFAI_PAT)

def get_embedding(text):
    try:
        prediction = embed_model.predict_by_bytes(text.encode("utf-8"), input_type="text")
        return prediction.outputs[0].data.embeddings[0].vector
    except Exception as e:
        print("❌ Embedding error:", e)
        return []

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "foods"
JSON_FILE = "foods.json"
LLM_MODEL = "llama3.2"

with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

existing_ids = set(collection.get()['ids'])
new_items = [item for item in food_data if item['id'] not in existing_ids]

if new_items:
    print(f"🆕 Adding {len(new_items)} new documents to Chroma...")
    for item in new_items:
        enriched_text = item["text"]
        if "region" in item:
            enriched_text += f" This food is popular in {item['region']}."
        if "type" in item:
            enriched_text += f" It is a type of {item['type']}."
        emb = get_embedding(enriched_text)
        if emb:
            collection.add(
                documents=[item["text"]],
                embeddings=[emb],
                ids=[item["id"]]
            )
else:
    print("✅ All documents already in ChromaDB.")

def rag_query(question):
    q_emb = get_embedding(question)
    if hasattr(q_emb, "tolist"):
        q_emb = q_emb.tolist()
    if not isinstance(q_emb, list):
        q_emb = list(q_emb)
    if not q_emb or not isinstance(q_emb[0], float):
        print("❌ Invalid embedding returned for query:", q_emb)
        return "Embedding failed."
    results = collection.query(query_embeddings=[q_emb], n_results=3)
    top_docs = results['documents'][0]
    context = "\n".join(top_docs)
    prompt = f"""Use ONLY the following context to answer the question. If the answer is not in the context, say "I don't know".

Context:
{context}

Question: {question}
Answer:"""
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"].strip()

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
async def ask_question(request: Request):
    data = await request.json()
    question = data.get("question", "")
    answer = rag_query(question)
    return {"answer": answer}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)