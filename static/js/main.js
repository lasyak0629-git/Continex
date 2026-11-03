// OWNER: Dev B
// OWNER: Dev B
let prevBlockers = null;

document.body.addEventListener("htmx:beforeSwap", () => {
  const c = document.querySelector(".counter");
  prevBlockers = c ? parseInt(c.dataset.value, 10) : null;
});

document.body.addEventListener("htmx:afterSwap", () => {
  const el = document.querySelector(".counter");
  if (!el || prevBlockers === null) return;
  const to = parseInt(el.dataset.value, 10);
  let cur = prevBlockers;
  if (cur === to) return;
  el.textContent = cur;
  const step = cur > to ? -1 : 1;
  const timer = setInterval(() => {
    cur += step;
    el.textContent = cur;
    el.style.color = "#198754";
    if (cur === to) clearInterval(timer);
  }, 450);
});