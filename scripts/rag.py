import json
import sys
from pathlib import Path

import numpy as np
import ollama


EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "phi3:mini"

TOP_K = 3


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def normalize(text):
    return text.lower().strip()


def keyword_score(query, text):
    """
    Simple keyword overlap.
    Works with both English and Devanagari text.
    """

    query_words = set(normalize(query).split())
    text_words = set(normalize(text).split())

    if not query_words:
        return 0.0

    matches = query_words.intersection(text_words)

    return len(matches) / len(query_words)


def retrieve(question, data):

    # Embed question
    response = ollama.embed(
        model=EMBED_MODEL,
        input=question
    )

    question_embedding = response["embeddings"][0]

    results = []

    for item in data:

        vector_score = cosine_similarity(
            question_embedding,
            item["embedding"]
        )

        keyword = keyword_score(
            question,
            item["text"]
        )

        # Same hybrid weighting that passed your test
        final_score = (
            0.60 * vector_score
            + 0.40 * keyword
        )

        results.append({
            "chunk_id": item["chunk_id"],
            "text": item["text"],
            "vector_score": vector_score,
            "keyword_score": keyword,
            "final_score": final_score
        })

    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return results[:TOP_K]


def generate_answer(question, retrieved_chunks):

    context_parts = []

    for chunk in retrieved_chunks:
        context_parts.append(
            f"[{chunk['chunk_id']}]\n{chunk['text']}"
        )

    context = "\n\n".join(context_parts)

    system_prompt = """
You are a transcript question-answering assistant.

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