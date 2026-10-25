/* UI for genuine portable ML inference, recommendation ranking and evidence NLP. */
const intelligence = {
  models: {},
  profile: null,
  seeds: [],
  experimentSynthetic: false,
  capacity: 0.2,
};
const featureLabels = {
  recency_days: "Days since last purchase",
  orders: "All-history purchase orders",
  gross_spend: "Gross spend (£)",
  tenure_days: "Days since first purchase",
  orders_30d: "Orders in last 30 days",
  spend_30d: "Spend in last 30 days (£)",
  unique_products: "Unique purchased products",
  average_order_value: "Average order value (£)",
};
const intelligenceRequirements = {
  prediction: ["propensity", "benchmark"],
  recommendations: ["recommender", "recommendation-benchmark"],
  assistant: ["knowledge"],
  experiment: [],
};
const intelligenceRender = {
  prediction: predictionStudio,
  recommendations: recommendationStudio,
  experiment: experimentStudio,
  assistant: assistantStudio,
};
function modelLoading() {
  return '<section class="panel loading" role="status">Loading the fitted model and its benchmark…</section>';
}
async function loadIntelligence(name) {
  if (!intelligence.models[name]) {
    const res = await fetch("models/" + name + ".json", { cache: "no-store" });
    if (!res.ok) throw Error("Could not load model artifact: " + name);
    intelligence.models[name] = await res.json();
  }
  return intelligence.models[name];
}
function benchmarkRows(rows) {
  return rows
    .map(
      (r) =>
        `<tr><td>${esc(r.model)}</td><td>${r.average_precision.toFixed(4)}</td><td>${r.roc_auc.toFixed(4)}</td><td>${r.model === "Training prevalence" ? "— (all tied)" : pct(r.precision_top20)}</td><td>${r.brier == null ? "—" : r.brier.toFixed(4)}</td></tr>`,
    )
    .join("");
}
function predictionStudio() {
  const a = intelligence.models.propensity,
    b = intelligence.models.benchmark;
  if (!a || !b) return modelLoading();
  if (!intelligence.profile) intelligence.profile = { ...a.example };
  const selected = b.test.find((r) => r.model.endsWith("October calibration"));
  const rfm = b.test.find((r) => r.model === "RFM rank");
  return `<div class="scope-note ml-scope"><b>GLOBAL HISTORICAL MODEL</b> · All markets · Training: Mar–Aug 2011 · Selection: Sep · Calibration: Oct · Final report: Nov. No current retailer feed or P&G data.</div>
  <div class="metrics">${metric("November average precision", selected.average_precision.toFixed(3), `${rfm.average_precision.toFixed(3)} for RFM; higher is better`, "⌘")}${metric("Top-20% purchase precision", pct(selected.precision_top20), `${pct(rfm.precision_top20)} with RFM on the same holdout`, "◎")}${metric("Eligible holdout shoppers", fmt(selected.n), "One final month; customers can recur in training", "▤")}${metric("ROC-AUC", selected.roc_auc.toFixed(3), "Ranking discrimination; not accuracy or causal lift", "↗")}</div>
  <div class="two-col"><section class="panel"><div class="panel-head"><div><h2>Score a shopper profile</h2><p>Actual inference from the exported ${esc(a.selected)}; edit behavior and recalculate.</p></div><span class="tag wine">FITTED MODEL</span></div><form id="ml-profile"><div class="form-grid">${a.features.map((f) => `<label class="field">${featureLabels[f]}<input type="number" id="ml-${f}" value="${intelligence.profile[f]}" min="0" step="${["gross_spend", "spend_30d", "average_order_value"].includes(f) ? ".01" : "1"}" required></label>`).join("")}</div><div class="live-controls"><button class="button" type="submit">Score profile ↗</button><button class="button secondary" type="button" id="ml-reset">Reset example</button></div></form><div class="note">Input is a scenario profile, not a published individual customer record. All history must precede the scoring cutoff. A high score predicts likely purchase, not that an offer will change behavior. No prospect identifiers or contact details are stored.</div></section>
  <section class="panel"><div class="panel-head"><div><h2>Purchase propensity and its drivers</h2><p>Target: at least one purchase in the subsequent 30 days</p></div><span class="tag">PREDICTED</span></div><div id="ml-score"></div></section></div>
  <section class="panel"><div class="panel-head"><div><h2>Same holdout. Different methods.</h2><p>Model selected by September average precision, not November results. No final-month tuning.</p></div><span class="tag green">NOVEMBER 2011</span></div><div class="table-wrap"><table><thead><tr><th>METHOD</th><th>AVG PRECISION ↑</th><th>ROC-AUC ↑</th><th>PRECISION / TOP 20% ↑</th><th>BRIER ↓</th></tr></thead><tbody>${benchmarkRows(b.test)}</tbody></table></div><div class="callout">Mixed result: October calibration did not improve November Brier score (0.1870 vs 0.1860 raw forest). Logistic regression slightly exceeds the forest on final-month average precision, although the forest won the earlier selection month. We retain the preselected model and show the alternatives.</div><div class="note">Paired bootstrap AP difference vs RFM: ${b.paired_bootstrap.estimate.toFixed(3)}; 95% percentile interval [${b.paired_bootstrap.lower.toFixed(3)}, ${b.paired_bootstrap.upper.toFixed(3)}], 500 shopper resamples. Conditional on one fixed model and one seasonal holdout; not proof of generalization or campaign impact.</div></section>
  <div class="two-col"><section class="panel"><div class="panel-head"><div><h2>Capacity planning with a probability model</h2><p>Historical holdout only · expected purchasers are not incremental conversions.</p></div></div><label class="field">Fraction of November shoppers to prioritize<select id="ml-capacity">${b.capacity.map((r) => `<option value="${r.fraction}" ${r.fraction === intelligence.capacity ? "selected" : ""}>${pct(r.fraction)}</option>`).join("")}</select></label><div id="capacity-result" class="results"></div><div class="note">This prioritizes likely purchasers. It cannot recommend who should receive an incentive. Promotion lift, consent and contact costs still require an experiment.</div></section>
  <section class="panel"><h2>Reliability and feature shift</h2><p>October-based calibration vs November observed outcomes</p><div class="table-wrap"><table><thead><tr><th>PREDICTED BIN</th><th>N</th><th>MEAN PREDICTION</th><th>OBSERVED</th></tr></thead><tbody>${b.reliability.map((r) => `<tr><td>${Math.round(r.lower * 100)}–${Math.round((r.lower + 0.1) * 100)}%</td><td>${fmt(r.n)}</td><td>${pct(r.predicted)}</td><td>${pct(r.observed)}</td></tr>`).join("")}</tbody></table></div><div class="note">Largest October→November population stability indices: ${b.drift
    .slice()
    .sort((a, c) => c.psi - a.psi)
    .slice(0, 3)
    .map((r) => `${esc(featureLabels[r.feature])}: ${r.psi.toFixed(3)}`)
    .join(
      "; ",
    )}. Coarse descriptive drift diagnostic, not an independently validated production alarm.</div></section></div>
  <section class="panel"><h2>Global feature inspection</h2><p>Single fixed-seed permutation on final holdout; average-precision drop when each input is shuffled.</p><div class="importance-grid">${b.importance.map((r) => `<div class="result-line"><span>${esc(featureLabels[r.feature])}</span><b>${r.average_precision_drop.toFixed(4)}</b></div>`).join("")}</div><div class="note">Correlated features can substitute for each other. Importance is predictive association, not a causal effect or a recommendation to manipulate that input. <a href="https://github.com/Pavan-amikula/brandscope/blob/main/docs/MODEL_CARD.md" target="_blank" rel="noopener">Read the model card ↗</a></div></section>`;
}
function scoreProfile() {
  const a = intelligence.models.propensity;
  try {
    for (const f of a.features)
      intelligence.profile[f] = Number($("#ml-" + f).value);
    const r = BrandML.predict(a, intelligence.profile);
    const max = Math.max(
      ...r.explanation.map((e) => Math.abs(e.contribution)),
      0.01,
    );
    $("#ml-score").innerHTML =
      `<div class="results"><div class="mini-label">MODELLED 30-DAY PURCHASE PROBABILITY</div><div class="result-big">${pct(r.probability)}</div><p>Uncalibrated model output: ${pct(r.raw_probability)}. This historical model is not validated for current Swedish FMCG shoppers.</p></div>${r.warnings.length ? `<div class="callout">Extrapolation warning: ${r.warnings.map(esc).join("; ")}. The model can calculate a number outside its training range; that does not establish reliability.</div>` : ""}<div class="row-title"><h2>Raw model path contributions</h2></div>${r.explanation
        .slice(0, 5)
        .map(
          (e) =>
            `<div class="driver-row"><span>${esc(featureLabels[e.feature])}</span><span class="driver-track"><i style="width:${(Math.abs(e.contribution) / max) * 100}%;background:${e.contribution >= 0 ? "#3f6556" : "#722e46"}"></i></span><b>${e.contribution >= 0 ? "+" : ""}${(e.contribution * 100).toFixed(1)} pp</b></div>`,
        )
        .join(
          "",
        )}<div class="note">Forest tree-path probability contributions before sigmoid calibration; not SHAP values, calibrated probability changes, or causal effects. Relative to each tree's root prediction. Profile relationships can be internally inconsistent even when numeric range checks pass.</div>`;
  } catch (e) {
    $("#ml-score").innerHTML = `<div class="error">${esc(e.message)}</div>`;
  }
}
function capacityResult() {
  const r = intelligence.models.benchmark.capacity.find(
    (r) => r.fraction === intelligence.capacity,
  );
  $("#capacity-result").innerHTML =
    `<div class="result-line"><span>Prioritized shoppers</span><b>${fmt(r.n)}</b></div><div class="result-line"><span>Sum of predicted purchases</span><b>${r.expected_purchasers.toFixed(1)}</b></div><div class="result-line"><span>Observed future purchasers</span><b>${fmt(r.observed_purchasers)}</b></div><div class="result-line"><span>Observed purchase precision</span><b>${pct(r.observed_precision)}</b></div>`;
}
function recommendationStudio() {
  const a = intelligence.models.recommender,
    b = intelligence.models["recommendation-benchmark"];
  if (!a || !b) return modelLoading();
  if (!intelligence.seeds.length) intelligence.seeds = [a.items[0].code];
  const s = b.test.find((r) => r.method === "svd"),
    p = b.test.find((r) => r.method === "popularity");
  return `<div class="scope-note ml-scope"><b>LEARNED PRODUCT FACTORS</b> · ${a.rank}-factor TruncatedSVD · Top ${a.items.length} pre-November products · No shopper IDs in the public artifact.</div><div class="metrics">${metric("November hit-rate@5", pct(s.hit_rate_at5), `${pct(p.hit_rate_at5)} popularity baseline`, "⊞")}${metric("Mean recall@5", pct(s.recall_at5), "Low recall remains visible; no sales-lift claim", "◎")}${metric("Eligible returning shoppers", fmt(s.eligible), "Must buy a novel product in the holdout", "▤")}${metric("Recommended catalog coverage", pct(s.catalog_coverage), `${pct(p.catalog_coverage)} for popularity`, "↗")}</div>
  <div class="two-col"><section class="panel"><div class="panel-head"><div><h2>Build a product discovery context</h2><p>Select one or two purchased products to calculate related recommendations.</p></div><span class="tag wine">ACTUAL INFERENCE</span></div><label class="field">First purchased product<select id="rec-seed1">${a.items.map((i) => `<option value="${esc(i.code)}" ${i.code === intelligence.seeds[0] ? "selected" : ""}>${esc(i.name)} · ${esc(i.code)}</option>`).join("")}</select></label><label class="field" style="margin-top:14px">Additional purchased product (optional)<select id="rec-seed2"><option value="">None</option>${a.items.map((i) => `<option value="${esc(i.code)}" ${i.code === intelligence.seeds[1] ? "selected" : ""}>${esc(i.name)} · ${esc(i.code)}</option>`).join("")}</select></label><div class="live-controls"><button id="recommend-products" class="button">Find relevant products ↗</button></div><div class="callout">The model learns co-purchase structure; it does not infer consumer motivation, availability, safety or product suitability. Review a recommendation before putting it in creative.</div><div class="note">No-history cold starts should use the displayed popularity fallback. Unknown product codes are rejected by the API. Selected seed products are excluded from both lists.</div></section>
  <section class="panel"><div class="panel-head"><div><h2>Personalized factors vs broad popularity</h2><p>Same candidate catalog, different ranking methods</p></div><span class="tag">COMPARE</span></div><div id="recommendation-results"></div></section></div>
  <section class="panel"><h2>Recommendation benchmark</h2><p>September selects rank/method. November is the final report; no recommendation outcomes were used in fitting its item factors.</p><div class="table-wrap"><table><thead><tr><th>METHOD</th><th>HIT-RATE@5</th><th>RECALL@5</th><th>PRECISION@5</th><th>MRR@5</th><th>CATALOG COVERAGE</th></tr></thead><tbody>${b.test.map((r) => `<tr><td>${r.method === "svd" ? "TruncatedSVD / 32 factors" : "Popularity baseline"}</td><td>${pct(r.hit_rate_at5)}</td><td>${pct(r.recall_at5)}</td><td>${pct(r.precision_at5)}</td><td>${r.mrr_at5.toFixed(4)}</td><td>${pct(r.catalog_coverage)}</td></tr>`).join("")}</tbody></table></div><div class="note">Eligible population: known shoppers with at least one new product purchase in the next 30 days. Previously bought products are excluded. Future products outside the fitted top-500 catalog count as misses. Only ${pct(s.target_catalog_coverage)} of novel target products are in the catalog. Browser inference uses the selected seeds; evaluation uses full weighted customer histories. That input-context difference limits transfer of benchmark metrics to this demo.</div></section>`;
}
function updateRecommendations() {
  const a = intelligence.models.recommender;
  intelligence.seeds = [$("#rec-seed1").value, $("#rec-seed2").value].filter(
    Boolean,
  );
  try {
    $("#recommendation-results").innerHTML = ["svd", "popularity"]
      .map(
        (method) =>
          `<div class="rec-list"><div class="mini-label">${method === "svd" ? "LEARNED FACTORS" : "POPULARITY FALLBACK"}</div>${BrandML.recommend(
            a,
            intelligence.seeds,
            method,
          )
            .map(
              (p, i) =>
                `<div class="rec-item"><span class="rec-rank">${i + 1}</span><div><b>${esc(p.name)}</b><small>${esc(p.code)} · ${fmt(p.orders)} historical purchase invoices</small></div></div>`,
            )
            .join("")}</div>`,
      )
      .join("");
  } catch (e) {
    $("#recommendation-results").innerHTML =
      `<div class="error">${esc(e.message)}</div>`;
  }
}
function experimentStudio() {
  return `<div class="scope-note ml-scope"><b>FIXED-HORIZON EXPERIMENT ANALYSIS</b> · One row per randomized eligible participant · Include nonconverters · GBP contribution after variable costs, incentives and campaign costs.</div><div class="two-col"><section class="panel"><div class="panel-head"><div><h2>Bring outcomes, not just assumptions</h2><p>CSV columns: participant_id, arm, converted, contribution</p></div><span class="tag wine">50:50 DESIGN</span></div><div class="live-controls"><button class="button secondary" id="load-experiment-demo">Load synthetic example</button><button class="button secondary" type="button" id="choose-experiment-file">Choose CSV</button><input id="experiment-file" type="file" accept=".csv,text/csv" class="visually-hidden"></div><label class="field">Paste or edit CSV (max 20,000 rows / 2 MB)<textarea id="experiment-csv" spellcheck="false" placeholder="participant_id,arm,converted,contribution&#10;participant-1,control,0,0&#10;participant-2,treatment,1,17.9" style="min-height:240px;font-family:monospace;font-size:10px"></textarea></label><div class="live-controls"><button class="button" id="analyse-experiment">Analyse outcomes ↗</button><span class="counter" id="experiment-provenance">No data loaded</span></div><div class="note">${state.api ? "This local mode sends the CSV records to the loopback Python API." : "Public preview calculates in this browser; uploaded CSV contents are not sent to a server."} Records are not saved to localStorage. This tool cannot verify randomization or consent from CSV alone.</div></section><section class="panel"><div class="panel-head"><div><h2>Contribution is the primary outcome</h2><p>Mean treatment − mean control, per assigned participant</p></div><span class="tag">ESTIMATED</span></div><div id="experiment-results"><div class="empty">Load the synthetic example or provide a randomized test CSV.</div></div></section></div><section class="panel brief"><h2>What makes an experiment result credible?</h2><div class="three-col"><div><h3>ASSIGNMENT</h3><p>Use original randomized assignment, one participant per row, and the predeclared allocation. A sample-ratio mismatch flag below p = 0.01 calls for investigation.</p></div><div><h3>MEASUREMENT</h3><p>Use complete, fixed outcome windows and include nonconverters. Contribution should include refunds, costs and incentives. Repeated checking can invalidate a fixed-horizon reading.</p></div><div><h3>UNCERTAINTY</h3><p>Intervals use a large-sample independent-participant approximation. Heavy tails, cluster assignment and multiple comparisons need a different analysis. Guardrails are not supplied by this CSV.</p></div></div></section>`;
}
async function analyseExperimentUI() {
  try {
    const text = $("#experiment-csv").value;
    const rows = BrandML.parseCSV(text);
    $("#experiment-results").innerHTML =
      '<div class="loading" role="status">Analysing participant outcomes…</div>';
    let result;
    if (state.api) {
      const res = await fetch("api/experiment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows }),
      });
      result = await res.json();
      if (!res.ok) throw Error(result.error);
    } else result = BrandML.analyse(rows);
    if (
      state.view !== "experiment" ||
      !$("#experiment-csv") ||
      $("#experiment-csv").value !== text
    )
      return;
    const r = result.contribution,
      c = result.conversion;
    $("#experiment-results").innerHTML =
      `<span class="tag ${intelligence.experimentSynthetic ? "wine" : ""}">${intelligence.experimentSynthetic ? "SYNTHETIC DEMONSTRATION" : "USER-PROVIDED / PROVENANCE UNVERIFIED"}</span><div class="results"><div class="mini-label">CONTRIBUTION DIFFERENCE / ASSIGNED PARTICIPANT</div><div class="result-big ${r.difference >= 0 ? "positive" : "negative"}">£${r.difference.toFixed(3)}</div><p>Approximate 95% interval: [£${r.lower.toFixed(3)}, £${r.upper.toFixed(3)}]</p><div class="result-line"><span>Control / treatment participants</span><b>${fmt(result.arms.control.n)} / ${fmt(result.arms.treatment.n)}</b></div><div class="result-line"><span>Secondary conversion difference</span><b>${(c.difference * 100).toFixed(2)} pp</b></div><div class="result-line"><span>Conversion interval</span><b>[${(c.lower * 100).toFixed(2)}, ${(c.upper * 100).toFixed(2)}] pp</b></div><div class="result-line"><span>50:50 sample-ratio p-value</span><b>${result.srm_p_value.toFixed(4)}</b></div></div><div class="callout"><b>${esc(result.decision)}</b>${intelligence.experimentSynthetic ? "<br>Synthetic outcome analysis illustrates the workflow; it is not evidence of a campaign being run." : ""}${result.conversion_normal_approximation_warning ? "<br>Rare conversion counts: normal conversion interval may be unreliable." : ""}</div><div class="note">No early-stopping, cluster, multiplicity or heavy-tail correction. A positive interval cannot establish valid implementation, consent or acceptable guardrails.</div>`;
  } catch (e) {
    if ($("#experiment-results"))
      $("#experiment-results").innerHTML =
        `<div class="error">${esc(e.message)}</div>`;
  }
}
function assistantStudio() {
  if (!intelligence.models.knowledge) return modelLoading();
  const a = intelligence.models.knowledge;
  return `<div class="scope-note ml-scope"><b>FITTED RETRIEVAL NLP</b> · ${a.chunks.length} source passages · TF-IDF cosine search · English project evidence · No external language-model calls.</div><section class="panel"><div class="panel-head"><div><h2>Ask about the evidence behind the project</h2><p>Answers are retrieved source passages with links; unsupported queries can be declined.</p></div><span class="tag wine">SOURCE BACKED</span></div><form id="ask-evidence" class="ask-form"><label class="field" style="flex:1">Question<input id="evidence-question" maxlength="1000" minlength="3" placeholder="Does high purchase propensity mean an offer will work?" required></label><button class="button" type="submit">Find evidence ↗</button></form><div class="question-chips">${["How large is the Swedish sample?", "What did the machine learning model achieve?", "Why can discounts reduce profit?", "How do I analyse an experiment?"].map((q) => `<button class="question-chip" data-question="${esc(q)}">${esc(q)}</button>`).join("")}</div><div id="evidence-answer" aria-live="polite"><div class="empty">Choose a question or ask about data, models, campaigns or limitations.</div></div></section><div class="callout">This assistant retrieves passages; it does not generate new explanations, browse the internet, or verify external company claims. Cosine similarity is a retrieval score, not confidence in correctness. Questions stay in this browser; source links open public project documents.</div>`;
}
function askEvidence(question) {
  try {
    const r = BrandML.retrieve(intelligence.models.knowledge, question);
    $("#evidence-answer").innerHTML = r.abstained
      ? '<div class="callout">No sufficiently similar supporting passage was found. Try a project-specific question about the dataset, model, experiment or commercial assumptions.</div>'
      : `<div class="row-title"><h2>Retrieved evidence</h2><span class="tag">NOT GENERATED TEXT</span></div>${r.matches.map((p, i) => `<article class="answer-passage"><div class="panel-head"><h3>${i + 1}. ${esc(p.title)}</h3><span class="tag">Similarity ${p.similarity.toFixed(3)}</span></div><p>${esc(p.text)}</p><a href="${esc(p.source)}" target="_blank" rel="noopener">Inspect supporting source ↗</a></article>`).join("")}`;
  } catch (e) {
    $("#evidence-answer").innerHTML =
      `<div class="error">${esc(e.message)}</div>`;
  }
}
async function bindIntelligenceView(view) {
  try {
    await Promise.all(intelligenceRequirements[view].map(loadIntelligence));
    if (state.view !== view) return;
    $("#content").innerHTML = intelligenceRender[view]();
    if (view === "prediction") {
      scoreProfile();
      capacityResult();
      $("#ml-profile").onsubmit = (e) => {
        e.preventDefault();
        if ($("#ml-profile").reportValidity()) scoreProfile();
      };
      $("#ml-reset").onclick = () => {
        intelligence.profile = { ...intelligence.models.propensity.example };
        bindIntelligenceView(view);
      };
      $("#ml-capacity").onchange = (e) => {
        intelligence.capacity = Number(e.target.value);
        capacityResult();
      };
    }
    if (view === "recommendations") {
      $("#recommend-products").onclick = updateRecommendations;
      updateRecommendations();
    }
    if (view === "experiment") {
      $("#choose-experiment-file").onclick = () => $("#experiment-file").click();
      $("#load-experiment-demo").onclick = async () => {
        try {
          const res = await fetch("models/synthetic-experiment.csv");
          if (!res.ok) throw Error("Demo unavailable");
          const csv = await res.text();
          if (state.view !== "experiment" || !$("#experiment-csv")) return;
          $("#experiment-csv").value = csv;
          intelligence.experimentSynthetic = true;
          $("#experiment-provenance").textContent =
            "SYNTHETIC · 8,000 participants";
          await analyseExperimentUI();
        } catch (e) {
          toast(e.message);
        }
      };
      $("#experiment-csv").oninput = () => {
        intelligence.experimentSynthetic = false;
        $("#experiment-provenance").textContent =
          "Edited data · unverified provenance";
      };
      $("#experiment-file").onchange = async (e) => {
        try {
          const file = e.target.files[0];
          if (!file) return;
          if (file.size > 2000000) throw Error("CSV exceeds 2 MB");
          const csv = await file.text();
          if (state.view !== "experiment" || !$("#experiment-csv")) return;
          $("#experiment-csv").value = csv;
          intelligence.experimentSynthetic = false;
          $("#experiment-provenance").textContent =
            "Uploaded CSV · unverified provenance";
        } catch (e) {
          toast(e.message);
        }
      };
      $("#analyse-experiment").onclick = analyseExperimentUI;
    }
    if (view === "assistant") {
      $("#ask-evidence").onsubmit = (e) => {
        e.preventDefault();
        askEvidence($("#evidence-question").value);
      };
      document.querySelectorAll("[data-question]").forEach(
        (b) =>
          (b.onclick = () => {
            $("#evidence-question").value = b.dataset.question;
            askEvidence(b.dataset.question);
          }),
      );
    }
  } catch (e) {
    if (state.view === view)
      $("#content").innerHTML =
        `<div class="error">${esc(e.message)}. Rebuild the model artifacts using the documented scripts, then reload.</div>`;
  }
}
