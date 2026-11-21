
from datasets import load_from_disk

components = [
    "corpus",
    "queries",
    "qrels",
    "answers",
    "top_ranked",
    "retrieved_docs"
]

for component in components:
    dataset = load_from_disk(f"data/{component}")

    print(f"\n--- {component.upper()} ---")

    for split in dataset:
        print(f"{split}: {len(dataset[split])} records")

    # Display one sample record
    split_name = list(dataset.keys())[0]
    print("Sample:", dataset[split_name][0])
