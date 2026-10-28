"""Thin, lazy wrapper around the optional ``ollama`` package."""

from __future__ import annotations


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama is missing or cannot be reached."""


def _require_ollama():
    try:
        import ollama
    except ImportError as exc:
        raise OllamaUnavailableError(
            "The 'ollama' Python package is not installed. "
            "Run: pip install -r requirements.txt"
        ) from exc
    return ollama


def embed_texts(model, texts):
    ollama = _require_ollama()
    try:
        response = ollama.embed(model=model, input=texts)
    except Exception as exc:
        raise OllamaUnavailableError(
            "Could not get embeddings from Ollama. Make sure the Ollama "
            f"service is running and the model '{model}' is installed "
            f"(ollama pull {model}). Details: {exc}"
        ) from exc
    return response


def chat(model, messages):
    ollama = _require_ollama()
    try:
        response = ollama.chat(model=model, messages=messages)
    except Exception as exc:
        raise OllamaUnavailableError(
            "Could not get a response from Ollama. Make sure the Ollama "
            f"service is running and the model '{model}' is installed "
            f"(ollama pull {model}). Details: {exc}"
        ) from exc
    return response
