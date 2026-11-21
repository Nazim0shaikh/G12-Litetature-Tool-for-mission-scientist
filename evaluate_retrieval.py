
import chromadb
from datasets import load_from_disk
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np

# ==========================================
# 1. CONFIGURATION
# ==========================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DB_PATH = "vector_db"

TOP_K = 10
BATCH_SIZE = 32

# ==========================================
# 2. LOAD DATA
# ==========================================

print("\n1. Loading development queries and qrels...")

queries = load_from_disk("data/queries")["dev"]
qrels = load_from_disk("data/qrels")["dev"]

# Map each query to its relevant passages
relevant_docs = {}

for row in qrels:
    relevant_docs.setdefault(row["query_id"], {})[
        row["corpus_id"]
    ] = row["score"]

print("Development queries:", len(queries))
print("Relevance judgments:", len(qrels))

# ==========================================
# 3. LOAD MODEL AND DATABASE
# ==========================================

print("\n2. Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_collection("qasper_passages")

print("Indexed passages:", collection.count())

# ==========================================
# 4. EVALUATION
# ==========================================

print("\n3. Evaluating retrieval...")

recall_5 = []
recall_10 = []
mrr_10 = []
ndcg_10 = []

evaluated = 0

for start in tqdm(range(0, len(queries), BATCH_SIZE)):

    batch = queries[start:start + BATCH_SIZE]

    query_ids = batch["id"]
    query_texts = batch["text"]

    embeddings = model.encode(
        query_texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    results = collection.query(
        query_embeddings=embeddings.tolist(),
        n_results=TOP_K
    )

    for i, query_id in enumerate(query_ids):

        # Ground-truth relevance judgments
        relevant = relevant_docs.get(query_id, {})

        if not relevant:
            continue

        retrieved = results["ids"][i]

        relevant_ids = {
            doc_id for doc_id, score in relevant.items()
            if score > 0
        }

        if not relevant_ids:
            continue

        evaluated += 1

        # Recall@5 and Recall@10
        hits_5 = len(set(retrieved[:5]) & relevant_ids)
        hits_10 = len(set(retrieved[:10]) & relevant_ids)

        recall_5.append(hits_5 / len(relevant_ids))
        recall_10.append(hits_10 / len(relevant_ids))

        # MRR@10 and nDCG@10
        reciprocal_rank = 0
        dcg = 0

        for rank, doc_id in enumerate(retrieved, start=1):

            if doc_id in relevant_ids:

                if reciprocal_rank == 0:
                    reciprocal_rank = 1 / rank

                relevance = relevant[doc_id]

                dcg += (2 ** relevance - 1) / np.log2(rank + 1)

        # Ideal DCG
        ideal_scores = sorted(
            [score for score in relevant.values() if score > 0],
            reverse=True
        )[:TOP_K]

        idcg = sum(
            (2 ** score - 1) / np.log2(rank + 1)
            for rank, score in enumerate(ideal_scores, start=1)
        )

        mrr_10.append(reciprocal_rank)
        ndcg_10.append(dcg / idcg if idcg > 0 else 0)

# ==========================================
# 5. DISPLAY RESULTS
# ==========================================

print("\n========== RETRIEVAL EVALUATION ==========")

print("Evaluated queries:", evaluated)

print(f"Recall@5:  {np.mean(recall_5):.4f}")
print(f"Recall@10: {np.mean(recall_10):.4f}")
print(f"MRR@10:    {np.mean(mrr_10):.4f}")
print(f"nDCG@10:   {np.mean(ndcg_10):.4f}")

print("\nEvaluation completed!")
