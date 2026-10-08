"""Minimal project entry point for validating the real song dataset."""
from dataset import FEATURE_COLUMNS, load_dataset


def main() -> None:
    dataset = load_dataset()
    print("VectorVibe — Mathematical Music Recommendation System")
    print(f"Songs loaded: {dataset.song_count}")
    print(f"Feature order: {', '.join(FEATURE_COLUMNS)}")
    print(f"Feature matrix shape: {dataset.song_count} x {dataset.feature_count}")
    print(f"First song: {dataset.songs[0].title}")


if __name__ == "__main__":
    main()
