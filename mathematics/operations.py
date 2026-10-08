"""Reusable deterministic linear-algebra operations for song feature vectors."""
from __future__ import annotations

import math
from typing import Sequence

Vector = Sequence[float]


def _validate_pair(a: Vector, b: Vector) -> None:
    if len(a) != len(b):
        raise ValueError(f"Vector dimensions must match, got {len(a)} and {len(b)}")
    if not all(math.isfinite(float(value)) for value in (*a, *b)):
        raise ValueError("Vectors must contain only finite numbers")


def dot_product(a: Vector, b: Vector) -> float:
    """Return the scalar dot product a·b."""
    _validate_pair(a, b)
    return math.fsum(float(x) * float(y) for x, y in zip(a, b))


def vector_norm(vector: Vector) -> float:
    """Return the Euclidean (L2) norm ||vector||."""
    values = tuple(float(value) for value in vector)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Vector must contain only finite numbers")
    return math.sqrt(math.fsum(value * value for value in values))


def cosine_similarity(a: Vector, b: Vector) -> float:
    """Return cosine similarity; if either vector is zero, define similarity as 0."""
    product = dot_product(a, b)
    denominator = vector_norm(a) * vector_norm(b)
    if denominator == 0.0:
        return 0.0
    # Clamp tiny floating-point overshoots to the mathematical range.
    return max(-1.0, min(1.0, product / denominator))


def angle_degrees(a: Vector, b: Vector) -> float | None:
    """Return the angle in degrees; return None if either vector has zero norm."""
    _validate_pair(a, b)
    if vector_norm(a) == 0.0 or vector_norm(b) == 0.0:
        return None
    cosine = cosine_similarity(a, b)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def vector_projection(song_vector: Vector, user_vector: Vector) -> tuple[float, ...]:
    """Project a song vector onto the user vector.

    For a zero user vector (undefined formula), return the zero vector with the
    song vector's dimension so callers can safely display/consume the result.
    """
    _validate_pair(song_vector, user_vector)
    user_squared_norm = dot_product(user_vector, user_vector)
    if user_squared_norm == 0.0:
        return tuple(0.0 for _ in song_vector)
    scale = dot_product(song_vector, user_vector) / user_squared_norm
    return tuple(scale * float(value) for value in user_vector)


def projection_alignment_score(song_vector: Vector, user_vector: Vector) -> float:
    """Return directional alignment for a projection, as cosine similarity [-1, 1].

    1 means same direction, 0 means orthogonal (or a zero vector), and -1 means
    opposite direction. For this dataset's nonnegative scores, the range is 0–1.
    """
    return cosine_similarity(song_vector, user_vector)


def rank_songs(query: Vector, feature_matrix: Sequence[Vector]) -> tuple[int, ...]:
    """Return row indices ordered by cosine similarity, descending.

    Ties retain original dataset order. A zero query yields all-zero similarities
    and therefore preserves row order.
    """
    ranked_scores: list[tuple[int, float]] = []
    for index, song_vector in enumerate(feature_matrix):
        ranked_scores.append((index, cosine_similarity(song_vector, query)))
    ranked_scores.sort(key=lambda item: (-item[1], item[0]))
    return tuple(index for index, _ in ranked_scores)


# Requested camelCase API aliases, retained alongside idiomatic Python names.
calculateDotProduct = dot_product
calculateNorm = vector_norm
calculateCosineSimilarity = cosine_similarity
calculateAngleDegrees = angle_degrees
calculateProjection = vector_projection
calculateProjectionAlignmentScore = projection_alignment_score
