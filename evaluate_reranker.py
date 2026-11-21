
import sqlite3
import re
import numpy as np
import chromadb

from datasets import load_from_disk
from sentence_transformers import SentenceTransformer, CrossEncoder
from tqdm import tqdm

# Configuration
DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

DB_PATH = "vector_db"
BM25_PATH = "bm25_database.db"

CANDIDATE_K = 100
RERANK_K = 50
FINAL_K = 10
RRF_K = 60
BATCH_SIZE = 32

print("\n1. Loading development queries and qrels...")

queries = load_from_disk("data/queries")["dev"]
qrels = load_from_disk("data/qrels")["dev"]

relevant_docs = {}

for row in qrels:
    relevant_docs.setdefault(row["query_id"], {})[row["corpus_id"]] = row["score"]

print("Development queries:", len(queries))

print("\n2. Loading dense retrieval model...")

dense_model = SentenceTransformer(DENSE_MODEL)

client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection("qasper_passages")

print("Dense passages:", collection.count())

print("\n3. Connecting to BM25 database...")

conn = sqlite3.connect(BM25_PATH)
cursor = conn.cursor()

print("\n4. Loading Cross-Encoder reranker...")

reranker = CrossEncoder(RERANKER_MODEL)

print("Reranker loaded successfully!")

# Store candidate pairs for reranking
all_pairs = []
query_records = []

print("\n5. Retrieving hybrid candidates...")

for start in tqdm(range(0, len(queries), BATCH_SIZE)):

    batch = queries[start:start + BATCH_SIZE]

    query_ids = batch["id"]
    query_texts = batch["text"]

    # Dense retrieval
    embeddings = dense_model.encode(
        query_texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    dense_results = collection.query(
        query_embeddings=embeddings.tolist(),
        n_results=CANDIDATE_K
    )

    for i, query_id in enumerate(query_ids):

        question = query_texts[i]

        # Dense ranking
        dense_ids = dense_results["ids"][i]

        # BM25 ranking
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

        # RRF fusion
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

        fused = sorted(
            rrf_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )

        candidate_ids = [
            doc_id for doc_id, score in fused[:RERANK_K]
        ]

        # Get candidate passage text from ChromaDB
        documents = collection.get(
            ids=candidate_ids,
            include=["documents"]
        )

        document_map = dict(zip(
            documents["ids"],
            documents["documents"]
        ))

        valid_ids = [
            doc_id for doc_id in candidate_ids
            if doc_id in document_map
        ]

        pairs = [
            [question, document_map[doc_id]]
            for doc_id in valid_ids
        ]

        pair_start = len(all_pairs)
        all_pairs.extend(pairs)

        query_records.append({
            "query_id": query_id,
            "candidate_ids": valid_ids,
            "pair_start": pair_start,
            "pair_count": len(valid_ids)
        })

conn.close()

print("\nTotal question-passage pairs:", len(all_pairs))

print("\n6. Reranking candidates with Cross-Encoder...")

scores = reranker.predict(
    all_pairs,
    batch_size=32,
    show_progress_bar=True
)

print("\n7. Evaluating reranked results...")

recall_5 = []
recall_10 = []
mrr_10 = []
ndcg_10 = []
candidate_recall_50 = []

evaluated = 0

for record in query_records:

    query_id = record["query_id"]
    candidate_ids = record["candidate_ids"]

    start = record["pair_start"]
    end = start + record["pair_count"]

    query_scores = scores[start:end]

    # Sort candidate passages by Cross-Encoder score
    ranked_indices = np.argsort(query_scores)[::-1][:FINAL_K]

    retrieved = [
        candidate_ids[index]
        for index in ranked_indices
    ]

    relevant = relevant_docs.get(query_id, {})

    relevant_ids = {
        doc_id for doc_id, score in relevant.items()
        if score > 0
    }

    if not relevant_ids:
        continue

    evaluated += 1

    # Candidate Recall@50: upper bound before reranking
    candidate_hits = len(
        set(candidate_ids) & relevant_ids
    )

    candidate_recall_50.append(
        candidate_hits / len(relevant_ids)
    )

    # Final Recall@5 and Recall@10
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
    )[:FINAL_K]

    idcg = sum(
        (2 ** score - 1) / np.log2(rank + 1)
        for rank, score in enumerate(ideal_scores, start=1)
    )

    ndcg_10.append(dcg / idcg if idcg > 0 else 0)


print("\n========== RERANKER EVALUATION ==========")

print("Evaluated queries:", evaluated)

print(f"Candidate Recall@50: {np.mean(candidate_recall_50):.4f}")
print(f"Final Recall@5:      {np.mean(recall_5):.4f}")
print(f"Final Recall@10:     {np.mean(recall_10):.4f}")
print(f"Final MRR@10:        {np.mean(mrr_10):.4f}")
print(f"Final nDCG@10:       {np.mean(ndcg_10):.4f}")

print("\nReranker evaluation completed!")
