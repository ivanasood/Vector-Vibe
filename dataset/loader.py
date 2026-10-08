"""Read and validate the project's authoritative song workbook."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import pandas as pd

FEATURE_COLUMNS: Tuple[str, ...] = (
    "Classical", "Pop", "Energetic", "Peaceful", "Romantic", "Tempo", "Mood"
)
REQUIRED_COLUMNS: Tuple[str, ...] = ("ID", "Song", *FEATURE_COLUMNS)
DEFAULT_WORKBOOK = Path(__file__).resolve().parents[1] / "data" / "Mathminiprojectsongsdataset.xlsx"


@dataclass(frozen=True)
class Song:
    """One workbook record; feature order is fixed by FEATURE_COLUMNS."""
    song_id: int
    title: str
    features: Tuple[float, ...]


@dataclass(frozen=True)
class SongDataset:
    """Loaded songs plus their row-major 100-by-7 feature matrix."""
    songs: Tuple[Song, ...]
    feature_matrix: Tuple[Tuple[float, ...], ...]

    @property
    def song_count(self) -> int:
        return len(self.songs)

    @property
    def feature_count(self) -> int:
        return len(FEATURE_COLUMNS)


def load_dataset(path: str | Path = DEFAULT_WORKBOOK) -> SongDataset:
    """Load workbook records without modifying or synthesizing any values.

    Raises ValueError if expected schema/data invariants do not hold.
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Song dataset workbook not found: {source}")
    frame = pd.read_excel(source, sheet_name=0)

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Workbook is missing required columns: {missing_columns}")
    if frame.empty:
        raise ValueError("Workbook contains no song records")
    if frame[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Workbook has missing values in required song data")
    if frame["Song"].duplicated().any():
        raise ValueError("Workbook contains duplicate song titles")
    if not all(pd.api.types.is_numeric_dtype(frame[column]) for column in FEATURE_COLUMNS):
        raise ValueError("All seven feature columns must be numeric")

    matrix = tuple(
        tuple(float(row[column]) for column in FEATURE_COLUMNS)
        for _, row in frame.iterrows()
    )
    songs = tuple(
        Song(song_id=int(row["ID"]), title=str(row["Song"]), features=vector)
        for (_, row), vector in zip(frame.iterrows(), matrix)
    )
    return SongDataset(songs=songs, feature_matrix=matrix)
