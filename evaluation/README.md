# Evaluation

## Retrieval

Use the development split only for tuning. The retrieval evaluator reports:

- Recall at 5
- Recall at 10
- MRR at 10
- nDCG at 10
- Candidate recall at 50

Metrics are averaged only across queries with at least one positive relevance
judgment. The test split must be reserved for final reporting.

## Answer quality

Generated outputs can be evaluated for answerability, lexical relevance,
unsupported claims, and evidence faithfulness. Lexical overlap is only a
transparent diagnostic. Scientific semantic correctness requires a qualified
model evaluator or human review.

## Citations

Citation evaluation has separate dimensions:

1. Existence: does the passage ID exist in the supplied evidence?
2. Precision: how many predicted citations are reference citations?
3. Recall: how many reference citations were retrieved?
4. Claim support: does the cited passage semantically support the claim?

A passage ID existing in the corpus does not prove that the passage supports
the associated claim.

## Refusal

Refusal results require explicit answerability labels. The metrics distinguish:

- correct refusal rate on unanswerable questions
- false refusal rate on answerable questions
- incorrect-answering rate on unanswerable questions

## Baseline preservation

The existing reranker evaluation script contains development-set baselines.
The reusable evaluator in `evaluation/retrieval_metrics.py` does not fabricate
or overwrite those values.
