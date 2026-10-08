"""Reusable mathematical operations for the recommendation system."""
from .operations import (
    angle_degrees,
    calculateAngleDegrees,
    calculateCosineSimilarity,
    calculateDotProduct,
    calculateNorm,
    calculateProjection,
    calculateProjectionAlignmentScore,
    cosine_similarity,
    dot_product,
    projection_alignment_score,
    rank_songs,
    vector_norm,
    vector_projection,
)

__all__ = [
    "calculateDotProduct", "calculateNorm", "calculateCosineSimilarity", "calculateAngleDegrees",
    "calculateProjection", "calculateProjectionAlignmentScore",
    "dot_product", "vector_norm", "cosine_similarity", "angle_degrees", "vector_projection",
    "projection_alignment_score", "rank_songs",
]
