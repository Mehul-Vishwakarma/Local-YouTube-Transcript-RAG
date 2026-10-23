"""Main entry point for the YouTube AI project pipeline.

Orchestrates the full workflow:
1. Fetch YouTube transcripts
2. Chunk transcripts into manageable pieces
3. Generate embeddings using Ollama
4. Enable hybrid search (semantic + keyword)
5. RAG-based question answering
"""

from src.fetch_transcript import main as fetch_main
from src.chunker import split_transcript, main as chunk_main
from src.embed_chunks import main as embed_main
from src.search import main as search_main
from src.rag import main as rag_main


def run_full_pipeline(video_id=None, transcript_path=None):
    """Run the full pipeline from transcript to searchable RAG system."""
    print("=" * 60)
    print("YOUTUBE AI PROJECT - FULL PIPELINE")
    print("=" * 60)

    # Step 1: Fetch transcript
    if video_id:
        print(f"\n[1/5] Fetching transcript for video ID: {video_id}")
        fetch_main()
    elif transcript_path and os.path.exists(transcript_path):
        print(f"\n[1/5] Using existing transcript: {transcript_path}")
    else:
        print("\n[1/5] Skipping transcript fetch (provide VIDEO_ID or transcript_path)")

    # Step 2: Chunk the transcript
    transcript_file = transcript_path or None
    if transcript_file and os.path.exists(transcript_file):
        print(f"\n[2/5] Chunking transcript...")
        chunk_main()
    else:
        print("\n[2/5] Skipping chunking (no transcript available)")

    # Step 3: Generate embeddings
    print(f"\n[3/5] Generating embeddings...")
    embed_main()

    # Step 4: Search (hybrid)
    print(f"\n[4/5] Running search...")
    search_main()

    # Step 5: RAG question answering
    print(f"\n[5/5] Running RAG question answering...")
    rag_main()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


def quick_search(question):
    """Run just the search and RAG steps on existing data."""
    print("\n" + "=" * 60)
    print("YOUTUBE AI - QUICK SEARCH & RAG")
    print("=" * 60)
    search_main()
    rag_main()
    print("=" * 60)


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd == "pipeline" and len(sys.argv) > 2:
            video_id = sys.argv[2]
            run_full_pipeline(video_id=video_id)
        elif cmd == "search" and len(sys.argv) > 2:
            question = " ".join(sys.argv[2:])
            # Need to change to project dir first
            import subprocess
            subprocess.run(["python", "src/search.py", question])
            subprocess.run(["python", "src/rag.py", question])
        elif cmd == "rag" and len(sys.argv) > 2:
            question = " ".join(sys.argv[2:])
            subprocess.run(["python", "src/rag.py", question])
        else:
            print(f"Unknown command: {cmd}")
            print("Available: pipeline <VIDEO_ID>, search <question>, rag <question>")
    else:
        # Interactive mode - just run search + RAG
        print("\nYouTube AI Project - Interactive Mode")
        print("=" * 50)
        question = input("\nAsk a question about the transcripts: ").strip()
        if question:
            quick_search(question)