(() => {
  const $ = (id) => document.getElementById(id);
  const bw = $("bw");
  let extra = {};
  try { bw.value = localStorage.getItem("bw") || ""; } catch (e) {}

  async function cargarExtra() {
    const q = new URLSearchParams({ bw: bw.value || 0, level: $("level").value, goal: $("goal").value });
    try { extra = await (await fetch("/api/extra?" + q)).json(); } catch (e) { extra = {}; }
    aplicar();
  }

  // Añade "Ver ejemplo" y el peso sugerido a cada ejercicio mostrado
  function aplicar() {
    document.querySelectorAll("#routine .ex").forEach((ex) => {
      const info = extra[ex.dataset.id];
      if (!info) return;
      if (!ex.querySelector(".ver")) {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "ver";
        b.dataset.id = ex.dataset.id;
        b.textContent = "Ver ejemplo";
        ex.querySelector(".sets").appendChild(b);
      }
      const kg = ex.querySelector(".kg");
      if (kg && (!kg.value || kg.dataset.auto === "1")) {
        kg.value = info.kg || "";
        kg.dataset.auto = info.kg ? "1" : "";
      }
    });
  }

  new MutationObserver(aplicar).observe($("routine"), { childList: true });
  $("routine").addEventListener("input", (ev) => {
    if (ev.target.classList.contains("kg")) ev.target.dataset.auto = "";
  });

  bw.addEventListener("change", () => {
    try { localStorage.setItem("bw", bw.value); } catch (e) {}
    cargarExtra();
  });
  $("level").addEventListener("change", cargarExtra);
  $("goal").addEventListener("change", cargarExtra);

  // ---- Ventana de ejemplo ----
  document.addEventListener("click", (ev) => {
    const b = ev.target.closest(".ver");
    if (!b || !extra[b.dataset.id]) return;
    const i = extra[b.dataset.id];
    $("vtitle").textContent = i.name;
    $("vtip").textContent = i.video ? i.tip : i.tip + " Aún no hay video guardado para este ejercicio: búscalo en YouTube con el botón.";
    $("vlink").href = i.search;
    $("vframe").innerHTML = i.video
      ? `<iframe src="${i.video}" title="Video: ${i.name}" allow="encrypted-media; picture-in-picture" allowfullscreen></iframe>`
      : `<img src="${i.photo}" alt="${i.name}">`;
    $("vdlg").showModal();
  });
  $("vclose").onclick = () => $("vdlg").close();
  $("vdlg").addEventListener("close", () => { $("vframe").innerHTML = ""; });

  cargarExtra();
})();
