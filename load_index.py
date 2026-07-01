import os
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer

def load_and_test_index():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "catalog", "index.faiss")
    metadata_path = os.path.join(base_dir, "catalog", "index_metadata.json")
    
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        print("Index or metadata not found. Please run build_index.py first.")
        return
        
    print(f"Loading FAISS index from {index_path}...")
    index = faiss.read_index(index_path)
    print(f"Index loaded. Total vectors: {index.ntotal}")
    
    print(f"Loading metadata from {metadata_path}...")
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    print(f"Metadata loaded. Total items: {len(metadata)}")
    
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    test_query = "Java Developer"
    print(f"\nPerforming test search for query: '{test_query}'")
    
    query_emb = model.encode([test_query])
    query_emb = np.array(query_emb).astype("float32")
    faiss.normalize_L2(query_emb)
    
    k = 3
    scores, indices = index.search(query_emb, k)
    
    print(f"\nTop {k} Results:")
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(metadata):
            item = metadata[idx]
            print(f"- {item['name']} (Score: {score:.4f})")
            print(f"  Type: {item['test_type']}")

if __name__ == "__main__":
    load_and_test_index()
