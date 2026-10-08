# VectorVibe

**Mathematical Music Recommendation System**  
University Linear Algebra / MFAD project.

## Project structure

```text
VectorVibe/
├── data/Mathminiprojectsongsdataset.xlsx  # sole song source; copied unchanged
├── dataset/loader.py                     # validated Song records and 100 × 7 matrix
├── mathematics/operations.py             # deterministic reusable linear algebra
├── recommendation/engine.py              # computes all-song scores and sorts before slicing
├── recommendation/explanations.py        # deterministic absolute-difference explanations
├── visualization/payloads.py             # actual chart, statistics, and histogram payloads
├── ui/server.py                          # Flask page/API connected to the engine
├── ui/templates/index.html               # preference builder and analysis/results states
├── ui/static/                            # responsive SVG visualizations and styles
├── tests/
└── main.py
```

## Data and feature order

Song and user vectors use `Classical, Pop, Energetic, Peaceful, Romantic, Tempo, Mood`. Workbook `ID` and `Song` are metadata; rows are built directly from the workbook with no synthetic values. The loader returns a row-major 100 × 7 matrix. The workbook has no artist column, so `SongScore.artist` is `None` rather than fabricated. The bundled workbook matches the uploaded source (SHA-256 `c11ce7e1c9635d9b0fec6b7831666beaf6e65462ce876e0ff32a3cff2fbbd2ff`).

## Mathematical and recommendation APIs

`mathematics.operations` provides reusable dot product, norm, cosine similarity, angle in degrees, projection, alignment score, and ranking functions (camelCase and snake_case APIs). `recommendation.recommend(dataset, user_vector, top_n=10)` computes every song’s score, sorts all songs by descending cosine similarity, retains the complete internal ranking, and returns the top 10 along with that ranking. All ranking is deterministic Linear Algebra, with no AI, popularity rule, or random selection.

## Interface and visualizations

The seven live 0–1 sliders show endpoint labels and current values; **Reset Preferences** restores all seven defaults to `0.50`. On Generate Playlist, the backend compares the preference vector against all 100 dataset songs and returns only the top 10 for recommendation display. A short accessible loading state precedes a smooth transition to results. If preferences change after a playlist was generated, the page marks the existing results as belonging to the previous vector. Each result includes the original seven features, paired user/song bars, and a deterministic explanation: the three smallest absolute feature differences are listed as closest matches, with up to two strictly larger remaining differences called out as gaps. Ties resolve in feature order. No model or external AI service is involved.

Charts are data-driven SVGs: (1) a horizontal Top 10 similarity chart with exact percentages; (2) a full-catalog similarity distribution for all 100 computed scores, with the Top 10 highlighted and remaining 90 distinguished; (3) a selected-song grouped user-versus-song comparison for all seven features; and (4) a song-cloud view labeled **“2D projection of the 7-dimensional feature space.”** This 2D plot is an orthogonal coordinate projection onto Classical (x) and Pop (y); the other five dimensions are explicitly omitted, so it does not claim to show the full 7D space. It includes all 100 songs, the generated user point, and selected recommended song.

The secondary **Dataset Overview** is calculated from the loaded workbook feature matrix. It reports total songs, feature count, matrix dimensions, and each feature’s minimum, maximum, and arithmetic mean. Its small histograms divide each feature’s observed min–max range into eight equal-width bins and show the actual number of songs in each bin.

Selecting a recommendation also opens a presentation-ready Mathematical Analysis with labeled U and S vectors, dot product, norms, cosine formula and percentage, arccos angle, directional-angle explanation, and the 7D vector projection. Angle is undefined when either vector has zero norm; projection onto a zero user vector is handled safely. No charts use mock or randomly generated data. No 100-row ranking table is displayed.

The page also includes **How VectorVibe Works**, a seven-step, first-year-friendly walkthrough: represent each song as a 7D vector; arrange all songs as `M ∈ ℝ^(100×7)`; build `U ∈ ℝ^7` from the sliders; compute dot products, norms, and cosine similarities; show the projection and cosine alignment; sort the 100 calculated scores; and display only the Top 10. The explanation mirrors the implemented recommendation flow and adds no separate algorithm.

Run from this directory:

```bash
python3 -m pip install -e '.[test]'
python3 -m ui.server
```

Open `http://localhost:8000`. API health check: `/api/health`. Run tests with `python3 -m pytest -q`.
