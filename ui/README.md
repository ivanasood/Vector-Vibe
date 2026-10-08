# VectorVibe UI

The responsive dark music-analytics interface uses seven live 0–1 preference sliders and the actual uploaded workbook. Generate Playlist compares the preference vector against all 100 songs, then returns the ten highest cosine-similarity results for display. A calculation card reports the dataset size, dimensions, matrix shape, songs compared, and recommendations displayed.

Each slider shows its feature name, current numeric value, and a labeled 0–1 scale. **Reset Preferences** restores all values to their `0.50` defaults. Generation includes a brief accessible loading state, then smoothly brings the results into view. A compact section navigation scrolls to Preferences, Recommendations, Mathematical Analysis, Visualizations, How It Works, and Dataset; links to analysis or charts explain when a playlist/selection is needed. Song-title buttons open the selected song’s analysis, and the active card is visibly highlighted. If sliders are changed after generation, a note clarifies that the displayed results use the previous vector.

Each Top 10 card includes a deterministic explanation derived from its seven real feature values and the current user vector. VectorVibe orders absolute feature differences, names the three smallest as the closest matches, and optionally identifies up to two remaining dimensions whose differences are strictly larger than the closest-match cutoff. Feature order resolves ties. The explanation is ordinary deterministic code—no LLM or external AI API.

Charts use source/calculated values only:

- A horizontal Top 10 Similarity Chart displays the ten ordered cosine scores with percentages.
- Similarity Distribution displays all 100 ranked scores, highlighting the Top 10 and distinguishing the other 90.
- Selecting a recommendation opens its grouped seven-feature user-versus-song comparison and Mathematical Analysis details.
- The **“2D projection of the 7-dimensional feature space”** plots the actual Classical and Pop coordinates for all 100 songs, along with the generated user vector and selected song. It is an orthogonal coordinate projection onto those two axes; the other five dimensions are omitted, so the view is not presented as the full 7D space.

The **How VectorVibe Works** section explains the implemented process in seven steps: song vectors, the `100 × 7` matrix, the user vector, dot products/norms/cosine similarity, projection and directional alignment, descending ranking of all 100 songs, and display of the Top 10.

The secondary **Dataset Overview** fetches statistics derived from the real workbook matrix: total songs, feature dimensions, matrix shape, and minimum, maximum, and arithmetic mean for every feature. Each small histogram shows actual song counts across eight equal-width bins spanning that feature’s observed min–max range.

No chart data is mocked or randomized. The workbook contains no artist column, so artist names are not invented. Run from the project root with `python3 -m ui.server` (default port 8000).
