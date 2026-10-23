import json
import sys
from pathlib import Path
import numpy as np
import ollama
import re

MODEL = "nomic-embed-text"
TOP_K = 3
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4

HINDI_STOPWORDS = {
    "है", "हैं", "हो", "होता", "होती", "होते", "क्या", "कैसे", "क्यों",
    "का", "की", "के", "को", "से", "में", "पर", "ने", "और", "ये", "वो",
    "कर", "करना", "करनी", "करना", "चाहिए", "रहना", "बताओ", "बताइए",
    "काम", "करता", "करते", "करती", "गया", "गई", "गए", "था", "थी", "थे",
    "मेरी", "मेरा", "मेरे", "आप", "तुम", "एक", "अपना", "अपने", "अपनी",
}


def normalize(text):
    return re.sub(r"[.,!?;:'\"()\[\]{}।॥।]+", " ", text.lower())


def tokenize(text):
    tokens = normalize(text).split()
    return [t for t in tokens if t not in HINDI_STOPWORDS]


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


def min_max_norm(values):
    lo = min(values)
    hi = max(values)
    if hi - lo < 1e-9:
        return [1.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def keyword_similarity(query_terms, text):
    if not query_terms:
        return 0.0
    text_lower = normalize(text)
    matched = sum(1 for term in query_terms if term in text_lower)
    return matched / len(query_terms)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    embedding_files = list(Path("chunks").glob("*/embeddings.json"))

    if not embedding_files:
        print("No embeddings.json found.")
        return

    embedding_file = embedding_files[0]

    data = json.loads(embedding_file.read_text(encoding="utf-8"))

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
    else:
        question = input("\nAsk a question: ").strip()

    if not question:
        print("No question entered.")
        return

    print("\nCreating question embedding...")

    response = ollama.embed(model=MODEL, input=question)
    question_embedding = response["embeddings"][0]

    query_terms = tokenize(question)
    print(f"Query terms (after stopword filter): {query_terms}")

    results = []

    for item in data:
        semantic = cosine_similarity(question_embedding, item["embedding"])
        keyword = keyword_similarity(query_terms, item["text"])

        results.append({
            "chunk_id": item["chunk_id"],
            "semantic": semantic,
            "keyword": keyword,
            "text": item["text"],
        })

    sem_scores = [r["semantic"] for r in results]
    kw_scores = [r["keyword"] for r in results]
    sem_norm = min_max_norm(sem_scores)
    kw_norm = min_max_norm(kw_scores)

    for r, s, k in zip(results, sem_norm, kw_norm):
        r["sem_norm"] = s
        r["kw_norm"] = k
        r["score"] = SEMANTIC_WEIGHT * s + KEYWORD_WEIGHT * k

    results.sort(key=lambda x: x["score"], reverse=True)

    print("\n" + "=" * 70)
    print(f"TOP {TOP_K} RESULTS (hybrid: {int(SEMANTIC_WEIGHT*100)}% semantic + {int(KEYWORD_WEIGHT*100)}% keyword)")
    print("=" * 70)

    for i, result in enumerate(results[:TOP_K], start=1):
        print(
            f"\n[{i}] {result['chunk_id']} "
            f"| final: {result['score']:.4f} "
            f"| semantic: {result['semantic']:.4f} (norm {result['sem_norm']:.2f}) "
            f"| keyword: {result['keyword']:.2f} (norm {result['kw_norm']:.2f})"
        )
        print("-" * 70)
        print(result["text"])
        print("-" * 70)


if __name__ == "__main__":
    main()