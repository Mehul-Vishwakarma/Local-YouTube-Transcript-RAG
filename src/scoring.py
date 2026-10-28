"""Reusable text and vector scoring helpers.

The functions here are deliberately defensive: malformed vectors or empty
inputs should produce a neutral score instead of crashing a search.
"""

from __future__ import annotations

import re

import numpy as np

HINDI_STOPWORDS = {
    "है", "हैं", "हो", "होता", "होती", "होते", "क्या", "कैसे", "क्यों",
    "का", "की", "के", "को", "से", "में", "पर", "ने", "और", "ये", "वो",
    "कर", "करना", "करनी", "चाहिए", "रहना", "बताओ", "बताइए",
    "काम", "करता", "करते", "करती", "गया", "गई", "गए", "था", "थी", "थे",
    "मेरी", "मेरा", "मेरे", "आप", "तुम", "एक", "अपना", "अपने", "अपनी",
}

_PUNCTUATION_RE = re.compile(r"[.,!?;:'\"()\[\]{}।॥]+")
_EPSILON = 1e-9


def normalize_text(text):
    """Lowercase text and replace punctuation with whitespace."""
    return _PUNCTUATION_RE.sub(" ", (text or "").lower())


def tokenize(text):
    """Split text into searchable terms, dropping Hindi stopwords."""
    return [token for token in normalize_text(text).split() if token not in HINDI_STOPWORDS]


def _as_vector(value):
    """Return a finite 1-D float array, or ``None`` for an invalid vector."""
    if value is None:
        return None
    try:
        vector = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        return None
    if vector.ndim != 1 or vector.size == 0:
        return None
    if not np.all(np.isfinite(vector)):
        return None
    return vector


def is_valid_vector(value):
    """A usable embedding must be finite, non-empty, and have a non-zero norm."""
    vector = _as_vector(value)
    if vector is None:
        return False
    return bool(np.linalg.norm(vector) > _EPSILON)


def cosine_similarity(left, right):
    """Cosine similarity that returns ``0.0`` for unusable vectors."""
    a = _as_vector(left)
    b = _as_vector(right)
    if a is None or b is None or a.shape != b.shape:
        return 0.0

    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator <= _EPSILON:
        return 0.0

    return float(np.clip(np.dot(a, b) / denominator, -1.0, 1.0))


def min_max_normalize(values):
    """Scale values into ``[0, 1]``.

    When every value is equal there is no relative ranking information, so the
    neutral result is all zeros. In particular, a list of all-zero keyword
    scores must not become a list of perfect (1.0) matches.
    """
    cleaned = []
    for value in values or []:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0
        cleaned.append(number if np.isfinite(number) else 0.0)

    if not cleaned:
        return []

    low = min(cleaned)
    high = max(cleaned)
    if high - low <= _EPSILON:
        return [0.0] * len(cleaned)

    return [(value - low) / (high - low) for value in cleaned]


def keyword_similarity(query_terms, text):
    """Fraction of query terms present in *text*."""
    if not query_terms:
        return 0.0

    haystack = normalize_text(text)
    matched = sum(1 for term in query_terms if term and term in haystack)
    return matched / len(query_terms)


def hybrid_score(
    semantic,
    keyword_normalized,
    semantic_weight=0.6,
    keyword_weight=0.4,
):
    """Combine an absolute semantic score with a normalized keyword score."""
    semantic_part = max(0.0, min(1.0, float(semantic)))
    keyword_part = max(0.0, min(1.0, float(keyword_normalized)))
    return semantic_weight * semantic_part + keyword_weight * keyword_part
