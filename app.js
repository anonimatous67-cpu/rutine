const $ = (id) => document.getElementById(id);
let plan = [];
let current = 0;
let timerId = null;

// ---------- Rutina ----------
async function generar() {
  const q = new URLSearchParams({ goal: $("goal").value, level: $("level").value, days: $("days").value });
  plan = await (await fetch("/api/routine?" + q)).json();
  current = 0;
  renderTabs();
  renderDay();
}

function renderTabs() {
  const nav = $("tabs");
  nav.hidden = false;
  nav.innerHTML = "";
  plan.forEach((d, i) => {
    const b = document.createElement("button");
    b.className = "tab";
    b.setAttribute("aria-selected", i === current);
    b.textContent = `Día ${d.day}: ${d.title}`;
    b.onclick = () => { current = i; renderTabs(); renderDay(); };
    nav.appendChild(b);
  });
}

function renderDay() {
  const box = $("routine");
  box.innerHTML = "";
  plan[current].exercises.forEach((e) => {
    const sets = Array.from({ length: e.sets }, (_, i) =>
      `<label class="set"><input type="checkbox" data-s> Serie ${i + 1}</label>`).join("");
    const el = document.createElement("article");
    el.className = "ex";
    el.dataset.id = e.id;
    el.innerHTML = `
      <img src="${e.photo}" alt="${e.name}" loading="lazy">
      <div>
        <h3>${e.name}</h3>
        <p class="meta"><b>${e.sets} series</b> x <b>${e.reps}</b> reps · descanso ${e.rest} s</p>
        <p class="tip">${e.tip}</p>
        <div class="sets">${sets}
          <input class="kg" type="number" min="0" step="0.5" placeholder="Peso kg" aria-label="Peso en kg para ${e.name}">
          <button class="rest" type="button" data-rest="${e.rest}">Descansar</button>
        </div>
      </div>`;
    box.appendChild(el);
  });
  $("savebar").hidden = false;
}

$("routine").addEventListener("change", (ev) => {
  if (!ev.target.matches("[data-s]")) return;
  const ex = ev.target.closest(".ex");
  const all = ex.querySelectorAll("[data-s]");
  ex.classList.toggle("done", [...all].every((c) => c.checked));
});

$("routine").addEventListener("click", (ev) => {
  const b = ev.target.closest("[data-rest]");
  if (b) iniciarTimer(+b.dataset.rest);
});

// ---------- Temporizador ----------
function iniciarTimer(seg) {
  clearInterval(timerId);
  $("timer").hidden = false;
  $("tval").textContent = seg;
  timerId = setInterval(() => {
    seg -= 1;
    $("tval").textContent = seg;
    if (seg <= 0) {
      clearInterval(timerId);
      $("tval").textContent = "¡Listo!";
      if (navigator.vibrate) navigator.vibrate(300);
      setTimeout(() => ($("timer").hidden = true), 2500);
    }
  }, 1000);
}
$("tstop").onclick = () => { clearInterval(timerId); $("timer").hidden = true; };

// ---------- Guardar e historial ----------
async function guardar() {
  const entries = [...document.querySelectorAll(".ex")].map((ex) => ({
    maquina: ex.querySelector("h3").textContent,
    series: ex.querySelectorAll("[data-s]:checked").length,
    peso: ex.querySelector(".kg").value,
  })).filter((e) => e.series > 0);
  if (!entries.length) { alert("Marca al menos una serie para guardar."); return; }
  const dia = `Día ${plan[current].day}: ${plan[current].title}`;
  await fetch("/api/log", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dia, entries }) });
  cargarHistorial();
  alert("Entrenamiento guardado.");
}

async function cargarHistorial() {
  const rows = await (await fetch("/api/history")).json();
  $("empty").hidden = rows.length > 0;
  $("hist").hidden = rows.length === 0;
  $("hist").querySelector("tbody").innerHTML = rows.map((r) =>
    `<tr><td>${r.fecha}</td><td>${r.dia}</td><td>${r.maquina}</td><td>${r.series}</td><td>${r.peso || "-"}</td></tr>`).join("");
}

// ---------- Catálogo de máquinas ----------
async function cargarMaquinas() {
  const list = await (await fetch("/api/machines")).json();
  $("machines").innerHTML = list.map((m) =>
    `<div class="card"><img src="${m.photo}" alt="${m.name}" loading="lazy"><div>${m.name}<small>${m.group}</small></div></div>`).join("");
}

$("gen").onclick = generar;
$("save").onclick = guardar;
cargarMaquinas();
cargarHistorial();
generar();
