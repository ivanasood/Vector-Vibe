from dataset import FEATURE_COLUMNS, load_dataset
from recommendation import explain_feature_differences
from ui.server import app


def test_home_has_top_ten_title_and_seven_live_slider_controls():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Top 10 Mathematical Recommendations" in page
    assert "all 100 songs" in page
    assert "highest cosine similarity" in page
    assert "Mathematical Analysis" in page
    assert "S · U = Σ(Sᵢ × Uᵢ)" in page
    assert "cos(θ) = (S · U) / (‖S‖ × ‖U‖)" in page
    assert "θ° = arccos(cosine similarity) × 180/π" in page
    assert "projᵤ(S) = ((S · U) / (U · U))U" in page
    assert "Top 10 Similarity Chart" in page
    assert "Similarity Distribution" in page
    assert "User vs Song Feature Comparison" in page
    assert "2D projection of the 7-dimensional feature space" in page
    assert "How VectorVibe Works" in page
    assert page.count('class="method-step"') == 6
    assert page.count('class="method-step method-step-final"') == 1
    assert "Represent songs as vectors" in page
    assert "Create the song matrix" in page
    assert "Create the user vector" in page
    assert "Calculate similarity" in page
    assert "Calculate alignment" in page
    assert "Rank all 100 songs" in page
    assert "Recommend the Top 10" in page
    assert "Dataset Overview" in page
    assert "Minimum" in page
    assert "Maximum" in page
    assert "Average" in page
    assert "actual number of songs in each bin" in page
    assert "M ∈ ℝ" in page
    assert "sim<sub>(1)</sub> ≥ sim<sub>(2)</sub>" in page
    assert page.count('class="preference-slider"') == 7
    assert page.count('class="slider-scale" aria-hidden="true"') == 7
    assert 'id="reset-preferences"' in page
    assert "Reset Preferences" in page
    for destination in ("preferences", "recommendations", "song-analysis", "visualizations", "how-it-works", "dataset-overview"):
        assert f'href="#{destination}"' in page
    assert 'id="results-stale-note"' in page
    assert 'id="zero-vector-note"' in page
    assert "All cosine scores are 0" in page
    assert "Full ranking" not in page
    assert 'id="ranking-list"' not in page


def test_ui_styles_respect_hidden_attribute_for_state_panels():
    css = app.test_client().get("/static/styles.css").get_data(as_text=True)
    assert "[hidden]" in css
    assert "display: none !important" in css


def test_dataset_overview_statistics_and_histograms_use_actual_workbook_values():
    dataset = load_dataset()
    response = app.test_client().get("/api/dataset-overview")
    assert response.status_code == 200
    body = response.get_json()
    assert body["totalSongs"] == 100
    assert body["featureCount"] == 7
    assert body["matrixDimensions"] == "100 × 7"
    assert body["featureNames"] == list(FEATURE_COLUMNS)
    assert len(body["features"]) == 7
    for index, feature in enumerate(body["features"]):
        values = [song.features[index] for song in dataset.songs]
        assert feature["name"] == FEATURE_COLUMNS[index]
        assert feature["minimum"] == min(values)
        assert feature["maximum"] == max(values)
        assert feature["average"] == sum(values) / len(values)
        assert len(feature["distribution"]) == body["histogramBinCount"] == 8
        assert sum(bin_["count"] for bin_ in feature["distribution"]) == 100
        assert feature["distribution"][0]["lowerBound"] == min(values)
        assert feature["distribution"][-1]["upperBound"] == max(values)


def test_top_ten_explanations_are_deterministic_and_based_on_actual_feature_differences():
    dataset = load_dataset()
    user_vector = list(dataset.songs[11].features)
    response = app.test_client().post("/api/recommendations", json={"userVector": user_vector})
    assert response.status_code == 200
    recommendations = response.get_json()["recommendations"]
    assert len(recommendations) == 10
    for item in recommendations:
        explanation = item["explanation"]
        assert explanation.startswith("Closest preference matches:")
        assert explanation == explain_feature_differences(item["features"], user_vector, FEATURE_COLUMNS)
        assert "Δ=" in explanation
    assert any("Largest differences:" in item["explanation"] for item in recommendations)


def test_api_compares_all_songs_but_returns_only_top_ten():
    dataset = load_dataset()
    client = app.test_client()
    response = client.post(
        "/api/recommendations",
        json={"userVector": list(dataset.songs[0].features)},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["songCount"] == 100
    assert body["featureDimensions"] == 7
    assert body["featureMatrixShape"] == "100 × 7"
    assert body["songsCompared"] == 100
    assert body["recommendationsDisplayed"] == 10
    assert len(body["recommendations"]) == 10
    assert [item["rank"] for item in body["recommendations"]] == list(range(1, 11))
    scores = [item["cosineSimilarity"] for item in body["recommendations"]]
    assert scores == sorted(scores, reverse=True)
    assert body["recommendations"][0]["title"] == dataset.songs[0].title
    assert body["recommendations"][0]["features"] == list(dataset.songs[0].features)
    assert body["recommendations"][0]["artist"] is None
    assert body["recommendations"][0]["dotProduct"] > 0
    assert body["recommendations"][0]["songNorm"] > 0
    assert body["recommendations"][0]["userNorm"] > 0
    assert len(body["recommendations"][0]["projection"]) == 7
    assert body["recommendations"][0]["projectionAlignmentScore"] == body["recommendations"][0]["cosineSimilarity"]
    assert body["recommendations"][0]["angleDegrees"] is not None
    distribution = body["similarityDistribution"]
    assert len(distribution) == 100
    assert [item["rank"] for item in distribution] == list(range(1, 101))
    distribution_scores = [item["cosineSimilarity"] for item in distribution]
    assert distribution_scores == sorted(distribution_scores, reverse=True)
    assert [item["songId"] for item in body["recommendations"]] == [item["songId"] for item in distribution[:10]]
    projection = body["vectorProjection2D"]
    assert projection["label"] == "2D projection of the 7-dimensional feature space"
    assert projection["xFeature"] == "Classical"
    assert projection["yFeature"] == "Pop"
    assert len(projection["points"]) == 100
    assert projection["points"][0]["x"] == dataset.songs[0].features[0]
    assert projection["points"][0]["y"] == dataset.songs[0].features[1]
    assert projection["userPoint"] == {"x": dataset.songs[0].features[0], "y": dataset.songs[0].features[1]}
    assert "fullRanking" not in body


def test_api_rejects_invalid_user_vector():
    client = app.test_client()
    response = client.post("/api/recommendations", json={"userVector": [0.5, 0.3]})
    assert response.status_code == 400
    assert "exactly 7" in response.get_json()["error"]


def test_api_marks_angle_undefined_for_zero_preference_vector():
    response = app.test_client().post("/api/recommendations", json={"userVector": [0] * 7})
    assert response.status_code == 200
    assert all(item["angleDegrees"] is None for item in response.get_json()["recommendations"])


def test_visualization_and_dataset_regions_are_keyboard_accessible():
    client = app.test_client()
    page = client.get("/").get_data(as_text=True)
    for element_id in (
        "top10-similarity-chart",
        "similarity-distribution-chart",
        "vector-projection-chart",
    ):
        assert f'id="{element_id}" class="svg-chart" tabindex="0" role="region"' in page
    assert 'id="result-count" role="status" aria-live="polite"' in page
    assert 'class="overview-table-wrap" tabindex="0" role="region"' in page

    css = client.get("/static/styles.css").get_data(as_text=True)
    assert "overflow-x: auto" in css
    assert "min-width: 680px" in css
    assert ".svg-chart:focus-visible" in css
    assert 'input[type="range"]:focus-visible' in css


def test_primary_recommendations_and_analysis_precede_secondary_visualizations():
    script = app.test_client().get("/static/app.js").get_data(as_text=True)
    assert "resultsContent.append(playlistList, analysisPanel, visualizationStack);" in script
