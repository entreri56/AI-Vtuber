"""
RAG Model - Retrieval Augmented Generation
Uses FAISS vector search + local LLM (Ollama) to generate responses
based on a knowledge base of personality/documents.
"""
from datetime import datetime
import os
import glob
import time
import warnings
import json
import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

from config import (
    CHAT_MESSAGES_DIR, RAG_SOURCE_DIR, OLLAMA_API_URL, OLLAMA_MODEL,
    RAG_TOP_K, EMBEDDING_MODEL_NAME,
)

# --- Suppress warnings ---
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", message=".*Torch was not compiled with flash attention.*")

# --- Load the embedding model ---
print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL_NAME}")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# --- Create FAISS index ---
dimension = 384  # all-MiniLM-L6-v2 produces 384-dim embeddings
index = faiss.IndexFlatL2(dimension)

# --- Load documents from knowledge base folder ---
def load_documents_from_folder(folder_path):
    documents = []
    file_paths = glob.glob(os.path.join(folder_path, "*.txt"))
    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file_contents = file.readlines()
            documents.extend([doc.strip() for doc in file_contents if doc.strip()])
        except FileNotFoundError:
            print(f"[WARNING] File not found: {file_path}")
    return documents



# --- Search FAISS index ---
def search_faiss_index(query, k=RAG_TOP_K):
    query_embedding = embedding_model.encode(query).reshape(1, -1).astype('float32')
    distances, indices = index.search(query_embedding, k)
    return indices



# --- Call Ollama / local LLM ---
def run_ollama(prompt):
    payload = {"model": OLLAMA_MODEL, "prompt": prompt}
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        if response.status_code == 200:
            response_text = response.text
            response_parts = response_text.strip().split('\n')
            final_response = ""
            for part in response_parts:
                try:
                    data = json.loads(part)
                    if data.get("done", False):
                        final_response += data.get("response", "")
                        break
                    final_response += data.get("response", "")
                except json.JSONDecodeError:
                    print(f"[WARNING] Failed to parse JSON part: {part}")
            return final_response.strip()
        else:
            return f"Error: {response.status_code}, {response.text}"
    except requests.exceptions.ConnectionError:
        return "[ERROR] Could not connect to Ollama. Is 'ollama serve' running?"



# --- RAG query pipeline ---
def query_rag(query, query_file):
    # Extract the user's name from the query file name
    user_name = os.path.basename(query_file).split('_')[0]

    indices = search_faiss_index(query)
    retrieved_docs = [documents[i] for i in indices[0]]
    context = "\n\n".join(retrieved_docs)
    prompt = (
        f"You are an AI VTuber responding to a viewer in a Twitch chat. "
        f"Use the personality context below to guide your tone and style. "
        f"Keep responses concise and conversational (2-4 sentences). "
        f"Address the viewer directly.\n\n"
        f"Personality Context:\n{context}\n\n"
        f"Viewer's message: {query}\n\n"
        f"Your response:"
    )

    response = run_ollama(prompt)

    # Create output directory if needed
    os.makedirs(RAG_SOURCE_DIR, exist_ok=True)

    # Save response with timestamp
    current_time = datetime.now()
    file_name = f"{user_name}_{current_time.strftime('%Y%m%d_%H%M%S')}_response.txt"
    full_file_path = os.path.join(RAG_SOURCE_DIR, file_name)

    # Clean up response and prepend username
    response_text = response.split("Your response:", 1)[-1].strip()
    full_response = f"{user_name}: {response_text}"

    with open(full_file_path, "w", encoding="utf-8") as file:
        file.write(full_response)

    return full_response



# --- Main loop ---
if __name__ == "__main__":
    # Load documents and build FAISS index
    print(f"[INFO] Loading documents from: {RAG_SOURCE_DIR}")
    documents = load_documents_from_folder(RAG_SOURCE_DIR)

    if not documents:
        print("[ERROR] No documents found in the knowledge base folder.")
        print(f"         Please add .txt files to: {RAG_SOURCE_DIR}")
        exit(1)

    print(f"[INFO] Loaded {len(documents)} document chunks. Building FAISS index...")
    document_embeddings = np.array(
        [embedding_model.encode(doc) for doc in documents], dtype='float32'
    )
    index.add(document_embeddings)
    print("[INFO] FAISS index ready.")

    processed_files = set()

    while True:
        txt_files = glob.glob(os.path.join(CHAT_MESSAGES_DIR, "*.txt"))
        new_files = [
            f for f in txt_files
            if f not in processed_files
            and not os.path.basename(f).startswith("streamelements")
        ]

        if new_files:
            latest_file = max(new_files, key=os.path.getmtime)
            with open(latest_file, "r", encoding="utf-8") as file:
                query = file.read().strip()

            if query:
                response_text = query_rag(query, latest_file)
                print("\nGenerated Response:\n", response_text)

            processed_files.add(latest_file)
        else:
            print("No new text files found. Waiting...")

        time.sleep(5)