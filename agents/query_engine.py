import json
import os
import faiss
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer


class LegalQueryEngine:
    def __init__(self, chunk_path="data/chunks.json", index_path="data/legal_index.faiss"):
        self.chunk_path = chunk_path
        self.index_path = index_path
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.chunk_texts = []
        self.chunk_metadata = []

    def load_chunks(self):
        with open(self.chunk_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        self.chunk_texts = [chunk['text'] for chunk in chunks]
        self.chunk_metadata = chunks
        print(f"📚 Loaded {len(self.chunk_texts)} text chunks.")

    def build_index(self):
        print("Embedding all chunks...")
        embeddings = self.model.encode(self.chunk_texts, show_progress_bar=True)
        dim = embeddings[0].shape[0]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(embeddings).astype("float32"))
        faiss.write_index(self.index, self.index_path)
        print(f"FAISS index saved to {self.index_path}.")

    def load_index(self):
        if not os.path.exists(self.index_path):
            raise FileNotFoundError("FAISS index not found. Please build it first.")
        self.index = faiss.read_index(self.index_path)
        print(f"Loaded FAISS index from {self.index_path}.")

    def query(self, user_query: str, top_k=5) -> List[Tuple[str, dict]]:
        query_embedding = self.model.encode([user_query])
        D, I = self.index.search(np.array(query_embedding).astype("float32"), top_k)
        results = []
        for idx in I[0]:
            if idx < len(self.chunk_metadata):
                results.append((self.chunk_texts[idx], self.chunk_metadata[idx]))
        return results


if __name__ == "__main__":
    engine = LegalQueryEngine()
    engine.load_chunks()
    engine.build_index()
