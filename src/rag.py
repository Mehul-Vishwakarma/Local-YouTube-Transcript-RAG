import json
import sys
import re
from pathlib import Path
import numpy as np
import ollama

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "phi3:mini"
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


def retrieve(question, data):
    response = ollama.embed(model=EMBED_MODEL, input=question)
    question_embedding = response["embeddings"][0]

    query_terms = tokenize(question)

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
        r["final_score"] = SEMANTIC_WEIGHT * s + KEYWORD_WEIGHT * k

    results.sort(key=lambda x: x["final_score"], reverse=True)

    return results[:TOP_K]


def generate_answer(question, chunks):
    system_prompt = """You are a transcript question-answering assistant.

Your ONLY source of information is the transcript context provided
by the user.

Rules:

1. Answer only from the supplied transcript context.
2. Do not use outside knowledge.
3. Do not invent facts.
4. If the context does not contain enough information to answer,
   clearly say that the provided transcript context does not contain
   enough information.
5. Preserve the meaning of the transcript.
6. You may explain the retrieved information clearly.
7. Do not claim something was taught if it is not present in the
   supplied context.
"""

    context = "\n\n---\n\n".join(chunk["text"] for chunk in chunks)

    user_prompt = f"""
Transcript context:

{context}

Question:

{question}

Answer the question using ONLY the transcript context.
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response["message"]["content"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        question = input("Ask a question: ").strip()
    else:
        question = " ".join(sys.argv[1:]).strip()

    if not question:
        print("No question provided.")
        return

    embedding_files = list(
        Path("chunks").glob("*/embeddings.json")
    )

    if not embedding_files:
        print("No embeddings.json found.")
        return

    embedding_file = embedding_files[0]

    data = json.loads(
        embedding_file.read_text(encoding="utf-8")
    )

    print("\nRetrieving relevant transcript chunks...")

    chunks = retrieve(
        question,
        data
    )

    print("\nRetrieved chunks:")

    for chunk in chunks:
        print(
            f"  {chunk['chunk_id']} "
            f"(score={chunk['final_score']:.4f})"
        )

    print("\nGenerating answer with Phi-3 Mini...\n")

    answer = generate_answer(
        question,
        chunks
    )

    print("=" * 70)
    print("ANSWER")
    print("=" * 70)
    print(answer)
    print("=" * 70)


if __name__ == "__main__":
    main()