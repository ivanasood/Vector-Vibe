import math

import pytest

from dataset import load_dataset
from mathematics.operations import (
    angle_degrees,
    calculateCosineSimilarity,
    calculateDotProduct,
    calculateNorm,
    calculateProjection,
    projection_alignment_score,
    rank_songs,
)
from recommendation import recommend


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


def test_dot_product_formula_and_actual_song(dataset):
    assert calculateDotProduct((1, 2, 3), (4, 5, 6)) == 32
    first = dataset.songs[0]
    expected = math.fsum(value * value for value in first.features)
    assert calculateDotProduct(first.features, first.features) == pytest.approx(expected)


def test_norm_formula_and_actual_song(dataset):
    assert calculateNorm((3, 4)) == pytest.approx(5)
    first = dataset.songs[0]
    assert calculateNorm(first.features) == pytest.approx(
        math.sqrt(math.fsum(value * value for value in first.features))
    )


def test_cosine_identical_orthogonal_and_actual_songs(dataset):
    first = dataset.songs[0].features
    assert calculateCosineSimilarity(first, first) == pytest.approx(1.0)
    assert calculateCosineSimilarity((1, 0), (0, 1)) == pytest.approx(0.0)
    swan_lake = next(s.features for s in dataset.songs if s.title.startswith("Tchaikovsky: Swan Lake"))
    tokyo_drift = next(s.features for s in dataset.songs if s.title == "Tokyo Drift (Fast & Furious)")
    assert calculateCosineSimilarity(swan_lake, tokyo_drift) == pytest.approx(0.49634342466287623)
    assert calculateCosineSimilarity(swan_lake, tokyo_drift) < 0.6


def test_angle_degrees_uses_cosine_and_handles_zero_vectors(dataset):
    first = dataset.songs[0].features
    assert angle_degrees(first, first) == pytest.approx(0.0, abs=1e-5)
    assert angle_degrees((1, 0), (0, 1)) == pytest.approx(90.0)
    assert angle_degrees((0,) * len(first), first) is None


def test_projection_formula_and_actual_song(dataset):
    assert calculateProjection((3, 4), (1, 0)) == pytest.approx((3, 0))
    first = dataset.songs[0].features
    assert calculateProjection(first, first) == pytest.approx(first)
    assert projection_alignment_score(first, first) == pytest.approx(1.0)


def test_zero_vectors_are_safe():
    assert calculateNorm((0, 0, 0)) == 0
    assert calculateDotProduct((0, 0), (1, 2)) == 0
    assert calculateCosineSimilarity((0, 0), (1, 2)) == 0
    assert calculateCosineSimilarity((0, 0), (0, 0)) == 0
    assert calculateProjection((1, 2), (0, 0)) == (0.0, 0.0)


def test_dimension_mismatch_is_rejected():
    with pytest.raises(ValueError, match="dimensions must match"):
        calculateDotProduct((1, 2), (1,))


def test_full_ranking_contains_all_scored_songs_and_top_ten(dataset):
    query = dataset.songs[0].features
    result = recommend(dataset, query)
    assert len(result.full_ranking) == 100
    assert len(result.ranking) == 100
    assert len(result.playlist) == 10
    assert [item.rank for item in result.full_ranking] == list(range(1, 101))
    assert all(len(item.features) == 7 and len(item.projection) == 7 for item in result.full_ranking)
    assert all(item.user_norm == pytest.approx(calculateNorm(query)) for item in result.full_ranking)
    assert all(item.song_norm == pytest.approx(calculateNorm(item.features)) for item in result.full_ranking)
    assert all(item.dot_product == pytest.approx(calculateDotProduct(item.features, query)) for item in result.full_ranking)
    assert all(
        result.full_ranking[i].cosine_similarity >= result.full_ranking[i + 1].cosine_similarity
        for i in range(99)
    )
    assert result.full_ranking[0].title == dataset.songs[0].title
    assert result.full_ranking[0].cosine_similarity == pytest.approx(1.0)
    assert result.full_ranking[0].angle_degrees == pytest.approx(0.0, abs=1e-5)
    assert all(row.artist is None for row in result.full_ranking)  # no artist field in source workbook


def test_changing_real_song_preference_vector_changes_recommendations(dataset):
    # Both test preferences come directly from actual workbook rows.
    classical_pref = next(s.features for s in dataset.songs if s.title.startswith("Tchaikovsky: Swan Lake"))
    pop_pref = next(s.features for s in dataset.songs if s.title == "Tokyo Drift (Fast & Furious)")
    first = recommend(dataset, classical_pref)
    second = recommend(dataset, pop_pref)
    assert first.user_vector != second.user_vector
    assert [r.song_id for r in first.full_ranking] != [r.song_id for r in second.full_ranking]
    assert [r.song_id for r in first.playlist] != [r.song_id for r in second.playlist]


def test_query_validation_and_custom_playlist_size(dataset):
    with pytest.raises(ValueError, match="must have 7 features"):
        recommend(dataset, (1, 2, 3))
    with pytest.raises(ValueError, match="nonnegative"):
        recommend(dataset, dataset.songs[0].features, top_n=-1)
    assert len(recommend(dataset, dataset.songs[0].features, top_n=2).playlist) == 2
