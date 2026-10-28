import math

from src.scoring import (
    cosine_similarity,
    hybrid_score,
    is_valid_vector,
    keyword_similarity,
    min_max_normalize,
    tokenize,
)


def test_min_max_normalize_regular_values():
    assert min_max_normalize([1.0, 3.0, 2.0]) == [0.0, 1.0, 0.5]


def test_min_max_normalize_all_zero_stays_zero():
    assert min_max_normalize([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]


def test_min_max_normalize_constant_positive_is_neutral():
    assert min_max_normalize([0.4, 0.4, 0.4]) == [0.0, 0.0, 0.0]


def test_min_max_normalize_handles_empty_and_invalid_values():
    assert min_max_normalize([]) == []
    assert min_max_normalize([1.0, "bad", float("nan")]) == [1.0, 0.0, 0.0]


def test_keyword_normalization_does_not_create_perfect_matches():
    keyword_scores = [0.0, 0.0, 0.0]
    normalized = min_max_normalize(keyword_scores)

    assert normalized == [0.0, 0.0, 0.0]
    assert hybrid_score(0.0, normalized[0]) == 0.0
    # A perfect semantic score plus zero keywords must not become 1.0.
    assert math.isclose(hybrid_score(1.0, normalized[0]), 0.6)


def test_zero_and_invalid_vectors_score_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity([], [1.0, 2.0]) == 0.0
    assert cosine_similarity(None, [1.0, 2.0]) == 0.0
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0
    assert cosine_similarity([float("nan"), 1.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity("not-a-vector", [1.0, 2.0]) == 0.0


def test_valid_vector_check():
    assert is_valid_vector([1.0, 2.0])
    assert not is_valid_vector([0.0, 0.0])
    assert not is_valid_vector([])
    assert not is_valid_vector([float("inf")])


def test_keyword_similarity_and_tokenize():
    terms = tokenize("What is RAG and how does it work?")
    assert "rag" in terms
    assert keyword_similarity(terms, "RAG works by retrieving context") > 0.0
    assert keyword_similarity([], "anything") == 0.0
