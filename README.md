

Acá tenés el **README.md** completo, listo para pegar en la raíz del repo:

```markdown
<div align="center">

# 💬 TONI

### Tu asistente de voz personal para Windows

**Offline · Privado · Liviano · Hecho en Argentina 🇦🇷**

![Version](https://img.shields.io/badge/versión-3.5-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/plataforma-Windows%2010%2F11-0078D6?style=for-the-badge&logo=windows)
![License](https://img.shields.io/badge/licencia-propietaria-red?style=for-the-badge)
![Made with](https://img.shields.io/badge/hecho%20con-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

<br>

<img src="https://raw.githubusercontent.com/SmokeyBlues28/toni/main/screenshot.png" alt="TONI Screenshot" width="720">

<br>

*"La tecnología tiene que escucharte a ti, y no al revés."*

</div>

---

## ¿Qué es TONI?

TONI es un asistente de voz **100% offline** para Windows, diseñado para personas que no quieren (o no pueden) lidiar con interfaces complicadas. Con solo decir **"Toni"** y dar una orden, la computadora hace lo que le pedís.

Pensado para **abuelas, abuelos, padres, tíos** y cualquier persona que quiera usar su PC con la voz, sin depender de internet, sin enviar datos a la nube y sin suscripciones.

---

## ✨ Características principales

### 🎤 Dos oídos inteligentes
- **Vosk** (offline, instantáneo): entiende comandos al toque.
- **Whisper** (IA local): se activa solo cuando Vosk no cacha un nombre propio, o con el botón 🎤 para búsquedas complejas.

### 🚀 Lo que Toni puede hacer

| Categoría | Ejemplos |
|---|---|
| **Abrir apps y webs** | *"Toni abre YouTube"* · *"Toni abre WhatsApp"* · *"Toni abre Netflix"* |
| **Buscar en Google** | *"Toni busca los redondos de ricota"* · *"Toni busca recetas de pizza"* |
| **Música y radio** | *"Toni poneme cumbia"* · *"Toni poneme la radio"* · *"Toni folklore"* |
| **Control multimedia** | *"Toni pausa"* · *"Toni siguiente tema"* · *"Toni tema anterior"* |
| **Volumen** | *"Toni subí el volumen"* · *"Toni bajá"* · *"Toni volumen a la mitad"* |
| **Hora y fecha** | *"Toni qué hora es"* · *"Toni qué día es"* |
| **Clima y dólar** | *"Toni el clima"* · *"Toni el dólar"* |
| **Recordatorios** | *"Toni recordame a las 3 la pastilla"* · *"Toni recordame todos los días a las 9 el desayuno"* |
| **Cerrar apps** | *"Toni cierra YouTube"* · *"Toni cierra todo"* |
| **Sistema** | *"Toni apagá"* · *"Toni reiniciá"* · *"Toni bloqueá"* · *"Toni suspendé"* |
| **Charla** | *"Toni quién sos"* · *"Toni te quiero"* · *"Toni me llamo Rosa"* |
| **Sorpresas** | *"Toni sorprendeme"* · *"Toni me aburro"* |

### 🔇 Control total del micrófono
- **Botón de mute** en la interfaz o con atajo global (`Ctrl+Alt+M`).
- **Pulsar para hablar** sin decir "Toni" (`Ctrl+Alt+H` o botón 🎤).
- Atajos configurables desde ⚙ Avanzado.

### 📖 OCR de pantalla (opcional)
- Botón 📖 o *"Toni leé la pantalla"*: lee el texto visible en pantalla y te lo dice en voz alta.
- Requiere [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado por separado.

### 🔄 Auto-actualización
- Toni se actualiza solo cuando hay una versión nueva, sin que el usuario haga nada.
- Verificación por SHA-256 para seguridad.

### 🧠 Aprende de vos
- **correcciones.json**: corregí lo que Whisper escucha mal (nombres, marcas, palabras raras).
- **alias_extra.json**: agregá apodos para tus apps desde la GUI.
- **links_extra.json**: agregá sitios web personalizados.
- **Exportar/importar perfil**: llevá tu configuración a otra PC.

---

## 📦 Instalación

### Opción 1: Instalador (recomendado)

1. Descargá **TONI-Setup.exe** desde [Releases](https://github.com/SmokeyBlues28/toni/releases/latest).
2. Ejecutalo → Siguiente → Siguiente → Listo.
3. TONI se abre solo. Decí **"Toni"** y esperá el bip.

### Opción 2: Portable

1. Descargá el `.zip` desde [Releases](https://github.com/SmokeyBlues28/toni/releases/latest).
2. Descomprimí donde quieras.
3. Ejecutá `TONI.exe`.

---

## 🛠 Requisitos

- **Windows 10/11** (64-bit)
- **Micrófono** (el integrado del notebook sirve)
- **~600 MB** de espacio en disco
- **No requiere internet** para funcionar (solo para auto-update y abrir webs)
- **No requiere GPU** (corre en cualquier CPU)

---

## 🎯 Para quién es TONI

| ✅ Es para vos si... | ❌ No es para vos si... |
|---|---|
| Querés controlar la PC con la voz | Necesitás un chatbot con IA generativa |
| Buscás algo offline y privado | Querés algo que funcione en Mac/Linux |
| Tenés familiares que no son tech-savvy | Necesitás dictado continuo profesional |
| Querés algo plug-and-play sin configurar | Buscás una alternativa a Alexa/Siri |

---

## ⚙ Configuración avanzada

Desde la GUI → botón **⚙ Avanzado**:

| Pestaña | Qué hace |
|---|---|
| **Apps** | Ver apps detectadas, agregar alias personalizados |
| **Audio** | Elegir micrófono, configurar atajos de teclado, ver modelo de voz |
| **Preferencias** | Elegir servicio de música (Spotify, Tidal...) y video (Netflix, Disney...) |
| **Config** | Arranque con Windows, letra grande, exportar/importar perfil |
| **Log** | Ver en tiempo real todo lo que Toni hace |

### Mejorar la precisión de voz

Para máxima precisión en nombres propios, descargá [`ggml-medium.bin`](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin) (~500 MB) y colocalo junto a `TONI.exe`. Reiniciá y Toni lo detecta solo.

---

## 📁 Estructura de archivos

```
TONI/
├── TONI.exe                    # Ejecutable principal
├── toni_config.json            # Configuración del usuario (se genera solo)
├── recordatorios.json          # Recordatorios programados
├── correcciones.json           # Correcciones de transcripción (editable)
├── alias_extra.json            # Alias personalizados de apps
├── links_extra.json            # Links web personalizados
├── apps_scan.json              # Inventario de apps (se genera solo)
├── toni_licencia.json          # Licencia de activación
├── toni.log                    # Log de ejecución
├── ggml-medium.bin             # (Opcional) Modelo Whisper mejorado
└── _internal/                  # Motor de voz y dependencias
    ├── whisper-cli.exe
    ├── ggml-small.bin
    ├── ggml.dll / whisper.dll
    └── vosk-model-small-es-0.42/
```

---

## 🔧 Compilar desde el código fuente

### Requisitos

```bash
pip install vosk sounddevice pyautogui pyttsx3 customtkinter pywin32 pyinstaller
```

### Archivos necesarios en la raíz

- `toni_core.py` — Motor de voz e intenciones
- `toni_gui.py` — Interfaz gráfica
- `toni.ico` — Ícono
- `whisper-cli.exe` + `ggml-small.bin` + DLLs de whisper.cpp
- `vosk-model-small-es-0.42/` — Modelo Vosk en español

### Build

```bash
build.bat
```

Genera `dist/TONI/TONI.exe` y opcionalmente el instalador con Inno Setup.

---

## 🔒 Privacidad

- **Todo el reconocimiento de voz es local.** No se envía audio ni texto a ningún servidor.
- **Sin telemetría.** Toni no recopila datos de uso.
- **Sin cuenta.** No hay login, registro ni suscripción.
- La única conexión a internet es para abrir las webs que el usuario pide y para el auto-update (verificado por SHA-256).

---

## 📸 Contacto

| | |
|---|---|
| **Creador** | Frahn |
| **Instagram** | [@merelesfrahn](https://instagram.com/merelesfrahn) |
| **Correo** | toni.ayuda.ar@gmail.com |

---

## 📋 Changelog

### v3.5 (actual)
- 🎧 Dos oídos: Vosk rápido + Whisper de respaldo
- 🔇 Control total del micrófono (mute + pulsar para hablar)
- ⌨️ Atajos globales configurables
- 🎵 Control multimedia (play/pausa/siguiente/anterior)
- 📖 OCR de pantalla (opcional)
- 🔊 Beeps dinámicos (sube=ok, baja=error)
- 📊 Visualizador de nivel de micrófono
- 🧹 Puerta de ruido liviana
- 📦 Exportar/importar perfil entre PCs

### v3.0
- 🧠 Integración de Whisper (whisper.cpp)
- 🔄 Auto-actualización con verificación SHA-256
- 🎨 GUI premium con customtkinter

### v2.x
- 🎤 Motor Vosk con alias fonéticos
- ⏰ Recordatorios diarios y semanales
- 🔍 Scanner automático de apps instaladas
- 🔒 Sistema de activación por máquina

---

<div align="center">

**TONI © Frahn · Hecho con ❤️ en Entre Ríos, Argentina**

*Si TONI te sirvió o le simplificó la vida a alguien que querés, contame por Instagram. Eso me hace el día.*

</div>
