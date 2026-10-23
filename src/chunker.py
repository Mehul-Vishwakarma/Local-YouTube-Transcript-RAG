import re
import sys
from pathlib import Path


def split_transcript(text, max_chars=1200, overlap_sentences=2):
    # Normalize whitespace without damaging Devanagari
    text = re.sub(r"\s+", " ", text).strip()

    # Split primarily at Hindi/English sentence endings
    sentences = re.split(r"(?<=[।!?])\s+", text)

    chunks = []
    current = []

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        test = " ".join(current + [sentence])

        if len(test) <= max_chars:
            current.append(sentence)
        else:
            if current:
                chunks.append(" ".join(current))

            # Keep a small overlap for context
            current = current[-overlap_sentences:] + [sentence]

    if current:
        chunks.append(" ".join(current))

    return chunks


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("Usage: python chunker.py <transcript.txt>")
        return

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"File not found: {input_file}")
        return

    text = input_file.read_text(encoding="utf-8")

    chunks = split_transcript(text)

    output_dir = Path("chunks")
    output_dir.mkdir(exist_ok=True)

    # Give each transcript its own chunk directory
    video_dir = output_dir / input_file.stem
    video_dir.mkdir(exist_ok=True)

    for old_file in video_dir.glob("chunk_*.txt"):
        old_file.unlink()

    for i, chunk in enumerate(chunks, start=1):
        output_file = video_dir / f"chunk_{i:03d}.txt"
        output_file.write_text(chunk, encoding="utf-8")

    print(f"\nTranscript: {input_file.name}")
    print(f"Characters: {len(text):,}")
    print(f"Chunks created: {len(chunks)}")
    print(f"Output: {video_dir}")

    print("\nFirst chunk preview:")
    print("-" * 60)
    print(chunks[0][:500])
    print("-" * 60)


if __name__ == "__main__":
    main()