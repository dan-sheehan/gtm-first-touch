/* Enrichment Chain - Frontend */
(function () {
  const PREFIX = window.APP_PREFIX || "";

  function apiBase() {
    return PREFIX;
  }

  function directApiBase() {
    if (PREFIX && window.location.port === "8000") {
      return "http://localhost:3011";
    }
    return PREFIX;
  }

  const form = document.getElementById("enrich-form");
  const enrichBtn = document.getElementById("enrich-btn");
  const statusEl = document.getElementById("enrich-status");
  const pipelineCard = document.getElementById("pipeline-card");
  const pipelineSteps = document.getElementById("pipeline-steps");
  const resultsCard = document.getElementById("results-card");
  const resultsTitle = document.getElementById("results-title");
  const resultsArea = document.getElementById("results-area");
  const savedList = document.getElementById("saved-list");
  const savedEmpty = document.getElementById("saved-empty");
  const icpSourcePanel = document.getElementById("icp-source-panel");
  const icpSourceMeta = document.getElementById("icp-source-meta");
  const icpAccountSelect = document.getElementById("icp-account-select");

  let providers = [];
  let icpAccounts = [];

  // -----------------------------------------------------------------------
  // Load providers
  // -----------------------------------------------------------------------

  function loadProviders() {
    fetch(apiBase() + "/api/providers")
      .then(r => r.json())
      .then(data => { providers = data.providers || []; })
      .catch(() => {});
  }

  loadProviders();

  // -----------------------------------------------------------------------
  // Load scored accounts from ICP Scorer
  // -----------------------------------------------------------------------

  function loadIcpAccounts() {
    fetch(apiBase() + "/api/icp-accounts")
      .then(r => r.json())
      .then(data => {
        icpAccounts = data.accounts || [];
        if (!icpAccounts.length) {
          icpSourcePanel.style.display = "none";
          return;
        }

        icpSourcePanel.style.display = "block";
        icpAccountSelect.innerHTML = icpAccounts.map(account => {
          const label = `${account.company_name} (${account.grade}, ${account.score})`;
          return `<option value="${account.id}">${esc(label)}</option>`;
        }).join("");

        useIcpAccount(icpAccounts[0], { auto: true });
        icpAccountSelect.addEventListener("change", function () {
          const selected = icpAccounts.find(account => String(account.id) === this.value);
          if (selected) useIcpAccount(selected);
        });
      })
      .catch(() => {});
  }

  function useIcpAccount(account, options) {
    const auto = options && options.auto;
    if (!auto || !form.company.value.trim()) {
      form.company.value = account.company_name || "";
    }
    icpSourceMeta.textContent = `${account.grade} fit / ${account.score} score`;
  }

  loadIcpAccounts();

  // -----------------------------------------------------------------------
  // Load saved enrichments
  // -----------------------------------------------------------------------

  function loadSaved() {
    fetch(apiBase() + "/api/enrichments")
      .then(r => r.json())
      .then(data => {
        if (data.enrichments && data.enrichments.length > 0) {
          savedEmpty.style.display = "none";
          savedList.innerHTML = data.enrichments.map(e => {
            const date = new Date(e.created_at + "Z").toLocaleDateString("en-US", {
              month: "short", day: "numeric", year: "numeric"
            });
            return `<div class="saved-item" data-id="${e.id}">
              <div>
                <div class="saved-item-name">${esc(e.company)}</div>
                <div class="saved-item-meta">${e.steps_completed} steps completed</div>
              </div>
              <div class="saved-item-date">${date}</div>
            </div>`;
          }).join("");

          savedList.querySelectorAll(".saved-item").forEach(el => {
            el.addEventListener("click", () => loadEnrichment(parseInt(el.dataset.id)));
          });
        } else {
          savedEmpty.style.display = "block";
          savedList.innerHTML = "";
        }
      })
      .catch(() => {});
  }

  loadSaved();

  // -----------------------------------------------------------------------
  // Load a saved enrichment
  // -----------------------------------------------------------------------

  function loadEnrichment(id) {
    fetch(apiBase() + "/api/enrichments/" + id)
      .then(r => r.json())
      .then(data => {
        pipelineCard.style.display = "none";
        renderResults(data.company, data.result);
        resultsCard.scrollIntoView({ behavior: "smooth" });
      })
      .catch(() => {});
  }

  // -----------------------------------------------------------------------
  // Run enrichment
  // -----------------------------------------------------------------------

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const company = form.company.value.trim();
    if (!company) return;

    enrichBtn.disabled = true;
    statusEl.textContent = "Starting enrichment...";
    resultsCard.style.display = "none";

    // Show pipeline steps
    pipelineCard.style.display = "block";
    pipelineSteps.innerHTML = providers.map(p =>
      `<div class="step-item" id="step-${esc(p.id)}">
        <div class="step-indicator pending"></div>
        <div class="step-info">
          <div class="step-label">${esc(p.label)}</div>
          <div class="step-desc">${esc(p.description)}</div>
        </div>
        <div class="step-status" id="step-status-${esc(p.id)}">Waiting</div>
      </div>`
    ).join("");

    const base = directApiBase();

    fetch(base + "/api/enrich", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company: company }),
    }).then(response => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullResult = {};

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            finishEnrichment(company, fullResult);
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop();

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const msg = JSON.parse(line.slice(6));

              if (msg.status && msg.step) {
                const stepEl = document.getElementById("step-" + msg.step);
                if (stepEl) {
                  stepEl.querySelector(".step-indicator").className = "step-indicator running";
                  document.getElementById("step-status-" + msg.step).textContent = "Running...";
                }
                statusEl.textContent = msg.status;
              }

              if (msg.step_done) {
                const stepEl = document.getElementById("step-" + msg.step_done);
                if (stepEl) {
                  const hasError = msg.result && msg.result.error;
                  stepEl.querySelector(".step-indicator").className = "step-indicator " + (hasError ? "error" : "done");
                  document.getElementById("step-status-" + msg.step_done).textContent = hasError ? "Error" : "Done";
                }
              }

              if (msg.done) {
                fullResult = msg.result || {};
                finishEnrichment(company, fullResult, msg.id);
                return;
              }
            } catch (_) {}
          }
          read();
        });
      }

      read();
    }).catch(err => {
      enrichBtn.disabled = false;
      statusEl.textContent = "Error: " + err.message;
    });

    function finishEnrichment(company, result, id) {
      enrichBtn.disabled = false;
      statusEl.textContent = id ? "Saved!" : "Done";
      renderResults(company, result);
      if (id) loadSaved();
      setTimeout(() => { statusEl.textContent = ""; }, 3000);
    }
  });

  // -----------------------------------------------------------------------
  // Render results
  // -----------------------------------------------------------------------

  function renderResults(company, result) {
    resultsCard.style.display = "block";
    resultsTitle.textContent = "Enrichment: " + company;

    const sections = [];

    // Web Research
    if (result.web_research) {
      const wr = result.web_research;
      sections.push(`<div class="result-section">
        <h3 class="result-section-title">Web Research</h3>
        ${wr.website_url ? `<div class="result-field"><span class="result-label">Website:</span> ${esc(wr.website_url)}</div>` : ""}
        ${wr.product_description ? `<p>${esc(wr.product_description)}</p>` : ""}
        ${wr.target_market ? `<div class="result-field"><span class="result-label">Target Market:</span> ${esc(wr.target_market)}</div>` : ""}
        ${wr.company_size ? `<div class="result-field"><span class="result-label">Size:</span> ${esc(wr.company_size)}</div>` : ""}
        ${wr.location ? `<div class="result-field"><span class="result-label">Location:</span> ${esc(wr.location)}</div>` : ""}
        ${wr.leadership && wr.leadership.length ? `<div class="result-field"><span class="result-label">Leadership:</span> ${wr.leadership.map(l => esc(l.name + " — " + l.title)).join(", ")}</div>` : ""}
        ${wr.recent_news && wr.recent_news.length ? `<ul class="result-list">${wr.recent_news.map(n => `<li>${esc(n)}</li>`).join("")}</ul>` : ""}
      </div>`);
    }

    // Tech Stack
    if (result.tech_stack) {
      const ts = result.tech_stack;
      const tags = [
        ...(ts.languages || []).map(t => ({ label: t, type: "lang" })),
        ...(ts.frameworks || []).map(t => ({ label: t, type: "fw" })),
        ...(ts.infrastructure || []).map(t => ({ label: t, type: "infra" })),
        ...(ts.data_tools || []).map(t => ({ label: t, type: "data" })),
        ...(ts.sales_tools || []).map(t => ({ label: t, type: "sales" })),
      ];
      sections.push(`<div class="result-section">
        <h3 class="result-section-title">Tech Stack ${ts.confidence ? `<span class="confidence-badge">${esc(ts.confidence)}</span>` : ""}</h3>
        <div class="tag-cloud">${tags.map(t => `<span class="tech-tag tag-${t.type}">${esc(t.label)}</span>`).join("")}</div>
      </div>`);
    }

    // Funding
    if (result.funding_signals) {
      const fs = result.funding_signals;
      sections.push(`<div class="result-section">
        <h3 class="result-section-title">Funding & Growth</h3>
        ${fs.total_raised ? `<div class="result-field"><span class="result-label">Total Raised:</span> ${esc(fs.total_raised)}</div>` : ""}
        ${fs.hiring_signals ? `<div class="result-field"><span class="result-label">Hiring:</span> ${esc(fs.hiring_signals)}</div>` : ""}
        ${fs.funding_rounds && fs.funding_rounds.length ? `<div class="funding-rounds">${fs.funding_rounds.map(r =>
          `<div class="funding-round"><strong>${esc(r.round || "")}</strong> — ${esc(r.amount || "")} ${r.date ? `(${esc(r.date)})` : ""}</div>`
        ).join("")}</div>` : ""}
        ${fs.growth_indicators && fs.growth_indicators.length ? `<ul class="result-list">${fs.growth_indicators.map(g => `<li>${esc(g)}</li>`).join("")}</ul>` : ""}
      </div>`);
    }

    // Competitive Landscape
    if (result.competitive_landscape) {
      const cl = result.competitive_landscape;
      sections.push(`<div class="result-section">
        <h3 class="result-section-title">Competitive Landscape</h3>
        ${cl.market_position ? `<div class="result-field"><span class="result-label">Position:</span> ${esc(cl.market_position)}</div>` : ""}
        ${cl.differentiation ? `<div class="result-field"><span class="result-label">Differentiation:</span> ${esc(cl.differentiation)}</div>` : ""}
        ${cl.direct_competitors && cl.direct_competitors.length ? `<div class="competitor-list"><strong>Direct:</strong> ${cl.direct_competitors.map(c => esc(c.name)).join(", ")}</div>` : ""}
        ${cl.adjacent_competitors && cl.adjacent_competitors.length ? `<div class="competitor-list"><strong>Adjacent:</strong> ${cl.adjacent_competitors.map(c => esc(c.name)).join(", ")}</div>` : ""}
      </div>`);
    }

    // Fallback for raw/error results
    if (sections.length === 0) {
      sections.push(`<div class="result-section">
        <pre class="raw-output">${esc(JSON.stringify(result, null, 2))}</pre>
      </div>`);
    }

    resultsArea.innerHTML = sections.join("");
  }

  // -----------------------------------------------------------------------
  // Utilities
  // -----------------------------------------------------------------------

  function esc(str) {
    if (!str) return "";
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
})();
