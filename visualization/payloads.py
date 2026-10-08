"""Small deterministic payload builders for data-derived UI visualizations."""
from __future__ import annotations

from typing import Sequence

from dataset.loader import FEATURE_COLUMNS, SongDataset


def similarity_distribution(ranked_songs: Sequence[object]) -> list[dict[str, object]]:
    """Return every computed song similarity, in the engine's descending rank order."""
    return [
        {
            "rank": int(song.rank),
            "songId": int(song.song_id),
            "title": str(song.title),
            "cosineSimilarity": float(song.cosine_similarity),
        }
        for song in ranked_songs
    ]


def feature_plane_projection(dataset: SongDataset, user_vector: Sequence[float]) -> dict[str, object]:
    """Project real 7D points onto the Classical/Pop coordinate plane.

    This is a coordinate projection (retaining the first two dataset features),
    not a claim that the complete seven-dimensional structure is visible.
    """
    if len(user_vector) != dataset.feature_count:
        raise ValueError(f"User vector must have {dataset.feature_count} features")
    x_feature, y_feature = FEATURE_COLUMNS[:2]
    return {
        "label": "2D projection of the 7-dimensional feature space",
        "projectionMethod": f"Orthogonal coordinate projection onto {x_feature} and {y_feature} axes",
        "xFeature": x_feature,
        "yFeature": y_feature,
        "omittedFeatures": list(FEATURE_COLUMNS[2:]),
        "points": [
            {
                "songId": song.song_id,
                "title": song.title,
                "x": float(song.features[0]),
                "y": float(song.features[1]),
            }
            for song in dataset.songs
        ],
        "userPoint": {"x": float(user_vector[0]), "y": float(user_vector[1])},
    }


def dataset_overview_payload(dataset: SongDataset, histogram_bin_count: int = 8) -> dict[str, object]:
    """Calculate per-feature descriptive statistics and equal-width histogram bins."""
    if histogram_bin_count < 1:
        raise ValueError("histogram_bin_count must be at least 1")
    row_count = dataset.song_count
    column_count = dataset.feature_count
    features: list[dict[str, object]] = []
    for index, name in enumerate(FEATURE_COLUMNS):
        values = [float(row[index]) for row in dataset.feature_matrix]
        minimum = min(values)
        maximum = max(values)
        average = sum(values) / len(values)
        span = maximum - minimum
        counts = [0] * histogram_bin_count
        if span == 0:
            counts[0] = len(values)
        else:
            for value in values:
                bin_index = min(int((value - minimum) / span * histogram_bin_count), histogram_bin_count - 1)
                counts[bin_index] += 1
        bins = []
        for bin_index, count in enumerate(counts):
            lower = minimum + span * bin_index / histogram_bin_count
            upper = maximum if bin_index == histogram_bin_count - 1 else minimum + span * (bin_index + 1) / histogram_bin_count
            bins.append({"lowerBound": lower, "upperBound": upper, "count": count})
        features.append({
            "name": name,
            "minimum": minimum,
            "maximum": maximum,
            "average": average,
            "distribution": bins,
        })
    return {
        "totalSongs": row_count,
        "featureCount": column_count,
        "matrixDimensions": f"{row_count} × {column_count}",
        "featureNames": list(FEATURE_COLUMNS),
        "histogramBinCount": histogram_bin_count,
        "features": features,
    }
