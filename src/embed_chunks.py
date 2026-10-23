import json
from pathlib import Path
import ollama


MODEL = "nomic-embed-text"


CHUNKS_DIR = Path("chunks")


def main():
    video_dirs = [p for p in CHUNKS_DIR.iterdir() if p.is_dir()]

    if not video_dirs:
        print("No chunk directory found.")
        return

    video_dir = video_dirs[0]
    chunk_files = sorted(video_dir.glob("chunk_*.txt"))

    if not chunk_files:
        print("No chunk files found.")
        return

    texts = [
        path.read_text(encoding="utf-8")
        for path in chunk_files
    ]

    print(f"Video: {video_dir.name}")
    print(f"Chunks: {len(texts)}")
    print("Generating embeddings...")

    response = ollama.embed(
        model=MODEL,
        input=texts
    )

    embeddings = response["embeddings"]

    data = []

    for path, text, embedding in zip(chunk_files, texts, embeddings):
        data.append({
            "chunk_id": path.stem,
            "text": text,
            "embedding": embedding
        })

    output_file = video_dir / "embeddings.json"

    output_file.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\nDone!")
    print(f"Embeddings generated: {len(embeddings)}")
    print(f"Vector dimensions: {len(embeddings[0])}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()