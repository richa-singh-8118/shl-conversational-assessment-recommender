import os
# Force PyTorch and avoid loading TensorFlow in transformers imports
os.environ["USE_TF"] = "NO"
os.environ["USE_TORCH"] = "YES"
# Bypasses the strict version checks of protobuf gencode/runtime
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def build_index():
    print("Building FAISS index...")
    catalog_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
    catalog_path = os.path.join(catalog_dir, "catalog", "catalog.json")
    index_path = os.path.join(catalog_dir, "catalog", "index.faiss")
    metadata_path = os.path.join(catalog_dir, "catalog", "index_metadata.json")

    # Ensure directories exist
    os.makedirs(os.path.dirname(catalog_path), exist_ok=True)

    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"catalog.json not found at {catalog_path}. Please run scraper.py first.")

    with open(catalog_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    # 1. Load sentence-transformers model
    print("Loading sentence-transformers/all-MiniLM-L6-v2 model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # 2. Prepare texts for embedding
    texts = []
    metadata = []
    for idx, item in enumerate(items):
        skills_str = ", ".join(item.get("skills", []))
        # Embed using: name description skills test_type
        text = f"Name: {item['name']}\nType: {item['test_type']}\nDescription: {item['description']}\nSkills: {skills_str}"
        texts.append(text)
        
        # Save mapping metadata
        metadata.append({
            "index": idx,
            "name": item["name"],
            "url": item["url"],
            "test_type": item["test_type"],
            "duration": item["duration"],
            "description": item["description"],
            "skills": item["skills"]
        })

    # 3. Generate embeddings
    print(f"Generating embeddings for {len(texts)} catalog items...")
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")

    # 4. Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)

    # 5. Build FAISS Inner Product index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # 6. Save index and metadata
    faiss.write_index(index, index_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"FAISS index built and saved successfully.")
    print(f"Index file: {index_path}")
    print(f"Metadata file: {metadata_path}")

if __name__ == "__main__":
    build_index()
