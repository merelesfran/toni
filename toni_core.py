VERSION = "3.5"
"""
TONI v3.5
- Dos oídos: Vosk rápido por defecto, Whisper de respaldo + 🎤.
- Beeps dinámicos (sube=ok, baja=error).
- Control multimedia (play/pausa/siguiente/anterior).
- Puerta de ruido liviana (sin dependencias).
- OCR de pantalla (inerte si no está instalado Tesseract).
"""
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import subprocess
import time
import threading
import pyautogui
import json
import winsound
import win32gui
import win32con
import winreg
import sys
import os
import re
import random
import array
import wave
import webbrowser
import unicodedata
import traceback
import ctypes
import ctypes.wintypes as wintypes
from collections import deque
from urllib.parse import quote_plus
from pathlib import Path
from datetime import datetime, date

if getattr(sys, "frozen", False):
    BASE = Path(sys.executable).parent
    RESOURCE = Path(sys._MEIPASS)
else:
    BASE = Path(__file__).parent
    RESOURCE = BASE

SCAN = BASE / "apps_scan.json"

# ============================================================
# WHISPER
# ============================================================
WHISPER_EXE = RESOURCE / "whisper-cli.exe"

def _elegir_modelo():
    for carpeta in (BASE, RESOURCE):
        med = carpeta / "ggml-medium.bin"
        if med.exists():
            return med
    for carpeta in (BASE, RESOURCE):
        sm = carpeta / "ggml-small.bin"
        if sm.exists():
            return sm
    return RESOURCE / "ggml-small.bin"

WHISPER_MODEL = _elegir_modelo()
WHISPER_OK = WHISPER_EXE.exists() and WHISPER_MODEL.exists()

WHISPER_PROMPT = ("Toni, abre YouTube. Que hora es. Que dia es. Recuerdame la pastilla. "
                  "Sube el volumen. Ponme cumbia. Busca Los Redondos. Busca Vilma Palma. "
                  "Yamila. Netflix. Spotify. WhatsApp. Facebook. El dolar. Noticias. Buenos dias.")

BLOQUES_BUFFER = 16
SILENCIO_BLOQUES = 10
MAX_BLOQUES = 70

model = Model(str(RESOURCE / "vosk-model-small-es-0.42"))
rec = KaldiRecognizer(model, 16000)
q = queue.Queue()

usuario = os.getlogin()

CREATE_NO_WINDOW = 0x08000000

URL_CLIMA = "https://www.google.com/search?q=clima"
URL_CLIMA_EXTENDIDO = "https://www.google.com/search?q=clima+extendido"
URL_GOOGLE = "https://www.google.com"

WAKE_WORDS = ["toni", "tony", "tomy", "tomi", "tonny", "toney", "doni", "tonin"]

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DIAS_KEYS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

URL_UPDATE = "https://raw.githubusercontent.com/SmokeyBlues28/toni/main/version.txt"

NUM_PALABRA = {"una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
               "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
               "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
               "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
               "veinte": 20, "veintiuna": 21, "veintiuno": 21, "veintidos": 22, "veintitres": 23}

def palabras_a_numeros(t):
    for p, n in NUM_PALABRA.items():
        t = re.sub(rf'\b{p}\b', str(n), t)
    return t

CORRECCIONES_BASE = {
    "shamila": "yamila", "iamila": "yamila",
    "iphone": "poneme", "ipone": "poneme",
    "búscalo": "busca los", "buscalo": "busca los",
    "rico horas": "de ricota", "redondos rico": "redondos de ricota",
    "es chuto": "youtube", "buka": "busca", "bilma": "vilma", "y que os": "quien sos",
}

def cargar_correcciones():
    d = dict(CORRECCIONES_BASE)
    p = BASE / "correcciones.json"
    if p.exists():
        try:
            d.update(json.load(open(p, encoding="utf-8")))
        except Exception:
            pass
    return d

CORRECCIONES = cargar_correcciones()

IDENTIDAD_TRIGGERS = ["quien sos", "quien sus", "quien soso", "quien soz", "que sos vos", "que sus vos", "que soso vos", "que soz", "como te llamas", "quien eres", "que eres", "quien eras", "que eras", "cual es tu nombre", "quien es usted", "que es usted", "hablame de vos", "hablame de ti", "que podes hacer", "que puedes hacer", "que sabes hacer"]

CHARLA_IDENTIDAD = ("Soy Toni, tu asistente de voz personal. Nací para hacerte la vida más fácil: "
                    "te abro la música, la tele, el diario y las noticias, te recuerdo las pastillas "
                    "y te hago compañía cuando quieres charlar. Me creó Frahn, un desarrollador "
                    "entrerriano que cree que la tecnología tiene que escucharte a ti, y no al revés.")

SORPRESAS = [
    ("una receta rica", "https://www.google.com/search?q=recetas+faciles+y+ricas"),
    ("un video interesante", "https://www.youtube.com/feed/trending"),
    ("música linda", "https://www.youtube.com/results?search_query=musica+para+relajarse"),
    ("un chiste", "https://www.google.com/search?q=chistes+cortos+y+graciosos"),
    ("fotos de paisajes", "https://www.google.com/search?q=paisajes+hermosos&tbm=isch"),
    ("noticias de hoy", "https://news.google.com"),
]

NOMBRES_APP_CONOCIDAS = [
    "excel", "word", "powerpoint", "outlook", "access",
    "discord", "steam", "epic", "obs",
    "tiktok", "roblox", "minecraft", "vlc",
]

SERVICIOS_MUSICA = {
    "spotify": "https://open.spotify.com",
    "tidal": "https://tidal.com",
    "apple music": "https://music.apple.com",
    "youtube music": "https://music.youtube.com",
    "deezer": "https://www.deezer.com",
}
SERVICIOS_VIDEO = {
    "netflix": "https://www.netflix.com",
    "disney plus": "https://www.disneyplus.com",
    "disney": "https://www.disneyplus.com",
    "prime video": "https://www.primevideo.com",
    "max": "https://www.max.com",
    "youtube": "https://www.youtube.com",
}
SERVICIOS_TODOS = {**SERVICIOS_MUSICA, **SERVICIOS_VIDEO}

APPS_UWP = {
    "calculadora": "Microsoft.WindowsCalculator",
    "alarmas": "Microsoft.WindowsAlarms",
    "reloj": "Microsoft.WindowsAlarms",
    "fotos": "Microsoft.Windows.Photos",
    "galeria": "Microsoft.Windows.Photos",
    "correo": "microsoft.windowscommunicationsapps",
    "calendario uwp": "microsoft.windowscommunicationsapps",
    "mapas": "Microsoft.WindowsMaps",
    "clima": "Microsoft.BingWeather",
    "noticias": "Microsoft.BingNews",
    "tiktok": "TikTok.TikTok",
    "instagram": "Facebook.InstagramBeta",
    "whatsapp": "WhatsApp.WhatsappDesktop",
    "netflix": "Netflix.Netflix",
    "prime video": "AmazonVideo.PrimeVideo",
    "spotify": "Spotify.Spotify",
    "hulu": "Hulu.Hulu",
}

# ============================================================
# CONFIG PERSISTENTE
# ============================================================
VOZ_ACTIVA = False
DEVICE_ID = None
STARTUP = False
LETRA_GRANDE = False
NOMBRE_USUARIO = ""
MUSICA_PREF = "spotify"
VIDEO_PREF = "netflix"
MUTE_MIC = False
HOTKEY_MUTE = "ctrl+alt+m"
HOTKEY_HABLAR = "ctrl+alt+h"
CONFIG_PATH = BASE / "toni_config.json"

def cargar_config():
    global VOZ_ACTIVA, DEVICE_ID, STARTUP, LETRA_GRANDE, NOMBRE_USUARIO, MUSICA_PREF, VIDEO_PREF, MUTE_MIC, HOTKEY_MUTE, HOTKEY_HABLAR
    if CONFIG_PATH.exists():
        try:
            c = json.load(open(CONFIG_PATH, encoding="utf-8"))
            VOZ_ACTIVA = c.get("voz", False)
            DEVICE_ID = c.get("device", None)
            STARTUP = c.get("startup", False)
            LETRA_GRANDE = c.get("letra", False)
            NOMBRE_USUARIO = c.get("nombre", "")
            MUSICA_PREF = c.get("musica_pref", "spotify")
            VIDEO_PREF = c.get("video_pref", "netflix")
            MUTE_MIC = c.get("mute", False)
            HOTKEY_MUTE = c.get("tecla_mute", "ctrl+alt+m")
            HOTKEY_HABLAR = c.get("tecla_hablar", "ctrl+alt+h")
        except Exception:
            pass

def guardar_config(**kw):
    c = {}
    if CONFIG_PATH.exists():
        try:
            c = json.load(open(CONFIG_PATH, encoding="utf-8"))
        except Exception:
            pass
    c.update(kw)
    json.dump(c, open(CONFIG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

cargar_config()

hook_accion = []
hook_voz = []
hook_ayuda = []

NIVEL_MIC = 0
HABLAR_AHORA = [False]

def pedir_hablar_ahora():
    if MUTE_MIC:
        notificar("[AVISO] El micrófono está muteado")
        hablar("El micrófono está silenciado")
        return
    HABLAR_AHORA[0] = True

def toggle_mute_mic():
    global MUTE_MIC
    MUTE_MIC = not MUTE_MIC
    guardar_config(mute=MUTE_MIC)
    estado = "silenciado" if MUTE_MIC else "activado"
    notificar(f"[MIC] Micrófono {estado}")
    hablar(f"Micrófono {estado}")

# ============================================================
# ATAJOS GLOBALES
# ============================================================
MOD_ALT, MOD_CTRL, MOD_SHIFT, MOD_WIN = 1, 2, 4, 8
WM_HOTKEY = 0x0312

def _vk_de_token(tok):
    tok = tok.upper()
    if len(tok) == 1 and tok.isalpha():
        return ord(tok)
    if tok.startswith("F") and tok[1:].isdigit():
        return 0x70 + int(tok[1:]) - 1
    if tok == "SPACE": return 0x20
    if tok == "TAB": return 0x09
    if tok == "ENTER": return 0x0D
    if tok == "ESC": return 0x1B
    if tok.isdigit(): return ord(tok)
    return 0

def _parse_combo(combo):
    mods, vk = 0, 0
    for part in combo.lower().split("+"):
        part = part.strip()
        if part == "ctrl": mods |= MOD_CTRL
        elif part == "alt": mods |= MOD_ALT
        elif part == "shift": mods |= MOD_SHIFT
        elif part == "win": mods |= MOD_WIN
        else: vk = _vk_de_token(part)
    return mods, vk

def loop_hotkeys():
    try:
        mods_m, vk_m = _parse_combo(HOTKEY_MUTE)
        mods_h, vk_h = _parse_combo(HOTKEY_HABLAR)
        ok1 = ctypes.windll.user32.RegisterHotKey(None, 1, mods_m, vk_m)
        ok2 = ctypes.windll.user32.RegisterHotKey(None, 2, mods_h, vk_h)
        if not (ok1 and ok2):
            print("[HOTKEY] Atajo en uso por otro programa, desactivado")
            return
        msg = wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY:
                if msg.wParam == 1:
                    toggle_mute_mic()
                elif msg.wParam == 2:
                    pedir_hablar_ahora()
    except Exception as e:
        print(f"[HOTKEY] Error: {e}")

threading.Thread(target=loop_hotkeys, daemon=True).start()

# ============================================================
# RECORDATORIOS RECURRENTES
# ============================================================
RECORDATORIOS_PATH = BASE / "recordatorios.json"

def cargar_recordatorios():
    if RECORDATORIOS_PATH.exists():
        try:
            return json.load(open(RECORDATORIOS_PATH, encoding="utf-8"))
        except Exception:
            return []
    return []

def guardar_recordatorios(lista):
    json.dump(lista, open(RECORDATORIOS_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

def disparar_recordatorio(r, hoy):
    winsound.Beep(1500, 300); time.sleep(0.2); winsound.Beep(1500, 300)
    notificar(f"[RECORDATORIO] {r['mensaje']}")
    hablar(f"Recordatorio: {r['mensaje']}")
    r["last_fired_day"] = hoy.isoformat()
    lista = cargar_recordatorios()
    for i, x in enumerate(lista):
        if x.get("mensaje") == r["mensaje"] and x.get("hora") == r.get("hora"):
            lista[i] = r
            break
    guardar_recordatorios(lista)

def loop_recordatorios_recurrentes():
    time.sleep(15)
    while True:
        try:
            now = datetime.now()
            hoy = now.date()
            for r in cargar_recordatorios():
                if r.get("tipo") not in ("diario", "semanal"):
                    continue
                if r.get("last_fired_day") == hoy.isoformat():
                    continue
                if now.hour != r.get("hora") or now.minute != r.get("minuto"):
                    continue
                if r["tipo"] == "diario":
                    disparar_recordatorio(r, hoy)
                elif r["tipo"] == "semanal":
                    if now.weekday() in r.get("dias", []):
                        disparar_recordatorio(r, hoy)
        except Exception as e:
            print(f"[RECORDATORIO] Error loop: {e}")
        time.sleep(30)

threading.Thread(target=loop_recordatorios_recurrentes, daemon=True).start()

def agregar_recordatorio_recurrente(tipo, mensaje, hora, minuto, dias=None):
    lista = cargar_recordatorios()
    entry = {
        "tipo": tipo,
        "mensaje": mensaje,
        "hora": hora,
        "minuto": minuto,
        "dias": dias or [],
        "last_fired_day": None,
    }
    lista.append(entry)
    guardar_recordatorios(lista)
    return entry

# ============================================================
# ONBOARDING
# ============================================================
def onboarding_si_corresponde():
    c = {}
    if CONFIG_PATH.exists():
        try:
            c = json.load(open(CONFIG_PATH, encoding="utf-8"))
        except Exception:
            pass
    if c.get("onboarding_done"):
        return
    def _onboard():
        time.sleep(4)
        hablar("Hola, soy Toni. Estoy para ayudarte.")
        notificar("[ONBOARDING] Bienvenida")
        time.sleep(3)
        hablar("Prueba decirme, por ejemplo, Toni abre YouTube, o Toni qué hora es. Dime también cómo te llamas para que te conozca.")
        time.sleep(6)
        for fn in hook_ayuda:
            try:
                fn()
            except Exception:
                pass
        guardar_config(onboarding_done=True)
    threading.Thread(target=_onboard, daemon=True).start()

threading.Thread(target=onboarding_si_corresponde, daemon=True).start()

# ============================================================
# FILTROS Y CONFIG DE APPS
# ============================================================
BASURA = [
    "unins", "setup", "install", "uninstall", "update", "updater", "helper",
    "crash", "service", "agent", "loader", "driver", "redist", "bootstrap",
    "elevat", "tray", "daemon", "background", "reporter", "monitor", "watcher",
    "checker", "converter", "transcoder", "renderer", "dumper", "collector",
    "sync", "proxy", "bridge", "configurator", "migrator", "activator",
    "applicator", "bstrace", "hypervisor", "cookie_exporter", "ie_to_edge",
    "copilot_setup", "webview2", "vcredist", "msiexec", "7z", "rg.exe",
    "tgrep", "openconsole", "vsce-sign", "code-tunnel", "nmakehlp", "cffi-gen",
    "pythonwin", "pythonservice", "idle.bat", "node.cmd", "pwsh", "t32.exe",
    "appverif", "appcert", "javacpl", "setlang", "appvlp", "softmanager",
    "multiinstance", "bugreport", "createdump", "sql", "twain", "tesseract",
    "gswin", "eps2eps", "fix-qdf", "tabtip", "pipanel", "msinfo32", "wab.exe",
    "imagingdevices", "setup_wm", "extexport", "collectsynclogs", "onedrive.app",
    "configsecurity", "offlinescanner", "mpcmd", "aoeurl", "screenshare",
    "iosplugin", "smartconnect", "rfdrive", "intel_pie", "bthci", "vsto",
    "misc.exe", "accicons", "eqnedt", "writingassistant", "model3dtranscoder",
    "actionsserver", "ai.exe", "restartagent", "smarttag", "appsharing",
    "mashup", "capture.exe", "integrator.exe", "appvdll", "officeclicktorun",
    "clicktorun", "ghost", "telemetry", "consent", "notification",
]

WHITELIST_SYS = [
    "control.exe", "cmd.exe", "taskmgr.exe", "regedit.exe", "cleanmgr.exe",
    "dfrgui.exe", "msconfig.exe", "perfmon.exe", "magnify.exe", "narrator.exe",
    "osk.exe", "livecaptions.exe", "voiceaccess.exe", "powershell.exe",
]

APPS_VIRTUALES = [
    {"nombre": "YouTube", "tipo": "url", "ruta": "https://www.youtube.com",
     "alias": ["youtube", "yutub", "yutu", "iutub", "yutube", "utub", "youtub", "tubu", "yutubee"], "cierre": "youtube"},
    {"nombre": "Facebook", "tipo": "url", "ruta": "https://www.facebook.com",
     "alias": ["facebook", "feijoo", "feijo", "feisbuk", "feisbuc", "feis", "feibu", "face", "facebu"], "cierre": "facebook"},
    {"nombre": "Instagram", "tipo": "url", "ruta": "https://www.instagram.com",
     "alias": ["instagram", "insta", "instagran", "instagra", "insta grama"], "cierre": "instagram"},
    {"nombre": "Netflix", "tipo": "url", "ruta": "https://www.netflix.com",
     "alias": ["netflix", "netfli", "netflis", "nefli", "neflis", "neflix", "netfliz"], "cierre": "netflix"},
    {"nombre": "Disney Plus", "tipo": "url", "ruta": "https://www.disneyplus.com",
     "alias": ["disney", "disnei", "disne", "disney plus", "disney mas", "disneplus"], "cierre": "disney"},
    {"nombre": "Prime Video", "tipo": "url", "ruta": "https://www.primevideo.com",
     "alias": ["prime", "prime video", "amazon", "amason", "praime", "praim"], "cierre": "prime video"},
    {"nombre": "Max", "tipo": "url", "ruta": "https://www.max.com",
     "alias": ["max", "hbo", "ache be o", "max video"], "cierre": "max"},
    {"nombre": "Flow", "tipo": "url", "ruta": "https://www.flow.com.ar",
     "alias": ["flow", "flou", "flao"], "cierre": "flow"},
    {"nombre": "WhatsApp Web", "tipo": "url", "ruta": "https://web.whatsapp.com",
     "alias": ["whatsapp", "wasa", "guasap", "wasap", "guasa", "wsp", "whasap", "wasapea", "guasapea", "wasapear"], "cierre": "whatsapp"},
    {"nombre": "Google", "tipo": "url", "ruta": URL_GOOGLE,
     "alias": ["google", "gugle", "guguel"], "cierre": "google"},
    {"nombre": "Correo", "tipo": "url", "ruta": "https://mail.google.com",
     "alias": ["correo", "el correo", "mail", "gmail", "casilla", "casilla de correo"], "cierre": "gmail"},
    {"nombre": "Calendario", "tipo": "url", "ruta": "https://calendar.google.com",
     "alias": ["calendario", "el calendario", "calendario de google"], "cierre": "calendar"},
    {"nombre": "Noticias", "tipo": "url", "ruta": "https://news.google.com",
     "alias": ["noticias", "las noticias", "noticiero", "el noticiero"], "cierre": "noticias"},
    {"nombre": "Dolar", "tipo": "url", "ruta": "https://www.dolarhoy.com",
     "alias": ["dolar", "dolar hoy", "el dolar", "a cuanto esta el dolar", "precio del dolar", "dolar blue"], "cierre": "dolar"},
    {"nombre": "Clima", "tipo": "url", "ruta": URL_CLIMA,
     "alias": ["clima", "tiempo", "temperatura", "llueve", "llover", "calor", "frio"], "cierre": "clima"},
    {"nombre": "Clima Extendido", "tipo": "url", "ruta": URL_CLIMA_EXTENDIDO,
     "alias": ["clima extendido", "extendido", "pronostico", "pronostico extendido", "clima de la semana", "clima semana"], "cierre": "clima"},
    {"nombre": "Clarin", "tipo": "url", "ruta": "https://www.clarin.com",
     "alias": ["clarin", "el clarin", "diario clarin"], "cierre": "clarin"},
    {"nombre": "La Nacion", "tipo": "url", "ruta": "https://www.lanacion.com.ar",
     "alias": ["la nacion", "nacion", "lanacion"], "cierre": "lanacion"},
    {"nombre": "Infobae", "tipo": "url", "ruta": "https://www.infobae.com",
     "alias": ["infobae", "info bae"], "cierre": "infobae"},
    {"nombre": "TN", "tipo": "url", "ruta": "https://www.tn.com.ar",
     "alias": ["te ene", "todo noticias"], "cierre": "tn"},
    {"nombre": "Pagina 12", "tipo": "url", "ruta": "https://www.pagina12.com.ar",
     "alias": ["pagina 12", "pagina doce"], "cierre": "pagina"},
    {"nombre": "Cumbia", "tipo": "url",
     "ruta": "https://www.youtube.com/results?search_query=cumbia+santafesina+en+vivo",
     "alias": ["cumbia", "cumbia santafesina", "cumbia villera", "poner cumbia", "poneme cumbia", "ponerme cumbia", "pon cumbia"],
     "cierre": "cumbia"},
    {"nombre": "Tango", "tipo": "url",
     "ruta": "https://www.youtube.com/results?search_query=tango+argentino+en+vivo",
     "alias": ["tango", "poner tango", "poneme tango", "ponerme tango", "pon tango"],
     "cierre": "tango"},
    {"nombre": "Folklore", "tipo": "url",
     "ruta": "https://www.youtube.com/results?search_query=folklore+argentino+en+vivo",
     "alias": ["folklore", "folclore", "poner folklore", "poneme folklore", "ponerme folklore", "zamba", "chacarera"],
     "cierre": "folklore"},
    {"nombre": "Rock Nacional", "tipo": "url",
     "ruta": "https://www.youtube.com/results?search_query=rock+nacional+argentino+en+vivo",
     "alias": ["rock nacional", "rock argentino", "poner rock", "poneme rock", "ponerme rock"],
     "cierre": "rock"},
    {"nombre": "Radio", "tipo": "url",
     "ruta": "https://www.youtube.com/results?search_query=radio+en+vivo+argentina",
     "alias": ["radio", "la radio", "poner la radio", "poneme la radio", "ponerme la radio"],
     "cierre": "radio"},
    {"nombre": "ChatGPT", "tipo": "url", "ruta": "https://chatgpt.com",
     "alias": ["chatgpt", "chat gpt", "chagpt", "chacgpt", "chaptgpt", "chat gp", "chat g p t"], "cierre": "chatgpt"},
    {"nombre": "Gemini", "tipo": "url", "ruta": "https://gemini.google.com",
     "alias": ["gemini", "gemine", "geminy", "yemini", "geminni", "geminis", "gemini google"], "cierre": "gemini"},
    {"nombre": "Claude", "tipo": "url", "ruta": "https://claude.ai",
     "alias": ["claude", "claudia", "claudio", "clode", "claud", "cloud", "claude ai", "clau"], "cierre": "claude"},
    {"nombre": "Copilot", "tipo": "url", "ruta": "https://copilot.microsoft.com",
     "alias": ["copilot", "copiloto", "copilo", "copilot microsoft"], "cierre": "copilot"},
    {"nombre": "DeepSeek", "tipo": "url", "ruta": "https://chat.deepseek.com",
     "alias": ["deepseek", "deep seek", "dipseek", "dipsik", "dip sik"], "cierre": "deepseek"},
    {"nombre": "Grok", "tipo": "url", "ruta": "https://grok.com",
     "alias": ["grok", "groc", "groq"], "cierre": "grok"},
    {"nombre": "Mistral", "tipo": "url", "ruta": "https://chat.mistral.ai",
     "alias": ["mistral", "mistrall", "le chat", "lechat", "mistral ai"], "cierre": "mistral"},
    {"nombre": "Perplexity", "tipo": "url", "ruta": "https://www.perplexity.ai",
     "alias": ["perplexity", "perplexiti", "perplexy", "perplexity ai"], "cierre": "perplexity"},
    {"nombre": "Qwen Web", "tipo": "url", "ruta": "https://chat.qwen.ai/",
     "alias": ["qwen web", "qwen studio", "cuen web", "quen web", "ia web"], "cierre": "qwen studio"},
    {"nombre": "NotebookLM", "tipo": "url", "ruta": "https://notebooklm.google.com/",
     "alias": ["notebook", "notebooklm"], "cierre": "notebook"},
]

SITIOS_RUTINARIOS = {
    "gmail": "https://mail.google.com",
    "correo": "https://mail.google.com",
    "mail": "https://mail.google.com",
    "yahoo": "https://www.yahoo.com",
    "hotmail": "https://outlook.live.com",
    "outlook": "https://outlook.live.com",
    "mercadolibre": "https://www.mercadolibre.com.ar",
    "mercado libre": "https://www.mercadolibre.com.ar",
    "maps": "https://maps.google.com",
    "mapa": "https://maps.google.com",
    "mapas": "https://maps.google.com",
    "traductor": "https://translate.google.com",
    "traducir": "https://translate.google.com",
    "wikipedia": "https://es.wikipedia.org",
    "calendario": "https://calendar.google.com",
    "drive": "https://drive.google.com",
    "fotos": "https://photos.google.com",
}

FONETICAS = {
    "brave": ["brady", "braid", "brav", "brabe", "breiv", "navegador", "browser", "internet", "buscador", "buscadores"],
    "chrome": ["crom", "crome", "google", "cromo", "navegador", "browser", "internet", "buscador", "buscadores"],
    "edge": ["edye", "eje", "microsoft edge", "navegador", "browser", "internet", "buscador", "buscadores"],
    "firefox": ["fayerfocs", "fayerfox", "faerfox", "navegador", "browser", "internet", "buscador", "buscadores"],
    "opera": ["opera", "navegador", "browser", "internet", "buscador", "buscadores"],
    "discord": ["discor", "disco"],
    "tidal": ["musica", "music", "musi", "canciones", "cancion", "melodia", "musiquita", "temas", "tema"],
    "qwen": ["cuen", "quen", "ia"],
    "obs": ["obes", "o be ese", "grabador"],
    "steam": ["stim", "esteam", "sting", "es tim", "estim", "stean", "steim"],
    "vlc": ["velece"],
    "bluestacks": ["blu", "blue", "blustacks"],
    "word": ["guord", "ward", "war", "wall", "wholr", "uord", "guor"],
    "excel": ["exel", "eksel", "eqsel", "exsel", "hoja de calculo", "hojas de calculo", "planilla", "planillas"],
    "winrar": ["rar", "uin rar"],
    "pdf24": ["pdf", "pe de efe"],
    "gpu": ["ge pe u"],
    "cpu-z": ["cpu", "ce pe u", "si pi u"],
    "afterburner": ["after"],
    "kdenlive": ["kden", "kadenlive"],
    "capcut": ["cap cut"],
    "roblox": ["roblo"],
    "epic": ["epik"],
    "tiktok": ["tic toc", "tik tok", "tic tok", "tikto"],
    "tikfinity": ["tic finiti"],
    "code": ["vscode", "ve ese code"],
}

APPS_BLUESTACKS = {
    "magis": ["magis", "maguis", "magiz", "mashis"],
    "xuper": ["xuper", "chuper", "yuper"],
}

# ============================================================
# UTILIDADES
# ============================================================
def normalizar(t):
    t = t.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')

def es_basura(nombre_exe):
    n = nombre_exe.lower()
    return any(p in n for p in BASURA)

def es_sistema_ruta(ruta):
    r = ruta.lower()
    return ("system32" in r or "syswow64" in r)

def nombre_amigable(app):
    acceso = app.get("acceso", "")
    if acceso:
        stem = Path(acceso).stem
        stem = stem.replace(" - Acceso directo", "").strip()
        if stem.lower().startswith(("uninstall", "desinstalar")):
            return None
        return stem
    return app.get("display_name") or Path(app.get("ruta", "")).stem

def notificar(msg):
    print(f"  {msg}")
    for fn in hook_accion:
        try:
            fn(msg)
        except Exception:
            pass

def hablar(texto):
    if not VOZ_ACTIVA:
        return
    def _h():
        try:
            import pyttsx3
            e = pyttsx3.init()
            e.setProperty('rate', 160)
            e.say(texto)
            e.runAndWait()
        except Exception:
            pass
    threading.Thread(target=_h, daemon=True).start()

def abrir_sitio_o_buscar(consulta):
    q2 = normalizar(consulta)
    for k, url in SITIOS_RUTINARIOS.items():
        if k in q2:
            abrir_url(url)
            return
    for app_conocida in NOMBRES_APP_CONOCIDAS:
        if app_conocida in q2:
            notificar(f"[AVISO] {consulta.capitalize()} no está instalada")
            hablar(f"{consulta.capitalize()} no está instalada en esta computadora")
            beep_error()
            return
    palabras = q2.split()
    if len(palabras) == 1 and palabras[0].isalnum():
        abrir_url("https://www.google.com/search?q=" + quote_plus(palabras[0]))
        return
    abrir_url("https://www.google.com/search?q=" + quote_plus(consulta))

def abrir_servicio(nombre, url_fallback):
    clave = normalizar(nombre)
    for e in REGISTRO:
        if e["tipo"] == "app" and (clave in normalizar(e["nombre"]) or normalizar(e["nombre"]) in clave):
            try:
                subprocess.Popen(e["ruta"])
                notificar(f"[ABRIR] {e['nombre']} (app instalada)")
                return
            except Exception:
                pass
    abrir_url(url_fallback)
    notificar(f"[ABRIR] {nombre.capitalize()} (web)")

# ============================================================
# RECORDATORIOS (una vez + recurrentes)
# ============================================================
RECORD_TRIGGERS = ["recordame", "recorda", "acordate", "recordatorio",
                   "recuerdame", "recuerda", "recordarme", "recuerdame a"]

def procesar_recordatorio(texto_n):
    es_recurrente = (
        "todos los dias" in texto_n or "todos los días" in texto_n
        or "todos los dias a" in texto_n
        or any(d in texto_n for d in DIAS_KEYS)
        or "lunes a viernes" in texto_n
    )

    if not any(k in texto_n for k in RECORD_TRIGGERS) and not es_recurrente:
        return False

    mensaje = texto_n
    for k in RECORD_TRIGGERS:
        mensaje = mensaje.replace(k, ' ')
    mensaje = re.sub(r'todos? los dias?', ' ', mensaje)
    mensaje = re.sub(r'lunes a viernes', ' ', mensaje)

    dias_detectados = []
    for i, dia in enumerate(DIAS_KEYS):
        if dia in mensaje:
            dias_detectados.append(i)
            mensaje = re.sub(dia, ' ', mensaje)
    if not dias_detectados and "todos" in texto_n:
        tipo = "diario"
    elif dias_detectados:
        tipo = "semanal"
    else:
        tipo = None

    mensaje = palabras_a_numeros(mensaje)

    delay = None
    hora = None
    minuto = None
    m = re.search(r'(?:a las|a la|alas)\s*(\d{1,2})(?:\s*y\s*(media|\d{1,2}))?', mensaje)
    if m:
        hora = int(m.group(1))
        seg = m.group(2)
        minuto = 30 if seg == "media" else int(seg or 0)
        mensaje = re.sub(r'(?:a las|a la|alas)\s*\d{1,2}(\s*y\s*(media|\d{1,2}))?', ' ', mensaje)

    mensaje = re.sub(r'\s+', ' ', mensaje).strip()
    if not mensaje:
        mensaje = "tu recordatorio"

    if tipo == "diario" and hora is not None:
        agregar_recordatorio_recurrente("diario", mensaje, hora, minuto)
        notificar(f"[RECORDATORIO DIARIO] {mensaje} a las {hora}:{minuto:02d}")
        hablar(f"Listo, todos los días a las {hora} te recuerdo: {mensaje}")
        return True
    if tipo == "semanal" and hora is not None and dias_detectados:
        agregar_recordatorio_recurrente("semanal", mensaje, hora, minuto, dias=dias_detectados)
        nombres_dias = ", ".join(DIAS[d] for d in dias_detectados)
        notificar(f"[RECORDATORIO SEMANAL] {mensaje} ({nombres_dias}) a las {hora}:{minuto:02d}")
        hablar(f"Listo, {nombres_dias} a las {hora} te recuerdo: {mensaje}")
        return True

    if not any(k in texto_n for k in RECORD_TRIGGERS):
        return False
    if hora is not None:
        now = datetime.now()
        target = now.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        delay = (target - now).total_seconds()
        if delay <= 0:
            delay += 24 * 3600
    else:
        m2 = re.search(r'en (\d+) (horas|hora|minutos|minuto)', mensaje)
        if m2:
            n = int(m2.group(1))
            delay = n * (3600 if 'hor' in m2.group(2) else 60)
            mensaje = re.sub(r'en \d+ (horas|hora|minutos|minuto)', ' ', mensaje)
    mensaje = re.sub(r'\s+', ' ', mensaje).strip()
    if not mensaje:
        mensaje = "tu recordatorio"
    if delay is None:
        notificar("[RECORDATORIO] Falta la hora")
        hablar("Dime a qué hora, o en cuánto tiempo")
        return True
    def fuego():
        time.sleep(delay)
        winsound.Beep(1500, 300); time.sleep(0.2); winsound.Beep(1500, 300)
        notificar(f"[RECORDATORIO] {mensaje}")
        hablar(f"Recordatorio: {mensaje}")
    threading.Thread(target=fuego, daemon=True).start()
    notificar(f"[RECORDATORIO] Programado: {mensaje}")
    hablar(f"Listo, te recuerdo: {mensaje}")
    return True

# ============================================================
# AUTO-UPDATE
# ============================================================
UPDATE_STATE_PATH = BASE / "toni_update_state.json"

def _update_bloqueado(remota):
    try:
        if UPDATE_STATE_PATH.exists():
            d = json.load(open(UPDATE_STATE_PATH, encoding="utf-8"))
            if d.get("version") == remota and time.time() - d.get("ts", 0) < 3600:
                return True
    except Exception:
        pass
    return False

def _marcar_update(remota):
    try:
        json.dump({"version": remota, "ts": time.time()},
                  open(UPDATE_STATE_PATH, "w", encoding="utf-8"))
    except Exception:
        pass

def chequear_update():
    if not URL_UPDATE:
        return
    time.sleep(10)
    while True:
        try:
            import urllib.request
            with urllib.request.urlopen(URL_UPDATE, timeout=10) as r:
                lineas = r.read().decode().strip().splitlines()
            remota = lineas[0].strip()
            url_exe = lineas[1].strip() if len(lineas) > 1 else ""
            sha = lineas[2].strip() if len(lineas) > 2 else ""
            if remota and remota != VERSION and url_exe:
                if _update_bloqueado(remota):
                    print(f"[UPDATE] {remota} ya intentada hace menos de 1h, espero al próximo ciclo")
                    time.sleep(6 * 3600)
                    continue
                notificar(f"[UPDATE] Versión {remota} disponible. Actualizando...")
                hablar("Voy a actualizarme solo. Puede tardar unos minutos, vuelvo enseguida.")
                _marcar_update(remota)
                auto_update(url_exe, sha)
                return
        except Exception as e:
            print(f"[UPDATE] check falló: {e}")
        time.sleep(6 * 3600)

def auto_update(url_exe, sha):
    try:
        import urllib.request
        import hashlib
        tmp = Path(os.environ.get("TEMP", ".")) / "TONI-Setup-nuevo.exe"
        notificar("[UPDATE] Descargando instalador...")
        urllib.request.urlretrieve(url_exe, tmp)
        if tmp.stat().st_size < 20_000_000:
            notificar("[UPDATE] Archivo demasiado chico, cancelando")
            hablar("No pude verificar la actualización. Quedo como estoy.")
            return
        if sha:
            h = hashlib.sha256()
            with open(tmp, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            if h.hexdigest().lower() != sha.lower():
                notificar("[UPDATE] Hash no coincide, cancelando por seguridad")
                hablar("No pude verificar la actualización. Quedo como estoy.")
                return
        notificar("[UPDATE] Instalando...")
        subprocess.Popen([str(tmp), "/VERYSILENT", "/CLOSEAPPLICATIONS"])
        time.sleep(2)
        os._exit(0)
    except Exception as e:
        notificar(f"[UPDATE] Error: {e}")
        hablar("No pude actualizarme ahora. Lo intento más tarde.")

threading.Thread(target=chequear_update, daemon=True).start()

# ============================================================
# SCANNER EMBEBIDO
# ============================================================
try:
    import win32com.client
    WIN32COM = True
except Exception:
    WIN32COM = False

def _resolver_shortcut(ruta_lnk):
    if not WIN32COM:
        return None
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(ruta_lnk))
        target = shortcut.Targetpath
        if target and os.path.exists(target) and target.lower().endswith('.exe'):
            return target
    except Exception:
        pass
    return None

def _escanear_menu():
    apps = {}
    rutas_menu = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs"),
    ]
    for menu_root in rutas_menu:
        if not menu_root.exists():
            continue
        for lnk in menu_root.rglob("*.lnk"):
            exe = _resolver_shortcut(lnk)
            if exe and not es_basura(Path(exe).name):
                rel = lnk.relative_to(menu_root)
                categoria = str(rel.parent) if rel.parent != Path(".") else "General"
                apps.setdefault(categoria, []).append({
                    "nombre": Path(exe).name,
                    "ruta": exe,
                    "acceso": str(lnk),
                })
    return apps

def _escanear_registro_apps():
    apps = {}
    claves = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, ruta in claves:
        try:
            with winreg.OpenKey(hive, ruta) as key:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(key, i); i += 1
                        try:
                            with winreg.OpenKey(key, sub) as sk:
                                try:
                                    nombre = winreg.QueryValueEx(sk, "DisplayName")[0]
                                    ruta_inst = winreg.QueryValueEx(sk, "InstallLocation")[0]
                                    icono = ""
                                    try:
                                        icono = winreg.QueryValueEx(sk, "DisplayIcon")[0]
                                    except Exception:
                                        pass
                                    exe = None
                                    if icono and os.path.exists(icono.split(",")[0]):
                                        exe = icono.split(",")[0]
                                    elif ruta_inst and os.path.exists(ruta_inst):
                                        for archivo in Path(ruta_inst).rglob("*.exe"):
                                            if not es_basura(archivo.name) and nombre.lower().replace(" ", "") in archivo.name.lower():
                                                exe = str(archivo); break
                                    if exe and not es_basura(Path(exe).name):
                                        apps.setdefault("Registro", []).append({
                                            "nombre": Path(exe).name, "ruta": exe, "display_name": nombre})
                                except (FileNotFoundError, OSError):
                                    pass
                        except (FileNotFoundError, OSError):
                            pass
                    except OSError:
                        break
        except (FileNotFoundError, OSError):
            pass
    return apps

def escanear_sistema():
    menu = _escanear_menu()
    reg = _escanear_registro_apps()
    todas = {}
    vistas = set()
    for categoria, lista in {**menu, **reg}.items():
        for app in lista:
            rk = app["ruta"].lower()
            if rk not in vistas:
                vistas.add(rk)
                todas.setdefault(categoria, []).append(app)
    return todas

# ============================================================
# NAVEGADOR + ABRIR WEB
# ============================================================
def navegador_default():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as k:
            progid = winreg.QueryValueEx(k, "ProgId")[0]
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{progid}\shell\open\command") as k:
            cmd = winreg.QueryValueEx(k, None)[0]
        exe = cmd.split('"')[1] if '"' in cmd else cmd.split(' ')[0]
        if os.path.isfile(exe):
            return exe
    except Exception as e:
        print(f"  [WEB] Registro no usable: {e}")
    for c in [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
    ]:
        if os.path.isfile(c):
            return c
    return None

def abrir_url(url):
    exe = navegador_default()

    if exe:
        try:
            subprocess.Popen([exe, f"--app={url}"])
            notificar(f"[WEB] OK modo app ({Path(exe).name})")
            return
        except Exception as e:
            print(f"  [WEB] capa1 app falló: {e}")

    if exe:
        try:
            subprocess.Popen([exe, url])
            notificar(f"[WEB] OK pestaña ({Path(exe).name})")
            return
        except Exception as e:
            print(f"  [WEB] capa2 pestaña falló: {e}")

    try:
        os.startfile(url)
        notificar("[WEB] OK shell")
        return
    except Exception as e:
        print(f"  [WEB] capa3 shell falló: {e}")

    try:
        subprocess.Popen(f'start "" "{url}"', shell=True, creationflags=CREATE_NO_WINDOW)
        notificar("[WEB] OK cmd start")
        return
    except Exception as e:
        print(f"  [WEB] capa4 cmd falló: {e}")

    notificar("[WEB] No se pudo abrir con ninguna capa")

def cerrar_url(palabra):
    p = palabra.lower()
    script = (
        "Get-Process chrome, msedge, brave, firefox -ErrorAction SilentlyContinue | "
        f"Where-Object {{$_.MainWindowTitle -like '*{p}*'}} | "
        "Stop-Process -Force"
    )
    try:
        subprocess.run(
            ["powershell", "-Command", script],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        return True
    except Exception:
        pass
    cerradas = 0
    def cb(hwnd, _):
        nonlocal cerradas
        try:
            titulo = win32gui.GetWindowText(hwnd).lower()
            if win32gui.IsWindowVisible(hwnd) and p in titulo:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                cerradas += 1
        except Exception:
            pass
    win32gui.EnumWindows(cb, None)
    return cerradas

def cerrar_uwp(nombre_clave):
    nombre_clave = normalizar(nombre_clave)
    pkg = APPS_UWP.get(nombre_clave)
    if not pkg:
        return False
    script = (
        f"Get-AppxPackage *{pkg}* | "
        "ForEach-Object {{ Get-Process -Id (Get-Process -Name $_.Name -ErrorAction SilentlyContinue).Id -ErrorAction SilentlyContinue }} | "
        "Stop-Process -Force -ErrorAction SilentlyContinue; "
        f"$procs = Get-Process | Where-Object {{$_.ProcessName -like '*{nombre_clave}*'}}; "
        "if ($procs) {{ $procs | Stop-Process -Force }}"
    )
    try:
        subprocess.run(
            ["powershell", "-Command", script],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        return True
    except Exception:
        return False

def buscar_bluestacks():
    for e in REGISTRO:
        if e["tipo"] == "app" and "bluestacks" in normalizar(e["nombre"]) \
           and "hd-player" in normalizar(e["proceso"] or ""):
            return e["ruta"]
    p = r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"
    return p if os.path.isfile(p) else None

# ============================================================
# CONSTRUCCIÓN DEL REGISTRO
# ============================================================
def construir_registro():
    registro = []
    por_nombre = {}
    vistas = set()

    extra = {}
    p_extra = BASE / "alias_extra.json"
    if p_extra.exists():
        try:
            extra = json.load(open(p_extra, encoding="utf-8"))
        except Exception:
            pass

    scan = {}
    if SCAN.exists():
        try:
            with open(SCAN, "r", encoding="utf-8") as f:
                scan = json.load(f)
        except Exception:
            scan = {}
    else:
        print("⚠️ No existe apps_scan.json (se genera solo al primer arranque).")

    for categoria, apps in scan.items():
        for app in apps:
            app = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in app.items()}
            ruta = app.get("ruta", "")
            nombre_exe = app.get("nombre", "")

            if not ruta.lower().endswith(".exe"):
                continue
            if not os.path.isfile(ruta):
                continue
            if es_basura(nombre_exe):
                continue
            if es_sistema_ruta(ruta) and nombre_exe.lower() not in WHITELIST_SYS:
                continue
            if ruta.lower() in vistas:
                continue

            friendly = nombre_amigable(app)
            if not friendly:
                continue

            clave = normalizar(friendly)

            if clave in por_nombre:
                existente = por_nombre[clave]
                if "pake-" in existente["ruta"].lower() and "pake-" not in ruta.lower():
                    registro.remove(existente)
                else:
                    continue

            vistas.add(ruta.lower())

            alias = set()
            alias.add(clave)
            alias.add(normalizar(Path(ruta).stem))
            for word in clave.split():
                if len(word) >= 3:
                    alias.add(word)
            for k, v in FONETICAS.items():
                if clave == k or k in clave.split() or clave.startswith(k + " ") or clave.startswith(k + "-"):
                    alias.update(v)
            alias.update(extra.get(clave, []))

            entry = {
                "nombre": friendly,
                "ruta": ruta,
                "proceso": nombre_exe,
                "tipo": "app",
                "alias": list(alias),
            }
            por_nombre[clave] = entry
            registro.append(entry)

    for virt in APPS_VIRTUALES:
        alias = set(virt["alias"])
        alias.add(normalizar(virt["nombre"]))
        registro.append({
            "nombre": virt["nombre"],
            "ruta": virt["ruta"],
            "proceso": None,
            "tipo": "url",
            "alias": list(alias),
            "cierre": virt.get("cierre", normalizar(virt["nombre"])),
        })

    p_links = BASE / "links_extra.json"
    if p_links.exists():
        try:
            links = json.load(open(p_links, encoding="utf-8"))
            for lk in links:
                alias = set(lk.get("alias", []))
                alias.add(normalizar(lk["nombre"]))
                registro.append({
                    "nombre": lk["nombre"],
                    "ruta": lk["ruta"],
                    "proceso": None,
                    "tipo": "url",
                    "alias": list(alias),
                    "cierre": lk.get("cierre", normalizar(lk["nombre"])),
                })
        except Exception as e:
            print(f"⚠️ links_extra.json inválido: {e}")

    alias_virt = set()
    for e in registro:
        if e["tipo"] == "url":
            alias_virt.update(normalizar(a) for a in e["alias"])
    registro = [e for e in registro
                if not (e["tipo"] == "app"
                        and "pake" in e["ruta"].lower()
                        and normalizar(e["nombre"]) in alias_virt)]

    claves_apps = {normalizar(e["nombre"]) for e in registro}
    for e in registro:
        clave = normalizar(e["nombre"])
        e["alias"] = [a for a in e["alias"] if not (a in claves_apps and a != clave)]

    return registro

REGISTRO = construir_registro()

# ============================================================
# AUTO-SCAN
# ============================================================
def auto_scan():
    time.sleep(1 if not SCAN.exists() else 5)
    try:
        nuevo = escanear_sistema()
        actual = {}
        if SCAN.exists():
            try:
                actual = json.load(open(SCAN, encoding="utf-8"))
            except Exception:
                actual = {}
        if nuevo != actual:
            json.dump(nuevo, open(SCAN, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            REGISTRO[:] = construir_registro()
            notificar(f"[SCAN] Inventario actualizado: {len(REGISTRO)} apps")
        else:
            print("  [SCAN] Sin cambios en el inventario")
    except Exception as e:
        print(f"  [SCAN] Error: {e}")
        traceback.print_exc()

threading.Thread(target=auto_scan, daemon=True).start()

# ============================================================
# BEEPS (v3.5 dinámicos) Y HELPERS
# ============================================================
def beep_ok():
    winsound.Beep(880, 60); winsound.Beep(1320, 90)

def beep_error():
    winsound.Beep(400, 120); winsound.Beep(240, 160)

def beep_nuclear():
    for _ in range(3):
        winsound.Beep(600, 50); time.sleep(0.02)

def beep_escucha():
    winsound.Beep(1200, 70)

def callback(indata, frames, t, status):
    global NIVEL_MIC
    b = bytes(indata)
    pico = 0
    try:
        m = array.array('h', b)
        for v in m:
            a = v if v >= 0 else -v
            if a > pico:
                pico = a
        NIVEL_MIC = pico
    except Exception:
        pass
    q.put((b, pico))

def cerrar_todo_nuclear():
    notificar("[☢️ NUCLEAR] Cerrando TODO...")
    hablar("Cerrando todo")
    beep_nuclear()
    cmd = f'taskkill /F /FI "USERNAME eq {usuario}" /FI "IMAGENAME ne explorer.exe" /FI "IMAGENAME ne dwm.exe" /FI "IMAGENAME ne winlogon.exe" /FI "IMAGENAME ne RuntimeBroker.exe"'
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def timer_minutos(minutos):
    def alerta():
        time.sleep(minutos * 60)
        winsound.Beep(1500, 300); time.sleep(0.2); winsound.Beep(1500, 300)
    threading.Thread(target=alerta).start()

def abrir_discord():
    ruta_update = Path(os.environ.get("LOCALAPPDATA", "")) / "Discord" / "Update.exe"
    if ruta_update.exists():
        subprocess.Popen([str(ruta_update), "--processStart", "Discord.exe"])
    else:
        for e in REGISTRO:
            if "discord" in normalizar(e["nombre"]) and e["tipo"] == "app":
                subprocess.Popen(e["ruta"]); return

# ============================================================
# v3.4/3.5: DOS OÍDOS + RUIDO + OCR
# ============================================================
def es_silencio_bloque(pico, umbral=400):
    return pico < umbral

def limpiar_ruido(bloques):
    try:
        data = b"".join(bloques)
        m = array.array('h', data)
        for i in range(len(m)):
            if -400 < m[i] < 400:
                m[i] = 0
        return m.tobytes()
    except Exception:
        return b"".join(bloques)

def grabar_frase(rolling):
    bloques = list(rolling)
    rolling.clear()
    silenciosos = 0
    while len(bloques) < MAX_BLOQUES:
        data, pico = q.get()
        bloques.append(data)
        if es_silencio_bloque(pico):
            silenciosos += 1
            if silenciosos >= SILENCIO_BLOQUES and len(bloques) > 12:
                break
        else:
            silenciosos = 0
    return bloques

def guardar_wav(bloques):
    ruta_wav = BASE / "_toni_frase.wav"
    with wave.open(str(ruta_wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(limpiar_ruido(bloques))
    return ruta_wav

def vosk_offline(bloques):
    r2 = KaldiRecognizer(model, 16000)
    for b in bloques:
        r2.AcceptWaveform(b)
    return json.loads(r2.FinalResult()).get("text", "").lower()

def whisper_wav(ruta_wav):
    notificar(f"🧠 Procesando con Whisper ({WHISPER_MODEL.name})...")
    try:
        out = subprocess.check_output(
            [str(WHISPER_EXE), "-m", str(WHISPER_MODEL), "-f", str(ruta_wav),
             "-l", "es", "-nt", "-np", "-t", "4"],
            creationflags=CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, timeout=120)
        texto = out.decode("utf-8", errors="replace")
        texto = re.sub(r"\[.*?\]", " ", texto)
        texto = " ".join(l for l in texto.splitlines() if l.strip())
        texto = texto.strip().lower()
        for k, v in CORRECCIONES.items():
            texto = texto.replace(k, v)
        return texto
    except Exception as e:
        notificar(f"[WHISPER] Error: {e}")
        return None

PALABRAS_COMANDO = ["abre","abri","abrir","abra","cierra","cerrar","cerrame","busca","buscar","buscame","volume","hora","dia","fecha","clima","dolar","noticia","musica","cumbia","tango","folklore","rock","radio","youtube","whatsapp","facebook","instagram","netflix","disney","prime","spotify","tidal","deezer","apaga","reinicia","traba","bloquea","silencia","mute","suspende","bateria","version","nombre","gracias","te quiero","te amo","ayuda","sorprend","aburro","buenos dias","buenas","timer","record","recuerd","acordate","calculadora","bloc","paint","lupa","configuracion","documentos","explorador","galeria","correo","navegador","internet","poneme","ponerme","pone","ponle","pelicula","serie","video","hoja","planilla","excel","word","discord","steam","quien","que eres","eres","pausa","siguiente","anterior","play"]

def parece_comando(t):
    if not t:
        return False
    if buscar_apps(t):
        return True
    tn = normalizar(t)
    return any(p in tn for p in PALABRAS_COMANDO)

def leer_pantalla():
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        notificar("[OCR] No instalado en esta copia")
        hablar("La lectura de pantalla no está instalada en esta copia.")
        return
    try:
        for p in [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                  r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]:
            if os.path.isfile(p):
                pytesseract.pytesseract.tesseract_cmd = p
                break
        img = pyautogui.screenshot()
        texto = pytesseract.image_to_string(img, lang="spa+eng").strip()
        if not texto:
            hablar("No encontré texto en la pantalla.")
            return
        notificar(f"[OCR] {texto[:80]}...")
        hablar("Leo lo que veo: " + texto[:300])
    except Exception as e:
        notificar(f"[OCR] Error: {e}")
        hablar("No pude leer la pantalla.")

# ============================================================
# MOTOR DE INTENCIONES
# ============================================================
def buscar_apps(texto):
    texto_n = normalizar(texto)
    mejor = {}
    for entry in REGISTRO:
        clave = normalizar(entry["nombre"])
        for alias in entry["alias"]:
            a = normalizar(alias)
            if not a:
                continue
            ok = (f" {a} " in f" {texto_n} ") if len(a) <= 3 else (a in texto_n)
            if ok:
                actual = mejor.get(a)
                if actual is None or len(clave) < len(normalizar(actual["nombre"])):
                    mejor[a] = entry
    hits = list({id(e): e for e in mejor.values()}.values())
    claves = [(normalizar(e["nombre"]), e) for e in hits]
    final = []
    for c, e in claves:
        if any(c != o and o.startswith(c) for o, _ in claves):
            continue
        final.append(e)
    return final

def limpiar_wake(texto):
    for palabra in WAKE_WORDS:
        texto = texto.replace(palabra, "")
    while "  " in texto:
        texto = texto.replace("  ", " ")
    return texto.strip()

def disculpa_no_entendi():
    notificar("[NO ENTENDIDO]")
    hablar("Perdón, no te entendí. ¿Me lo repites por favor?")
    beep_error()

def procesar_y_ejecutar(texto):
    texto = limpiar_wake(texto)
    texto_n = normalizar(texto)
    texto_n = texto_n.replace("ponerme", "poneme")
    if not texto_n:
        return

    notificar(f"Comando: '{texto}'")

    m_nombre = re.search(r'\b(?:me llamo|mi nombre es|soy|llamame|me dicen)\s+(\w+)', texto_n)
    if m_nombre and not any(k in texto_n for k in IDENTIDAD_TRIGGERS):
        nuevo_nombre = m_nombre.group(1).capitalize()
        global NOMBRE_USUARIO
        NOMBRE_USUARIO = nuevo_nombre
        guardar_config(nombre=nuevo_nombre)
        notificar(f"[NOMBRE] Ahora me acuerdo: {nuevo_nombre}")
        hablar(f"Mucho gusto {nuevo_nombre}, de ahora en más te voy a llamar así")
        beep_ok()
        return

    VERBOS_CERRAR = ["cierra", "sierra", "serra", "cerrar", "serrar", "cerra",
                     "mata", "limpia", "cierre", "cierren", "sierre", "sierren",
                     "serra", "serran", "cerre", "cerro", "cierro",
                     "saca", "sacar", "quita", "quitar", "oculta", "ocultar",
                     "apaga", "apagar", "cerrame", "cierrame", "sierreme",
                     "serrame", "cierrenme", "cierreme", "cierrenlo", "cierralo",
                     "cierrela", "cerralo", "cerrala", "matalo", "matala",
                     "salir", "salí", "salga"]
    es_cerrar = any(v in texto_n for v in VERBOS_CERRAR)

    if es_cerrar and any(p in texto_n for p in ["todo", "toda", "todas"]):
        cerrar_todo_nuclear()
        return

    if "reinicia" in texto_n:
        notificar("[SISTEMA] Reiniciando"); hablar("Reiniciando"); beep_ok()
        subprocess.run("shutdown /r /t 5"); return
    if "traba" in texto_n or "bloquea" in texto_n:
        notificar("[SISTEMA] Trabando"); hablar("Trabando"); beep_ok()
        subprocess.run("rundll32.exe user32.dll,LockWorkStation"); return

    if any(a in texto_n for a in ["silencia", "mutea", "sin volumen", "mute", "en silencio"]):
        pyautogui.press('volumemute'); notificar("[SISTEMA] Silenciado"); hablar("Silenciado"); beep_ok(); return

    # v3.5: control multimedia
    if any(a in texto_n for a in ["siguiente tema", "siguiente cancion", "tema siguiente"]):
        pyautogui.press('nexttrack'); notificar("[MEDIA] Siguiente"); beep_ok(); return
    if any(a in texto_n for a in ["tema anterior", "cancion anterior", "anterior"]):
        pyautogui.press('prevtrack'); notificar("[MEDIA] Anterior"); beep_ok(); return
    if any(a in texto_n for a in ["pausa", "pausalo", "detene", "play", "reanuda", "seguir reproduciendo"]):
        pyautogui.press('playpause'); notificar("[MEDIA] Play/Pausa"); beep_ok(); return

    if "volumen" in texto_n:
        if any(v in texto_n for v in ["al 50", "a la mitad", "mitad", "al cincuenta", "en 50"]):
            for _ in range(50):
                pyautogui.press('volumedown')
            for _ in range(25):
                pyautogui.press('volumeup')
            notificar("[SISTEMA] Volumen al 50%"); hablar("Volumen al cincuenta por ciento"); beep_ok(); return
        if any(v in texto_n for v in ["subi", "sube", "subir", "subile", "alto", "fuerte", "mas"]):
            for _ in range(10):
                pyautogui.press('volumeup')
            notificar("[SISTEMA] Volumen +20"); hablar("Subiendo el volumen"); beep_ok(); return
        if any(v in texto_n for v in ["baja", "bajale", "bajar", "bajo", "suave", "menos"]):
            for _ in range(10):
                pyautogui.press('volumedown')
            notificar("[SISTEMA] Volumen -20"); hablar("Bajando el volumen"); beep_ok(); return

    if any(a in texto_n for a in ["suspende", "dormi", "reposo", "descansa"]):
        notificar("[SISTEMA] Suspendiendo"); hablar("Suspendiendo la computadora"); beep_ok()
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"]); return

    if "baja todo" in texto_n or "esconde" in texto_n:
        pyautogui.hotkey('win', 'd'); notificar("[SISTEMA] Bajando todo"); hablar("Bajando todo"); beep_ok(); return

    if "que hora" in texto_n or "la hora" in texto_n:
        now = datetime.now()
        frase = f"Son las {now.hour} en punto" if now.minute == 0 else f"Son las {now.hour} y {now.minute}"
        notificar(f"[HORA] {now.hour}:{now.minute:02d}"); hablar(frase); beep_ok(); return

    if "que dia" in texto_n or "que fecha" in texto_n or "la fecha" in texto_n:
        now = datetime.now()
        frase = f"Hoy es {DIAS[now.weekday()]} {now.day} de {MESES[now.month - 1]}"
        notificar(f"[FECHA] {now.day:02d}/{now.month:02d}/{now.year}"); hablar(frase); beep_ok(); return

    if "bateria" in texto_n:
        try:
            out = subprocess.check_output(
                ["powershell", "-Command", "(Get-CimInstance Win32_Battery).EstimatedChargeRemaining"],
                creationflags=CREATE_NO_WINDOW).decode()
            nums = [int(x) for x in out.split() if x.isdigit()]
            if nums:
                notificar(f"[BATERÍA] {nums[0]}%"); hablar(f"Batería en {nums[0]} por ciento")
            else:
                notificar("[BATERÍA] PC enchufada, sin batería"); hablar("Esta computadora está enchufada, no tiene batería")
        except Exception:
            notificar("[BATERÍA] No pude leerla"); hablar("No pude leer la batería")
        beep_ok(); return

    if any(k in texto_n for k in IDENTIDAD_TRIGGERS):
        notificar("[IDENTIDAD] Presentación"); hablar(CHARLA_IDENTIDAD); beep_ok(); return
    if any(k in texto_n for k in ["que version", "version sos", "version sus", "version soz", "en que version", "version tenes", "version tienes", "que version eres"]):
        notificar(f"[VERSIÓN] {VERSION}"); hablar(f"Soy la versión {VERSION}"); beep_ok(); return
    if any(k in texto_n for k in ["como me llamo", "cual es mi nombre", "sabes mi nombre", "sabes como me llamo"]):
        if NOMBRE_USUARIO:
            notificar(f"[NOMBRE] Te llamas {NOMBRE_USUARIO}"); hablar(f"Te llamas {NOMBRE_USUARIO}"); beep_ok()
        else:
            notificar("[NOMBRE] No sé tu nombre todavía"); hablar("Todavía no me dijiste cómo te llamas. Dime: Toni, me llamo Rosa"); beep_ok()
        return
    if "te quiero" in texto_n or "te amo" in texto_n:
        respuesta = "Yo también te quiero mucho" + (f", {NOMBRE_USUARIO}" if NOMBRE_USUARIO else "")
        notificar("[CARIÑO] Yo también"); hablar(respuesta); beep_ok(); return
    if "gracias" in texto_n:
        respuesta = "De nada, para eso estoy" + (f", {NOMBRE_USUARIO}" if NOMBRE_USUARIO else "")
        notificar("[CARIÑO] De nada"); hablar(respuesta); beep_ok(); return
    if any(k in texto_n for k in ["ayuda", "no entiendo", "no se usar", "como se usa", "ensename"]):
        notificar("[AYUDA] Abriendo la guía"); hablar("Abriendo la ayuda")
        for fn in hook_ayuda:
            try:
                fn()
            except Exception:
                pass
        beep_ok(); return
    if any(k in texto_n for k in ["lee la pantalla", "leé la pantalla", "lee pantalla", "ocr", "que dice la pantalla"]):
        notificar("[OCR] Leyendo pantalla...")
        threading.Thread(target=leer_pantalla, daemon=True).start()
        beep_ok(); return
    if any(k in texto_n for k in ["sorprendeme", "sorprende", "me aburro", "aburrido", "aburrida", "aburri"]):
        nombre, url = random.choice(SORPRESAS)
        notificar(f"[SORPRESA] {nombre}"); hablar(f"Te traje {nombre}")
        abrir_url(url); beep_ok(); return
    if procesar_recordatorio(texto_n):
        beep_ok(); return

    if any(p in texto_n for p in ["buscador", "navegador", "internet", "explorador web", "paginas web", "paginas"]):
        if any(v in VERBOS_CERRAR for v in texto_n.split()):
            pass
        else:
            notificar("[ABRIR] Navegador web"); hablar("Abriendo el navegador")
            exe = navegador_default()
            if exe:
                subprocess.Popen([exe, URL_GOOGLE])
            else:
                webbrowser.open(URL_GOOGLE)
            beep_ok(); return

    if es_cerrar:
        hits = buscar_apps(texto)
        if hits:
            for e in hits:
                if e["tipo"] == "url":
                    clave_cierre = e.get("cierre", e["nombre"].lower())
                    if normalizar(e["nombre"]) in APPS_UWP:
                        cerrar_uwp(normalizar(e["nombre"]))
                    else:
                        cerrar_url(clave_cierre)
                    notificar(f"[CERRAR] {e['nombre']} (cerrada)")
                    hablar(f"Cerrando {e['nombre']}")
                elif e["proceso"]:
                    nombre_n = normalizar(e["nombre"])
                    if nombre_n in APPS_UWP:
                        cerrar_uwp(nombre_n)
                    else:
                        subprocess.run(
                            f'taskkill /IM {e["proceso"]} /F',
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
                    notificar(f"[CERRAR] {e['nombre']}")
                    hablar(f"Cerrando {e['nombre']}")
            beep_ok()
            return
        if "apaga" in texto_n:
            notificar("[SISTEMA] Apagando"); hablar("Apagando la computadora"); beep_ok()
            subprocess.run("shutdown /s /t 5"); return
        disculpa_no_entendi()
        return

    for app_bs, alias in APPS_BLUESTACKS.items():
        if any(a in texto_n for a in alias):
            ruta_bs = buscar_bluestacks()
            if ruta_bs:
                notificar(f"[ABRIR] {app_bs.capitalize()} (BlueStacks)")
                hablar(f"Abriendo {app_bs}")
                subprocess.Popen([ruta_bs, "--launch", app_bs.capitalize()])
                beep_ok()
            else:
                notificar("[AVISO] BlueStacks no está instalado en esta PC")
                hablar("BlueStacks no está instalado en esta computadora")
                beep_error()
            return

    if "discord" in texto_n or "discor" in texto_n:
        notificar("[ABRIR] Discord"); hablar("Abriendo Discord"); abrir_discord(); beep_ok(); return

    hits = buscar_apps(texto)
    if hits:
        for e in hits:
            notificar(f"[ABRIR] {e['nombre']}")
            hablar(f"Abriendo {e['nombre']}")
            if e["tipo"] == "url":
                abrir_url(e["ruta"])
            else:
                try:
                    subprocess.Popen(e["ruta"])
                except Exception:
                    notificar(f"[AVISO] {e['nombre']} no está instalado o no se pudo abrir")
                    hablar(f"{e['nombre']} no está instalado")
        beep_ok()
        return

    tokens = set(texto_n.split())
    if tokens & {"poneme", "ponerme", "pone", "pon", "ponle", "ponele"}:
        if any(v in texto_n for v in ["pelicula", "peli", "serie", "algo para ver", "video", "una peli"]):
            notificar(f"[ABRIR] Video en {VIDEO_PREF}")
            hablar("Abriendo tu servicio de video")
            abrir_servicio(VIDEO_PREF, SERVICIOS_VIDEO.get(VIDEO_PREF, "https://www.netflix.com"))
            beep_ok(); return
        if any(m in texto_n for m in ["musica", "cancion", "canciones", "temas", "musiquita"]) or len(tokens) <= 2:
            notificar(f"[ABRIR] Música en {MUSICA_PREF}")
            hablar("Abriendo tu música")
            abrir_servicio(MUSICA_PREF, SERVICIOS_MUSICA.get(MUSICA_PREF, "https://open.spotify.com"))
            beep_ok(); return

    if any(a in texto_n for a in ["hoja de calculo", "hojas de calculo", "planilla"]):
        excel = next((e for e in REGISTRO if e["tipo"] == "app" and "excel" in normalizar(e["nombre"])), None)
        if excel:
            notificar("[ABRIR] Excel (hoja de cálculo)")
            subprocess.Popen(excel["ruta"])
        else:
            notificar("[ABRIR] Hojas de cálculo de Google")
            abrir_url("https://docs.google.com/spreadsheets")
        hablar("Abriendo la hoja de cálculo"); beep_ok(); return

    if "calculadora" in texto_n:
        notificar("[ABRIR] Calculadora"); hablar("Abriendo la calculadora")
        subprocess.Popen("calc.exe"); beep_ok(); return

    if any(a in texto_n for a in ["galeria", "mis fotos", "fotos mias", "mis imagenes"]):
        notificar("[ABRIR] Galería"); hablar("Abriendo tu galería")
        subprocess.Popen(["explorer.exe", str(Path.home() / "Pictures")]); beep_ok(); return

    if any(a in texto_n for a in ["bloc de notas", "notepad", "bloc"]):
        notificar("[ABRIR] Bloc de notas"); hablar("Abriendo el bloc de notas")
        subprocess.Popen("notepad.exe"); beep_ok(); return

    if any(a in texto_n for a in ["paint", "pintar"]):
        notificar("[ABRIR] Paint"); hablar("Abriendo el paint")
        subprocess.Popen("mspaint.exe"); beep_ok(); return

    if any(a in texto_n for a in ["lupa", "aumentar", "agrandar", "mas grande", "no veo"]):
        notificar("[ABRIR] Lupa"); hablar("Abriendo la lupa")
        subprocess.Popen("Magnify.exe"); beep_ok(); return

    if "configuracion" in texto_n:
        notificar("[ABRIR] Configuración"); hablar("Abriendo la configuración")
        subprocess.Popen("start ms-settings:", shell=True, creationflags=CREATE_NO_WINDOW); beep_ok(); return

    if any(a in texto_n for a in ["documentos", "mis documentos"]):
        notificar("[ABRIR] Documentos"); hablar("Abriendo tus documentos")
        subprocess.Popen(["explorer.exe", str(Path.home() / "Documents")]); beep_ok(); return

    if any(a in texto_n for a in ["explorador", "mis archivos", "archivos", "carpetas", "carpeta"]):
        notificar("[ABRIR] Explorador de archivos"); hablar("Abriendo tus archivos")
        subprocess.Popen("explorer.exe"); beep_ok(); return

    VERBOS_ABRIR = ["abrir", "abri", "abre", "abra", "entrar", "entra", "anda a", "vamos a", "llevame"]
    for vb in VERBOS_ABRIR:
        if vb in texto_n:
            resto = texto_n.split(vb, 1)[1].strip()
            resto = re.sub(r'^(el |la |los |las |un |una |me |al |a )', '', resto).strip()
            if resto:
                resto_n = normalizar(resto)
                svc_match = next((s for s in SERVICIOS_TODOS if s in resto_n or resto_n in s), None)
                if svc_match:
                    notificar(f"[ABRIR] {svc_match.capitalize()}")
                    hablar(f"Abriendo {svc_match}")
                    abrir_servicio(svc_match, SERVICIOS_TODOS[svc_match])
                    beep_ok()
                    return
                es_app_conocida = any(k in resto_n for k in NOMBRES_APP_CONOCIDAS)
                if es_app_conocida:
                    notificar(f"[AVISO] {resto.capitalize()} no está instalada")
                    hablar(f"{resto.capitalize()} no está instalada en esta computadora")
                    beep_error()
                    return
                notificar(f"[ABRIR] {resto}")
                hablar(f"Abriendo {resto}")
                abrir_sitio_o_buscar(resto)
                beep_ok()
            return

    VERBOS_BUSCAR = ["buscame", "buscá", "buscar", "busca", "busco", "googlea", "googlear"]
    for vb in VERBOS_BUSCAR:
        if vb in texto_n:
            consulta = texto_n.split(vb, 1)[1].strip()
            if consulta:
                consulta_n = normalizar(consulta)
                es_app_conocida = any(k in consulta_n for k in NOMBRES_APP_CONOCIDAS)
                if es_app_conocida:
                    notificar(f"[AVISO] {consulta.capitalize()} no está instalada")
                    hablar(f"{consulta.capitalize()} no está instalada en esta computadora")
                    beep_error()
                    return
                notificar(f"[BUSCAR] {consulta}")
                hablar(f"Buscando {consulta}")
                abrir_sitio_o_buscar(consulta)
            else:
                notificar("[ABRIR] Google")
                hablar("Abriendo Google")
                abrir_url(URL_GOOGLE)
            beep_ok()
            return

    if "buenos dias" in texto_n or "buen dia" in texto_n:
        saludo = "Buenos días" + (f", {NOMBRE_USUARIO}" if NOMBRE_USUARIO else "")
        now = datetime.now()
        fecha = f"Hoy es {DIAS[now.weekday()]} {now.day} de {MESES[now.month - 1]}"
        hora = f"Son las {now.hour} y {now.minute}" if now.minute != 0 else f"Son las {now.hour} en punto"
        hablar(f"{saludo}. {fecha}. {hora}. Te abro el clima.")
        notificar(f"[SALUDO] {saludo}"); beep_ok(); abrir_url(URL_CLIMA); return
    if "buenas noches" in texto_n:
        despedida = "Buenas noches" + (f", {NOMBRE_USUARIO}" if NOMBRE_USUARIO else "")
        notificar("[SALUDO] Buenas noches"); hablar(despedida); beep_nuclear()
        time.sleep(1); subprocess.run("shutdown /s /t 5"); return
    if "buenas tardes" in texto_n:
        saludo = "Buenas tardes" + (f", {NOMBRE_USUARIO}" if NOMBRE_USUARIO else "")
        hablar(saludo); notificar(f"[SALUDO] {saludo}"); beep_ok(); return
    if "timer" in texto_n or "temporizador" in texto_n or "pomodoro" in texto_n:
        notificar("[TIMER] 25 minutos"); hablar("Timer de 25 minutos"); beep_ok(); timer_minutos(25); return

    disculpa_no_entendi()

# ============================================================
# BUCLE DE VOZ (dos oídos)
# ============================================================
def escuchar_loop():
    with sd.RawInputStream(samplerate=16000, blocksize=2000, dtype="int16", channels=1, callback=callback, device=DEVICE_ID):
        rolling = deque(maxlen=BLOQUES_BUFFER)
        while True:
            data, pico = q.get()

            if MUTE_MIC:
                continue

            rolling.append(data)

            # 🎤 pulsar para hablar: siempre Whisper
            if HABLAR_AHORA[0]:
                HABLAR_AHORA[0] = False
                beep_escucha()
                notificar("🎙 Te escucho (directo)...")
                bloques = grabar_frase(rolling)
                frase = whisper_wav(guardar_wav(bloques)) if WHISPER_OK else None
                if not frase:
                    frase = vosk_offline(bloques)
                if frase:
                    for fn in hook_voz:
                        try: fn(frase)
                        except Exception: pass
                    try:
                        procesar_y_ejecutar(frase)
                    except Exception as e:
                        beep_error(); notificar(f"[ERROR] {e}"); traceback.print_exc()
                else:
                    hablar("Perdón, no escuché nada.")
                continue

            # Wake word por Vosk
            if rec.AcceptWaveform(data):
                tw = json.loads(rec.Result()).get("text", "").lower()
                                if any(w in tw for w in WAKE_WORDS):
                    # v3.6: respuesta rápida con el texto de Vosk en vivo
                    texto_vosk = limpiar_wake(tw)
                    elegido = texto_vosk
                    # Solo si Vosk no cachó nada útil, ir por Whisper (lento)
                    if WHISPER_OK and not parece_comando(texto_vosk):
                        beep_escucha()
                        notificar("🎙 Te escucho...")
                        bloques = grabar_frase(rolling)
                        tws = whisper_wav(guardar_wav(bloques))
                        if tws:
                            elegido = tws
                    if elegido:
                        print(f"\nVoz: '{elegido}'")
                        for fn in hook_voz:
                            try: fn(elegido)
                            except Exception: pass
                        try:
                            procesar_y_ejecutar(elegido)
                        except Exception as e:
                            beep_error(); notificar(f"[ERROR] {e}"); traceback.print_exc()
                    else:
                        notificar("[SIN AUDIO] No escuché nada")
                        hablar("Perdón, no escuché nada. ¿Me lo repites?")

if __name__ == "__main__":
    print("=" * 60)
    print(f"TONI v{VERSION} - CONSOLA ({usuario})")
    print(f"Whisper: {'ACTIVO 🧠 (' + WHISPER_MODEL.name + ')' if WHISPER_OK else 'NO ENCONTRADO (modo Vosk)'}")
    print(f"Atajos: mute={HOTKEY_MUTE} hablar={HOTKEY_HABLAR}")
    print(f"Apps en registro: {len(REGISTRO)} | Voz: {'ON' if VOZ_ACTIVA else 'OFF'}")
    print("=" * 60 + "\n")
    escuchar_loop()