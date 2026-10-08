"""Deterministic, value-based explanations for song/user feature alignment."""
from __future__ import annotations

from typing import Sequence

from dataset.loader import FEATURE_COLUMNS


def explain_feature_differences(
    song_features: Sequence[float],
    user_preferences: Sequence[float],
    feature_names: Sequence[str] = FEATURE_COLUMNS,
    match_count: int = 3,
    gap_count: int = 2,
) -> str:
    """Describe the closest and most different dimensions using absolute deltas.

    Ties are resolved by the dataset's feature order. The three smallest
    absolute differences are reported as closest matches. Up to two dimensions
    outside that group are named as gaps only if their differences are strictly
    larger than the largest difference in the closest group.
    """
    if len(song_features) != len(user_preferences) or len(song_features) != len(feature_names):
        raise ValueError("Song features, user preferences, and feature names must have equal lengths")
    if match_count < 1 or gap_count < 0:
        raise ValueError("match_count must be positive and gap_count nonnegative")
    if not song_features:
        raise ValueError("At least one feature is required")

    differences = [
        (index, str(feature_names[index]), abs(float(song_features[index]) - float(user_preferences[index])))
        for index in range(len(song_features))
    ]
    ordered = sorted(differences, key=lambda item: (item[2], item[0]))
    closest = ordered[:min(match_count, len(ordered))]
    closest_cutoff = closest[-1][2]
    closest_indices = {item[0] for item in closest}
    gaps = [
        item for item in sorted(differences, key=lambda value: (-value[2], value[0]))
        if item[0] not in closest_indices and item[2] > closest_cutoff
    ][:gap_count]

    def describe(items: Sequence[tuple[int, str, float]]) -> str:
        labels = [f"{name} (Δ={difference:.3f})" for _, name, difference in items]
        if len(labels) == 1:
            return labels[0]
        if len(labels) == 2:
            return f"{labels[0]} and {labels[1]}"
        return f"{', '.join(labels[:-1])}, and {labels[-1]}"

    explanation = f"Closest preference matches: {describe(closest)}."
    if gaps:
        explanation += f" Largest differences: {describe(gaps)}."
    return explanation
