(function () {
  function readCount() {
    var el = document.getElementById("blocker-number");
    return el ? parseInt(el.textContent, 10) : null;
  }
  var previous = readCount();

  document.body.addEventListener("htmx:afterSwap", function (evt) {
    var el = document.getElementById("blocker-number");
    if (!el) return;
    var target = parseInt(el.textContent, 10);
    if (previous === null || isNaN(target) || previous === target) { previous = target; return; }
    var from = previous, step = from > target ? -1 : 1, value = from;
    el.textContent = value;
    var timer = setInterval(function () {
      value += step;
      el.textContent = value;
      el.classList.add("pulse");
      setTimeout(function () { el.classList.remove("pulse"); }, 250);
      if (value === target) { clearInterval(timer); previous = target; }
    }, 700);
  });
})();