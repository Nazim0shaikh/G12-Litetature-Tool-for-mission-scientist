
from datasets import load_from_disk
from sentence_transformers import SentenceTransformer
import chromadb
from pathlib import Path
from tqdm import tqdm

# ==========================================
# 1. CONFIGURATION
# ==========================================

DATA_PATH = "data/corpus"
DB_PATH = "vector_db"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

BATCH_SIZE = 256
EMBEDDING_BATCH_SIZE = 32

# ==========================================
# 2. LOAD DATASET
# ==========================================

print("\n1. Loading research corpus...")

corpus = load_from_disk(DATA_PATH)["train"]

total_records = len(corpus)

print(f"Total passages: {total_records}")

# ==========================================
# 3. LOAD EMBEDDING MODEL
# ==========================================

print("\n2. Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded successfully!")

# ==========================================
# 4. INITIALIZE CHROMADB
# ==========================================

print("\n3. Initializing ChromaDB...")

Path(DB_PATH).mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_or_create_collection(
    name="qasper_passages",
    metadata={"hnsw:space": "cosine"}
)

print("ChromaDB initialized successfully!")

# ==========================================
# 5. GENERATE EMBEDDINGS AND INDEX DATA
# ==========================================

print("\n4. Generating embeddings and indexing passages...")

for start in tqdm(range(0, total_records, BATCH_SIZE)):

    end = min(start + BATCH_SIZE, total_records)

    # Retrieve batch as dictionary of lists
    batch = corpus[start:end]

    ids = list(batch["id"])
    texts = list(batch["text"])

    # Generate embeddings
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=EMBEDDING_BATCH_SIZE
    )

    # Prepare metadata
    metadatas = []

    for i in range(len(ids)):

        passage_id = ids[i]

        metadata = {
            "title": batch["title"][i],
            "section_name": batch["section_name"][i],
            "paper_id": passage_id.rsplit("_", 1)[0]
        }

        metadatas.append(metadata)

    # Validate batch consistency
    assert len(ids) == len(texts)
    assert len(ids) == len(metadatas)
    assert len(ids) == len(embeddings)

    # Store in ChromaDB
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

# ==========================================
# 6. VERIFY DATABASE
# ==========================================

print("\n5. Verifying database...")

indexed_count = collection.count()

print(f"Expected passages: {total_records}")
print(f"Indexed passages: {indexed_count}")

if indexed_count == total_records:
    print("\nSUCCESS! All passages indexed successfully.")
else:
    print("\nWARNING: Indexed count does not match expected count.")

print(f"Database location: {Path(DB_PATH).resolve()}")

print("\nRAG indexing process completed!")
