import os
# Configure environment overrides
os.environ["USE_TF"] = "NO"
os.environ["USE_TORCH"] = "YES"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VectorStore, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.index_path = os.path.join(base_dir, "catalog", "index.faiss")
        self.metadata_path = os.path.join(base_dir, "catalog", "index_metadata.json")
        
        print(f"Initializing VectorStore with index={self.index_path}...")
        
        # Load FAISS index
        if not os.path.exists(self.index_path):
             raise FileNotFoundError(f"FAISS index not found at {self.index_path}. Run build_index.py first.")
        self.index = faiss.read_index(self.index_path)
        
        # Load Metadata
        if not os.path.exists(self.metadata_path):
             raise FileNotFoundError(f"Metadata not found at {self.metadata_path}. Run build_index.py first.")
        with open(self.metadata_path, "r", encoding="utf-8") as f:
             self.metadata = json.load(f)
             
        # Load Model
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self._initialized = True

    def search(self, query: str, top_k: int = 10):
        # Encode query
        query_emb = self.model.encode([query])
        query_emb = np.array(query_emb).astype("float32")
        # Normalize for cosine similarity
        faiss.normalize_L2(query_emb)
        
        # Search index
        scores, indices = self.index.search(query_emb, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
             if idx < len(self.metadata):
                  item = self.metadata[idx].copy()
                  item["vector_score"] = float(score)
                  results.append(item)
        return results

# Singleton helper
_store = None
def get_vector_store():
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
