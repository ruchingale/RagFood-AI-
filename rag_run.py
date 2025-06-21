import os
import json
import chromadb
import requests

# Constants
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "foods"
JSON_FILE = "foods.json"
EMBED_MODEL = "mxbai-embed-large"
LLM_MODEL = "llama3.2"

# Load data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

# Setup ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# Ollama embedding function
def get_embedding(text):
    response = requests.post("http://localhost:11434/api/embeddings", json={
        "model": EMBED_MODEL,
        "prompt": text
    })
    return response.json()["embedding"]

# Add only new items
existing_ids = set(collection.get()['ids'])
new_items = [item for item in food_data if item['id'] not in existing_ids]

if new_items:
    print(f"🆕 Adding {len(new_items)} new documents to Chroma...")
    for item in new_items:
        # Enhance text with region/type
        enriched_text = item["text"]
        if "region" in item:
            enriched_text += f" This food is popular in {item['region']}."
        if "type" in item:
            enriched_text += f" It is a type of {item['type']}."

        emb = get_embedding(enriched_text)

        collection.add(
            documents=[item["text"]],  # Use original text as retrievable context
            embeddings=[emb],
            ids=[item["id"]]
        )
else:
    print("✅ All documents already in ChromaDB.")

# RAG query
def rag_query(question):
    q_emb = get_embedding(question)
    results = collection.query(query_embeddings=[q_emb], n_results=2)
    context = "\n".join(results['documents'][0])

    prompt = f"""Use the following context to answer the question.

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

# Interactive loop
print("\n🧠 RAG is ready. Ask a question (type 'exit' to quit):\n")
while True:
    question = input("You: ")
    if question.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break
    answer = rag_query(question)
    print("🤖:", answer)
