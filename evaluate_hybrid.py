
import sqlite3
import re
import numpy as np
import chromadb

from datasets import load_from_disk
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

DB_PATH = "vector_db"
BM25_PATH = "bm25_database.db"

TOP_K = 10
CANDIDATE_K = 100
RRF_K = 60
BATCH_SIZE = 32

print("\n1. Loading development queries and qrels...")

queries = load_from_disk("data/queries")["dev"]
qrels = load_from_disk("data/qrels")["dev"]

relevant_docs = {}

for row in qrels:
    relevant_docs.setdefault(row["query_id"], {})[row["corpus_id"]] = row["score"]

print("Development queries:", len(queries))
print("Relevance judgments:", len(qrels))

print("\n2. Loading dense retrieval system...")

model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection("qasper_passages")

print("Dense passages:", collection.count())

print("\n3. Connecting to BM25...")

conn = sqlite3.connect(BM25_PATH)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM corpus_fts")
print("BM25 passages:", cursor.fetchone()[0])

print("\n4. Running hybrid retrieval with RRF...")

recall_5 = []
recall_10 = []
mrr_10 = []
ndcg_10 = []

evaluated = 0

for start in tqdm(range(0, len(queries), BATCH_SIZE)):

    batch = queries[start:start + BATCH_SIZE]

    query_ids = batch["id"]
    query_texts = batch["text"]

    # Dense retrieval
    embeddings = model.encode(
        query_texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    dense_results = collection.query(
        query_embeddings=embeddings.tolist(),
        n_results=CANDIDATE_K
    )

    # Process each query
    for i, query_id in enumerate(query_ids):

        question = query_texts[i]

        # 1. Get dense ranking
        dense_ids = dense_results["ids"][i]

        # 2. Get BM25 ranking
        terms = list(dict.fromkeys(
            re.findall(r"\w+", question.lower())
        ))

        bm25_ids = []

        if terms:
            fts_query = " OR ".join(
                '"' + term.replace('"', '""') + '"'
                for term in terms
            )

            results = cursor.execute("""
                SELECT id
                FROM corpus_fts
                WHERE corpus_fts MATCH ?
                ORDER BY bm25(
                    corpus_fts, 0.0, 2.0, 1.0, 1.0
                ) ASC
                LIMIT ?
            """, (fts_query, CANDIDATE_K)).fetchall()

            bm25_ids = [row[0] for row in results]

        # 3. Reciprocal Rank Fusion
        rrf_scores = {}

        for rank, doc_id in enumerate(dense_ids, start=1):
            rrf_scores[doc_id] = (
                rrf_scores.get(doc_id, 0)
                + 1 / (RRF_K + rank)
            )

        for rank, doc_id in enumerate(bm25_ids, start=1):
            rrf_scores[doc_id] = (
                rrf_scores.get(doc_id, 0)
                + 1 / (RRF_K + rank)
            )

        # Sort by combined RRF score
        fused_results = sorted(
            rrf_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )

        retrieved = [
            doc_id for doc_id, score in fused_results[:TOP_K]
        ]

        # 4. Evaluate against qrels
        relevant = relevant_docs.get(query_id, {})

        relevant_ids = {
            doc_id for doc_id, score in relevant.items()
            if score > 0
        }

        if not relevant_ids:
            continue

        evaluated += 1

        hits_5 = len(set(retrieved[:5]) & relevant_ids)
        hits_10 = len(set(retrieved[:10]) & relevant_ids)

        recall_5.append(hits_5 / len(relevant_ids))
        recall_10.append(hits_10 / len(relevant_ids))

        # MRR@10 and DCG@10
        reciprocal_rank = 0
        dcg = 0

        for rank, doc_id in enumerate(retrieved, start=1):

            if doc_id in relevant_ids:

                if reciprocal_rank == 0:
                    reciprocal_rank = 1 / rank

                relevance = relevant[doc_id]

                dcg += (
                    (2 ** relevance - 1)
                    / np.log2(rank + 1)
                )

        mrr_10.append(reciprocal_rank)

        ideal_scores = sorted(
            [score for score in relevant.values() if score > 0],
            reverse=True
        )[:TOP_K]

        idcg = sum(
            (2 ** score - 1) / np.log2(rank + 1)
            for rank, score in enumerate(ideal_scores, start=1)
        )

        ndcg_10.append(dcg / idcg if idcg > 0 else 0)


conn.close()

print("\n========== HYBRID RETRIEVAL RESULTS ==========")

print("Evaluated queries:", evaluated)
print(f"Recall@5:  {np.mean(recall_5):.4f}")
print(f"Recall@10: {np.mean(recall_10):.4f}")
print(f"MRR@10:    {np.mean(mrr_10):.4f}")
print(f"nDCG@10:   {np.mean(ndcg_10):.4f}")

print("\nHybrid retrieval evaluation completed!")
