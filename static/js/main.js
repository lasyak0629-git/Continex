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

document.addEventListener("DOMContentLoaded", function () {
  // show chosen file names in the upload dropzone
  var dz = document.getElementById("dz");
  if (dz) {
    var input = dz.querySelector("input[type=file]");
    var list = document.getElementById("file-list");
    if (input && list) {
      input.addEventListener("change", function () {
        list.innerHTML = "";
        Array.prototype.forEach.call(input.files, function (f) {
          var chip = document.createElement("span");
          chip.className = "chip";
          chip.textContent = f.name + " (" + Math.max(1, Math.round(f.size / 1024)) + " KB)";
          list.appendChild(chip);
        });
      });
    }
    ["dragenter", "dragover"].forEach(function (e) {
      dz.addEventListener(e, function () { dz.classList.add("over"); });
    });
    ["dragleave", "drop"].forEach(function (e) {
      dz.addEventListener(e, function () { dz.classList.remove("over"); });
    });
  }

  // loading state for slow actions (AI extraction)
  document.querySelectorAll("form[data-loading]").forEach(function (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector("button[type=submit], button:not([type])");
      if (btn) {
        btn.innerHTML = '<span class="spinner-inline"></span>' + (form.dataset.loading || "Working...");
        setTimeout(function () { btn.disabled = true; }, 0);
      }
    });
  });
});