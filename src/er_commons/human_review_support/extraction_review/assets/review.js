const cards = [...document.querySelectorAll(".item")];
const queueCounts = window.TASK04_QUEUE_COUNTS;
const TOC = "toc";
const NOT_TOC = "not_toc";
const REVIEWABLE_TOC_QUEUES = new Set(["toc_review", "positive_toc"]);
const queueLabels = {
  all: "All items",
  failure: "Failures",
  warning: "Warnings",
  valid_page: "Valid pages",
  table: "Tables",
  toc_review: "TOC review",
  positive_toc: "Positive TOCs",
};
const legacyStorageKey =
  `task04-toc-review:${document.title}:${window.location.pathname}?review=c12`;
const storageKey = `task04-toc-review:${document.title}:task03j-final`;

function requiredElement(selector) {
  const element = document.querySelector(selector);
  if (!element) throw new Error(`Task 04 review UI is missing required element: ${selector}`);
  return element;
}

function readStoredDecisions(key) {
  const serialized = localStorage.getItem(key);
  if (!serialized) return {};
  try {
    const value = JSON.parse(serialized);
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch (error) {
    console.warn(`Ignoring malformed Task 04 browser state at ${key}`, error);
    return {};
  }
}

const storedTocState = {
  ...readStoredDecisions(legacyStorageKey),
  ...readStoredDecisions(storageKey),
};
const tocState = { ...(window.TASK04_INITIAL_TOC_DECISIONS ?? {}), ...storedTocState };
const tocEntryIds = new Set(
  cards
    .filter((card) => card.dataset.queue === "toc_review")
    .map((card) => card.querySelector("[data-toc-yes]")?.dataset.entryId)
    .filter(Boolean),
);
const positiveEntryIds = new Set(
  cards
    .filter((card) => card.dataset.queue === "positive_toc")
    .map((card) => card.querySelector("[data-toc-no]")?.dataset.entryId)
    .filter(Boolean),
);

let visible = [];
let cursor = 0;
let activeFilter = "all";
let hideReviewed = localStorage.getItem(`${storageKey}:hide-reviewed`) === "true";

document.querySelectorAll("[data-count]").forEach((element) => {
  element.textContent = queueCounts[element.dataset.count] ?? 0;
});

function saveState() {
  localStorage.setItem(storageKey, JSON.stringify(tocState));
  const tocReviewed = countDecisions(tocEntryIds);
  requiredElement("#toc-progress").textContent =
    `TOC candidates: ${tocReviewed} of ${queueCounts.toc_review ?? 0} labeled`;
  const positiveFlagged = Object.entries(tocState).filter(
    ([entryId, value]) => positiveEntryIds.has(entryId) && value === NOT_TOC,
  ).length;
  const positiveReviewed = countDecisions(positiveEntryIds);
  requiredElement("#positive-progress").textContent =
    `Positive TOCs: ${positiveReviewed} of ${queueCounts.positive_toc ?? 0} reviewed · ` +
    `${positiveFlagged} false positives`;
}

function isDisposition(value) {
  return value === TOC || value === NOT_TOC;
}

function countDecisions(entryIds) {
  return Object.entries(tocState).filter(
    ([entryId, value]) => entryIds.has(entryId) && isDisposition(value),
  ).length;
}

function cardIsReviewed(card) {
  const control = card.querySelector("[data-toc-yes], [data-toc-no]");
  if (!control) return false;
  const value = tocState[control.dataset.entryId];
  return isDisposition(value);
}

function syncImages(activeCard) {
  cards.forEach((card) => {
    if (card !== activeCard) {
      card.querySelectorAll("img[data-src]").forEach((img) => img.removeAttribute("src"));
    }
  });
  activeCard?.querySelectorAll("img[data-src]").forEach((img) => {
    if (!img.getAttribute("src")) img.src = img.dataset.src;
  });
}

function syncTocButton(card) {
  const button = card?.querySelector("[data-toc-yes]");
  if (button) {
    const tagged = tocState[button.dataset.entryId] === TOC;
    button.classList.toggle("tagged", tagged);
    button.textContent = tagged ? "Tagged TOC ✓ (click to clear)" : "TOC (T)";
  }
  const negative = card?.querySelector("[data-toc-no]");
  if (negative) {
    const tagged = tocState[negative.dataset.entryId] === NOT_TOC;
    negative.classList.toggle("tagged", tagged);
    const suffix = Boolean(negative.dataset.runSuffixEntryIds);
    negative.textContent = tagged
      ? `Tagged Not TOC ✓ (click to clear${suffix ? " suffix" : ""})`
      : `Not TOC${suffix ? " through run end" : ""} (F)`;
  }
}

function show() {
  cards.forEach((card) => { card.hidden = true; });
  const card = visible[cursor];
  const total = visible.length;
  const position = total ? cursor + 1 : 0;
  const progress = requiredElement("#progressbar");
  requiredElement("#status").textContent = total ? `${position} of ${total}` : "No items";
  requiredElement("#progress-caption").textContent = total
    ? `Position through the ${queueLabels[activeFilter].toLowerCase()} list`
    : "No review items in this queue";
  requiredElement("#progress-fill").style.width =
    `${total ? (position / total) * 100 : 0}%`;
  progress.setAttribute("aria-valuemax", String(Math.max(total, 1)));
  progress.setAttribute("aria-valuenow", String(position));
  syncImages(card);
  syncTocButton(card);
  if (card) {
    card.hidden = false;
    card.scrollIntoView({ block: "start" });
  }
}

function refresh(filter = "all") {
  activeFilter = filter;
  visible = cards.filter(
    (card) =>
      (filter === "all" || card.dataset.queue === filter) &&
      (!hideReviewed || !cardIsReviewed(card)),
  );
  cursor = 0;
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === filter);
  });
  requiredElement("#queue-label").textContent = queueLabels[filter] ?? "Review items";
  show();
}

function advance() {
  if (hideReviewed) {
    visible = cards.filter(
      (card) =>
        (activeFilter === "all" || card.dataset.queue === activeFilter) &&
        !cardIsReviewed(card),
    );
    cursor = visible.length ? cursor % visible.length : 0;
    show();
    return;
  }
  if (visible.length) {
    cursor = (cursor + 1) % visible.length;
    show();
  }
}

function tagCurrentToc() {
  const button = visible[cursor]?.querySelector("[data-toc-yes]");
  if (!button) return;
  if (tocState[button.dataset.entryId] === TOC) {
    delete tocState[button.dataset.entryId];
    saveState();
    show();
    return;
  }
  tocState[button.dataset.entryId] = TOC;
  saveState();
  advance();
}

function rejectCurrentToc() {
  const button = visible[cursor]?.querySelector("[data-toc-no]");
  if (!button) return;
  const suffixIds = runSuffixEntryIds(button);
  if (tocState[button.dataset.entryId] === NOT_TOC) {
    suffixIds.forEach((entryId) => delete tocState[entryId]);
    saveState();
    show();
    return;
  }
  suffixIds.forEach((entryId) => {
    tocState[entryId] = NOT_TOC;
  });
  saveState();
  if (hideReviewed) {
    refresh(activeFilter);
    return;
  }
  const next = visible.findIndex((card, index) => index > cursor && !cardIsReviewed(card));
  const first = visible.findIndex((card) => !cardIsReviewed(card));
  cursor = next >= 0 ? next : first >= 0 ? first : cursor;
  show();
}

function runSuffixEntryIds(button) {
  const currentEntryId = button.dataset.entryId;
  if (!currentEntryId) throw new Error("TOC decision button has no entry identity");
  try {
    const parsed = JSON.parse(button.dataset.runSuffixEntryIds || "[]");
    if (Array.isArray(parsed) && parsed.every((entryId) => typeof entryId === "string")) {
      return parsed.length ? parsed : [currentEntryId];
    }
  } catch (error) {
    console.warn(`Ignoring malformed TOC run suffix for ${currentEntryId}`, error);
  }
  return [currentEntryId];
}

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => refresh(button.dataset.filter));
});
requiredElement("#previous").addEventListener("click", () => {
  if (visible.length) {
    cursor = (cursor + visible.length - 1) % visible.length;
    show();
  }
});
requiredElement("#next").addEventListener("click", () => advance());
document.querySelectorAll("[data-toc-yes]").forEach((button) => {
  button.addEventListener("click", tagCurrentToc);
});
document.querySelectorAll("[data-toc-no]").forEach((button) => {
  button.addEventListener("click", rejectCurrentToc);
});
requiredElement("#toggle-overlays").addEventListener("click", (event) => {
  const hidden = document.body.classList.toggle("hide-overlays");
  event.currentTarget.textContent = hidden ? "Boxes off" : "Boxes on";
  event.currentTarget.setAttribute("aria-pressed", String(!hidden));
});
requiredElement("#hide-reviewed").addEventListener("change", (event) => {
  hideReviewed = event.currentTarget.checked;
  localStorage.setItem(`${storageKey}:hide-reviewed`, String(hideReviewed));
  refresh(activeFilter);
});
requiredElement("#export-toc").addEventListener("click", () => {
  const payload = {
    schema_version: "er_commons.task04a_toc_review_decisions.v1",
    review_run_id: window.TASK04_REVIEW_RUN_ID,
    review_title: document.title,
    entries: Object.entries(tocState)
      .filter(([, disposition]) => isDisposition(disposition))
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([entry_id, disposition]) => ({ entry_id, disposition })),
  };
  const link = document.createElement("a");
  link.href = URL.createObjectURL(
    new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }),
  );
  link.download = `${window.TASK04_REVIEW_RUN_ID}-toc_review_decisions.json`;
  link.click();
  URL.revokeObjectURL(link.href);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") requiredElement("#previous").click();
  if (event.key === "ArrowRight") requiredElement("#next").click();
  if (event.key.toLowerCase() === "t" && REVIEWABLE_TOC_QUEUES.has(activeFilter)) tagCurrentToc();
  if (event.key.toLowerCase() === "f" && REVIEWABLE_TOC_QUEUES.has(activeFilter)) rejectCurrentToc();
});

saveState();
requiredElement("#hide-reviewed").checked = hideReviewed;
refresh();
