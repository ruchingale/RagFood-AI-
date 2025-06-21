import os
import json
import chromadb
import requests

# 🧠 Constants
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "foods"
JSON_FILE = "foods.json"
EMBED_MODEL = "mxbai-embed-large"
LLM_MODEL = "llama3.2"

# 🔗 Set up persistent ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# 🧠 Ollama embedding function
def get_embedding(text):
    response = requests.post("http://localhost:11434/api/embeddings", json={
        "model": EMBED_MODEL,
        "prompt": text
    })
    return response.json()["embedding"]

# 💾 Load food data from existing JSON
with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

# ✅ Add only new items (based on ID)
existing_ids = set(collection.get()['ids'])
new_items = [item for item in food_data if item['id'] not in existing_ids]

if new_items:
    print(f"🆕 Adding {len(new_items)} new documents to Chroma...")
    for item in new_items:
        emb = get_embedding(item['text'])
        collection.add(
            documents=[item['text']],
            embeddings=[emb],
            ids=[item['id']]
        )
else:
    print("✅ All documents already embedded in ChromaDB.")

# 🤖 RAG Query function
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

# 🧑‍💻 Interactive CLI
print("\n🧠 RAG is ready. Type a question below (or 'exit' to quit):\n")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break
    answer = rag_query(user_input)
    print("🤖:", answer)
