const state = {
  index: null,
  category: "all",
  query: "",
  visible: [],
  selectedId: null,
};

const list = document.querySelector("#case-list");
const detail = document.querySelector("#detail");
const filters = document.querySelector("#filters");
const visibleCount = document.querySelector("#visible-count");
const search = document.querySelector("#search");

const escapeHtml = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const pageLabel = (pages) =>
  pages.length === 1 ? `PDF page ${pages[0]}` : `PDF pages ${pages.join(", ")}`;

async function loadJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function renderFilters() {
  const entries = [["all", "All cases", state.index.case_count]];
  const labels = new Map(state.index.items.map((item) => [item.category, item.category_label]));
  for (const [category, count] of Object.entries(state.index.category_counts)) {
    entries.push([category, labels.get(category), count]);
  }
  filters.innerHTML = entries
    .map(
      ([category, label, count]) => `
        <button class="filter ${state.category === category ? "active" : ""}"
                data-category="${escapeHtml(category)}">
          <span>${escapeHtml(label)}</span><span class="count">${count}</span>
        </button>`,
    )
    .join("");
  filters.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.category = button.dataset.category;
      applyFilters();
      renderFilters();
    });
  });
}

function applyFilters() {
  const query = state.query.toLowerCase();
  state.visible = state.index.items.filter((item) => {
    const categoryMatch = state.category === "all" || item.category === state.category;
    const searchText = `${item.source_label} ${item.target_label} ${item.reason}`.toLowerCase();
    return categoryMatch && searchText.includes(query);
  });
  visibleCount.textContent = `${state.visible.length} of ${state.index.case_count} cases`;
  renderList();
}

function renderList() {
  if (!state.visible.length) {
    list.innerHTML = '<p class="no-results">No cases match this filter.</p>';
    return;
  }
  list.innerHTML = state.visible
    .map(
      (item) => `
        <button class="case-row ${item.item_id === state.selectedId ? "selected" : ""}"
                data-id="${item.item_id}" data-url="${item.detail_url}">
          <span class="case-number">${item.item_id.replace("case-", "")}</span>
          <span class="case-copy">
            <strong>${escapeHtml(item.source_label)}</strong>
            <span class="target">${escapeHtml(item.target_label)}</span>
            <span class="meta">${escapeHtml(item.category_label)} · ${escapeHtml(pageLabel(item.physical_pages))}</span>
          </span>
        </button>`,
    )
    .join("");
  list.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => selectCase(button.dataset.id, button.dataset.url));
  });
}

async function selectCase(id, url) {
  state.selectedId = id;
  renderList();
  detail.innerHTML = '<div class="loading-panel"><div class="loading-mark"></div><p>Loading one case…</p></div>';
  try {
    const item = await loadJson(url);
    if (state.selectedId !== id) return;
    renderDetail(item);
    history.replaceState(null, "", `#${id}`);
  } catch (error) {
    detail.replaceChildren(document.querySelector("#error-template").content.cloneNode(true));
  }
}

function renderDetail(item) {
  const currentIndex = state.visible.findIndex((candidate) => candidate.item_id === item.item_id);
  const contexts = item.contexts.map(renderContext).join("");
  const units = item.units.map(renderUnit).join("");
  const nearby = item.nearby_units
    .map(
      (unit) => `
        <li><span>${unit.relative_position < 0 ? "Before" : "After"}</span>
          <strong>${escapeHtml(unit.official_label)}</strong>
          <small>${escapeHtml(pageLabel(unit.physical_pages))}</small>
        </li>`,
    )
    .join("");
  detail.innerHTML = `
    <article class="case-detail">
      <nav class="case-nav" aria-label="Case navigation">
        <button id="previous" ${currentIndex <= 0 ? "disabled" : ""}>← Previous</button>
        <span>${currentIndex + 1} / ${state.visible.length}</span>
        <button id="next" ${currentIndex < 0 || currentIndex >= state.visible.length - 1 ? "disabled" : ""}>Next →</button>
      </nav>

      <div class="case-heading">
        <span class="category-tag">${escapeHtml(item.category_label)}</span>
        <p class="case-id">${escapeHtml(item.item_id)} · ${escapeHtml(item.reason)}</p>
        <h2>${escapeHtml(item.target_label_visible)}</h2>
        <p class="question">${escapeHtml(item.question)}</p>
      </div>

      <section class="status-card">
        <div><span>Current outcome</span><strong>${escapeHtml(item.current_outcome)}</strong></div>
        <div><span>Resolver rule</span><code>${escapeHtml(item.resolver_rule)}</code></div>
        <div class="candidate-note"><span>Why this is here</span><p>${escapeHtml(item.candidate_summary)}</p></div>
      </section>

      <section>
        <div class="section-heading"><div><p class="section-kicker">Accepted source text</p><h3>Mention in context</h3></div>
          <span>Page images stay unloaded until opened.</span></div>
        ${contexts || '<p class="empty-inline">No mention span is available for this grouped case.</p>'}
      </section>

      <section>
        <div class="section-heading"><div><p class="section-kicker">Compared identities</p><h3>Source units</h3></div>
          <span>Full text is fetched one unit at a time.</span></div>
        <div class="units">${units}</div>
      </section>

      <section class="nearby-section">
        <div class="section-heading"><div><p class="section-kicker">Document order</p><h3>Nearby units</h3></div></div>
        <ol class="nearby-list">${nearby}</ol>
      </section>

      <details class="provenance">
        <summary>IDs and provenance</summary>
        <pre>${escapeHtml(JSON.stringify(item.provenance, null, 2))}</pre>
      </details>
    </article>`;

  detail.querySelector("#previous")?.addEventListener("click", () => selectVisible(currentIndex - 1));
  detail.querySelector("#next")?.addEventListener("click", () => selectVisible(currentIndex + 1));
  detail.querySelectorAll("[data-load-image]").forEach((button) => {
    button.addEventListener("click", () => loadImage(button));
  });
  detail.querySelectorAll("[data-load-unit]").forEach((button) => {
    button.addEventListener("click", () => loadUnit(button));
  });
}

function renderContext(context) {
  const image = context.page_image;
  const imageControl = image
    ? `<button class="secondary" data-load-image data-url="${escapeHtml(image.url)}"
               data-page="${context.physical_page}">Load cached page image · ${Math.round(image.byte_size / 1024)} KB</button>`
    : '<span class="unavailable">No cached render available</span>';
  return `
    <div class="context-card">
      <div class="context-meta"><strong>PDF page ${context.physical_page}</strong>${imageControl}</div>
      <blockquote>${escapeHtml(context.before)}<mark>${escapeHtml(context.match)}</mark>${escapeHtml(context.after)}</blockquote>
      <div class="image-slot" aria-live="polite"></div>
    </div>`;
}

function renderUnit(unit) {
  return `
    <div class="unit-card">
      <div><span class="unit-role">${escapeHtml(unit.role)}</span>
        <h4>${escapeHtml(unit.official_label)}</h4>
        <p>${escapeHtml(unit.unit_kind)} · ${escapeHtml(pageLabel(unit.physical_pages))}</p></div>
      <button class="secondary" data-load-unit data-url="${escapeHtml(unit.full_text_url)}">Load full unit text</button>
      <div class="unit-text" aria-live="polite"></div>
    </div>`;
}

function selectVisible(index) {
  const item = state.visible[index];
  if (item) selectCase(item.item_id, item.detail_url);
}

function loadImage(button) {
  const slot = button.closest(".context-card").querySelector(".image-slot");
  const image = document.createElement("img");
  image.alt = `Accepted cached render of PDF page ${button.dataset.page}`;
  image.loading = "lazy";
  image.decoding = "async";
  image.src = button.dataset.url;
  slot.replaceChildren(image);
  button.remove();
}

async function loadUnit(button) {
  const target = button.closest(".unit-card").querySelector(".unit-text");
  button.disabled = true;
  button.textContent = "Loading…";
  try {
    const unit = await loadJson(button.dataset.url);
    target.innerHTML = unit.sections
      .map(
        (section) => `<div class="unit-section"><span>PDF page ${section.physical_page}</span><pre>${escapeHtml(section.text)}</pre></div>`,
      )
      .join("");
    button.remove();
  } catch (error) {
    button.disabled = false;
    button.textContent = "Try loading full text again";
  }
}

search.addEventListener("input", () => {
  state.query = search.value.trim();
  applyFilters();
});

document.addEventListener("keydown", (event) => {
  if (event.target.matches("input, button, summary")) return;
  const index = state.visible.findIndex((item) => item.item_id === state.selectedId);
  if (event.key === "ArrowLeft") selectVisible(index - 1);
  if (event.key === "ArrowRight") selectVisible(index + 1);
});

loadJson("data/index.json")
  .then((index) => {
    state.index = index;
    document.querySelector("#page-title").textContent = index.title;
    document.title = index.title;
    search.placeholder = `Search ${index.case_count} cases`;
    renderFilters();
    applyFilters();
    const requested = location.hash.slice(1);
    const first = index.items.find((item) => item.item_id === requested) || index.items[0];
    if (first) selectCase(first.item_id, first.detail_url);
  })
  .catch(() => detail.replaceChildren(document.querySelector("#error-template").content.cloneNode(true)));
