/* Discovery Call Prep - Frontend */
(function () {
  const PREFIX = window.APP_PREFIX || "";

  function apiBase() {
    return PREFIX;
  }

  function directApiBase() {
    if (PREFIX && window.location.port === "8000") {
      return "http://localhost:3005";
    }
    return PREFIX;
  }

  // -----------------------------------------------------------------------
  // Elements
  // -----------------------------------------------------------------------

  const form = document.getElementById("research-form");
  const researchBtn = document.getElementById("research-btn");
  const statusEl = document.getElementById("research-status");
  const sellingAs = document.getElementById("selling_as");
  const outputCard = document.getElementById("output-card");
  const outputTitle = document.getElementById("output-title");
  const outputArea = document.getElementById("output-area");
  const resultsSection = document.getElementById("results-section");
  const companyTitle = document.getElementById("company-title");
  const companyBullets = document.getElementById("company-bullets");
  const prospectTitle = document.getElementById("prospect-title");
  const prospectFields = document.getElementById("prospect-fields");
  const prospectBullets = document.getElementById("prospect-bullets");
  const saveBtn = document.getElementById("save-btn");
  const exportBtn = document.getElementById("export-btn");
  const deleteBtn = document.getElementById("delete-btn");
  const savedList = document.getElementById("saved-list");
  const savedEmpty = document.getElementById("saved-empty");

  let currentPrepId = null;
  let currentResult = null;
  let hasEdits = false;

  // -----------------------------------------------------------------------
  // Load company contexts for dropdown
  // -----------------------------------------------------------------------

  function loadCompanies() {
    fetch(apiBase() + "/api/companies")
      .then(r => r.json())
      .then(data => {
        (data.companies || []).forEach(c => {
          const opt = document.createElement("option");
          opt.value = c.key;
          opt.textContent = c.name;
          sellingAs.appendChild(opt);
        });
      })
      .catch(() => {});
  }

  loadCompanies();

  // -----------------------------------------------------------------------
  // Load saved preps
  // -----------------------------------------------------------------------

  function loadSaved() {
    fetch(apiBase() + "/api/preps")
      .then(r => r.json())
      .then(data => {
        if (data.preps && data.preps.length > 0) {
          savedEmpty.style.display = "none";
          savedList.innerHTML = data.preps.map(p => {
            const date = new Date(p.created_at + "Z").toLocaleDateString("en-US", {
              month: "short", day: "numeric", year: "numeric"
            });
            const label = (p.company_name || p.company_url) + " — " + p.prospect_name;
            const meta = p.selling_as ? "Selling as " + p.selling_as.replace("-", " ").replace(/\b\w/g, c => c.toUpperCase()) : "Generic";
            return `<div class="saved-item" data-id="${p.id}">
              <div>
                <div class="saved-item-name">${escapeHtml(label)}</div>
                <div class="saved-item-meta">${escapeHtml(meta)}</div>
              </div>
              <div class="saved-item-date">${date}</div>
            </div>`;
          }).join("");

          savedList.querySelectorAll(".saved-item").forEach(el => {
            el.addEventListener("click", () => loadPrep(parseInt(el.dataset.id)));
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
  // Load a saved prep into results view
  // -----------------------------------------------------------------------

  function loadPrep(id) {
    fetch(apiBase() + "/api/preps/" + id)
      .then(r => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then(data => {
        currentPrepId = data.id;
        currentResult = {
          company: data.company_bullets,
          prospect: data.prospect_data,
        };
        outputCard.style.display = "none";
        renderResults(currentResult);
        resultsSection.scrollIntoView({ behavior: "smooth" });
      })
      .catch(() => {});
  }

  // -----------------------------------------------------------------------
  // Research form submit
  // -----------------------------------------------------------------------

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const data = {
      company_url: form.company_url.value.trim(),
      prospect_name: form.prospect_name.value.trim(),
      selling_as: form.selling_as.value,
    };

    if (!data.company_url || !data.prospect_name) return;

    currentPrepId = null;
    currentResult = null;
    hasEdits = false;
    resultsSection.style.display = "none";
    outputCard.style.display = "block";
    outputTitle.textContent = "Researching...";
    outputArea.innerHTML = '<span class="streaming-cursor"></span>';
    researchBtn.disabled = true;
    statusEl.textContent = "Searching the web...";

    const base = directApiBase();
    let streamText = "";

    fetch(base + "/api/research", {
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
                researchBtn.disabled = false;
                statusEl.textContent = "";
                return;
              }
              if (msg.status) {
                outputArea.innerHTML = '<span class="streaming-cursor"></span> ' + escapeHtml(msg.status);
              }
              if (msg.text) {
                streamText += msg.text;
                outputArea.textContent = streamText;
                outputArea.innerHTML += '<span class="streaming-cursor"></span>';
                outputArea.scrollTop = outputArea.scrollHeight;
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
      researchBtn.disabled = false;
      statusEl.textContent = "";
    });

    function finishStream(id, result) {
      researchBtn.disabled = false;
      statusEl.textContent = id ? "Done!" : "";

      if (result) {
        currentPrepId = id;
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
  // Render structured results
  // -----------------------------------------------------------------------

  function renderResults(data) {
    const company = data.company || {};
    const prospect = data.prospect || {};

    resultsSection.style.display = "block";
    hasEdits = false;
    saveBtn.style.display = "none";

    // Company card
    companyTitle.textContent = "About " + (company.name || "the Company");
    companyBullets.innerHTML = (company.bullets || []).map((b, i) =>
      `<li><input type="text" class="bullet-text" data-type="company" data-index="${i}" value="${escapeAttr(b)}" /></li>`
    ).join("");

    // Prospect card
    prospectTitle.textContent = "About " + (prospect.name || "the Prospect");

    const fields = [
      { key: "current_role", label: "Role" },
      { key: "linkedin_url", label: "LinkedIn" },
      { key: "college", label: "College" },
      { key: "hobbies", label: "Hobbies" },
      { key: "sports_teams", label: "Sports" },
    ];

    prospectFields.innerHTML = fields.map(f => {
      const val = prospect[f.key] || "Not available";
      const isLink = f.key === "linkedin_url" && val !== "Not available" && val.startsWith("http");
      const cls = val === "Not available" ? " not-available" : "";
      return `<div class="field-row">
        <span class="field-label">${f.label}</span>
        <input type="text" class="field-value${cls}" data-field="${f.key}" value="${escapeAttr(val)}" />
      </div>`;
    }).join("");

    prospectBullets.innerHTML = (prospect.bullets || []).map((b, i) =>
      `<li><input type="text" class="bullet-text" data-type="prospect" data-index="${i}" value="${escapeAttr(b)}" /></li>`
    ).join("");

    // Track edits
    resultsSection.querySelectorAll("input").forEach(input => {
      input.addEventListener("input", () => {
        hasEdits = true;
        saveBtn.style.display = "inline-flex";
      });
    });
  }

  // -----------------------------------------------------------------------
  // Save edits
  // -----------------------------------------------------------------------

  saveBtn.addEventListener("click", function () {
    if (!currentPrepId || !currentResult) return;

    const company = { ...currentResult.company };
    const prospect = { ...currentResult.prospect };

    // Read company bullets
    company.bullets = [];
    companyBullets.querySelectorAll(".bullet-text").forEach(input => {
      company.bullets.push(input.value);
    });

    // Read prospect fields
    prospectFields.querySelectorAll(".field-value").forEach(input => {
      prospect[input.dataset.field] = input.value;
    });

    // Read prospect bullets
    prospect.bullets = [];
    prospectBullets.querySelectorAll(".bullet-text").forEach(input => {
      prospect.bullets.push(input.value);
    });

    fetch(apiBase() + "/api/preps/" + currentPrepId, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_bullets: company,
        prospect_data: prospect,
      }),
    })
      .then(r => r.json())
      .then(() => {
        saveBtn.style.display = "none";
        hasEdits = false;
        currentResult = { company, prospect };
        statusEl.textContent = "Saved!";
        setTimeout(() => { statusEl.textContent = ""; }, 2000);
      })
      .catch(() => {
        statusEl.textContent = "Save failed";
      });
  });

  // -----------------------------------------------------------------------
  // Export markdown
  // -----------------------------------------------------------------------

  exportBtn.addEventListener("click", function () {
    if (!currentPrepId) return;
    window.open(apiBase() + "/api/preps/" + currentPrepId + "/export", "_blank");
  });

  // -----------------------------------------------------------------------
  // Delete
  // -----------------------------------------------------------------------

  deleteBtn.addEventListener("click", function () {
    if (!currentPrepId) return;
    if (!confirm("Delete this call prep?")) return;

    fetch(apiBase() + "/api/preps/" + currentPrepId, { method: "DELETE" })
      .then(() => {
        currentPrepId = null;
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

  function escapeAttr(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
})();
