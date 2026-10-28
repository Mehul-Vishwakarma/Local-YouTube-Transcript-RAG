# Local YouTube Transcript RAG

A local-first tool that fetches YouTube course transcripts, chunks them,
embeds them with Ollama, and answers questions with source attribution. It
works with English and Hindi transcripts and does not require any paid API or
cloud database.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) running locally
- Two Ollama models:

```bash
ollama pull nomic-embed-text
ollama pull phi3:mini
```

`nomic-embed-text` creates embeddings and `phi3:mini` writes the final answer.
Ollama normally runs as a background service after installation. If it is not
running, start it with:

```bash
ollama serve
```

## Install

```bash
pip install -r requirements.txt
```

For development and tests:

```bash
pip install -r requirements-dev.txt
```

## Repository structure

```
youtube-ai-tool/
├── src/
│   ├── main.py              # Pipeline orchestration and CLI
│   ├── fetch_transcript.py  # YouTube transcript fetching
│   ├── chunker.py           # Sentence-aware, size-bounded chunking
│   ├── embed_chunks.py      # Ollama embeddings for every video index
│   ├── search.py            # Hybrid semantic + keyword search
│   ├── rag.py               # Thresholded RAG answers with sources
│   ├── paths.py             # Project-root path resolution
│   ├── scoring.py           # Vector/text scoring helpers
│   ├── store.py             # Manifest and embeddings readers/writers
│   └── ollama_client.py     # Lazy Ollama wrapper and error messages
├── scripts/
│   ├── fetch_transcript.py  # Compatibility wrapper for src/fetch_transcript.py
│   ├── rag.py               # Compatibility wrapper for src/rag.py
│   ├── create_resume.py     # Unrelated resume helper
│   └── generate_audit_report.py
├── tests/                   # Offline pytest suite
├── transcripts/             # Raw transcript .txt files + .meta.json sidecars
├── chunks/                  # Generated indexes (created at runtime)
├── run.bat                  # Windows menu runner
├── fetch_transcript.bat     # Windows transcript fetcher
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

Transcripts and chunks always resolve to `<project-root>/transcripts/` and
`<project-root>/chunks/`, regardless of the terminal's current directory.

## Quick start

### 1. Fetch a transcript

```bash
python src/fetch_transcript.py VIDEO_ID
```

Example:

```bash
python src/fetch_transcript.py e7oU6ZCvRrw
```

The transcript is saved as `transcripts/<VIDEO_ID>.txt`, with title and source
metadata in `transcripts/<VIDEO_ID>.meta.json`. Using the video ID as the
filename prevents collisions between videos with similar titles. Existing
title-based transcript files are still supported.

### 2. Chunk transcripts

Process every transcript in `transcripts/`:

```bash
python src/chunker.py transcripts
```

Process one file:

```bash
python src/chunker.py transcripts/VIDEO_ID.txt
```

The chunker writes `chunks/<VIDEO_ID>/chunks.json`, individual
`chunk_001.txt` files, and metadata for each chunk. Normal chunks are at most
1200 characters with two sentences of overlap. Overlong sentences are
hard-wrapped so the size limit is always respected. Empty transcripts produce
an empty manifest instead of crashing.

### 3. Generate embeddings

```bash
python src/embed_chunks.py
```

Every video directory under `chunks/` is embedded, not just the first one.
Each `chunks/<VIDEO_ID>/embeddings.json` record contains the chunk text,
embedding, video ID, video title, and chunk ID.

### 4. Search

```bash
python src/search.py "What is RAG?" --top-k 5
```

Search loads all available video indexes and ranks results across all videos.
The hybrid score combines absolute semantic similarity with normalized keyword
coverage. If every keyword score is zero, keyword normalization stays zero
instead of making every chunk look like a perfect keyword match.

### 5. Ask a question

```bash
python src/rag.py "What is RAG?"
```

If no retrieved chunk meets the relevance threshold, the tool does not call the
LLM. It reports:

> The indexed transcripts do not contain enough relevant information to answer
> this question.

Successful answers include the source video title, video ID, and chunk ID for
each supporting chunk.

### 6. Run the full pipeline

```bash
python src/main.py pipeline VIDEO_ID --question "What is RAG?"
```

Chunk and embed all existing transcripts without fetching a new video:

```bash
python src/main.py pipeline
```

Other commands:

```bash
python src/main.py search "What is RAG?"
python src/main.py rag "What is RAG?"
python src/main.py            # interactive question prompt
```

On Windows, `run.bat` provides a menu for the same operations, and
`fetch_transcript.bat` wraps transcript fetching. Batch mode passes the
`transcripts` directory rather than a `*.txt` wildcard, so it works correctly in
`cmd.exe`.

## Configuration

Settings can be changed with environment variables or command-line flags.

| Setting | Default | Environment variable |
| --- | --- | --- |
| Embedding model | `nomic-embed-text` | `YOUTUBE_RAG_EMBED_MODEL` |
| Answer model | `phi3:mini` | `YOUTUBE_RAG_LLM_MODEL` |
| Top results | `3` | `YOUTUBE_RAG_TOP_K` |
| Minimum relevance | `0.25` | `YOUTUBE_RAG_MIN_RELEVANCE` |
| Semantic weight | `0.6` | `YOUTUBE_RAG_SEMANTIC_WEIGHT` |
| Keyword weight | `0.4` | `YOUTUBE_RAG_KEYWORD_WEIGHT` |
| Transcripts directory | `<root>/transcripts` | `YOUTUBE_RAG_TRANSCRIPTS_DIR` |
| Chunks directory | `<root>/chunks` | `YOUTUBE_RAG_CHUNKS_DIR` |

Command-line options include `--top-k`, `--min-score`, `--chunks-dir`, `--model`,
and `--llm-model` where applicable.

The default minimum relevance is intentionally conservative. Lower it (for
example `--min-score 0.15`) if relevant answers are being rejected. Raise it if
unrelated chunks are being treated as evidence. The threshold only has meaning
when the embeddings were generated with the same embedding model used for
search.

## Data formats

- `transcripts/<VIDEO_ID>.meta.json` stores `video_id`, `video_title`,
  transcript filename, character count, and fetch time.
- `chunks/<VIDEO_ID>/chunks.json` stores the source video metadata and every
  chunk's `chunk_id`, `text`, `video_id`, and `video_title`.
- `chunks/<VIDEO_ID>/embeddings.json` stores the same metadata plus each chunk's
  embedding vector.

Malformed manifests, empty indexes, missing embedding files, invalid or
zero-length vectors, and unreachable Ollama services are reported without
crashing the pipeline.

## Tests

The test suite is fully offline. It mocks YouTube and Ollama, so it does not
need network access or a running Ollama server.

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q src scripts tests
```

## Troubleshooting

### `Could not get embeddings from Ollama`

- Make sure Ollama is installed and running: `ollama serve`
- Verify the model exists: `ollama pull nomic-embed-text`
- Run `ollama list` to see installed models.

### `No chunk directories with chunks were found`

Run the chunker first:

```bash
python src/chunker.py transcripts
```

### `No relevant chunks were found at the configured threshold`

- Confirm the index was embedded with `python src/embed_chunks.py`.
- Lower `--min-score` slightly.
- Do not mix embeddings created by different embedding models.
- Check that the question is about content actually present in the transcripts.

### The answer says the transcripts do not contain enough information

This is expected when retrieval finds no evidence above the threshold or the
retrieved text does not support the question. The tool deliberately avoids
inventing an answer. Re-index the relevant video or adjust the threshold.

### Non-ASCII / Hindi text looks wrong in a terminal

The Python entry points reconfigure standard output to UTF-8. On older Windows
consoles, run `chcp 65001` before starting a command, or use Windows Terminal.

### Regenerating an index

Re-running the chunker deletes that video's old `chunk_*.txt` files and stale
`embeddings.json`, then writes a fresh manifest. Re-run
`python src/embed_chunks.py` afterward. Transcripts themselves are never
deleted.

## License

This project is for educational purposes. See the licenses for
`youtube-transcript-api`, NumPy, and Ollama.
