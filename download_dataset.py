
from datasets import load_dataset
from pathlib import Path

DATASET_NAME = "DinoStackAI/qasper-rag"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

components = [
    "corpus",
    "queries",
    "qrels",
    "answers",
    "top_ranked",
    "retrieved_docs"
]

for component in components:
    print(f"\nDownloading: {component}")

    dataset = load_dataset(
        DATASET_NAME,
        component
    )

    output_path = DATA_DIR / component

    dataset.save_to_disk(str(output_path))

    print(f"Saved: {output_path}")

print("\nAll QASPER components downloaded successfully!")
