
import chromadb
from sentence_transformers import SentenceTransformer

# 1. Load embedding model
print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# 2. Connect to existing database
print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path="vector_db"
)

collection = client.get_collection(
    name="qasper_passages"
)

print("Total indexed passages:", collection.count())

# 3. Ask a research question
question = input("\nEnter your research question: ")

# 4. Convert question into embedding
query_embedding = model.encode(
    question,
    normalize_embeddings=True
).tolist()

# 5. Search database
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)

# 6. Display retrieved passages
print("\n========== SEARCH RESULTS ==========")

for i in range(len(results["ids"][0])):

    print(f"\nResult {i + 1}")

    print("Passage ID:", results["ids"][0][i])

    print("Paper:", results["metadatas"][0][i]["title"])

    print("Section:", results["metadatas"][0][i]["section_name"])

    print("Similarity distance:", results["distances"][0][i])

    print("\nPassage:")
    print(results["documents"][0][i])

    print("-" * 60)
