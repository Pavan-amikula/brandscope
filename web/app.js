"use strict";
const $ = (s) => document.querySelector(s);
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const fmt = (n) =>
  Number(n).toLocaleString("en-GB", { maximumFractionDigits: 0 });
const money = (n) =>
  new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(n);
const pct = (n) => `${(100 * n).toFixed(1)}%`;
const shortMoney = (n) =>
  Math.abs(n) >= 1e6
    ? `£${(n / 1e6).toFixed(2)}m`
    : Math.abs(n) >= 1e3
      ? `£${(n / 1e3).toFixed(1)}k`
      : money(n);
const colors = ["#722e46", "#b18080", "#4d7566", "#ae985f", "#959b99"];
const state = {
  data: null,
  view: "overview",
  market: "All markets",
  window: "full",
  api: false,
  events: [],
  totals: { events: 0, amount_pence: 0, synthetic_events: 0 },
  timer: null,
  simulator: null,
  plans: [],
  plan: {
    title: "Win back valuable shoppers",
    audience: 2000,
    baseline: 5,
    lift: 3,
    aov: 45,
    margin: 45,
    discount: 5,
    cost: 600,
  },
};
const titles = {
  overview: [
    "Find the next growth opportunity.",
    "From retail signals to a sharper marketing decision.",
  ],
  shoppers: [
    "Know the shopper behind the sale.",
    "Understand who returns, what they buy, and where to focus.",
  ],
  campaign: [
    "Give every marketing pound a job.",
    "Build a commercial hypothesis. Make the economics explicit.",
  ],
  live: [
    "See activation as it happens.",
    "A working event pipeline, with a clear boundary between evidence and simulation.",
  ],
  evidence: [
    "Make the evidence easy to trust.",
    "Trace every number back to the data, the method, and its limits.",
  ],
};
const labels = {
  overview: "Growth overview",
  shoppers: "Shopper intelligence",
  campaign: "Campaign studio",
  live: "Activation monitor",
  evidence: "Evidence & methods",
};
function selected() {
  return state.data.markets[state.market][state.window];
}
function toast(text) {
  $("#toast").textContent = text;
  $("#toast").classList.add("show");
  setTimeout(() => $("#toast").classList.remove("show"), 3500);
}
function metric(label, value, note, symbol = "↗") {
  return `<div class="metric"><div class="label">${label}<span>${symbol}</span></div><div class="value">${value}</div><small>${note}</small></div>`;
}
function chart(data) {
  if (!data.length)
    return '<div class="empty">No purchases in this market and window.</div>';
  const w = 660,
    h = 210,
    left = 52,
    right = 15,
    top = 15,
    bottom = 30,
    max = Math.max(...data.map((d) => d.revenue), 1) * 1.15;
  const x = (i) =>
      left + (i * (w - left - right)) / Math.max(data.length - 1, 1),
    y = (v) => h - bottom - (v / max) * (h - top - bottom);
  const points = data.map((d, i) => `${x(i)},${y(d.revenue)}`).join(" ");
  return `<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Monthly gross merchandise sales in GBP. Last month is a partial month."><defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#722e46" stop-opacity=".13"/><stop offset="100%" stop-color="#722e46" stop-opacity="0"/></linearGradient></defs>${[0, 0.25, 0.5, 0.75, 1].map((f) => `<line class="gridline" x1="${left}" x2="${w - right}" y1="${y(max * f)}" y2="${y(max * f)}"/><text x="0" y="${y(max * f) + 4}">${shortMoney(max * f)}</text>`).join("")}<polygon points="${left},${h - bottom} ${points} ${x(data.length - 1)},${h - bottom}" fill="url(#area)"/><polyline class="line" points="${points}"/>${data.map((d, i) => `<circle cx="${x(i)}" cy="${y(d.revenue)}" r="3" fill="#722e46"><title>${d.month}: ${money(d.revenue)} · ${fmt(d.orders)} orders</title></circle>${data.length < 8 || i % 2 === 0 ? `<text x="${x(i)}" y="${h - 5}" text-anchor="middle">${new Date(d.month + "-15").toLocaleDateString("en-GB", { month: "short" })}</text>` : ""}`).join("")}</svg>`;
}
function segmentRows(data) {
  return data.segments
    .slice()
    .sort((a, b) => b.revenue - a.revenue)
    .map(
      (s, i) =>
        `<div class="segment-row"><div class="segment-name"><span class="swatch" style="background:${colors[i % colors.length]}"></span><span>${esc(s.segment)}<small class="muted" style="display:block;margin-left:0;font-size:9px">${fmt(s.customers)} shoppers</small></span></div><div><span class="small muted">${pct(s.share)} of identified shoppers</span><div class="bar"><span style="width:${100 * s.share}%;background:${colors[i % colors.length]}"></span></div></div><div class="right">${shortMoney(s.revenue)}<small class="muted" style="display:block;font-size:8px">historical gross sales</small></div></div>`,
    )
    .join("");
}
function scopeNote() {
  return `<div class="scope-note">${state.window === "90d" ? "Window-specific segmentation and cohorts: earlier purchases outside the window are not included. " : ""}${state.market === "Sweden" ? "Swedish orders belong to a UK retailer; this is a small export sample, not a Swedish market estimate. " : ""}Gift-retailer data includes wholesale buyers. No brand, competitor, margin, media exposure, or consumer survey data is available.</div>`;
}
function overview() {
  const d = selected(),
    k = d.kpis,
    risk = d.segments.find((s) => s.segment === "At risk · high value");
  return `
 <div class="metrics">${metric("Net merchandise sales", shortMoney(k.net_sales), `${money(k.returns)} in recorded returns`)}${metric("Purchase orders", fmt(k.orders), `${fmt(k.units)} units purchased`, "▤")}${metric("Identified shoppers", fmt(k.customers), "Anonymous orders remain in sales totals", "◎")}${metric("Repeat shopper rate", pct(k.repeat_rate), "2+ purchase invoices within selected window", "⟳")}</div>
 <div class="grid-main"><section class="panel"><div class="panel-head"><div><h2>The sales trajectory</h2><p>Gross merchandise sales · monthly · GBP</p></div><span class="tag">OBSERVED</span></div>${chart(d.monthly)}<div class="legend"><span><i></i>Recorded gross sales</span><span>Dec 2011 is partial (through 9 Dec)</span></div><div class="note">Net sales = ${money(k.gross_sales)} gross sales − ${money(k.returns)} recorded returns. Returns are recorded in their transaction month, not attributed to an original order.</div></section>
 <section class="panel opportunity"><div class="eyebrow">OPPORTUNITY / 01</div><h2>${risk ? "Re-engage valuable shoppers." : "Build the next repeat purchase."}</h2><p>${risk ? `${fmt(risk.customers)} shoppers have historical spend in the top quartile and no purchase in over 90 days. Test relevance before increasing incentives.` : "Use recent purchase behavior to test a relevant follow-up. Small samples need careful interpretation."}</p><div class="stat">${risk ? shortMoney(risk.revenue) : shortMoney(k.aov)}<small>${risk ? "historical gross sales in the at-risk segment · not recoverable revenue" : "average purchase order · includes wholesale orders"}</small></div><button class="button light" data-go="campaign">Build a test brief <span>↗</span></button></section></div>
 <div class="grid-main"><section class="panel"><div class="panel-head"><div><h2>The shopper portfolio</h2><p>RFM rules translated into marketing audiences</p></div><button class="text-button" data-go="shoppers">Explore shoppers ↗</button></div>${segmentRows(d)}</section><section class="panel"><div class="panel-head"><div><h2>Where demand comes from</h2><p>Revenue within this retailer, not market share</p></div><span class="tag">GROSS SALES</span></div>${d.countries
   .slice(0, 5)
   .map(
     (c, i) =>
       `<div style="margin-bottom:20px"><div style="display:flex;justify-content:space-between;font-size:11px"><span>${esc(c.country)}</span><span>${shortMoney(c.revenue)}</span></div><div class="bar" style="height:7px"><span style="width:${(100 * c.revenue) / Math.max(k.gross_sales, 1)}%;background:${i ? "#b18080" : "#722e46"}"></span></div></div>`,
   )
   .join(
     "",
   )}<div class="note">Select Sweden or Nordics above to inspect the actual export orders. Currency remains GBP; no inferred SEK conversion.</div></section></div>
 <div class="decision-strip"><span class="number">01</span><div><h3>Recommendation: protect contribution before scaling reach.</h3><p>Translate shopper signals into a controlled test, with discount cannibalization and sample size included.</p></div><button class="text-button" data-go="campaign">Open campaign studio ↗</button></div>${scopeNote()}`;
}
function shoppers() {
  const d = selected(),
    k = d.kpis;
  return `<div class="metrics">${metric("Identified sales", shortMoney(k.identified_sales), "Positive purchases with customer IDs")}${metric("Average order value", money(k.aov), "Gross sales / distinct purchase invoices", "▤")}${metric("Shopper segments", fmt(d.segments.length), "Mutually exclusive, transparent rules", "◎")}${metric("Observed repeat rate", pct(k.repeat_rate), "Descriptive, not campaign response", "⟳")}</div>
 <section class="panel"><div class="panel-head"><div><h2>Segment → insight → action</h2><p>Recency measured at ${state.data.meta.reference}. High value = top 25% of gross shopper spend.</p></div><span class="tag wine">RFM / RULE BASED</span></div><div class="table-wrap"><table><thead><tr><th>SHOPPER GROUP</th><th>SHOPPERS</th><th>MEDIAN RECENCY</th><th>GROSS SPEND</th><th>MARKETING HYPOTHESIS</th></tr></thead><tbody>${d.segments.map((s) => `<tr><td>${esc(s.segment)}</td><td>${fmt(s.customers)}</td><td>${fmt(s.recency)} days</td><td>${money(s.revenue)}</td><td>${{ Champions: "Protect loyalty with early access", "At risk · high value": "Test a relevant reactivation message", "Loyal shoppers": "Test cross-sell with basket evidence", "New shoppers": "Test an onboarding follow-up", "Reactivation pool": "Test low-cost relevance before discounts" }[s.segment]}</td></tr>`).join("")}</tbody></table></div></section>
 <div class="two-col"><section class="panel"><div class="panel-head"><div><h2>Do shoppers come back?</h2><p>Calendar-month cohort retention · unique purchasing shoppers</p></div><span class="tag">OBSERVED</span></div><div class="table-wrap"><table class="heatmap"><thead><tr><th>COHORT / N</th>${[0, 1, 2, 3, 4, 5, 6].map((i) => `<th>M${i}</th>`).join("")}</tr></thead><tbody>${d.cohorts.map((c) => `<tr><td>${esc(c.month)}<small>n = ${fmt(c.size)}</small></td>${c.retention.map((v) => (v === null ? '<td class="muted">—</td>' : `<td style="background:rgba(114,46,70,${0.04 + v * 0.75});color:${v > 0.55 ? "#fff" : "#722e46"}">${Math.round(v * 100)}%</td>`)).join("")}</tr>`).join("")}</tbody></table></div><div class="note">M0 = acquisition month in the selected window. Blank cells are unobserved. Final observed month is incomplete; small cohorts are unstable.</div></section>
 <section class="panel"><div class="panel-head"><div><h2>Test a useful product pairing</h2><p>Basket associations among the top 35 products by order frequency</p></div><span class="tag">HYPOTHESIS</span></div>${
   d.rules
     .slice(0, 3)
     .map(
       (r) =>
         `<div class="source-item"><b style="font-size:10px">${esc(r.a)}<span class="muted"> → </span>${esc(r.b)}</b><div class="mini-metrics"><div><b>${r.lift.toFixed(1)}×</b><span>association lift</span></div><div><b>${pct(r.confidence)}</b><span>P(B | A)</span></div><div><b>${fmt(r.baskets)}</b><span>joint baskets</span></div></div></div>`,
     )
     .join("") ||
   "<p>No product pairs meet the minimum of five joint baskets.</p>"
 }<div class="note">Association lift = P(A ∩ B) / [P(A)P(B)]. This is co-purchase evidence, not incremental sales or causal lift. Wholesale orders can inflate pairings.</div></section></div>
 <section class="panel"><div class="panel-head"><div><h2>Product opportunity list</h2><p>Merchandise codes only · positive purchases</p></div><input class="search" id="product-search" placeholder="Find a product…" aria-label="Search products"></div><div class="table-wrap"><table><thead><tr><th>PRODUCT</th><th>CODE</th><th>GROSS SALES</th><th>UNITS</th><th>ORDERS</th></tr></thead><tbody id="product-rows">${productRows(d.products)}</tbody></table></div></section>${scopeNote()}`;
}
function productRows(rows) {
  return (
    rows
      .map(
        (p) =>
          `<tr><td>${esc(p.name)}</td><td>${esc(p.code)}</td><td>${money(p.revenue)}</td><td>${fmt(p.units)}</td><td>${fmt(p.orders)}</td></tr>`,
      )
      .join("") || '<tr><td colspan="5">No matching products.</td></tr>'
  );
}
function economics(p) {
  const N = +p.audience,
    b = +p.baseline / 100,
    l = +p.lift / 100,
    a = +p.aov,
    m = +p.margin / 100,
    d = +p.discount / 100,
    c = +p.cost;
  if (
    ![N, b, l, a, m, d, c].every(Number.isFinite) ||
    N < 0 ||
    b < 0 ||
    l < 0 ||
    b + l > 1 ||
    a <= 0 ||
    m < 0 ||
    m > 1 ||
    d < 0 ||
    d >= 1 ||
    c < 0
  )
    throw Error(
      "Use valid positive inputs; baseline + lift must be at most 100%.",
    );
  const contribution = N * a * (l * m - (b + l) * d) - c,
    pooled = (b + b + l) / 2;
  const sample = l
    ? Math.ceil(
        (1.959964 * Math.sqrt(2 * pooled * (1 - pooled)) +
          0.841621 * Math.sqrt(b * (1 - b) + (b + l) * (1 - b - l))) **
          2 /
          l ** 2,
      )
    : null;
  const denominator = N * a * (m - d),
    breakeven = denominator > 0 ? (c + N * a * b * d) / denominator : null;
  return {
    contribution,
    incremental: N * l,
    revenue: N * l * a,
    sample,
    breakeven,
    feasible: sample !== null && sample * 2 <= N,
    roi: c ? contribution / c : null,
  };
}
function campaign() {
  const p = state.plan;
  return `<div class="callout">PLANNING SANDBOX · Inputs below are explicit assumptions, not estimates from this dataset. GBP units throughout. No campaign has been launched or measured.</div><div class="two-col"><section class="panel"><div class="panel-head"><div><h2>The commercial hypothesis</h2><p>Change an assumption to recalculate the decision.</p></div><span class="tag wine">WHAT IF</span></div><form id="plan-form"><div class="form-grid"><label class="field full">Campaign name<input id="plan-title" value="${esc(p.title)}" maxlength="120" required></label>${[
    ["audience", "Eligible audience", 1, 10000000, 1],
    ["aov", "Order value (£)", 0.01, 100000, 0.01],
    ["baseline", "Baseline conversion (%)", 0, 99, 0.1],
    ["lift", "Incremental conversion (pp)", 0, 50, 0.1],
    ["margin", "Contribution margin before discount (%)", 0, 100, 1],
    ["discount", "Discount on all treatment orders (%)", 0, 99, 1],
    ["cost", "Campaign cost (£)", 0, 1000000, 1],
  ]
    .map(
      ([id, label, min, max, step]) =>
        `<label class="field">${label}<input id="plan-${id}" type="number" min="${min}" max="${max}" step="${step}" value="${p[id]}" required></label>`,
    )
    .join(
      "",
    )}</div></form><div class="scope-note">Margin includes variable product and fulfilment costs. Campaign cost is additional. Order value is before discounts. Incremental conversion uses percentage points, not relative % uplift.</div><div class="live-controls"><button id="save-plan" class="button">Save scenario ↗</button><button id="download-plan" class="button secondary">Download brief</button></div><div id="saved-plans"></div></section>
 <section class="panel"><div class="panel-head"><div><h2>Contribution, not just revenue</h2><p>Campaign vs. no-campaign counterfactual under your assumptions</p></div><span class="tag">MODELLED</span></div><div id="plan-results"></div><div class="brief"><h3>TEST DESIGN</h3><p>Randomize eligible, consented shoppers 50:50 into treatment and a no-message control. Use a fixed 30-day outcome window. Primary outcome: incremental contribution per eligible shopper. Conversion is a secondary outcome.</p><h3>DECISION RULE</h3><p>Pre-register the analysis. Scale only if the contribution estimate is positive with uncertainty supporting the decision, and unsubscribe and return-rate guardrails pass. The conversion sample estimate below does not power the monetary primary outcome.</p><h3>MESSAGE DIRECTION / ENGLISH + SWEDISH DRAFT</h3><p>“A thoughtful follow-up, based on what you liked.”<br>“En omtänksam uppföljning, baserad på det du gillade.”</p><p class="muted">Concept copy only. Validate language, relevance, consent and local market fit with a Swedish-speaking reviewer.</p></div></section></div>`;
}
function updatePlan() {
  try {
    const p = state.plan,
      r = economics(p);
    $("#plan-results").innerHTML =
      `<div class="results"><div class="mini-label">MODELLED INCREMENTAL CONTRIBUTION</div><div class="result-big ${r.contribution >= 0 ? "positive" : "negative"}">${money(r.contribution)}</div><p>${r.contribution >= 0 ? "Positive under these assumptions. Validate before scaling." : "Negative under these assumptions. Redesign the offer or cost structure."}</p><div class="result-line"><span>Incremental orders</span><b>${fmt(r.incremental)}</b></div><div class="result-line"><span>Incremental gross revenue before discounts</span><b>${money(r.revenue)}</b></div><div class="result-line"><span>Net contribution / campaign cost</span><b>${r.roi === null ? "Not defined (zero cost)" : pct(r.roi)}</b></div><div class="result-line"><span>Break-even conversion gain</span><b>${r.breakeven === null ? "Not attainable with this margin" : `${(r.breakeven * 100).toFixed(2)} pp`}</b></div><div class="result-line"><span>Conversion sample / arm (approx.)</span><b>${r.sample === null ? "No finite sample (zero lift)" : fmt(r.sample)}</b></div></div><div class="callout">${r.feasible ? "Audience passes the approximate conversion sample check." : "Audience is too small for the planned conversion effect, or effect is zero."} 80% power, two-sided α = 0.05, independent Bernoulli outcomes. Estimate excludes clustering, multiplicity, noncompliance, and profit variance.</div><div class="note">Δ contribution = N × AOV × [lift × margin − (baseline + lift) × discount] − campaign cost. Discounts on baseline purchases reduce contribution too. Audience is the proposed total rollout population; pilot test requires twice the sample per arm.</div>`;
  } catch (e) {
    $("#plan-results").innerHTML = `<div class="error">${esc(e.message)}</div>`;
  }
}
function savedPlans() {
  const el = $("#saved-plans");
  if (!el) return;
  el.innerHTML = `<div class="note">${state.plans.length} saved scenario${state.plans.length === 1 ? "" : "s"} · ${state.api ? "SQLite on this computer" : "this browser only"}</div>${state.plans
    .slice(0, 4)
    .map(
      (p) =>
        `<div class="result-line"><span>${esc(p.title)}</span><span class="muted small">${esc((p.timestamp || "").slice(0, 10))}</span></div>`,
    )
    .join("")}`;
}
function live() {
  return `<div class="metrics" id="live-metrics"></div><section class="panel"><div class="live-header"><div><h2><span class="status-dot"></span>Activation event stream</h2><p>Refreshes every 2 seconds · separate from historical UCI data</p></div><span class="tag wine">${state.api ? "SQLITE API" : "BROWSER DEMO STORE"}</span></div><div class="callout">${state.api ? "Real HTTP ingestion with durable SQLite persistence and event-ID deduplication. Generated demonstration events are marked synthetic." : "Static preview: generated events persist in this browser only. Run python server.py for the real HTTP ingestion API and SQLite persistence."} This is not a connection to P&G, live retailer sales, or an advertising platform.</div><div class="live-controls"><button class="button" id="add-event">Send one demo event ↗</button><button class="button secondary" id="toggle-stream">${state.simulator ? "Pause demo stream" : "Start demo stream"}</button><label class="field" style="min-width:140px">Demo market<select id="event-market"><option>Sweden</option><option>Norway</option><option>Denmark</option><option>Finland</option><option>United Kingdom</option></select></label><span class="counter" id="event-message" role="status"></span></div><div class="table-wrap"><table><thead><tr><th>RECEIVED (UTC)</th><th>EVENT ID</th><th>MARKET</th><th>CHANNEL</th><th>AMOUNT (GBP)</th><th>PROVENANCE</th></tr></thead><tbody id="event-rows"></tbody></table></div><div class="note">Newest 30 events shown. Totals cover all persisted events. Duplicate event IDs are ignored. All demo amounts are GBP even when the market is Sweden. Monitor totals do not change historical analytics.</div></section><div class="two-col"><section class="panel"><h2>Connect a real event source locally</h2><p>POST /api/events · Content-Type: application/json</p><pre style="white-space:pre-wrap;font-size:10px;background:#f2efe7;padding:17px;border-radius:4px">{
  "event_id": "order-unique-0001",
  "market": "Sweden",
  "channel": "CRM",
  "amount_pence": 4500,
  "synthetic": false
}</pre><div class="note">Local demo server binds to 127.0.0.1. For shared use, add authentication, ingestion signatures, consent governance, rate limiting, and operational monitoring first.</div></section><section class="panel brief"><h2>What a brand manager learns</h2><h3>BEFORE THE TEST</h3><p>Define the audience, control group, exposure and purchase attribution window. Keep the budget and success criteria in the decision brief.</p><h3>DURING THE TEST</h3><p>Monitor event freshness and duplicate handling. These order events alone cannot establish conversion: a trustworthy denominator requires eligible and assigned shoppers.</p><h3>AFTER THE TEST</h3><p>Join randomized assignment and outcome data, measure incremental contribution, report uncertainty and guardrails. No fabricated campaign outcome is displayed here.</p></section></div>`;
}
function renderEvents() {
  if (state.view !== "live") return;
  const t = state.totals;
  $("#live-metrics").innerHTML =
    metric("Ingested events", fmt(t.events), "All persisted events", "◉") +
    metric(
      "Recorded order value",
      money(t.amount_pence / 100),
      "Demonstration feed · not campaign lift",
      "▤",
    ) +
    metric(
      "Synthetic events",
      fmt(t.synthetic_events),
      "Explicit provenance flag",
      "◎",
    ) +
    metric(
      "Refresh interval",
      "2 sec",
      state.api
        ? "HTTP API → SQLite → browser"
        : "Static preview → browser storage",
      "⟳",
    );
  $("#event-rows").innerHTML =
    state.events
      .map(
        (e) =>
          `<tr><td>${esc(e.timestamp.replace("T", " ").slice(0, 19))}</td><td><code>${esc(e.event_id.slice(0, 22))}</code></td><td>${esc(e.market)}</td><td>${esc(e.channel)}</td><td>${money(e.amount_pence / 100)}</td><td><span class="pill">${e.synthetic ? "SYNTHETIC" : "EXTERNAL"}</span></td></tr>`,
      )
      .join("") ||
    '<tr><td colspan="6" class="empty">No events yet. Send a demo event to exercise the pipeline.</td></tr>';
}
async function refreshEvents() {
  try {
    if (state.api) {
      const res = await fetch("api/events");
      if (!res.ok) throw Error("API unavailable");
      const payload = await res.json();
      state.events = payload.events;
      state.totals = payload.totals;
    } else {
      const all = JSON.parse(localStorage.getItem("brandscope-events") || "[]");
      state.events = all.slice(-30).reverse();
      state.totals = {
        events: all.length,
        amount_pence: all.reduce((s, e) => s + e.amount_pence, 0),
        synthetic_events: all.filter((e) => e.synthetic).length,
      };
    }
    renderEvents();
  } catch (e) {
    if (state.view === "live")
      $("#event-message").textContent = `Could not refresh: ${e.message}`;
  }
}
async function sendEvent() {
  const market = $("#event-market")?.value || "Sweden";
  const event = {
    event_id: "demo-" + crypto.randomUUID(),
    market,
    channel: ["CRM", "Retail media", "Paid social", "Organic"][
      Math.floor(Math.random() * 4)
    ],
    amount_pence: 1500 + Math.floor(Math.random() * 8500),
    synthetic: true,
  };
  try {
    if (state.api) {
      const res = await fetch("api/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(event),
      });
      if (!res.ok) throw Error((await res.json()).error);
    } else {
      const all = JSON.parse(localStorage.getItem("brandscope-events") || "[]");
      all.push({ ...event, timestamp: new Date().toISOString() });
      localStorage.setItem("brandscope-events", JSON.stringify(all));
    }
    await refreshEvents();
    if (state.view === "live")
      $("#event-message").textContent = "Demo event stored successfully.";
  } catch (e) {
    toast("Event not saved: " + e.message);
  }
}
function evidence() {
  const q = state.data.quality;
  return `<div class="metrics">${metric("Source rows", fmt(q.raw_rows), "Full workbook, not a cherry-picked sample", "▤")}${metric("Retained merchandise rows", fmt(q.retained_rows), "Sales and recorded returns retained", "✓")}${metric("Duplicates removed", fmt(q.duplicates_removed), "Exact duplicates across source columns", "⟳")}${metric("Audit reconciliation", q.reconciliation_passed ? "Passed" : "Failed", "Raw = duplicates + exclusions + retained", "✓")}</div><div class="two-col"><section class="panel"><div class="panel-head"><div><h2>From source to decision</h2><p>A reproducible pipeline with explicit data boundaries</p></div><span class="tag green">AUDITABLE</span></div><div class="steps">${[
    [
      "01",
      "Download & fingerprint",
      "UCI Online Retail ZIP; SHA-256 recorded in docs/results.json. Source spans 1 Dec 2010–9 Dec 2011.",
    ],
    [
      "02",
      "Clean without hiding returns",
      `${fmt(q.non_merchandise_or_invalid_removed)} non-merchandise or invalid rows excluded after exact deduplication. Positive prices, nonzero quantities, nonmissing descriptions, five-digit stock codes with an optional letter.`,
    ],
    [
      "03",
      "Keep missing-ID sales visible",
      `${fmt(q.missing_customer_rows)} retained rows lack a customer ID. Sales include them; shopper-level metrics and cohorts exclude them.`,
    ],
    [
      "04",
      "Separate facts from assumptions",
      "Sales, RFM and cohorts are historical. Margin, media budget, conversion and discount are planning assumptions. Events generated by the demo are synthetic.",
    ],
    [
      "05",
      "Evaluate before claiming value",
      "Temporal repurchase ranking backtests use past features only. Campaign incrementality requires a randomized field test.",
    ],
  ]
    .map(
      ([n, t, d]) =>
        `<div class="step"><span class="muted small">${n}</span><div><b>${t}</b><p>${d}</p></div></div>`,
    )
    .join(
      "",
    )}</div><div class="note" style="overflow-wrap:anywhere">Source ZIP SHA-256: ${esc(q.sha256)}</div></section><section class="panel"><div class="panel-head"><div><h2>Research & design references</h2><p>Original implementation; methods and inspiration are attributed</p></div></div><div class="source-list"><div class="source-item"><a href="https://archive.ics.uci.edu/dataset/352/online%2Bretail" target="_blank" rel="noopener">UCI Online Retail · Chen (2015) ↗</a><p>CC BY 4.0. Real transaction data; historical gifts and wholesale purchases, not P&G data.</p></div><div class="source-item"><a href="https://doi.org/10.1057/dbm.2012.17" target="_blank" rel="noopener">Chen, Sain & Guo · RFM segmentation (2012) ↗</a><p>Research motivates customer-centric analysis. This project uses transparent rules rather than reproducing the paper’s clustering model.</p></div><div class="source-item"><a href="https://dl.acm.org/doi/10.1145/3487553.3524707" target="_blank" rel="noopener">Wan et al. · Fast RFM, ACM WWW (2022) ↗</a><p>Article abstract reviewed in the ACM side panel. It studies efficient RFM pattern mining; this project uses simple auditable rules and does not claim to reproduce that algorithm.</p></div><div class="source-item"><a href="https://exp-platform.com/practical-guide/" target="_blank" rel="noopener">Kohavi, Henne & Sommerfield · ACM KDD (2007) ↗</a><p>Controlled experimentation informs the holdout test brief, power check and causal boundaries. No full-paper redistribution.</p></div><div class="source-item"><a href="https://learn.microsoft.com/en-us/power-bi/create-reports/sample-retail-analysis" target="_blank" rel="noopener">Microsoft · Retail Analysis interface reference ↗</a><p>Executive KPI hierarchy and drill-down workflow inspired the information structure. Interface and source code are original.</p></div><div class="source-item"><a href="https://github.com/akmalariq/ecommerce-data-analysis" target="_blank" rel="noopener">Comparable public RFM project ↗</a><p>Reviewed for reproducible analytics structure. BrandScope adds campaign contribution economics, decision briefs and live ingestion.</p></div></div></section></div>
 <section class="panel"><div class="panel-head"><div><h2>Does RFM ranking identify likely repeat purchasers?</h2><p>Three historical 30-day holdouts · top 20% ranking · all markets · full pre-cutoff history</p></div><span class="tag wine">OUT-OF-TIME CHECK</span></div><div class="table-wrap"><table><thead><tr><th>FEATURE CUTOFF</th><th>ELIGIBLE</th><th>TOP 20% / N</th><th>OVERALL REPURCHASE</th><th>RFM PRECISION</th><th>SPEND-ONLY PRECISION</th><th>RFM / OVERALL</th></tr></thead><tbody>${state.data.evaluation.map((r) => `<tr><td>${r.cutoff}</td><td>${fmt(r.eligible)}</td><td>${fmt(r.targeted)}</td><td>${pct(r.overall_repurchase_rate)}</td><td>${pct(r.rfm_precision)}</td><td>${pct(r.monetary_precision)}</td><td>${r.ranking_lift.toFixed(2)}×</td></tr>`).join("")}</tbody></table></div><div class="note">Score = mean(percentile frequency, percentile monetary, 1 − percentile recency), ranked descending, ID for ties. Overall rate is an expected random-targeting baseline. These overlapping-population historical checks are descriptive ranking diagnostics, not independent experiments, calibrated probabilities, or causal campaign lift. No tuned model or statistical significance claim.</div></section><div class="callout">ROLE ALIGNMENT · Shopper insight → RFM and cohort analysis. Analytical capability → reproducible audit and temporal evaluation. Marketing strategy → audience, message and experiment brief. Profitable growth → contribution and break-even economics. Communication → English brief and Swedish draft. Leadership → project decisions and a 10-week action plan. Eligibility, language proficiency and real team leadership must be evidenced separately.</div>`;
}
function navigate(view) {
  if (!titles[view]) view = "overview";
  state.view = view;
  history.replaceState(null, "", "#" + view);
  document.querySelectorAll("nav button").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
    if (b.dataset.view === view) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
  $("#crumb").textContent = labels[view];
  $("#page-title").textContent = titles[view][0];
  $("#page-subtitle").textContent = titles[view][1];
  $("#content").innerHTML = { overview, shoppers, campaign, live, evidence }[
    view
  ]();
  bindView();
}
function bindView() {
  document.querySelectorAll("[data-go]").forEach(
    (b) =>
      (b.onclick = () => {
        navigate(b.dataset.go);
        window.scrollTo({ top: 0, behavior: "smooth" });
      }),
  );
  if (state.view === "shoppers")
    $("#product-search").oninput = (e) => {
      $("#product-rows").innerHTML = productRows(
        selected().products.filter((p) =>
          p.name.toLowerCase().includes(e.target.value.toLowerCase()),
        ),
      );
    };
  if (state.view === "campaign") {
    updatePlan();
    savedPlans();
    $("#plan-form").oninput = () => {
      for (const id of [
        "audience",
        "baseline",
        "lift",
        "aov",
        "margin",
        "discount",
        "cost",
      ])
        state.plan[id] = Number($("#plan-" + id).value);
      state.plan.title = $("#plan-title").value;
      updatePlan();
    };
    $("#save-plan").onclick = savePlan;
    $("#download-plan").onclick = downloadBrief;
  }
  if (state.view === "live") {
    renderEvents();
    $("#add-event").onclick = sendEvent;
    $("#toggle-stream").onclick = () => {
      if (state.simulator) {
        clearInterval(state.simulator);
        state.simulator = null;
      } else {
        sendEvent();
        state.simulator = setInterval(sendEvent, 3000);
      }
      $("#toggle-stream").textContent = state.simulator
        ? "Pause demo stream"
        : "Start demo stream";
    };
  }
}
async function savePlan() {
  if (!$("#plan-form").reportValidity()) return;
  try {
    economics(state.plan);
    const obj = {
      ...state.plan,
      timestamp: new Date().toISOString(),
      market: state.market,
      window: state.window,
      assumptions: true,
    };
    if (state.api) {
      const res = await fetch("api/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(obj),
      });
      if (!res.ok) throw Error("API rejected scenario");
    }
    state.plans.unshift(obj);
    if (!state.api)
      localStorage.setItem("brandscope-plans", JSON.stringify(state.plans));
    savedPlans();
    toast("Scenario saved with assumptions attached.");
  } catch (e) {
    toast(e.message);
  }
}
function downloadBrief() {
  try {
    const p = state.plan,
      r = economics(p),
      d = selected();
    const text = `# BrandScope — Decision brief\n\n## Business question\nHow can shopper insights guide profitable growth?\n\nMarket: ${state.market}. Analysis window: ${state.window}. Source: UCI Online Retail, 2010–2011; GBP. Historical gift retailer with wholesale buyers, not P&G data or Swedish FMCG market data.\n\n## Observed evidence\n- Net merchandise sales: ${money(d.kpis.net_sales)}\n- Identified shoppers: ${fmt(d.kpis.customers)}\n- Repeat shopper rate: ${pct(d.kpis.repeat_rate)}\n\n## Proposed campaign: ${p.title}\nAll inputs below are assumptions. No campaign was run.\n- Eligible rollout audience: ${p.audience}\n- Baseline conversion: ${p.baseline}%\n- Assumed incremental conversion: ${p.lift} percentage points\n- Order value: GBP ${p.aov}; margin: ${p.margin}%; discount on all treatment purchases: ${p.discount}%\n- Additional campaign cost: GBP ${p.cost}\n- Modelled incremental contribution: ${money(r.contribution)}\n- Approximate conversion sample per arm: ${r.sample ?? "undefined"}; enough audience: ${r.feasible}\n\n## Experiment and decision\nRandomize eligible consented shoppers 50:50 into treatment and no-message control. Fixed 30-day outcome window. Primary outcome: contribution per eligible shopper. Secondary: purchase conversion. Power monetary outcome from pilot variance before launch; the sample calculator powers conversion only. Guardrails: returns, opt-outs, complaints. Scale only with positive contribution supported by uncertainty and acceptable guardrails.\n\n## Communication concept\nEN: A thoughtful follow-up, based on what you liked.\nSV draft: En omtänksam uppföljning, baserad på det du gillade.\nSwedish copy requires local review.\n\n## Limitations\nNo observed margins, channel exposure, campaign response, market share or brand awareness. RFM ranking diagnostics are not causal lift. Synthetic event feed is isolated from the historical data.\n\n## Sources\n- Chen (2015), UCI Online Retail, CC BY 4.0: https://doi.org/10.24432/C5BW33\n- Chen, Sain & Guo (2012): https://doi.org/10.1057/dbm.2012.17\n- Kohavi et al., KDD 2007: https://exp-platform.com/practical-guide/\n`;
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/markdown" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "brandscope-decision-brief.md";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast("Decision brief downloaded.");
  } catch (e) {
    toast("Brief unavailable: " + e.message);
  }
}
async function init() {
  try {
    const res = await fetch("data.json");
    if (!res.ok) throw Error("Could not load data.json");
    state.data = await res.json();
    if (["localhost", "127.0.0.1"].includes(location.hostname)) {
      try {
        const health = await fetch("api/health");
        state.api = health.ok && (await health.json()).status === "ok";
      } catch {}
    }
    $("#connection").textContent = state.api
      ? "Local API connected"
      : "Interactive static preview";
    $("#date-label").textContent =
      `${state.data.meta.start} → ${state.data.meta.end}`;
    if (state.api) {
      try {
        const plans = await (await fetch("api/plans")).json();
        state.plans = plans.map((p) => ({
          ...JSON.parse(p.payload),
          id: p.id,
          timestamp: p.timestamp,
        }));
      } catch {}
    } else
      state.plans = JSON.parse(
        localStorage.getItem("brandscope-plans") || "[]",
      );
    document.querySelectorAll("nav button").forEach(
      (b) =>
        (b.onclick = () => {
          navigate(b.dataset.view);
          window.scrollTo({ top: 0 });
        }),
    );
    for (const id of ["market", "window"])
      $("#" + id).onchange = (e) => {
        state[id] = e.target.value;
        navigate(state.view);
      };
    $(".brand").onclick = (e) => {
      e.preventDefault();
      navigate("overview");
      window.scrollTo({ top: 0 });
    };
    $("#export").onclick = downloadBrief;
    await refreshEvents();
    navigate(location.hash.slice(1) || "overview");
    state.timer = setInterval(refreshEvents, 2000);
    window.addEventListener("beforeunload", () => {
      clearInterval(state.timer);
      clearInterval(state.simulator);
    });
  } catch (e) {
    $("#content").innerHTML =
      `<div class="error">${esc(e.message)}. Serve this folder over HTTP using python server.py.</div>`;
  }
}
init();
