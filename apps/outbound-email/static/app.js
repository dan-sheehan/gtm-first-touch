/* Outbound Email Helper - Frontend */
(function () {
  const PREFIX = window.APP_PREFIX || "";

  function apiBase() {
    return PREFIX;
  }

  function directApiBase() {
    if (PREFIX && window.location.port === "8000") {
      return "http://localhost:3008";
    }
    return PREFIX;
  }

  // -----------------------------------------------------------------------
  // Elements
  // -----------------------------------------------------------------------

  const form = document.getElementById("generate-form");
  const generateBtn = document.getElementById("generate-btn");
  const statusEl = document.getElementById("generate-status");
  const outputCard = document.getElementById("output-card");
  const outputTitle = document.getElementById("output-title");
  const outputArea = document.getElementById("output-area");
  const resultsSection = document.getElementById("results-section");
  const resultsTitle = document.getElementById("results-title");
  const signalSummary = document.getElementById("signal-summary");
  const emailCards = document.getElementById("email-cards");
  const exportBtn = document.getElementById("export-btn");
  const deleteBtn = document.getElementById("delete-btn");
  const savedList = document.getElementById("saved-list");
  const savedEmpty = document.getElementById("saved-empty");
  const enrichmentSourcePanel = document.getElementById("enrichment-source-panel");
  const enrichmentSourceMeta = document.getElementById("enrichment-source-meta");
  const enrichmentAccountSelect = document.getElementById("enrichment-account-select");

  let currentSeqId = null;
  let currentResult = null;
  let enrichedAccounts = [];
  let selectedEnrichment = null;

  // -----------------------------------------------------------------------
  // Load enriched accounts from Enrichment
  // -----------------------------------------------------------------------

  function loadEnrichedAccounts() {
    fetch(apiBase() + "/api/enriched-accounts")
      .then(r => r.json())
      .then(data => {
        enrichedAccounts = data.accounts || [];
        if (!enrichedAccounts.length) {
          enrichmentSourcePanel.style.display = "none";
          return;
        }

        enrichmentSourcePanel.style.display = "block";
        enrichmentAccountSelect.innerHTML = enrichedAccounts.map(account => {
          const label = account.company_name || account.company_url;
          return `<option value="${account.id}">${escapeHtml(label)}</option>`;
        }).join("");

        useEnrichedAccount(enrichedAccounts[0], { auto: true });
        enrichmentAccountSelect.addEventListener("change", function () {
          const selected = enrichedAccounts.find(account => String(account.id) === this.value);
          if (selected) useEnrichedAccount(selected);
        });
      })
      .catch(() => {});
  }

  function setFieldValue(field, value, auto) {
    if (!field || !value) return;
    if (!auto || !field.value.trim()) {
      field.value = value;
    }
  }

  function useEnrichedAccount(account, options) {
    const auto = options && options.auto;
    selectedEnrichment = account;
    setFieldValue(form.company_url, account.company_url || account.company_name, auto);
    setFieldValue(form.prospect_name, account.prospect_name, auto);
    setFieldValue(form.prospect_title, account.prospect_title, auto);
    setFieldValue(form.department, account.department, auto);

    const details = [];
    if (account.steps_completed) details.push(account.steps_completed + " enrichment steps");
    if (account.prospect_title) details.push(account.prospect_title);
    enrichmentSourceMeta.textContent = details.join(" / ") || "Ready for outbound";
  }

  loadEnrichedAccounts();

  // -----------------------------------------------------------------------
  // Load saved sequences
  // -----------------------------------------------------------------------

  function loadSaved() {
    fetch(apiBase() + "/api/sequences")
      .then(r => r.json())
      .then(data => {
        if (data.sequences && data.sequences.length > 0) {
          savedEmpty.style.display = "none";
          savedList.innerHTML = data.sequences.map(s => {
            const date = new Date(s.created_at + "Z").toLocaleDateString("en-US", {
              month: "short", day: "numeric", year: "numeric"
            });
            const label = s.company_name || s.company_url;
            const meta = [s.prospect_name, s.prospect_title, s.department].filter(Boolean).join(" / ") || "General outreach";
            return `<div class="saved-item" data-id="${s.id}">
              <div>
                <div class="saved-item-name">${escapeHtml(label)}</div>
                <div class="saved-item-meta">${escapeHtml(meta)}</div>
              </div>
              <div class="saved-item-date">${date}</div>
            </div>`;
          }).join("");

          savedList.querySelectorAll(".saved-item").forEach(el => {
            el.addEventListener("click", () => loadSequence(parseInt(el.dataset.id)));
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
  // Load a saved sequence into results view
  // -----------------------------------------------------------------------

  function loadSequence(id) {
    fetch(apiBase() + "/api/sequences/" + id)
      .then(r => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then(data => {
        currentSeqId = data.id;
        currentResult = {
          company_name: data.company_name,
          account_signal_summary: data.account_signal_summary || data.ai_usage_summary || "",
          emails: data.emails,
        };
        outputCard.style.display = "none";
        renderResults(currentResult);
        resultsSection.scrollIntoView({ behavior: "smooth" });
      })
      .catch(() => {});
  }

  // -----------------------------------------------------------------------
  // Generate form submit
  // -----------------------------------------------------------------------

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const data = {
      company_url: form.company_url.value.trim(),
      company_name: selectedEnrichment ? selectedEnrichment.company_name : "",
      account_signal_summary: selectedEnrichment ? selectedEnrichment.account_signal_summary : "",
      enrichment_context: selectedEnrichment ? selectedEnrichment.enrichment_context : null,
      prospect_name: form.prospect_name.value.trim(),
      prospect_title: form.prospect_title.value.trim(),
      department: form.department.value.trim(),
    };

    if (!data.company_url) return;

    currentSeqId = null;
    currentResult = null;
    resultsSection.style.display = "none";
    outputCard.style.display = "block";
    outputTitle.textContent = "Generating...";
    outputArea.innerHTML = '<span class="streaming-cursor"></span>';
    generateBtn.disabled = true;
    statusEl.textContent = "Researching company...";

    const base = directApiBase();

    fetch(base + "/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }).then(response => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            finishStream();
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop();

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const msg = JSON.parse(line.slice(6));
              if (msg.error) {
                outputArea.innerHTML = `<p style="color:var(--danger)">${escapeHtml(msg.error)}</p>`;
                generateBtn.disabled = false;
                statusEl.textContent = "";
                return;
              }
              if (msg.status) {
                outputArea.innerHTML = '<span class="streaming-cursor"></span> ' + escapeHtml(msg.status);
              }
              if (msg.done) {
                finishStream(msg.id, msg.result);
                return;
              }
            } catch (_) {}
          }
          read();
        });
      }

      read();
    }).catch(err => {
      outputArea.innerHTML = `<p style="color:var(--danger)">Connection error: ${escapeHtml(err.message)}</p>`;
      generateBtn.disabled = false;
      statusEl.textContent = "";
    });

    function finishStream(id, result) {
      generateBtn.disabled = false;
      statusEl.textContent = id ? "Done!" : "";

      if (result) {
        currentSeqId = id;
        currentResult = result;
        outputCard.style.display = "none";
        renderResults(result);
        loadSaved();
      } else {
        outputTitle.textContent = "Raw Output";
      }

      setTimeout(() => { statusEl.textContent = ""; }, 3000);
    }
  });

  // -----------------------------------------------------------------------
  // Render email cards
  // -----------------------------------------------------------------------

  const TYPE_LABELS = {
    initial: "1 - Initial",
    follow_up_1: "2 - Follow-up 1",
    follow_up_2: "3 - Follow-up 2",
    breakup: "4 - Breakup",
  };

  function renderResults(data) {
    const emails = data.emails || [];
    const companyName = data.company_name || "Unknown";

    resultsSection.style.display = "block";
    resultsTitle.textContent = "Email Sequence: " + companyName;

    const summary = data.account_signal_summary || data.ai_usage_summary || "";
    if (summary) {
      signalSummary.style.display = "block";
      signalSummary.textContent = summary;
    } else {
      signalSummary.style.display = "none";
    }

    emailCards.innerHTML = emails.map((email, i) => {
      const label = TYPE_LABELS[email.type] || ("Email " + (i + 1));
      return `<div class="card email-card">
        <div class="email-card-header">
          <span class="email-type-label">${escapeHtml(label)}</span>
          <button class="copy-btn" data-index="${i}" title="Copy email">Copy</button>
        </div>
        <div class="email-subject"><strong>Subject:</strong> ${escapeHtml(email.subject || "")}</div>
        <div class="email-body">${escapeHtml(email.body || "")}</div>
      </div>`;
    }).join("");

    // Attach copy handlers
    emailCards.querySelectorAll(".copy-btn").forEach(btn => {
      btn.addEventListener("click", function () {
        const idx = parseInt(this.dataset.index);
        const email = emails[idx];
        if (!email) return;
        const text = "Subject: " + (email.subject || "") + "\n\n" + (email.body || "");
        navigator.clipboard.writeText(text).then(() => {
          this.textContent = "Copied!";
          setTimeout(() => { this.textContent = "Copy"; }, 2000);
        });
      });
    });
  }

  // -----------------------------------------------------------------------
  // Export markdown
  // -----------------------------------------------------------------------

  exportBtn.addEventListener("click", function () {
    if (!currentSeqId) return;
    window.open(apiBase() + "/api/sequences/" + currentSeqId + "/export", "_blank");
  });

  // -----------------------------------------------------------------------
  // Delete
  // -----------------------------------------------------------------------

  deleteBtn.addEventListener("click", function () {
    if (!currentSeqId) return;
    if (!confirm("Delete this email sequence?")) return;

    fetch(apiBase() + "/api/sequences/" + currentSeqId, { method: "DELETE" })
      .then(() => {
        currentSeqId = null;
        currentResult = null;
        resultsSection.style.display = "none";
        loadSaved();
      });
  });

  // -----------------------------------------------------------------------
  // Utilities
  // -----------------------------------------------------------------------

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }
})();
