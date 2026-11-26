"""Lógica de Don Climas (sin interfaz gráfica).

Monitoreo meteorológico para transporte terrestre: consulta de clima,
evaluación de riesgo vial y cálculo de la métrica de usabilidad SUS.
"""
import hashlib
import json
import os
import random
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
SUS_PATH = os.path.join(BASE_DIR, "sus_results.json")

# ---------------------------------------------------------------- login ----
USUARIOS = {"admin": hashlib.sha256(b"1234").hexdigest()}
MAX_INTENTOS = 2


def validar_login(usuario: str, clave: str) -> bool:
    h = hashlib.sha256(clave.encode()).hexdigest()
    return USUARIOS.get(usuario.strip()) == h


# --------------------------------------------------------------- config ----
def cargar_config() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar_config(datos: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------- clima ----
class ErrorClima(Exception):
    pass


def categoria(cond_id: int) -> str:
    """Agrupa el código de OpenWeatherMap en una categoría visual."""
    if 200 <= cond_id < 300:
        return "tormenta"
    if 300 <= cond_id < 600:
        return "lluvia"
    if 600 <= cond_id < 700:
        return "nieve"
    if 700 <= cond_id < 800:
        return "niebla"
    if cond_id == 800:
        return "despejado"
    return "nublado"


def _get_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise ErrorClima("API Key inválida o aún no activada.")
        if e.code == 404:
            raise ErrorClima("Ciudad no encontrada.")
        raise ErrorClima(f"Error del servicio ({e.code}).")
    except (urllib.error.URLError, TimeoutError):
        raise ErrorClima("Sin conexión con el servicio meteorológico.")


def consultar_clima(ciudad: str, api_key: str) -> dict:
    """Consulta OpenWeatherMap. Con la clave 'demo' devuelve datos simulados."""
    if api_key.strip().lower() == "demo":
        return _clima_demo(ciudad)
    q = urllib.parse.quote(ciudad)
    k = urllib.parse.quote(api_key.strip())
    base = "https://api.openweathermap.org/data/2.5"
    act = _get_json(f"{base}/weather?q={q}&appid={k}&units=metric&lang=es")
    pron = _get_json(f"{base}/forecast?q={q}&appid={k}&units=metric&lang=es&cnt=3")
    tz = timezone(timedelta(seconds=act.get("timezone", 0)))
    lluvia = act.get("rain", {}).get("1h", 0.0) + act.get("snow", {}).get("1h", 0.0)
    w = act["weather"][0]
    filas = []
    for it in pron.get("list", [])[:3]:
        hora = datetime.fromtimestamp(it["dt"], tz).strftime("%H:%M")
        filas.append((hora, f"{it['main']['temp']:.0f} °C",
                      it["weather"][0]["description"].capitalize()))
    datos = {
        "ciudad": f"{act['name']}, {act['sys'].get('country', '')}".strip(", "),
        "temp": act["main"]["temp"],
        "humedad": act["main"]["humidity"],
        "viento": act["wind"].get("speed", 0) * 3.6,
        "visibilidad": act.get("visibility", 10000) / 1000,
        "lluvia": lluvia,
        "condicion": w["description"].capitalize(),
        "cond_id": w["id"],
        "pronostico": filas,
    }
    datos["categoria"] = categoria(datos["cond_id"])
    datos["riesgo"] = calcular_riesgo(datos)
    return datos


def _clima_demo(ciudad: str) -> dict:
    escenarios = [
        ("Cielo despejado", 800, 27, 40, 12, 10, 0.0),
        ("Nubes dispersas", 802, 22, 55, 20, 10, 0.0),
        ("Lluvia moderada", 501, 18, 85, 30, 6, 4.2),
        ("Tormenta eléctrica", 211, 20, 90, 55, 3, 12.0),
        ("Niebla", 741, 12, 95, 8, 0.6, 0.0),
        ("Nieve ligera", 600, -1, 90, 20, 2, 1.5),
    ]
    c, cid, t, h, v, vis, ll = random.choice(escenarios)
    ahora = datetime.now()
    d = {
        "ciudad": ciudad or "Celaya, GTO",
        "temp": t, "humedad": h, "viento": v, "visibilidad": vis,
        "lluvia": ll, "condicion": c, "cond_id": cid,
        "pronostico": [((ahora + timedelta(hours=3 * i)).strftime("%H:%M"),
                        f"{t + random.randint(-3, 3)} °C", c)
                       for i in range(1, 4)],
    }
    d["categoria"] = categoria(cid)
    d["riesgo"] = calcular_riesgo(d)
    return d


# --------------------------------------------------------------- riesgo ----
def calcular_riesgo(d: dict) -> str:
    """Riesgo vial 'bajo' / 'medio' / 'alto' por puntos acumulados."""
    p = 0
    vis, ll, vi, t = d["visibilidad"], d["lluvia"], d["viento"], d["temp"]
    p += 3 if vis < 1 else 2 if vis < 4 else 1 if vis < 8 else 0
    p += 3 if ll >= 7.6 else 2 if ll >= 2.5 else 1 if ll > 0 else 0
    p += 3 if vi >= 60 else 2 if vi >= 40 else 1 if vi >= 25 else 0
    p += 2 if t <= 0 else 1 if t >= 40 else 0
    p += {"tormenta": 3, "nieve": 3, "niebla": 1}.get(categoria(d["cond_id"]), 0)
    return "alto" if p >= 5 else "medio" if p >= 2 else "bajo"


RECOMENDACION = {
    "despejado": "Buenas condiciones. Mantén la velocidad y distancia habituales.",
    "nublado": "Cielo cubierto. Enciende luces y revisa el pronóstico de la ruta.",
    "lluvia": "Pavimento mojado: reduce velocidad y aumenta la distancia de frenado.",
    "tormenta": "Tormenta eléctrica: evita zonas inundables y considera detener la unidad.",
    "niebla": "Visibilidad reducida: luces bajas/antiniebla y velocidad moderada.",
    "nieve": "Riesgo de hielo: usa cadenas/llantas adecuadas y conduce con extrema cautela.",
}

# ------------------------------------------------------------------ SUS ----
SUS_PREGUNTAS = [
    "Creo que me gustaría usar este sistema con frecuencia.",
    "Encontré el sistema innecesariamente complejo.",
    "Pensé que el sistema era fácil de usar.",
    "Creo que necesitaría el apoyo de un técnico para usar este sistema.",
    "Encontré que las diversas funciones estaban bien integradas.",
    "Pensé que había demasiada inconsistencia en este sistema.",
    "Imagino que la mayoría de las personas aprendería a usarlo rápidamente.",
    "Encontré el sistema muy incómodo de usar.",
    "Me sentí muy seguro/a usando el sistema.",
    "Necesité aprender muchas cosas antes de poder usar el sistema.",
]


def calcular_sus(resp: list) -> float:
    """SUS: impares aportan (r-1), pares (5-r); suma x 2.5 -> 0..100."""
    if len(resp) != 10 or any(not 1 <= r <= 5 for r in resp):
        raise ValueError("Se requieren 10 respuestas entre 1 y 5.")
    total = sum((r - 1) if i % 2 == 0 else (5 - r) for i, r in enumerate(resp))
    return total * 2.5


def clasificar_sus(p: float) -> str:
    if p >= 85:
        return "Excelente (A)"
    if p >= 72:
        return "Buena (B)"
    if p >= 68:
        return "Aceptable, sobre el promedio (C)"
    if p >= 51:
        return "Pobre (D)"
    return "Inaceptable (F)"


def cargar_sus() -> list:
    try:
        with open(SUS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def guardar_sus(participante: str, resp: list) -> float:
    puntaje = calcular_sus(resp)
    datos = cargar_sus()
    datos.append({"participante": participante or "Anónimo",
                  "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                  "respuestas": resp, "puntaje": puntaje})
    with open(SUS_PATH, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    return puntaje
