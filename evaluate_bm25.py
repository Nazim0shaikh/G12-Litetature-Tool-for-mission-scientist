
import sqlite3
import re
import numpy as np
from datasets import load_from_disk
from tqdm import tqdm

DB_PATH = "bm25_database.db"
TOP_K = 10

print("\n1. Loading development queries and qrels...")

queries = load_from_disk("data/queries")["dev"]
qrels = load_from_disk("data/qrels")["dev"]

relevant_docs = {}

for row in qrels:
    relevant_docs.setdefault(row["query_id"], {})[row["corpus_id"]] = row["score"]

print("Development queries:", len(queries))
print("Relevance judgments:", len(qrels))

print("\n2. Connecting to BM25 database...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM corpus_fts")
print("Indexed passages:", cursor.fetchone()[0])

print("\n3. Evaluating BM25 retrieval...")

recall_5 = []
recall_10 = []
mrr_10 = []
ndcg_10 = []

evaluated = 0

for query in tqdm(queries):

    query_id = query["id"]
    question = query["text"]

    # Convert question into FTS5 search terms
    terms = list(dict.fromkeys(re.findall(r"\w+", question.lower())))

    if not terms:
        continue

    fts_query = " OR ".join(
        '"' + term.replace('"', '""') + '"'
        for term in terms
    )

    results = cursor.execute("""
        SELECT id
        FROM corpus_fts
        WHERE corpus_fts MATCH ?
        ORDER BY bm25(corpus_fts, 0.0, 2.0, 1.0, 1.0) ASC
        LIMIT ?
    """, (fts_query, TOP_K)).fetchall()

    retrieved = [row[0] for row in results]

    relevant = relevant_docs.get(query_id, {})

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

    # MRR@10 and DCG@10
    reciprocal_rank = 0
    dcg = 0

    for rank, doc_id in enumerate(retrieved, start=1):

        if doc_id in relevant_ids:

            if reciprocal_rank == 0:
                reciprocal_rank = 1 / rank

            relevance = relevant[doc_id]
            dcg += (2 ** relevance - 1) / np.log2(rank + 1)

    mrr_10.append(reciprocal_rank)

    # Ideal DCG
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

print("\n========== BM25 EVALUATION RESULTS ==========")

print("Evaluated queries:", evaluated)
print(f"Recall@5:  {np.mean(recall_5):.4f}")
print(f"Recall@10: {np.mean(recall_10):.4f}")
print(f"MRR@10:    {np.mean(mrr_10):.4f}")
print(f"nDCG@10:   {np.mean(ndcg_10):.4f}")

print("\nBM25 evaluation completed!")
