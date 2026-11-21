
import sqlite3
from datasets import load_from_disk
from pathlib import Path
from tqdm import tqdm

# ==========================================
# 1. CONFIGURATION
# ==========================================

DATA_PATH = "data/corpus"
DB_PATH = "bm25_database.db"

BATCH_SIZE = 1000

# ==========================================
# 2. LOAD CORPUS
# ==========================================

print("\n1. Loading research corpus...")

corpus = load_from_disk(DATA_PATH)["train"]

print("Total passages:", len(corpus))

# ==========================================
# 3. INITIALIZE SQLITE DATABASE
# ==========================================

print("\n2. Initializing SQLite FTS5...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS corpus_fts")

cursor.execute("""
    CREATE VIRTUAL TABLE corpus_fts
    USING fts5(
        id UNINDEXED,
        title,
        section_name,
        text,
        tokenize='porter unicode61'
    )
""")

conn.commit()

print("FTS5 initialized successfully!")

# ==========================================
# 4. INDEX RESEARCH PASSAGES
# ==========================================

print("\n3. Indexing research passages...")

for start in tqdm(range(0, len(corpus), BATCH_SIZE)):

    end = min(start + BATCH_SIZE, len(corpus))

    batch = corpus[start:end]

    records = []

    for i in range(len(batch["id"])):

        records.append((
            batch["id"][i],
            batch["title"][i] or "",
            batch["section_name"][i] or "",
            batch["text"][i] or ""
        ))

    cursor.executemany("""
        INSERT INTO corpus_fts
        (id, title, section_name, text)
        VALUES (?, ?, ?, ?)
    """, records)

    conn.commit()

# ==========================================
# 5. VERIFY DATABASE
# ==========================================

cursor.execute("SELECT COUNT(*) FROM corpus_fts")

count = cursor.fetchone()[0]

print("\n4. Database verification")

print("Expected passages:", len(corpus))
print("Indexed passages:", count)

if count == len(corpus):
    print("\nSUCCESS! BM25 indexing completed.")
else:
    print("\nWARNING: Record count mismatch.")

conn.close()

print("\nDatabase saved at:", Path(DB_PATH).resolve())
