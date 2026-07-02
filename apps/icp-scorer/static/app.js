/* ICP Scorer - Frontend */
(function () {
  const PREFIX = window.APP_PREFIX || "";

  function apiBase() {
    return PREFIX;
  }

  const form = document.getElementById("score-form");
  const scoreBtn = document.getElementById("score-btn");
  const statusEl = document.getElementById("score-status");
  const resultCard = document.getElementById("result-card");
  const resultTitle = document.getElementById("result-title");
  const scoreNumber = document.getElementById("score-number");
  const scoreGrade = document.getElementById("score-grade");
  const breakdownArea = document.getElementById("breakdown-area");
  const savedList = document.getElementById("saved-list");
  const savedEmpty = document.getElementById("saved-empty");
  const dimContainer = document.getElementById("dimensions-container");

  let model = null;

  // -----------------------------------------------------------------------
  // Load scoring model and build form
  // -----------------------------------------------------------------------

  function loadModel() {
    fetch(apiBase() + "/api/model")
      .then(r => r.json())
      .then(data => {
        model = data;
        renderDimensions(data.dimensions);
      })
      .catch(() => {});
  }

  function renderDimensions(dimensions) {
    dimContainer.innerHTML = dimensions.map(dim => {
      const options = dim.options.map(opt =>
        `<option value="${esc(opt.value)}">${esc(opt.label)}</option>`
      ).join("");
      return `<div class="form-group">
        <label for="dim-${esc(dim.id)}">${esc(dim.label)} <span class="hint">(weight: ${dim.weight}%)</span></label>
        <select id="dim-${esc(dim.id)}" name="${esc(dim.id)}" required>
          <option value="">Select...</option>
          ${options}
        </select>
      </div>`;
    }).join("");
  }

  loadModel();

  // -----------------------------------------------------------------------
  // Load saved scores
  // -----------------------------------------------------------------------

  function loadSaved() {
    fetch(apiBase() + "/api/scores")
      .then(r => r.json())
      .then(data => {
        if (data.scores && data.scores.length > 0) {
          savedEmpty.style.display = "none";
          savedList.innerHTML = data.scores.map(s => {
            const date = new Date(s.created_at + "Z").toLocaleDateString("en-US", {
              month: "short", day: "numeric", year: "numeric"
            });
            const gradeClass = "grade-" + s.grade.toLowerCase();
            return `<div class="saved-item" data-id="${s.id}">
              <div>
                <div class="saved-item-name">${esc(s.company_name)}</div>
                <div class="saved-item-meta">${date}</div>
              </div>
              <div class="saved-item-score">
                <span class="mini-score">${s.score}</span>
                <span class="mini-grade ${gradeClass}">${s.grade}</span>
              </div>
            </div>`;
          }).join("");
        } else {
          savedEmpty.style.display = "block";
          savedList.innerHTML = "";
        }
      })
      .catch(() => {});
  }

  loadSaved();

  // -----------------------------------------------------------------------
  // Score form submit
  // -----------------------------------------------------------------------

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!model) return;

    const selections = {};
    model.dimensions.forEach(dim => {
      const sel = document.getElementById("dim-" + dim.id);
      if (sel) selections[dim.id] = sel.value;
    });

    const data = {
      company_name: form.company_name.value.trim(),
      selections: selections,
    };

    if (!data.company_name) return;

    scoreBtn.disabled = true;
    statusEl.textContent = "Scoring...";

    fetch(apiBase() + "/api/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then(r => r.json())
      .then(result => {
        scoreBtn.disabled = false;
        statusEl.textContent = "";

        if (result.error) {
          statusEl.textContent = result.error;
          return;
        }

        renderResult(result);
        loadSaved();
      })
      .catch(err => {
        scoreBtn.disabled = false;
        statusEl.textContent = "Error: " + err.message;
      });
  });

  // -----------------------------------------------------------------------
  // Render score result
  // -----------------------------------------------------------------------

  function renderResult(result) {
    resultCard.style.display = "block";
    resultTitle.textContent = result.company_name;

    const gradeClass = "grade-" + result.grade.toLowerCase();
    scoreNumber.textContent = result.score;
    scoreGrade.className = "score-grade " + gradeClass;
    scoreGrade.textContent = result.grade;

    const breakdown = result.breakdown || [];
    breakdownArea.innerHTML = `<div class="breakdown-grid">
      ${breakdown.map(b => {
        const pct = b.score;
        const barColor = pct >= 70 ? "var(--green)" : pct >= 40 ? "var(--yellow)" : "var(--red)";
        return `<div class="breakdown-row">
          <div class="breakdown-label">${esc(b.label)} <span class="breakdown-weight">${b.weight}%</span></div>
          <div class="breakdown-bar-container">
            <div class="breakdown-bar" style="width:${pct}%;background:${barColor}"></div>
          </div>
          <div class="breakdown-score">${b.score}</div>
        </div>`;
      }).join("")}
    </div>`;

    resultCard.scrollIntoView({ behavior: "smooth" });
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
