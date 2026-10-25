/* Portable model contract. Shared by browser UI and dependency-free Node checks. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.BrandML = factory();
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const sigmoid = (x) => 1 / (1 + Math.exp(-Math.max(-700, Math.min(700, x))));
  function predict(artifact, profile) {
    if (
      Object.keys(profile).sort().join("|") !==
      artifact.features.slice().sort().join("|")
    )
      throw Error("Supply exactly the documented features.");
    const warnings = [];
    const x = artifact.features.map((f) => {
      const v = profile[f];
      if (typeof v !== "number" || !Number.isFinite(v) || v < 0)
        throw Error(f + " must be a finite nonnegative number.");
      if (
        !["gross_spend", "spend_30d", "average_order_value"].includes(f) &&
        !Number.isInteger(v)
      )
        throw Error(f + " must be a whole number.");
      if (v < artifact.ranges[f].min || v > artifact.ranges[f].max)
        warnings.push(f + " outside training range");
      return Math.log1p(v);
    });
    if (
      profile.orders_30d > profile.orders ||
      profile.spend_30d > profile.gross_spend
    )
      throw Error("30-day purchases cannot exceed all-history purchases.");
    if (profile.recency_days > profile.tenure_days)
      throw Error("Recency cannot exceed tenure.");
    if (
      profile.orders < 1 ||
      profile.gross_spend <= 0 ||
      profile.unique_products < 1
    )
      throw Error("The trained population requires prior positive purchases.");
    if (profile.recency_days > 30 && profile.orders_30d > 0)
      throw Error(
        "A purchase over 30 days ago cannot have orders in the trailing 30 days.",
      );
    if ((profile.orders_30d === 0) !== (profile.spend_30d === 0))
      throw Error(
        "Trailing orders and spend must both be zero or both positive.",
      );
    const m = artifact.model;
    let raw;
    let terms = x.map(() => 0);
    if (m.kind === "logistic") {
      terms = x.map((v, i) => ((v - m.mean[i]) / m.scale[i]) * m.coef[i]);
      raw = sigmoid(m.intercept + terms.reduce((a, b) => a + b, 0));
    } else {
      // Match sklearn's float32 tree inputs, including split-boundary cases.
      for (let i = 0; i < x.length; i++) x[i] = Math.fround(x[i]);
      let sum = 0;
      for (const tree of m.trees) {
        let node = 0;
        while (tree.left[node] !== -1) {
          const f = tree.feature[node];
          const child =
            x[f] <= tree.threshold[node] ? tree.left[node] : tree.right[node];
          terms[f] +=
            (tree.probability[child] - tree.probability[node]) / m.trees.length;
          node = child;
        }
        sum += tree.probability[node];
      }
      raw = sum / m.trees.length;
    }
    const clipped = Math.min(1 - 1e-9, Math.max(1e-9, raw));
    const probability = sigmoid(
      artifact.calibrator.intercept +
        artifact.calibrator.coef * Math.log(clipped / (1 - clipped)),
    );
    return {
      probability,
      raw_probability: raw,
      warnings,
      explanation: artifact.features
        .map((feature, i) => ({ feature, contribution: terms[i] }))
        .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)),
      model_version: artifact.version,
    };
  }
  function recommend(artifact, codes, method = artifact.selected, limit = 5) {
    if (!Array.isArray(codes) || codes.length < 1 || codes.length > 20)
      throw Error("Choose 1–20 products.");
    const indexes = new Map(artifact.items.map((p, i) => [p.code, i]));
    if (codes.some((c) => !indexes.has(c)))
      throw Error("Unknown product code.");
    if (!["svd", "popularity"].includes(method))
      throw Error("Unsupported recommendation method.");
    const chosen = new Set(codes.map((c) => indexes.get(c)));
    const query = artifact.vectors[0].map((_, j) =>
      [...chosen].reduce((s, i) => s + artifact.vectors[i][j], 0),
    );
    return artifact.items
      .map((p, i) => ({
        ...p,
        index: i,
        method,
        score:
          method === "svd"
            ? artifact.vectors[i].reduce((s, v, j) => s + v * query[j], 0)
            : p.orders,
      }))
      .filter((p) => !chosen.has(p.index))
      .sort((a, b) => b.score - a.score || a.code.localeCompare(b.code))
      .slice(0, limit);
  }
  function retrieve(artifact, question, limit = 3) {
    if (
      typeof question !== "string" ||
      question.trim().length < 3 ||
      question.length > 1000
    )
      throw Error("Question must contain 3–1000 characters.");
    const counts = {};
    for (const t of question.toLowerCase().match(/[\p{L}\p{N}_]{2,}/gu) || []) {
      if (Object.hasOwn(artifact.vocabulary, t)) {
        const i = artifact.vocabulary[t];
        counts[i] = (counts[i] || 0) + 1;
      }
    }
    const query = {};
    let sum = 0;
    for (const [i, n] of Object.entries(counts)) {
      query[i] = n * artifact.idf[i];
      sum += query[i] ** 2;
    }
    const norm = Math.sqrt(sum);
    if (!norm) return { answer: null, matches: [], abstained: true };
    const matches = artifact.chunks
      .map((c, i) => ({
        ...c,
        similarity:
          artifact.vectors[i].reduce(
            (s, [j, v]) => s + (query[j] || 0) * v,
            0,
          ) / norm,
      }))
      .filter((c) => c.similarity >= artifact.threshold)
      .sort((a, b) => b.similarity - a.similarity || a.id.localeCompare(b.id))
      .slice(0, limit);
    return {
      answer: matches[0]?.text || null,
      matches,
      abstained: matches.length === 0,
    };
  }
  function parseCSV(text) {
    if (typeof text !== "string" || text.length > 2000000)
      throw Error("CSV must be at most 2 MB.");
    const lines = [];
    let row = [];
    let field = "";
    let quoted = false;
    text = text.replace(/^\uFEFF/, "");
    for (let i = 0; i <= text.length; i++) {
      const c = i === text.length ? "\n" : text[i];
      if (c === '"') {
        if (quoted && text[i + 1] === '"') {
          field += '"';
          i++;
        } else quoted = !quoted;
      } else if (c === "," && !quoted) {
        row.push(field);
        field = "";
      } else if ((c === "\n" || c === "\r") && !quoted) {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(field);
        if (row.some((v) => v.trim())) lines.push(row);
        row = [];
        field = "";
      } else field += c;
    }
    if (quoted) throw Error("Unclosed quoted CSV field.");
    const header = lines.shift() || [];
    const required = ["participant_id", "arm", "converted", "contribution"];
    if (!required.every((k) => header.includes(k)))
      throw Error("Required columns: " + required.join(", "));
    if (lines.length > 20000) throw Error("Maximum 20000 participants.");
    const seen = new Set();
    return lines.map((r, i) => {
      const obj = Object.fromEntries(
        header.map((k, j) => [k, (r[j] || "").trim()]),
      );
      if (!obj.participant_id || seen.has(obj.participant_id))
        throw Error(
          "Row " + (i + 2) + ": missing or duplicate participant_id.",
        );
      seen.add(obj.participant_id);
      obj.arm = obj.arm.toLowerCase();
      if (!["control", "treatment"].includes(obj.arm))
        throw Error("Invalid arm in row " + (i + 2));
      if (!["0", "1"].includes(obj.converted))
        throw Error("converted must be 0 or 1.");
      const contribution = Number(obj.contribution);
      if (
        !obj.contribution ||
        !Number.isFinite(contribution) ||
        Math.abs(contribution) > 1e8
      )
        throw Error("Invalid contribution.");
      return {
        participant_id: obj.participant_id,
        arm: obj.arm,
        converted: Number(obj.converted),
        contribution,
      };
    });
  }
  function erfc(x) {
    const t = 1 / (1 + 0.3275911 * x);
    const polynomial =
      ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) *
        t +
        0.254829592) *
      t;
    return polynomial * Math.exp(-x * x);
  }
  function analyse(rows) {
    const arms = {};
    for (const arm of ["control", "treatment"]) {
      const a = rows.filter((r) => r.arm === arm),
        n = a.length;
      if (n < 30) throw Error("At least 30 participants in each arm required.");
      const mean = a.reduce((s, r) => s + r.contribution, 0) / n;
      const conversions = a.reduce((s, r) => s + r.converted, 0);
      arms[arm] = {
        n,
        mean_contribution: mean,
        conversions,
        conversion: conversions / n,
        variance:
          a.reduce((s, r) => s + (r.contribution - mean) ** 2, 0) / (n - 1),
      };
    }
    const c = arms.control,
      t = arms.treatment,
      n = c.n + t.n;
    const chi = ((c.n - n / 2) ** 2 + (t.n - n / 2) ** 2) / (n / 2);
    const srm = erfc(Math.sqrt(chi / 2));
    const diff = t.mean_contribution - c.mean_contribution,
      se = Math.sqrt(t.variance / t.n + c.variance / c.n);
    const conv = t.conversion - c.conversion,
      convSE = Math.sqrt(
        (t.conversion * (1 - t.conversion)) / t.n +
          (c.conversion * (1 - c.conversion)) / c.n,
      );
    const lower = diff - 1.959964 * se,
      upper = diff + 1.959964 * se;
    return {
      n,
      arms,
      srm_p_value: srm,
      contribution: { difference: diff, lower, upper, standard_error: se },
      conversion: {
        difference: conv,
        lower: conv - 1.959964 * convSE,
        upper: conv + 1.959964 * convSE,
      },
      conversion_normal_approximation_warning:
        Math.min(
          c.conversions,
          t.conversions,
          c.n - c.conversions,
          t.n - t.conversions,
        ) < 10,
      decision:
        srm < 0.01
          ? "Investigate assignment imbalance"
          : lower > 0
            ? "Positive contribution evidence; review guardrails"
            : upper < 0
              ? "Evidence of harm; stop and investigate"
              : "Inconclusive contribution; do not claim a win",
    };
  }
  return { predict, recommend, retrieve, parseCSV, analyse };
});
