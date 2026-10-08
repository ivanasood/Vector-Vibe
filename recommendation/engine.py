"""Deterministic full-catalog recommendation engine using the math layer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from dataset.loader import SongDataset
from mathematics import operations


@dataclass(frozen=True)
class SongScore:
    """One song's complete mathematical recommendation record."""
    song_id: int
    title: str
    artist: str | None
    features: tuple[float, ...]
    dot_product: float
    song_norm: float
    user_norm: float
    cosine_similarity: float
    angle_degrees: float | None
    projection: tuple[float, ...]
    projection_alignment_score: float
    rank: int


@dataclass(frozen=True)
class RecommendationResult:
    """Top playlist plus the complete descending ranking of the catalog."""
    user_vector: tuple[float, ...]
    playlist: tuple[SongScore, ...]
    full_ranking: tuple[SongScore, ...]

    @property
    def ranking(self) -> tuple[SongScore, ...]:
        """Short alias for the full ranking."""
        return self.full_ranking


def recommend(
    dataset: SongDataset,
    query_vector: Sequence[float],
    top_n: int = 10,
) -> RecommendationResult:
    """Score every dataset song and return top_n plus all ranked song results.

    Ranking is solely by descending cosine similarity. Equal scores retain
    workbook order. No popularity, randomness, AI, or external data is used.
    The current workbook has no artist column, so artist is None for each row.
    """
    if len(query_vector) != dataset.feature_count:
        raise ValueError(
            f"User vector must have {dataset.feature_count} features, got {len(query_vector)}"
        )
    if top_n < 0:
        raise ValueError("top_n must be nonnegative")

    user = tuple(float(value) for value in query_vector)
    user_norm = operations.vector_norm(user)
    scored: list[SongScore] = []

    # Calculate and retain all requested per-song values before sorting.
    for song in dataset.songs:
        vector = song.features
        dot = operations.dot_product(vector, user)
        song_norm = operations.vector_norm(vector)
        similarity = operations.cosine_similarity(vector, user)
        angle = operations.angle_degrees(vector, user)
        projection = operations.vector_projection(vector, user)
        alignment = operations.projection_alignment_score(vector, user)
        scored.append(
            SongScore(
                song_id=song.song_id,
                title=song.title,
                artist=None,
                features=tuple(vector),
                dot_product=dot,
                song_norm=song_norm,
                user_norm=user_norm,
                cosine_similarity=similarity,
                angle_degrees=angle,
                projection=projection,
                projection_alignment_score=alignment,
                rank=0,
            )
        )

    # Stable sort preserves source workbook order for exact ties.
    scored.sort(key=lambda result: -result.cosine_similarity)
    full_ranking = tuple(
        SongScore(
            song_id=result.song_id,
            title=result.title,
            artist=result.artist,
            features=result.features,
            dot_product=result.dot_product,
            song_norm=result.song_norm,
            user_norm=result.user_norm,
            cosine_similarity=result.cosine_similarity,
            angle_degrees=result.angle_degrees,
            projection=result.projection,
            projection_alignment_score=result.projection_alignment_score,
            rank=position,
        )
        for position, result in enumerate(scored, start=1)
    )
    return RecommendationResult(
        user_vector=user,
        playlist=full_ranking[:top_n],
        full_ranking=full_ranking,
    )
