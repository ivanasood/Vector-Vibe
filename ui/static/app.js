const form = document.querySelector("#preference-form");
const sliders = [...document.querySelectorAll(".preference-slider")];
const vectorCells = [...document.querySelectorAll(".vector-cell b")];
const emptyState = document.querySelector("#empty-state");
const resultsContent = document.querySelector("#results-content");
const loadingState = document.querySelector("#loading-state");
const errorState = document.querySelector("#error-state");
const playlistList = document.querySelector("#playlist-list");
const button = document.querySelector("#generate-button");
const resetButton = document.querySelector("#reset-preferences");
const resultCount = document.querySelector("#result-count");
const analysisPanel = document.querySelector("#song-analysis");
const resultsPanel = document.querySelector("#recommendations");
const resultsStaleNote = document.querySelector("#results-stale-note");
const zeroVectorNote = document.querySelector("#zero-vector-note");
const sectionNav = document.querySelector(".section-nav");
const sectionNavStatus = document.querySelector("#section-nav-status");
const visualizationStack = document.querySelector("#visualizations");
// Keep the primary playlist and analysis before the supplementary charts.
resultsContent.append(playlistList, analysisPanel, visualizationStack);
let lastGeneratedVector = null;
const DEFAULT_PREFERENCE = "0.50";

function currentVector() {
  return sliders.map((slider) => Number(slider.value));
}

function displayValue(value, digits = 2) {
  return Number(value).toFixed(digits);
}

function updatePreferenceDisplays() {
  sliders.forEach((slider, index) => {
    const value = Number(slider.value);
    const pct = value * 100;
    slider.style.background = `linear-gradient(to right, var(--accent) ${pct}%, #424a43 ${pct}%) center / 100% 4px no-repeat`;
    const output = slider.closest(".slider-row").querySelector(".slider-value");
    output.value = displayValue(value);
    output.textContent = displayValue(value);
    slider.setAttribute(
      "aria-valuetext",
      `${displayValue(value)} on a 0 to 1 scale`,
    );
    vectorCells[index].textContent = displayValue(value);
  });
  if (lastGeneratedVector !== null) {
    const current = currentVector();
    resultsStaleNote.hidden = current.every(
      (value, index) => value === lastGeneratedVector[index],
    );
  }
}

function addText(parent, tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

function formatVector(vector) {
  return `[${vector.map((value) => displayValue(value, 3)).join(", ")}]`;
}

const SVG_NS = "http://www.w3.org/2000/svg";

function svgNode(tag, attributes = {}) {
  const element = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([name, value]) =>
    element.setAttribute(name, String(value)),
  );
  return element;
}

function svgLabel(svg, text) {
  const title = svgNode("title");
  title.textContent = text;
  svg.append(title);
}

function renderOverviewHistogram(feature) {
  const width = 260;
  const height = 58;
  const left = 8;
  const right = 8;
  const baseline = 40;
  const maxBarHeight = 23;
  const bins = feature.distribution;
  const counts = bins.map((bin) => Number(bin.count));
  const maxCount = Math.max(1, ...counts);
  const slotWidth = (width - left - right) / bins.length;
  const svg = svgNode("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `${feature.name} value distribution across ${bins.length} equal-width bins from ${displayValue(feature.minimum, 4)} to ${displayValue(feature.maximum, 4)}; total ${counts.reduce((sum, value) => sum + value, 0)} songs`,
  });
  svgLabel(svg, `${feature.name} histogram. Bin counts: ${counts.join(", ")}.`);
  svg.append(
    svgNode("line", {
      x1: left,
      y1: baseline,
      x2: width - right,
      y2: baseline,
      class: "overview-histogram-axis",
    }),
  );
  bins.forEach((bin, index) => {
    const count = Number(bin.count);
    const barWidth = Math.min(18, slotWidth - 6);
    const x = left + index * slotWidth + (slotWidth - barWidth) / 2;
    const barHeight =
      count === 0 ? 0 : Math.max(2, (count / maxCount) * maxBarHeight);
    const y = baseline - barHeight;
    const bar = svgNode("rect", {
      x,
      y,
      width: barWidth,
      height: barHeight,
      rx: 2,
      class: "overview-histogram-bar",
    });
    const lower = Number(bin.lowerBound).toFixed(4);
    const upper = Number(bin.upperBound).toFixed(4);
    const intervalEnd = index === bins.length - 1 ? "]" : ")";
    const title = svgNode("title");
    title.textContent = `${feature.name}: ${count} songs in [${lower}, ${upper}${intervalEnd}`;
    bar.append(title);
    svg.append(bar);
    const label = svgNode("text", {
      x: x + barWidth / 2,
      y: Math.max(10, y - 2),
      "text-anchor": "middle",
      class: "overview-histogram-count",
    });
    label.textContent = String(count);
    svg.append(label);
  });
  return svg;
}

function renderDatasetOverview(payload) {
  document.querySelector("#overview-total-songs").textContent = String(
    payload.totalSongs,
  );
  document.querySelector("#overview-feature-count").textContent = String(
    payload.featureCount,
  );
  document.querySelector("#overview-matrix-dimensions").textContent =
    payload.matrixDimensions;
  const body = document.querySelector("#dataset-feature-stat-rows");
  body.replaceChildren();
  payload.features.forEach((feature) => {
    const row = document.createElement("tr");
    addText(row, "th", "overview-feature-name", feature.name).setAttribute(
      "scope",
      "row",
    );
    addText(row, "td", "overview-numeric", Number(feature.minimum).toFixed(4));
    addText(row, "td", "overview-numeric", Number(feature.maximum).toFixed(4));
    addText(
      row,
      "td",
      "overview-numeric overview-average",
      Number(feature.average).toFixed(4),
    );
    const distribution = document.createElement("td");
    distribution.className = "overview-histogram-cell";
    distribution.append(renderOverviewHistogram(feature));
    row.append(distribution);
    body.append(row);
  });
}

async function loadDatasetOverview() {
  const error = document.querySelector("#overview-error");
  try {
    const response = await fetch("/api/dataset-overview");
    const payload = await response.json();
    if (!response.ok)
      throw new Error(payload.error || "Dataset overview could not be loaded.");
    if (
      payload.totalSongs !== 100 ||
      payload.featureCount !== 7 ||
      payload.features?.length !== 7 ||
      payload.features.reduce(
        (sum, feature) =>
          sum +
          feature.distribution.reduce(
            (binSum, bin) => binSum + Number(bin.count),
            0,
          ),
        0,
      ) !== 700
    ) {
      throw new Error(
        "Dataset overview did not contain the expected statistics for all songs and features.",
      );
    }
    renderDatasetOverview(payload);
  } catch (exception) {
    error.textContent =
      exception.message || "Dataset overview could not be loaded.";
    error.hidden = false;
    const body = document.querySelector("#dataset-feature-stat-rows");
    body.replaceChildren();
    const row = document.createElement("tr");
    const cell = addText(row, "td", "overview-loading", error.textContent);
    cell.colSpan = 5;
    body.append(row);
  }
}

function chartClamp(value) {
  return Math.max(0, Math.min(1, Number(value)));
}

function renderTop10SimilarityChart(items) {
  const container = document.querySelector("#top10-similarity-chart");
  container.replaceChildren();
  const width = 760;
  const left = 230;
  const plotWidth = 430;
  const rowHeight = 24;
  const top = 17;
  const axisHeight = 29;
  const height = top + items.length * rowHeight + axisHeight;
  const svg = svgNode("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": "Top ten songs ordered by cosine similarity",
  });
  svgLabel(
    svg,
    "Top 10 Similarity Chart. Horizontal bars show actual cosine similarity scores from highest to lowest.",
  );

  [0, 0.5, 1].forEach((tick) => {
    const x = left + tick * plotWidth;
    svg.append(
      svgNode("line", {
        x1: x,
        y1: top - 4,
        x2: x,
        y2: top + items.length * rowHeight - 3,
        class: "chart-grid-line",
      }),
    );
    const label = svgNode("text", {
      x,
      y: height - 7,
      "text-anchor": tick === 0 ? "start" : tick === 1 ? "end" : "middle",
      class: "chart-axis-label",
    });
    label.textContent = `${Math.round(tick * 100)}%`;
    svg.append(label);
  });

  items.forEach((item, index) => {
    const y = top + index * rowHeight;
    const score = chartClamp(item.cosineSimilarity);
    const title = svgNode("title");
    title.textContent = `Rank ${item.rank}: ${item.title} — ${(Number(item.cosineSimilarity) * 100).toFixed(2)}% cosine similarity`;
    const songLabel = svgNode("text", {
      x: 0,
      y: y + 12,
      class: `chart-song-label${index === 0 ? " chart-song-label-best" : ""}`,
    });
    songLabel.textContent =
      item.title.length > 31 ? `${item.title.slice(0, 29)}…` : item.title;
    songLabel.append(title);
    svg.append(songLabel);
    svg.append(
      svgNode("rect", {
        x: left,
        y: y + 2,
        width: plotWidth,
        height: 12,
        rx: 4,
        class: "chart-bar-track",
      }),
    );
    svg.append(
      svgNode("rect", {
        x: left,
        y: y + 2,
        width: score * plotWidth,
        height: 12,
        rx: 4,
        class: index === 0 ? "chart-bar-best" : "chart-bar-top10",
      }),
    );
    const percent = svgNode("text", {
      x: left + plotWidth + 12,
      y: y + 12,
      class: `chart-percent${index === 0 ? " chart-percent-best" : ""}`,
    });
    percent.textContent = `${(Number(item.cosineSimilarity) * 100).toFixed(2)}%`;
    svg.append(percent);
  });
  container.append(svg);
}

function renderSimilarityDistribution(items) {
  const container = document.querySelector("#similarity-distribution-chart");
  container.replaceChildren();
  const width = 760;
  const height = 300;
  const left = 49;
  const right = 18;
  const top = 14;
  const bottom = 31;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const rowHeight = plotHeight / items.length;
  const svg = svgNode("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label":
      "Cosine similarity distribution for all 100 songs, sorted by rank; top ten highlighted",
  });
  svgLabel(
    svg,
    "Similarity Distribution for all one hundred songs. Each row is a song sorted by cosine similarity. The first ten are highlighted.",
  );

  [0, 0.5, 1].forEach((tick) => {
    const x = left + tick * plotWidth;
    svg.append(
      svgNode("line", {
        x1: x,
        y1: top,
        x2: x,
        y2: top + plotHeight,
        class: "chart-grid-line",
      }),
    );
    const label = svgNode("text", {
      x,
      y: height - 7,
      "text-anchor": tick === 0 ? "start" : tick === 1 ? "end" : "middle",
      class: "chart-axis-label",
    });
    label.textContent = tick.toFixed(1);
    svg.append(label);
  });
  [1, 10, 50, 100].forEach((rank) => {
    const item = items.find((song) => Number(song.rank) === rank);
    if (!item) return;
    const y = top + (rank - 0.5) * rowHeight;
    const label = svgNode("text", {
      x: left - 8,
      y: y + 3,
      "text-anchor": "end",
      class: "chart-rank-label",
    });
    label.textContent = String(rank);
    svg.append(label);
  });
  items.forEach((item, index) => {
    const score = chartClamp(item.cosineSimilarity);
    const y = top + index * rowHeight + rowHeight * 0.12;
    const bar = svgNode("rect", {
      x: left,
      y,
      width: score * plotWidth,
      height: Math.max(1.2, rowHeight * 0.76),
      rx: 1,
      class:
        Number(item.rank) <= 10
          ? "distribution-bar-top10"
          : "distribution-bar-rest",
    });
    const title = svgNode("title");
    title.textContent = `Rank ${item.rank}: ${item.title} — ${(Number(item.cosineSimilarity) * 100).toFixed(2)}%`;
    bar.append(title);
    svg.append(bar);
  });
  container.append(svg);
}

function renderVectorProjection(data, selectedSong) {
  const container = document.querySelector("#vector-projection-chart");
  container.replaceChildren();
  const width = 560;
  const height = 350;
  const left = 54;
  const right = 20;
  const top = 16;
  const bottom = 48;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const mapX = (value) => left + chartClamp(value) * plotWidth;
  const mapY = (value) => top + (1 - chartClamp(value)) * plotHeight;
  const svg = svgNode("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `${data.label}; x axis ${data.xFeature}; y axis ${data.yFeature}; shows all 100 dataset songs, the selected song, and the user vector`,
  });
  svgLabel(
    svg,
    `${data.label}. Orthogonal coordinate projection showing ${data.xFeature} versus ${data.yFeature}; remaining features are omitted.`,
  );

  [0, 0.25, 0.5, 0.75, 1].forEach((tick) => {
    const x = mapX(tick);
    const y = mapY(tick);
    svg.append(
      svgNode("line", {
        x1: x,
        y1: top,
        x2: x,
        y2: top + plotHeight,
        class: "chart-grid-line",
      }),
    );
    svg.append(
      svgNode("line", {
        x1: left,
        y1: y,
        x2: left + plotWidth,
        y2: y,
        class: "chart-grid-line",
      }),
    );
    const xLabel = svgNode("text", {
      x,
      y: top + plotHeight + 16,
      "text-anchor": "middle",
      class: "chart-axis-label",
    });
    xLabel.textContent = tick.toFixed(2);
    svg.append(xLabel);
    const yLabel = svgNode("text", {
      x: left - 8,
      y: y + 3,
      "text-anchor": "end",
      class: "chart-axis-label",
    });
    yLabel.textContent = tick.toFixed(2);
    svg.append(yLabel);
  });
  svg.append(
    svgNode("line", {
      x1: left,
      y1: top + plotHeight,
      x2: left + plotWidth,
      y2: top + plotHeight,
      class: "chart-axis-line",
    }),
  );
  svg.append(
    svgNode("line", {
      x1: left,
      y1: top,
      x2: left,
      y2: top + plotHeight,
      class: "chart-axis-line",
    }),
  );
  const xTitle = svgNode("text", {
    x: left + plotWidth / 2,
    y: height - 5,
    "text-anchor": "middle",
    class: "chart-axis-title",
  });
  xTitle.textContent = data.xFeature;
  svg.append(xTitle);
  const yTitle = svgNode("text", {
    x: 13,
    y: top + plotHeight / 2,
    "text-anchor": "middle",
    class: "chart-axis-title",
    transform: `rotate(-90 13 ${top + plotHeight / 2})`,
  });
  yTitle.textContent = data.yFeature;
  svg.append(yTitle);

  data.points.forEach((point) => {
    const dot = svgNode("circle", {
      cx: mapX(point.x),
      cy: mapY(point.y),
      r: 3,
      class: "vector-song-point",
    });
    const title = svgNode("title");
    title.textContent = `${point.title}: ${data.xFeature} ${displayValue(point.x)}, ${data.yFeature} ${displayValue(point.y)}`;
    dot.append(title);
    svg.append(dot);
  });
  const selected = data.points.find(
    (point) => Number(point.songId) === Number(selectedSong.songId),
  );
  if (selected) {
    svg.append(
      svgNode("circle", {
        cx: mapX(selected.x),
        cy: mapY(selected.y),
        r: 7,
        class: "vector-selected-ring",
      }),
    );
  }
  const user = data.userPoint;
  const ux = mapX(user.x);
  const uy = mapY(user.y);
  svg.append(
    svgNode("path", {
      d: `M ${ux} ${uy - 7} L ${ux + 7} ${uy} L ${ux} ${uy + 7} L ${ux - 7} ${uy} Z`,
      class: "vector-user-point",
    }),
  );
  container.append(svg);

  const legend = document.createElement("div");
  legend.className = "vector-legend";
  [
    ["All 100 songs", "legend-dot-songs"],
    ["Selected song", "legend-dot-selected"],
    ["User vector", "legend-dot-user"],
  ].forEach(([label, className]) => {
    const item = document.createElement("span");
    const dot = document.createElement("i");
    dot.className = className;
    item.append(dot, document.createTextNode(label));
    legend.append(item);
  });
  container.append(legend);
}

function renderFeatureComparison(card, song, userVector, featureOrder) {
  const chart = document.createElement("div");
  chart.className = "feature-comparison";
  const legend = document.createElement("div");
  legend.className = "comparison-legend";
  addText(legend, "span", "legend-spacer", "FEATURE");
  addText(legend, "span", "legend-user", "USER PREFERENCE");
  addText(legend, "span", "legend-song", "SONG FEATURES");
  chart.append(legend);

  featureOrder.forEach((feature, index) => {
    const userValue = Number(userVector[index]);
    const songValue = Number(song.features[index]);
    const row = document.createElement("div");
    row.className = "comparison-row";
    addText(row, "span", "feature-name", feature);

    const userGroup = document.createElement("div");
    userGroup.className = "bar-group user-group";
    addText(userGroup, "span", "bar-value", displayValue(userValue));
    const userTrack = document.createElement("span");
    userTrack.className = "bar-track";
    const userBar = document.createElement("span");
    userBar.className = "bar-fill user-fill";
    userBar.style.width = `${Math.max(0, Math.min(100, userValue * 100))}%`;
    userTrack.append(userBar);
    userGroup.append(userTrack);

    const songGroup = document.createElement("div");
    songGroup.className = "bar-group song-group";
    addText(songGroup, "span", "bar-value", displayValue(songValue));
    const songTrack = document.createElement("span");
    songTrack.className = "bar-track";
    const songBar = document.createElement("span");
    songBar.className = "bar-fill song-fill";
    songBar.style.width = `${Math.max(0, Math.min(100, songValue * 100))}%`;
    songTrack.append(songBar);
    songGroup.append(songTrack);

    row.append(userGroup, songGroup);
    chart.append(row);
  });
  card.append(chart);
}

function showAnalysis(song, userVector, featureOrder, vectorProjectionData) {
  document.querySelectorAll(".playlist-card").forEach((card) => {
    card.classList.toggle(
      "is-selected",
      card.dataset.songId === String(song.songId),
    );
  });
  document.querySelectorAll(".analysis-button").forEach((control) => {
    const selected = Number(control.dataset.songId) === song.songId;
    control.setAttribute("aria-pressed", String(selected));
    control.textContent = selected
      ? "Analysis selected"
      : "View mathematical analysis";
  });
  document.querySelector("#analysis-title").textContent = song.title;
  document.querySelector("#analysis-rank").textContent =
    `RANK ${String(song.rank).padStart(2, "0")}`;
  const namedFeatures = `[${featureOrder.join(", ")}]`;
  document.querySelector("#analysis-user-definition").textContent =
    `U = ${namedFeatures}`;
  document.querySelector("#analysis-song-definition").textContent =
    `S = ${namedFeatures}`;
  document.querySelector("#analysis-user-vector").textContent =
    formatVector(userVector);
  document.querySelector("#analysis-song-vector").textContent = formatVector(
    song.features,
  );
  const selectedFeatureChart = document.querySelector(
    "#selected-feature-chart",
  );
  selectedFeatureChart.replaceChildren();
  renderFeatureComparison(selectedFeatureChart, song, userVector, featureOrder);
  document.querySelector("#vector-plane-note").textContent =
    `Coordinates use ${vectorProjectionData.xFeature} (x) and ${vectorProjectionData.yFeature} (y); the remaining dimensions (${vectorProjectionData.omittedFeatures.join(", ")}) are omitted from this view.`;
  renderVectorProjection(vectorProjectionData, song);
  document.querySelector("#analysis-dot-value").textContent =
    `= ${displayValue(song.dotProduct, 6)}`;
  document.querySelector("#analysis-norm-song").textContent =
    `‖S‖ = ${displayValue(song.songNorm, 6)}`;
  document.querySelector("#analysis-norm-user").textContent =
    `‖U‖ = ${displayValue(song.userNorm, 6)}`;
  const cosine = Number(song.cosineSimilarity);
  document.querySelector("#analysis-cosine-value").textContent =
    `= ${displayValue(cosine, 6)}`;
  document.querySelector("#analysis-cosine-percent").textContent =
    `Cosine similarity: ${(cosine * 100).toFixed(2)}%`;
  document.querySelector("#analysis-angle-value").textContent =
    song.angleDegrees === null
      ? "Undefined (a zero vector has no direction)"
      : `= ${displayValue(song.angleDegrees, 3)}°`;
  document.querySelector("#analysis-projection").textContent = formatVector(
    song.projection,
  );
  document.querySelector("#analysis-projection-note").textContent =
    Number(song.userNorm) === 0
      ? "U is the zero vector; its projection is undefined mathematically, so the safe result is the zero vector."
      : "Computed from the selected song vector and this generated preference vector.";
  analysisPanel.hidden = false;
  analysisPanel.scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth",
    block: "nearest",
  });
}

function renderPlaylist(items, userVector, featureOrder, vectorProjectionData) {
  playlistList.replaceChildren();
  analysisPanel.hidden = true;
  for (const item of items) {
    const card = document.createElement("article");
    card.className = `playlist-card${item.rank === 1 ? " is-top-match" : ""}`;
    card.dataset.songId = String(item.songId);

    const topLine = document.createElement("div");
    topLine.className = "playlist-topline";
    const rankBadge = document.createElement("span");
    rankBadge.className = "playlist-rank";
    addText(rankBadge, "b", "", String(item.rank).padStart(2, "0"));
    const info = document.createElement("div");
    info.className = "song-info";
    const titleButton = document.createElement("button");
    titleButton.type = "button";
    titleButton.className = "song-title song-title-select";
    titleButton.textContent = item.title;
    titleButton.setAttribute(
      "aria-label",
      `View mathematical analysis for ${item.title}`,
    );
    titleButton.addEventListener("click", () =>
      showAnalysis(item, userVector, featureOrder, vectorProjectionData),
    );
    info.append(titleButton);
    addText(
      info,
      "div",
      "song-subtitle",
      item.artist ||
        (item.rank === 1 ? "TOP MATHEMATICAL MATCH" : `SONG ID ${item.songId}`),
    );
    const score = document.createElement("div");
    score.className = "score-box";
    addText(
      score,
      "span",
      "score-value",
      `${(Number(item.cosineSimilarity) * 100).toFixed(1)}%`,
    );
    addText(score, "span", "score-label", "SIMILARITY");
    topLine.append(rankBadge, info, score);
    card.append(topLine);

    const scoreStrip = document.createElement("div");
    scoreStrip.className = "score-strip";
    if (item.rank === 1)
      addText(scoreStrip, "span", "top-match-label", "BEST MATCH");
    addText(
      scoreStrip,
      "span",
      "alignment-score",
      `Projection / alignment · ${displayValue(item.projectionAlignmentScore, 4)}`,
    );
    const spacer = document.createElement("span");
    spacer.className = "score-strip-spacer";
    scoreStrip.append(spacer);
    const detailButton = document.createElement("button");
    detailButton.type = "button";
    detailButton.className = "analysis-button";
    detailButton.dataset.songId = String(item.songId);
    detailButton.setAttribute("aria-pressed", "false");
    detailButton.textContent = "View mathematical analysis";
    detailButton.addEventListener("click", () =>
      showAnalysis(item, userVector, featureOrder, vectorProjectionData),
    );
    scoreStrip.append(detailButton);
    card.append(scoreStrip);

    addText(card, "p", "recommendation-explanation", item.explanation);
    renderFeatureComparison(card, item, userVector, featureOrder);
    playlistList.append(card);
  }
}

function updateSummary(payload) {
  document.querySelector("#stat-dataset").textContent =
    `${payload.songCount} songs`;
  document.querySelector("#stat-dimensions").textContent = String(
    payload.featureDimensions,
  );
  document.querySelector("#stat-matrix").textContent =
    payload.featureMatrixShape;
  document.querySelector("#stat-compared").textContent = String(
    payload.songsCompared,
  );
  document.querySelector("#stat-displayed").textContent = String(
    payload.recommendationsDisplayed,
  );
}

sliders.forEach((slider) =>
  slider.addEventListener("input", updatePreferenceDisplays),
);
resetButton.addEventListener("click", () => {
  sliders.forEach((slider) => {
    slider.value = DEFAULT_PREFERENCE;
  });
  updatePreferenceDisplays();
  sectionNavStatus.hidden = true;
});

sectionNav.addEventListener("click", (event) => {
  const link = event.target.closest("a");
  if (!link) return;
  const scrollToRecommendations = () =>
    resultsPanel.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
      block: "start",
    });
  if (link.hasAttribute("data-requires-analysis") && analysisPanel.hidden) {
    event.preventDefault();
    sectionNavStatus.textContent =
      "Generate a playlist, then select a song to view its mathematical analysis.";
    sectionNavStatus.hidden = false;
    scrollToRecommendations();
    return;
  }
  if (
    link.hasAttribute("data-requires-visualizations") &&
    resultsContent.hidden
  ) {
    event.preventDefault();
    sectionNavStatus.textContent =
      "Generate a playlist to reveal the data-backed visualizations.";
    sectionNavStatus.hidden = false;
    scrollToRecommendations();
    return;
  }
  sectionNavStatus.hidden = true;
});

updatePreferenceDisplays();
loadDatasetOverview();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const requestStartedAt = performance.now();
  errorState.hidden = true;
  emptyState.hidden = true;
  resultsContent.hidden = true;
  loadingState.hidden = false;
  zeroVectorNote.hidden = true;
  button.disabled = true;
  resultsPanel.setAttribute("aria-busy", "true");
  sectionNavStatus.hidden = true;
  resultCount.textContent = "CALCULATING";

  try {
    const response = await fetch("/api/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userVector: currentVector() }),
    });
    const payload = await response.json();
    const minimumLoadingRemainder =
      180 - (performance.now() - requestStartedAt);
    if (minimumLoadingRemainder > 0) {
      await new Promise((resolve) =>
        setTimeout(resolve, minimumLoadingRemainder),
      );
    }
    if (!response.ok)
      throw new Error(payload.error || "Recommendation request failed.");
    if (
      payload.songCount !== 100 ||
      payload.songsCompared !== 100 ||
      payload.recommendations?.length !== 10 ||
      payload.recommendations.some(
        (item) => typeof item.explanation !== "string" || !item.explanation,
      ) ||
      payload.similarityDistribution?.length !== 100 ||
      payload.vectorProjection2D?.points?.length !== 100
    ) {
      throw new Error(
        "Expected the complete 100-song calculation, its chart data, and exactly ten recommendations.",
      );
    }
    updateSummary(payload);
    renderTop10SimilarityChart(payload.recommendations);
    renderSimilarityDistribution(payload.similarityDistribution);
    renderPlaylist(
      payload.recommendations,
      payload.userVector,
      payload.featureOrder,
      payload.vectorProjection2D,
    );
    lastGeneratedVector = payload.userVector.map(Number);
    updatePreferenceDisplays();
    zeroVectorNote.hidden = !payload.userVector.every(
      (value) => Number(value) === 0,
    );
    resultCount.textContent = "TOP 10 / 100";
    resultsContent.hidden = false;
    requestAnimationFrame(() =>
      resultsPanel.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      }),
    );
  } catch (error) {
    errorState.textContent =
      error.message || "Unable to calculate recommendations. Please try again.";
    errorState.hidden = false;
    emptyState.hidden = true;
    resultCount.textContent = "TRY AGAIN";
  } finally {
    loadingState.hidden = true;
    button.disabled = false;
    resultsPanel.setAttribute("aria-busy", "false");
  }
});
