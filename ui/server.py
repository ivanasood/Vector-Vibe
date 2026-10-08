"""Small web API and page server for the VectorVibe local application."""
from __future__ import annotations

import math
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from dataset import FEATURE_COLUMNS, load_dataset
from recommendation import explain_feature_differences, recommend
from visualization import dataset_overview_payload, feature_plane_projection, similarity_distribution

ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__, template_folder=str(ROOT / "ui" / "templates"), static_folder=str(ROOT / "ui" / "static"))
_DATASET = load_dataset()


@app.get("/")
def home():
    return render_template("index.html", feature_columns=FEATURE_COLUMNS)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "songs": _DATASET.song_count, "dimensions": _DATASET.feature_count})


@app.get("/api/dataset-overview")
def dataset_overview():
    return jsonify(dataset_overview_payload(_DATASET))


@app.post("/api/recommendations")
def recommendations():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("userVector"), list):
        return jsonify({"error": "Send a JSON object with a seven-value userVector array."}), 400

    raw_vector = payload["userVector"]
    if len(raw_vector) != len(FEATURE_COLUMNS):
        return jsonify({"error": f"userVector must contain exactly {len(FEATURE_COLUMNS)} values."}), 400
    try:
        user_vector = tuple(float(value) for value in raw_vector)
    except (TypeError, ValueError):
        return jsonify({"error": "Every userVector value must be numeric."}), 400
    if not all(math.isfinite(value) for value in user_vector):
        return jsonify({"error": "Preference values must be finite numbers."}), 400
    if not all(0.0 <= value <= 1.0 for value in user_vector):
        return jsonify({"error": "Every preference value must be between 0 and 1."}), 400

    # recommend() computes and sorts the complete catalog before slicing this top ten.
    result = recommend(_DATASET, user_vector, top_n=10)

    def serialize(item):
        return {
            "rank": item.rank,
            "songId": item.song_id,
            "title": item.title,
            "artist": item.artist,
            "features": item.features,
            "dotProduct": item.dot_product,
            "songNorm": item.song_norm,
            "userNorm": item.user_norm,
            "cosineSimilarity": item.cosine_similarity,
            "angleDegrees": item.angle_degrees,
            "projection": item.projection,
            "projectionAlignmentScore": item.projection_alignment_score,
            "explanation": explain_feature_differences(item.features, result.user_vector, FEATURE_COLUMNS),
        }

    return jsonify({
        "featureOrder": FEATURE_COLUMNS,
        "userVector": result.user_vector,
        "songCount": _DATASET.song_count,
        "featureDimensions": _DATASET.feature_count,
        "featureMatrixShape": f"{_DATASET.song_count} × {_DATASET.feature_count}",
        "songsCompared": len(result.full_ranking),
        "recommendationsDisplayed": len(result.playlist),
        "recommendations": [serialize(item) for item in result.playlist],
        "similarityDistribution": similarity_distribution(result.full_ranking),
        "vectorProjection2D": feature_plane_projection(_DATASET, result.user_vector),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=False)
