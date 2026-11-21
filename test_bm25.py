
import sqlite3
import re

conn = sqlite3.connect("bm25_database.db")
cursor = conn.cursor()

question = input("Enter your research question: ")

# Extract searchable terms
terms = re.findall(r"\w+", question.lower())

# Create safe FTS5 OR query
fts_query = " OR ".join(
    '"' + term.replace('"', '""') + '"'
    for term in terms
)

if not fts_query:
    print("Please enter a valid question.")
    conn.close()
    raise SystemExit

results = cursor.execute("""
    SELECT
        id,
        title,
        section_name,
        text,
        bm25(corpus_fts, 0.0, 2.0, 1.0, 1.0) AS score
    FROM corpus_fts
    WHERE corpus_fts MATCH ?
    ORDER BY score ASC
    LIMIT 5
""", (fts_query,)).fetchall()

print("\n========== BM25 RESULTS ==========")

for i, result in enumerate(results, 1):

    passage_id, title, section, text, score = result

    print(f"\nResult {i}")
    print("Passage ID:", passage_id)
    print("Paper:", title)
    print("Section:", section)
    print("BM25 Score:", score)
    print("Passage:", text[:500])
    print("-" * 60)

conn.close()
