"""Nạp nhanh embeddings đã tính sẵn từ data/index/dense/v1 vào Qdrant."""
import json
import warnings
from pathlib import Path
import numpy as np
from qdrant_client import QdrantClient, models

from team1_data.retrieval.dense import (
    VECTOR_NAME,
    COLLECTION_ALIAS,
    point_id,
    KEYWORD_INDEXES,
    filter_chunks,
    load_chunks,
    DEFAULT_LEGAL_STATUS,
    UPSERT_BATCH,
)

ROOT = Path(__file__).resolve().parents[1]
DENSE_DIR = ROOT / "data" / "index" / "dense" / "v1"
CHUNKS_FILE = ROOT / "data" / "doanh-nghiep" / "processed" / "chunks.jsonl"

def main():
    manifest = json.loads((DENSE_DIR / "index_manifest.json").read_text(encoding="utf-8"))
    name = manifest["collection"]
    dim = manifest["embedding_dim"]
    
    print(f"Connecting to Qdrant localhost:6333...")
    client = QdrantClient("http://localhost:6333", timeout=30)
    
    if client.collection_exists(name):
        print(f"Collection {name} already exists. Points count: {client.count(name).count}")
        return

    print(f"Loading precomputed embeddings from {DENSE_DIR / 'embeddings.npy'}...")
    embeddings = np.load(DENSE_DIR / "embeddings.npy")
    chunks = filter_chunks(load_chunks(CHUNKS_FILE), manifest["legal_status"])
    
    print(f"Loaded {len(chunks)} chunks and {embeddings.shape} vectors. Creating collection {name}...")
    client.create_collection(
        collection_name=name,
        vectors_config={VECTOR_NAME: models.VectorParams(size=dim, distance=models.Distance.COSINE)},
    )
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        for field in KEYWORD_INDEXES:
            client.create_payload_index(name, field, models.PayloadSchemaType.KEYWORD)
        client.create_payload_index(name, "effective_date", models.PayloadSchemaType.DATETIME)

    print("Upserting points to Qdrant in batches...")
    for start in range(0, len(chunks), UPSERT_BATCH):
        batch_chunks = chunks[start:start + UPSERT_BATCH]
        batch_vecs = embeddings[start:start + UPSERT_BATCH]
        points = [
            models.PointStruct(id=point_id(c["chunk_id"]), vector={VECTOR_NAME: v.tolist()}, payload=c)
            for c, v in zip(batch_chunks, batch_vecs)
        ]
        client.upsert(name, points=points, wait=True)
        print(f"Upserted {min(start + UPSERT_BATCH, len(chunks))}/{len(chunks)} points...")

    count = client.count(name, exact=True).count
    client.update_collection_aliases(change_aliases_operations=[
        models.CreateAliasOperation(create_alias=models.CreateAlias(collection_name=name, alias_name=COLLECTION_ALIAS)),
    ])
    print(f"SUCCESS! Collection {name} ready with {count} points!")

if __name__ == "__main__":
    main()
