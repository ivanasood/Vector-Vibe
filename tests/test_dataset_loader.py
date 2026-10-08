from dataset import FEATURE_COLUMNS, load_dataset


def test_uploaded_dataset_loads_as_100_by_7():
    dataset = load_dataset()
    assert dataset.song_count == 100
    assert dataset.feature_count == 7
    assert len(dataset.feature_matrix) == 100
    assert all(len(vector) == 7 for vector in dataset.feature_matrix)
    assert len(dataset.songs) == 100
    assert FEATURE_COLUMNS == (
        "Classical", "Pop", "Energetic", "Peaceful", "Romantic", "Tempo", "Mood"
    )


def test_song_records_preserve_workbook_feature_order():
    dataset = load_dataset()
    assert dataset.feature_matrix[0] == dataset.songs[0].features
    assert dataset.songs[0].title == "Aaoge Tum Kabhi"
    assert dataset.songs[0].features == (0.05, 0.65, 0.55, 0.70, 0.65, 0.48, 0.55)
