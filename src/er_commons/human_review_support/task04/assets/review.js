const cards = [...document.querySelectorAll(".item")];
const queueCounts = window.TASK04_QUEUE_COUNTS;
const queueLabels = {
  all: "All items",
  failure: "Failures",
  warning: "Warnings",
  valid_page: "Valid pages",
  table: "Tables",
};

let visible = [];
let cursor = 0;
let activeFilter = "all";

document.querySelectorAll("[data-count]").forEach((element) => {
  element.textContent = queueCounts[element.dataset.count] ?? 0;
});

function show() {
  cards.forEach((card) => { card.hidden = true; });
  const card = visible[cursor];
  const total = visible.length;
  const position = total ? cursor + 1 : 0;
  const percent = total ? (position / total) * 100 : 0;
  const progress = document.querySelector("#progressbar");

  document.querySelector("#status").textContent = total ? `${position} of ${total}` : "No items";
  document.querySelector("#progress-caption").textContent = total
    ? `Position through the ${queueLabels[activeFilter].toLowerCase()} list`
    : "No review items in this queue";
  document.querySelector("#progress-fill").style.width = `${percent}%`;
  progress.setAttribute("aria-valuemax", String(Math.max(total, 1)));
  progress.setAttribute("aria-valuenow", String(position));
  if (card) {
    card.hidden = false;
    card.scrollIntoView({ block: "start" });
  }
}

function refresh(filter = "all") {
  activeFilter = filter;
  visible = cards.filter((card) => filter === "all" || card.dataset.queue === filter);
  cursor = 0;
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === filter);
  });
  document.querySelector("#queue-label").textContent = queueLabels[filter] ?? "Review items";
  show();
}

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => refresh(button.dataset.filter));
});
document.querySelector("#previous").addEventListener("click", () => {
  if (visible.length) {
    cursor = (cursor + visible.length - 1) % visible.length;
    show();
  }
});
document.querySelector("#next").addEventListener("click", () => {
  if (visible.length) {
    cursor = (cursor + 1) % visible.length;
    show();
  }
});
document.querySelector("#toggle-overlays").addEventListener("click", (event) => {
  const hidden = document.body.classList.toggle("hide-overlays");
  event.currentTarget.textContent = hidden ? "Boxes off" : "Boxes on";
  event.currentTarget.setAttribute("aria-pressed", String(!hidden));
});
document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") document.querySelector("#previous").click();
  if (event.key === "ArrowRight") document.querySelector("#next").click();
});

refresh();
