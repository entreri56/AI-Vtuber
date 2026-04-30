from pydub import AudioSegment
import pyaudio
import wave
import os
import glob
import warnings
from datetime import datetime
import time  # For adding delay
import faiss
import numpy as np
import json
import requests
from sentence_transformers import SentenceTransformer

# Paths
chat_messages_folder = r'E:\AIVtuber\Version1.8\ChatMessages'
documents_folder_path = r"E:\AIVtuber\Version1.8\RAGSourceText"

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", message=".*Torch was not compiled with flash attention.*")

# Load the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
llama_api_url = "http://127.0.0.1:11434/api/generate"

# Create FAISS index
dimension = 384
index = faiss.IndexFlatL2(dimension)

# Load documents
def load_documents_from_folder(folder_path):
    documents = []
    file_paths = glob.glob(os.path.join(folder_path, "*.txt"))
    for file_path in file_paths:
        try:
            with open(file_path, "r") as file:
                file_contents = file.readlines()
            documents.extend([doc.strip() for doc in file_contents if doc.strip()])
        except FileNotFoundError:
            print(f"File not found: {file_path}")
    return documents

documents = load_documents_from_folder(documents_folder_path)
if not documents:
    print("No documents found. Please check the folder path and contents.")
    exit(1)

# Generate and add embeddings
document_embeddings = np.array([embedding_model.encode(doc) for doc in documents], dtype='float32')
index.add(document_embeddings)

# Search FAISS
def search_faiss_index(query, k=5):
    query_embedding = embedding_model.encode(query).reshape(1, -1)
    distances, indices = index.search(query_embedding, k)
    return indices

# LLaMA API
def run_ollama(prompt):
    payload = {"model": "nemotron-mini", "prompt": prompt}
    response = requests.post(llama_api_url, json=payload)
    if response.status_code == 200:
        try:
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
                    print(f"Failed to parse JSON part: {part}")
            return final_response.strip()
        except ValueError:
            return f"Failed to parse JSON response: {response.text}"
    else:
        return f"Error: {response.status_code}, {response.text}"

# RAG process with response extraction
def query_rag(query, query_file):
    # Extract the user's name from the query file name
    user_name = os.path.basename(query_file).split('_')[0]

    indices = search_faiss_index(query)
    retrieved_docs = [documents[i] for i in indices[0]]
    context = "\n\n".join(retrieved_docs)
    prompt = f"Context: {context}\n\nQuestion: {query}"
    response = run_ollama(prompt)
    
    # Create output directory if it doesn't exist
    output_file_path = r"E:\AIVtuber\Version1.8\RAGSourceText"
    os.makedirs(output_file_path, exist_ok=True)
    
    # Generate filename with username and timestamp
    current_time = datetime.now()
    file_name = f"{user_name}_{current_time.strftime('%Y%m%d_%H%M%S')}_response.txt"
    full_file_path = os.path.join(output_file_path, file_name)
    
    # Prepend username and save response
    response_text = response.split("Response:", 1)[-1].strip()
    full_response = f"{user_name}: {response_text}"
    
    with open(full_file_path, "w") as file:
        file.write(full_response)
    
    return full_response  # Return the full response with username


# Main loop
if __name__ == "__main__":
    processed_files = set()  # Track processed files to avoid duplication

    while True:
        # Find all .txt files in the ChatMessages folder
        txt_files = glob.glob(os.path.join(chat_messages_folder, "*.txt"))
        
        # Filter out files that start with "streamelements" and keep only new files
        new_files = [f for f in txt_files if f not in processed_files and not os.path.basename(f).startswith("streamelements")]

        if new_files:
            latest_file = max(new_files, key=os.path.getmtime)  # Find the most recent new file
            with open(latest_file, "r") as file:
                query = file.read().strip()

            if query:
                response_text = query_rag(query, latest_file)
                print("\nGenerated Response:\n", response_text)

            # Mark the file as processed
            processed_files.add(latest_file)

        else:
            print("No new text files found in the ChatMessages folder. Waiting for new files...")

        # Wait before checking for new files again
        time.sleep(5)
