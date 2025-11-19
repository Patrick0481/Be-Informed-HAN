import streamlit as st
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import ollama   # Ollama import
import os
from pathlib import Path
from streamlit_chat import message
from PIL import Image
import io

# ----------------------------
# Setup
# ----------------------------

# ⚡ Ollama client instellen zodat het de lokale daemon in dezelfde container gebruikt
ollama_host = "http://127.0.0.1:11434"
ollama_client = ollama.OllamaClient(host=ollama_host)

# Embedder pad
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

DB_PATH = Path(__file__).parent / "local_db"
DB_PATH.mkdir(exist_ok=True)

chroma_client = chromadb.Client(Settings(
    persist_directory=str(DB_PATH),
    is_persistent=True
))
collection = chroma_client.get_or_create_collection("pdf_docs")

# ----------------------------
# Functies
# ----------------------------
def pdf_to_chunks(pdf_file, chunk_size=800):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks

def index_pdf(pdf_file):
    chunks = pdf_to_chunks(pdf_file)
    if not chunks:
        st.warning(f"⚠️ Geen tekst gevonden in {pdf_file.name}, indexeren overgeslagen.")
        return
    embeddings = embedder.encode(chunks).tolist()
    ids = [f"{pdf_file.name}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": pdf_file.name} for _ in chunks]
    collection.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metadatas)
    st.success(f"✅ Geïndexeerd {len(chunks)} chunks van {pdf_file.name}")

def get_context(question, top_k=3):
    results = collection.query(query_texts=[question], n_results=top_k)
    return "\n\n".join(results["documents"][0])

def resize_image(image_file, max_size=512):
    """Resize afbeelding en return als bytes"""
    img = Image.open(image_file)
    img.thumbnail((max_size, max_size))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()

def query_qwen(user_text, image_file=None):
    message_payload = {"role": "user", "content": user_text}

    if image_file is not None:
        img_bytes = resize_image(image_file)
        message_payload["images"] = [img_bytes]

    # 🔹 Gebruik hier de Ollama-client die we net hebben aangemaakt
    response = ollama_client.chat(
        model="qwen3-vl:2b",
        messages=[message_payload]
    )
    return response["message"]["content"]
