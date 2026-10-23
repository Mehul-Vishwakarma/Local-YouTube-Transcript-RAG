# YouTube AI Course Project

A comprehensive project for fetching YouTube transcripts, chunking them, generating embeddings, and enabling RAG-based question answering.

## Project Structure

```
YouTubeAI/
├── docs/              # Documentation and guides
├── scripts/           # Helper scripts and batch operations
├── src/               # Source code module
│   ├── fetch_transcript.py    # Fetch YouTube video transcripts
│   ├── chunker.py             # Split transcripts into chunks
│   ├── embed_chunks.py        # Generate embeddings using Ollama
│   └── search.py              # Hybrid semantic + keyword search
│   └── rag.py                 # RAG question answering system
├── chunks/              # Generated chunk files and embeddings
├── transcripts/         # Raw YouTube transcript TXT files
├── archive/             # Archive of original materials
├── resume/              # Resume-related documents
├── docs/                # Written docs and guides
└── requirements.txt     # Project dependencies
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Fetch a transcript

```bash
python src/fetch_transcript.py <VIDEO_ID>
```

Example:
```bash
python src/fetch_transcript.py e7oU6ZCvRrw
```

### 3. Chunk the transcript

```bash
python src/chunker.py transcripts/<filename>.txt
```

### 4. Generate embeddings

```bash
python src/embed_chunks.py
```

This will process all chunk directories and generate `embeddings.json` in each.

### 5. Search and ask questions

```bash
python src/search.py "your question here"
```

or

```bash
python src/rag.py "your question here"
```

## Pipeline Overview

1. **Fetch** - Download transcript from YouTube using `youtube-transcript-api`
2. **Chunk** - Split transcript into manageable pieces (default: 1200 chars with 2 sentence overlap)
3. **Embed** - Generate vector embeddings using Ollama's `nomic-embed-text` model
4. **Search** - Hybrid search combining semantic similarity and keyword matching
5. **RAG** - Retrieve relevant chunks and generate answers using an LLM (Phi-3 Mini)

## Available Scripts

- `scripts/reorganize.py` - Reorganize project files and fix filenames
- `scripts/generate_audit_report.py` - Generate visual resume/LinkedIn audit report (requires python-docx)
- `scripts/try.py` - Demo script for fetching transcripts
- `scripts/create_resume.py` - Resume generation helper

## Configuration

Model settings can be adjusted in each source file:

- `MODEL = "nomic-embed-text"` - Embedding model (used in embed_chunks.py, search.py, rag.py)
- `LLM_MODEL = "phi3:mini"` - LLM for RAG answer generation (rag.py)
- `TOP_K = 3` - Number of search results to return (search.py, rag.py)
- `SEMANTIC_WEIGHT = 0.6` - Semantic search weighting (search.py, rag.py)
- `KEYWORD_WEIGHT = 0.4` - Keyword search weighting (search.py, rag.py)

## License

This project is for educational purposes. See individual third-party licenses for youtube-transcript-api and Ollama.