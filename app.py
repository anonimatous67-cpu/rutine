"""Rutina de Gym - Flask + SQLite.
Ejecutar:  pip install flask  ->  python app.py  ->  http://127.0.0.1:5000
Para cambiar/añadir máquinas edita el diccionario MACHINES (img = static/img/mN.jpg)."""
import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request, render_template

app = Flask(__name__, template_folder='.', static_folder='.')

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gym.db")

# Nombres según las fotos (algunas están borrosas: corrígelos aquí si hace falta)
MACHINES = {
    "prensa":   {"name": "Prensa de piernas 45°", "group": "Pierna", "img": 2,
                 "tip": "Pies al ancho de hombros, baja hasta 90° sin despegar la cadera del asiento."},
    "hack":     {"name": "Hack squat", "group": "Pierna", "img": 1,
                 "tip": "Espalda pegada al respaldo; empuja con todo el pie, sin bloquear rodillas."},
    "extension": {"name": "Extensión de cuádriceps", "group": "Pierna", "img": 10,
                  "tip": "Sube explosivo, baja en 3 segundos controlando."},
    "curlfem":  {"name": "Curl femoral sentado", "group": "Pierna", "img": 6,
                 "tip": "Cadera fija; lleva talones hacia los glúteos y vuelve lento."},
    "banco_ext": {"name": "Banco ajustable (curl/extensión)", "group": "Pierna", "img": 11,
                  "tip": "Ajusta el rodillo a la altura del tobillo antes de empezar."},
    "gemelos":  {"name": "Gemelos sentado", "group": "Pierna", "img": 12,
                 "tip": "Pausa de 1 segundo arriba y estira completo abajo."},
    "hipthrust": {"name": "Hip thrust", "group": "Glúteo", "img": 8,
                  "tip": "Barbilla al pecho, sube la cadera y aprieta glúteos 1 segundo."},
    "cadera":   {"name": "Cadera de pie (multi-ángulo)", "group": "Glúteo", "img": 7,
                 "tip": "Torso recto, movimiento lento desde la cadera, sin balanceo."},
    "aductor":  {"name": "Aductores / abductores", "group": "Glúteo", "img": 3,
                 "tip": "Abre y cierra con control; no rebotes al final del recorrido."},
    "abductor": {"name": "Abductor sentado", "group": "Glúteo", "img": 14,
                 "tip": "Inclina un poco el torso hacia delante para sentir más el glúteo."},
    "pressbanca": {"name": "Press banca plano", "group": "Empuje", "img": 16,
                   "tip": "Escápulas juntas, baja al pecho y empuja en línea recta. Pide spotter."},
    "palanca":  {"name": "Press con palancas de discos", "group": "Empuje", "img": 20,
                 "tip": "Codos a 45° del torso; extiende sin bloquear del todo."},
    "remo_t":   {"name": "Remo en T (landmine)", "group": "Tirón", "img": 17,
                 "tip": "Espalda neutra, tira hacia el abdomen y junta escápulas."},
    "remo_p":   {"name": "Remo con palanca de discos", "group": "Tirón", "img": 18,
                 "tip": "Pecho apoyado, tira con los codos, no con las manos."},
    "polea":    {"name": "Torre de poleas", "group": "Tirón", "img": 19,
                 "tip": "Jalón, face pull o tríceps: elige el agarre y mantén el core firme."},
    "abdominal": {"name": "Banco abdominal declinado", "group": "Core", "img": 13,
                  "tip": "Sube enrollando el torso; no tires del cuello."},
}

# Plantillas de días: cada día = (título, [ids de máquinas])
SPLITS = {
    3: [("Pierna", ["prensa", "hack", "extension", "curlfem", "gemelos"]),
        ("Empuje + Core", ["pressbanca", "palanca", "polea", "abdominal"]),
        ("Tirón + Glúteo", ["remo_t", "remo_p", "polea", "hipthrust", "abductor"])],
    4: [("Pierna", ["prensa", "hack", "extension", "curlfem", "gemelos"]),
        ("Empuje", ["pressbanca", "palanca", "polea"]),
        ("Glúteo + Core", ["hipthrust", "cadera", "aductor", "abductor", "abdominal"]),
        ("Tirón", ["remo_t", "remo_p", "polea", "banco_ext"])],
    5: [("Pierna", ["prensa", "hack", "extension", "gemelos"]),
        ("Empuje", ["pressbanca", "palanca", "polea"]),
        ("Glúteo", ["hipthrust", "cadera", "aductor", "abductor"]),
        ("Tirón", ["remo_t", "remo_p", "polea"]),
        ("Pierna 2 + Core", ["curlfem", "banco_ext", "prensa", "gemelos", "abdominal"])],
}

GOALS = {  # series, repeticiones, descanso (s)
    "hipertrofia": (3, "8-12", 75),
    "fuerza":      (4, "4-6", 150),
    "definicion":  (3, "12-15", 45),
}


# ---- Máquinas nuevas (añadidas sin modificar lo anterior) ----
MACHINES.update({
    "remo_polea":   {"name": "Remo sentado en polea baja", "group": "Tirón", "img": 23,
                     "tip": "Pies en los apoyos, espalda recta; tira hacia el ombligo y junta escápulas."},
    "remo_t_pecho": {"name": "Remo en T con apoyo de pecho", "group": "Tirón", "img": 22,
                     "tip": "Pecho firme en el soporte; tira con los codos y aprieta la espalda 1 segundo."},
})
# Se suman a los días de Tirón (máximo 6 ejercicios por día)
for _dias in SPLITS.values():
    for _titulo, _ids in _dias:
        if _titulo.startswith("Tirón"):
            for _nuevo in ("remo_polea", "remo_t_pecho"):
                if _nuevo not in _ids and len(_ids) < 6:
                    _ids.append(_nuevo)


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, dia TEXT,
            maquina TEXT, series INTEGER, peso REAL)""")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/machines")
def machines():
    return jsonify([{"id": k, **v, "photo": f"/static/img/m{v['img']}.jpg"} for k, v in MACHINES.items()])


@app.route("/api/routine")
def routine():
    goal = request.args.get("goal", "hipertrofia")
    level = request.args.get("level", "principiante")
    days = int(request.args.get("days", 3))
    days = days if days in SPLITS else 3
    sets, reps, rest = GOALS.get(goal, GOALS["hipertrofia"])
    if level == "principiante":
        sets = max(2, sets - 1)
    elif level == "avanzado":
        sets += 1
    plan = []
    for i, (title, ids) in enumerate(SPLITS[days], 1):
        plan.append({"day": i, "title": title, "exercises": [
            {"id": m, **MACHINES[m], "photo": f"/static/img/m{MACHINES[m]['img']}.jpg",
             "sets": sets, "reps": reps, "rest": rest} for m in ids]})
    return jsonify(plan)


@app.route("/api/log", methods=["POST"])
def add_log():
    data = request.get_json(force=True)
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    with db() as con:
        for e in data.get("entries", []):
            con.execute("INSERT INTO logs(fecha,dia,maquina,series,peso) VALUES(?,?,?,?,?)",
                        (fecha, data.get("dia", ""), e["maquina"], int(e["series"]), float(e["peso"] or 0)))
    return jsonify(ok=True)


@app.route("/api/history")
def history():
    with db() as con:
        rows = con.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 60").fetchall()
    return jsonify([dict(r) for r in rows])


# ---- Peso sugerido + videos de ejemplo (añadido sin modificar lo anterior) ----
import re
from urllib.parse import quote_plus

# Para ver el video dentro de la web pega el enlace o el ID de YouTube de cada ejercicio.
# Ejemplo:  "prensa": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
# Si un ejercicio no tiene video, el botón abre una búsqueda en YouTube.
VIDEOS = {}

# Fracción del peso corporal como carga inicial aproximada (0 = sin sugerencia)
COEF_PESO = {
    "prensa": 1.0, "hack": 0.6, "extension": 0.35, "curlfem": 0.3, "banco_ext": 0.3,
    "gemelos": 0.5, "hipthrust": 0.6, "cadera": 0.15, "aductor": 0.3, "abductor": 0.3,
    "pressbanca": 0.5, "palanca": 0.4, "remo_t": 0.35, "remo_p": 0.4, "polea": 0.4,
    "remo_polea": 0.4, "remo_t_pecho": 0.35, "abdominal": 0,
}
NIVEL_F = {"principiante": 0.6, "intermedio": 0.85, "avanzado": 1.0}
OBJ_F = {"fuerza": 1.15, "hipertrofia": 1.0, "definicion": 0.85}


def _embed(v):
    v = (v or "").strip()
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", v) or re.fullmatch(r"([A-Za-z0-9_-]{11})", v)
    return f"https://www.youtube.com/embed/{m.group(1)}" if m else ""


@app.route("/api/extra")
def extra():
    try:
        bw = float(request.args.get("bw", 0) or 0)
    except ValueError:
        bw = 0
    bw = bw if 30 <= bw <= 250 else 0
    f = NIVEL_F.get(request.args.get("level"), 0.85) * OBJ_F.get(request.args.get("goal"), 1.0)
    out = {}
    for k, m in MACHINES.items():
        c = COEF_PESO.get(k, 0)
        kg = max(2.5, round(bw * c * f / 2.5) * 2.5) if bw and c else ""
        out[k] = {"name": m["name"], "tip": m["tip"], "photo": f"/static/img/m{m['img']}.jpg",
                  "video": _embed(VIDEOS.get(k)), "kg": kg,
                  "search": "https://www.youtube.com/results?search_query=" + quote_plus(f"como hacer {m['name']} técnica correcta")}
    return jsonify(out)


init_db()
if __name__ == "__main__":
    app.run(debug=True)
