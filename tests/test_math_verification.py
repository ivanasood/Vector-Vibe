"""Independent formula checks against the actual workbook and recommendation API."""
import math

import pytest

from dataset import FEATURE_COLUMNS, load_dataset
from ui.server import app


QUERY = (0.27, 0.73, 0.46, 0.21, 0.68, 0.59, 0.84)


def manual_metrics(song_vector, user_vector):
    """Recompute formulas directly, independently of mathematics.operations."""
    dot = sum(song * user for song, user in zip(song_vector, user_vector))
    song_norm = math.sqrt(sum(value * value for value in song_vector))
    user_norm = math.sqrt(sum(value * value for value in user_vector))
    denominator = song_norm * user_norm
    cosine = 0.0 if denominator == 0.0 else max(-1.0, min(1.0, dot / denominator))
    angle = None if song_norm == 0.0 or user_norm == 0.0 else math.degrees(math.acos(cosine))
    user_squared_norm = sum(value * value for value in user_vector)
    projection = (
        tuple(0.0 for _ in user_vector)
        if user_squared_norm == 0.0
        else tuple((dot / user_squared_norm) * value for value in user_vector)
    )
    return dot, song_norm, user_norm, cosine, angle, projection


def test_three_real_song_calculations_match_independent_manual_formulas():
    dataset = load_dataset()
    assert dataset.song_count == 100
    assert len(FEATURE_COLUMNS) == 7
    response = app.test_client().post("/api/recommendations", json={"userVector": QUERY})
    assert response.status_code == 200
    body = response.get_json()

    # Use the first three real songs surfaced by the application's actual ranking.
    for result in body["recommendations"][:3]:
        expected = manual_metrics(result["features"], QUERY)
        assert result["dotProduct"] == pytest.approx(expected[0], abs=1e-12)
        assert result["songNorm"] == pytest.approx(expected[1], abs=1e-12)
        assert result["userNorm"] == pytest.approx(expected[2], abs=1e-12)
        assert result["cosineSimilarity"] == pytest.approx(expected[3], abs=1e-12)
        assert result["angleDegrees"] == pytest.approx(expected[4], abs=1e-10)
        assert result["projection"] == pytest.approx(expected[5], abs=1e-12)


def test_manual_scores_for_all_100_rows_produce_the_displayed_top_ten():
    dataset = load_dataset()
    manual_scores = [
        (index, manual_metrics(song.features, QUERY)[3])
        for index, song in enumerate(dataset.songs)
    ]
    manual_scores.sort(key=lambda item: (-item[1], item[0]))

    body = app.test_client().post(
        "/api/recommendations", json={"userVector": QUERY}
    ).get_json()
    assert body["songCount"] == 100
    assert body["featureDimensions"] == 7
    assert body["featureMatrixShape"] == "100 × 7"
    assert body["songsCompared"] == 100
    assert len(dataset.feature_matrix) == 100
    assert all(len(row) == 7 for row in dataset.feature_matrix)

    distribution = body["similarityDistribution"]
    assert len(distribution) == 100
    expected_ids = [dataset.songs[index].song_id for index, _ in manual_scores]
    assert [row["songId"] for row in distribution] == expected_ids
    for row, (_, expected_score) in zip(distribution, manual_scores):
        assert row["cosineSimilarity"] == pytest.approx(expected_score, abs=1e-12)

    recommendations = body["recommendations"]
    assert len(recommendations) == 10
    assert [row["songId"] for row in recommendations] == expected_ids[:10]
    assert [row["songId"] for row in recommendations] == [row["songId"] for row in distribution[:10]]


def test_identical_real_song_vectors_and_zero_user_vector_are_safe():
    dataset = load_dataset()
    first_song = dataset.songs[0]
    client = app.test_client()

    identical = client.post(
        "/api/recommendations", json={"userVector": list(first_song.features)}
    ).get_json()
    identical_result = next(
        row for row in identical["recommendations"] if row["songId"] == first_song.song_id
    )
    assert identical_result["cosineSimilarity"] == pytest.approx(1.0, abs=1e-12)
    assert identical_result["angleDegrees"] == pytest.approx(0.0, abs=1e-5)
    assert identical_result["projection"] == pytest.approx(first_song.features, abs=1e-12)

    zero = client.post("/api/recommendations", json={"userVector": [0.0] * 7}).get_json()
    assert zero["songsCompared"] == 100
    assert len(zero["similarityDistribution"]) == 100
    assert all(row["cosineSimilarity"] == 0.0 for row in zero["similarityDistribution"])
    assert [row["songId"] for row in zero["recommendations"]] == [
        song.song_id for song in dataset.songs[:10]
    ]
    assert all(row["userNorm"] == 0.0 for row in zero["recommendations"])
    assert all(row["angleDegrees"] is None for row in zero["recommendations"])
    assert all(row["projection"] == [0.0] * 7 for row in zero["recommendations"])
