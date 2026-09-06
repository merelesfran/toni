"""
TONI v3.5 - OPEN SOURCE
Sin activación por key. Distribuido "tal cual", bajo responsabilidad del usuario.
"""
import sys
import os
import time
import json
import winreg
import subprocess
from pathlib import Path
from tkinter import filedialog

if sys.stdout is None or sys.stderr is None:
    _base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    _log = open(_base / "toni.log", "w", encoding="utf-8", errors="replace")
    sys.stdout = _log
    sys.stderr = _log

if sys.stdin is None:
    sys.stdin = open(os.devnull, "r")

import customtkinter as ctk
import threading
import webbrowser
import sounddevice as sd

BG = "#0b1220"
SURFACE = "#101a2c"
BORDER = "#1c2a40"
HOVER = "#16233a"
ACCENT = "#5eb1ff"
TEXT = "#e8eef7"
DIM = "#8fa3bd"
SUCCESS = "#2dd4a7"
WARNING = "#f5b453"
ERROR = "#f47171"

NOMBRE_AUTOR = "Frahn"
INSTAGRAM = "merelesfrahn"
CORREO_CONTACTO = "toni.ayuda.ar@gmail.com"
MARCA = f"TONI © {NOMBRE_AUTOR} · IG: @{INSTAGRAM} · {CORREO_CONTACTO}"

DISCLAIMER = ("TONI se distribuye «tal cual», sin garantías de ningún tipo, expresas o implícitas. "
              "El uso de TONI es bajo tu propia responsabilidad. Sus autores no se responsabilizan por "
              "daños, pérdidas de datos, mal funcionamiento, decisiones tomadas en base a su salida, ni "
              "cualquier consecuencia derivada de su uso. Al usar TONI aceptás estos términos.")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_splash = ctk.CTk()
_splash.overrideredirect(True)
_splash.configure(fg_color=BG)
_w, _h = 460, 340
_x = (_splash.winfo_screenwidth() - _w) // 2
_y = (_splash.winfo_screenheight() - _h) // 2
_splash.geometry(f"{_w}x{_h}+{_x}+{_y}")
ctk.CTkLabel(_splash, text="💬", font=ctk.CTkFont(size=64), text_color=ACCENT).pack(pady=(40, 0))
ctk.CTkLabel(_splash, text="TONI", font=ctk.CTkFont(size=32, weight="bold"), text_color=TEXT).pack()
ctk.CTkLabel(_splash, text="Cargando...", font=ctk.CTkFont(size=13), text_color=DIM).pack(pady=(4, 0))
ctk.CTkLabel(_splash, text=MARCA, font=ctk.CTkFont(size=10), text_color=DIM).pack(pady=(10, 0))
ctk.CTkLabel(_splash, text="Software libre · uso bajo tu responsabilidad", font=ctk.CTkFont(size=9), text_color=DIM).pack(pady=(4, 0))
_splash.update()

import toni_core as core

BASE = core.BASE

if core.LETRA_GRANDE:
    ctk.set_widget_scaling(1.25)

def poner_icono(ventana):
    try:
        if getattr(sys, "frozen", False):
            p = Path(sys._MEIPASS) / "toni.ico"
        else:
            p = BASE / "toni.ico"
        if p.exists():
            ventana.iconbitmap(str(p))
    except Exception:
        pass

class ActionTile(ctk.CTkButton):
    def __init__(self, master, icon, title, command):
        super().__init__(
            master,
            text=f"{icon}   {title}",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=74,
            corner_radius=14,
            fg_color=SURFACE,
            hover_color=HOVER,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            anchor="w",
            command=command,
        )

class Ayuda(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Cómo hablarle a TONI")
        poner_icono(self)
        self.geometry("700x700")
        self.configure(fg_color=BG)
        ctk.CTkLabel(self, text="Guía de uso", font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT).pack(anchor="w", padx=30, pady=(28, 4))
        ctk.CTkLabel(self, text="Toni entiende órdenes, no conversaciones. Decí la palabra clave y listo.", font=ctk.CTkFont(size=13), text_color=DIM).pack(anchor="w", padx=30)
        apps_conocidas = sorted({e["nombre"] for e in core.REGISTRO if e["tipo"] == "app"})
        lista_apps = ", ".join(apps_conocidas[:14])
        texto = (
            "EJEMPLOS QUE FUNCIONAN:\n\n"
            "   • Toni abre YouTube / mostrame Netflix\n"
            "   • Toni poneme música / cumbia / tango / la radio\n"
            "   • Toni busca los redondos / vilma palma\n"
            "   • Toni cierra / sacá / quitá YouTube\n"
            "   • Toni cierra todo / apaga\n"
            "   • Toni qué hora es / qué día es / qué versión sos\n"
            "   • Toni quién eres / te quiero / me llamo Rosa\n"
            "   • Toni subí / bajá el volumen / volumen a la mitad\n"
            "   • Toni pausa / siguiente tema / tema anterior\n"
            "   • Toni recuérdame a las 3 la pastilla\n"
            "   • Toni sorpréndeme / me aburro / Toni ayuda\n\n"
            "ATAJOS DE TECLADO (funcionan en toda la PC):\n"
            f"   • {core.HOTKEY_MUTE.upper()} → silenciar / activar el micrófono\n"
            f"   • {core.HOTKEY_HABLAR.upper()} → pulsar para hablar sin decir 'Toni'\n"
            "   (Se cambian en ⚙ Avanzado → Audio, y se aplican al reiniciar)\n\n"
            f"APPS DISPONIBLES:\n   {lista_apps}… y más.\n\n"
            "En ⚙ Avanzado → Preferencias elegís tu servicio de música\n"
            "y de video (Spotify, Tidal, Apple Music, Netflix, Disney...).\n\n"
            "¿DUDAS?\n"
            f"   {CORREO_CONTACTO} · IG @{INSTAGRAM}\n\n"
            f"{MARCA}\n\n"
            f"AVISO LEGAL:\n{DISCLAIMER}"
        )
        txt = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14, family="Consolas"), wrap="word",
                             fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
        txt.pack(fill="both", expand=True, padx=30, pady=(16, 28))
        txt.insert("end", texto)
        txt.configure(state="disabled")

class Contacto(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Contacto - TONI")
        poner_icono(self)
        self.geometry("520x470")
        self.configure(fg_color=BG)
        ctk.CTkLabel(self, text="💬", font=ctk.CTkFont(size=48), text_color=ACCENT).pack(pady=(36, 8))
        ctk.CTkLabel(self, text="Contactanos", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT).pack()
        ctk.CTkLabel(self, text="Estamos para ayudarte", font=ctk.CTkFont(size=13), text_color=DIM).pack(pady=(2, 20))
        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=30, pady=8)
        ctk.CTkLabel(card, text=CORREO_CONTACTO, font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT).pack(pady=(18, 12))
        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.pack(pady=(0, 18))
        ctk.CTkButton(bf, text="📋 Copiar", width=130, height=38, font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=ACCENT, hover_color="#4a9de8", text_color="#06101f", corner_radius=10, command=self.copiar).pack(side="left", padx=5)
        ctk.CTkButton(bf, text="✉ Escribir", width=130, height=38, font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color="transparent", border_width=1, border_color=ACCENT, text_color=ACCENT,
                      hover_color=HOVER, corner_radius=10, command=self.escribir).pack(side="left", padx=5)
        self.lbl_ok = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.lbl_ok.pack(pady=8)
        ctk.CTkLabel(self, text=f"📸 @{INSTAGRAM}", font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT).pack(pady=(4, 8))
        ctk.CTkButton(self, text="Seguir en Instagram", width=190, height=38, font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=ACCENT, hover_color="#4a9de8", text_color="#06101f", corner_radius=10, command=self.seguir_ig).pack()

    def copiar(self):
        self.clipboard_clear()
        self.clipboard_append(CORREO_CONTACTO)
        self.lbl_ok.configure(text="✓ Correo copiado al portapapeles")

    def escribir(self):
        webbrowser.open(f"mailto:{CORREO_CONTACTO}")

    def seguir_ig(self):
        webbrowser.open(f"https://instagram.com/{INSTAGRAM}")

class ToniSimple(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"TONI v{core.VERSION}")
        poner_icono(self)
        self.geometry("960x640")
        self.minsize(600, 460)
        self.configure(fg_color=BG)
        self.pulse_step = 0
        self.pulse_direction = 1

        footer = ctk.CTkFrame(self, fg_color=BG, height=52)
        footer.pack(side="bottom", fill="x", padx=24, pady=(8, 16))
        footer.pack_propagate(False)
        nav = ctk.CTkFrame(footer, fg_color="transparent")
        nav.pack(side="left", pady=6)
        ctk.CTkButton(nav, text="⚙ Avanzado", width=100, height=38, font=ctk.CTkFont(size=12, weight="bold"),
                      fg_color="transparent", hover_color=HOVER, text_color=DIM, corner_radius=8, command=self.abrir_avanzado).pack(side="left", padx=3)
        ctk.CTkButton(nav, text="❓ Ayuda", width=86, height=38, font=ctk.CTkFont(size=12, weight="bold"),
                      fg_color="transparent", hover_color=HOVER, text_color=DIM, corner_radius=8, command=self.abrir_ayuda).pack(side="left", padx=3)
        ctk.CTkButton(nav, text="💬 Contacto", width=100, height=38, font=ctk.CTkFont(size=12, weight="bold"),
                      fg_color="transparent", hover_color=HOVER, text_color=DIM, corner_radius=8, command=self.abrir_contacto).pack(side="left", padx=3)
        self.btn_voz = ctk.CTkButton(footer, text="", width=140, height=38, font=ctk.CTkFont(size=12, weight="bold"),
                                     fg_color=ACCENT, hover_color="#4a9de8", text_color="#06101f", corner_radius=10, command=self.toggle_voz)
        self.btn_voz.pack(side="right", pady=6)
        self.actualizar_btn_voz()
        ctk.CTkLabel(footer, text=f"{MARCA} · v{core.VERSION}", font=ctk.CTkFont(size=10), text_color=DIM).pack(side="right", padx=10)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", padx=28, pady=(20, 6))
        t = ctk.CTkFrame(header, fg_color="transparent")
        t.pack(side="left")
        ctk.CTkLabel(t, text="TONI", font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(t, text="asistente de voz", font=ctk.CTkFont(size=11), text_color=DIM).pack(anchor="w")

        self.barra_mic = ctk.CTkProgressBar(header, width=120, height=6, corner_radius=3,
                                            fg_color=SURFACE, progress_color=ACCENT)
        self.barra_mic.pack(side="right", padx=(0, 12))
        self.barra_mic.set(0)

        mic_frame = ctk.CTkFrame(header, fg_color="transparent")
        mic_frame.pack(side="right")
        self.btn_mic = ctk.CTkButton(mic_frame, text="", width=44, height=38, font=ctk.CTkFont(size=16),
                                     fg_color=SURFACE, hover_color=HOVER, border_width=1, border_color=BORDER,
                                     corner_radius=10, command=self.toggle_mic)
        self.btn_mic.pack(side="left", padx=(0, 6))
        self.btn_hablar = ctk.CTkButton(mic_frame, text="🎤", width=44, height=38, font=ctk.CTkFont(size=16),
                                        fg_color=SURFACE, hover_color=HOVER, border_width=1, border_color=BORDER,
                                        corner_radius=10, command=self.hablar_ahora)
        self.btn_hablar.pack(side="left", padx=(0, 6))
        self.btn_ocr = ctk.CTkButton(mic_frame, text="📖", width=44, height=38, font=ctk.CTkFont(size=16),
                                     fg_color=SURFACE, hover_color=HOVER, border_width=1, border_color=BORDER,
                                     corner_radius=10, command=lambda: threading.Thread(target=core.leer_pantalla, daemon=True).start())
        self.btn_ocr.pack(side="left", padx=(0, 10))

        st = ctk.CTkFrame(header, fg_color=SURFACE, corner_radius=10, border_width=1, border_color=BORDER)
        st.pack(side="right", padx=(0, 10))
        sti = ctk.CTkFrame(st, fg_color="transparent")
        sti.pack(padx=14, pady=8)
        self.lbl_escucha = ctk.CTkLabel(sti, text="●", font=ctk.CTkFont(size=16), text_color=SUCCESS)
        self.lbl_escucha.pack(side="left", padx=(0, 7))
        self.lbl_estado = ctk.CTkLabel(sti, text="Escuchando", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT)
        self.lbl_estado.pack(side="left")

        self.actualizar_btn_mic()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=BORDER,
                                        scrollbar_button_hover_color=HOVER)
        scroll.pack(fill="both", expand=True, padx=28, pady=6)

        self.lbl_voz = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=14), text_color=DIM, wraplength=820)
        self.lbl_voz.pack(pady=(6, 4))
        self.lbl_accion = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT, wraplength=820)
        self.lbl_accion.pack(pady=(0, 10))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(4, 12))
        for i in range(3):
            grid.grid_rowconfigure(i, weight=1)
        for i in range(2):
            grid.grid_columnconfigure(i, weight=1)
        acciones = [
            ("🎵", "Música", "abre musica"),
            ("▶", "YouTube", "abre youtube"),
            ("💬", "WhatsApp", "abre whatsapp"),
            ("⛅", "Clima", "abre clima"),
            ("🗑", "Cerrar todo", "cierra todo"),
            ("⏻", "Apagar", "apaga"),
        ]
        for i, (icon, title, cmd) in enumerate(acciones):
            tile = ActionTile(grid, icon, title, lambda c=cmd: self.ejecutar(c))
            tile.grid(row=i // 2, column=i % 2, padx=7, pady=7, sticky="nsew")

        core.hook_accion.append(self.on_accion)
        core.hook_voz.append(self.on_voz)
        core.hook_ayuda.append(self._ayuda_hook)
        threading.Thread(target=core.escuchar_loop, daemon=True).start()
        self.animar_pulso()

    def _ayuda_hook(self):
        self.after(0, self.abrir_ayuda)

    def toggle_mic(self):
        core.toggle_mute_mic()
        self.actualizar_btn_mic()

    def actualizar_btn_mic(self):
        if core.MUTE_MIC:
            self.btn_mic.configure(text="🔇", border_color=ERROR)
            self.lbl_estado.configure(text="Mic silenciado", text_color=ERROR)
            self.lbl_escucha.configure(text_color=ERROR)
        else:
            self.btn_mic.configure(text="🎙", border_color=BORDER)
            self.lbl_estado.configure(text="Escuchando", text_color=TEXT)
            self.lbl_escucha.configure(text_color=SUCCESS)

    def hablar_ahora(self):
        core.pedir_hablar_ahora()

    def animar_pulso(self):
        self.pulse_step += self.pulse_direction
        if self.pulse_step >= 10:
            self.pulse_direction = -1
        elif self.pulse_step <= 0:
            self.pulse_direction = 1
        if not core.MUTE_MIC and not str(self.lbl_estado.cget("text")).startswith(("Procesando", "Te escucho", "Mic")):
            intensity = self.pulse_step / 10.0
            r = int(45 + (94 - 45) * intensity)
            g = int(212 + (177 - 212) * intensity)
            b = int(167 + (255 - 167) * intensity)
            self.lbl_escucha.configure(text_color=f"#{r:02x}{g:02x}{b:02x}")
        try:
            nivel = min(getattr(core, "NIVEL_MIC", 0) / 4000.0, 1.0)
            self.barra_mic.set(nivel)
        except Exception:
            pass
        self.after(120, self.animar_pulso)

    def actualizar_btn_voz(self):
        self.btn_voz.configure(text=f"🔊 Voz: {'ON' if core.VOZ_ACTIVA else 'OFF'}")

    def toggle_voz(self):
        core.VOZ_ACTIVA = not core.VOZ_ACTIVA
        core.guardar_config(voz=core.VOZ_ACTIVA)
        self.actualizar_btn_voz()

    def ejecutar(self, comando):
        self.lbl_voz.configure(text=f"Botón: {comando}")
        threading.Thread(target=core.procesar_y_ejecutar, args=(comando,), daemon=True).start()

    def on_voz(self, texto):
        def _upd():
            self.lbl_voz.configure(text=f"Dijiste: “{texto}”")
            self.lbl_estado.configure(text="Procesando...", text_color=WARNING)
            self.lbl_escucha.configure(text_color=WARNING)
        self.after(0, _upd)

    def on_accion(self, msg):
        def _upd():
            self.lbl_accion.configure(text=msg)
            if msg.startswith("🎙"):
                self.lbl_estado.configure(text="Te escucho", text_color=ACCENT)
                self.lbl_escucha.configure(text_color=ACCENT)
            elif msg.startswith("[MIC]"):
                self.actualizar_btn_mic()
            else:
                color = ERROR if ("NO ENTENDIDO" in msg or "ERROR" in msg or "AVISO" in msg) else SUCCESS
                if not core.MUTE_MIC:
                    self.lbl_estado.configure(text="Escuchando", text_color=TEXT)
                    self.lbl_escucha.configure(text_color=color)
                    self.after(1200, lambda: self.lbl_escucha.configure(text_color=SUCCESS))
        self.after(0, _upd)

    def abrir_avanzado(self):
        Avanzado(self)

    def abrir_ayuda(self):
        Ayuda(self)

    def abrir_contacto(self):
        Contacto(self)

class Avanzado(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"TONI v{core.VERSION} - Configuración avanzada")
        poner_icono(self)
        self.geometry("780x620")
        self.configure(fg_color=BG)
        ctk.CTkLabel(self, text="Configuración avanzada", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT).pack(anchor="w", padx=28, pady=(24, 12))
        tabs = ctk.CTkTabview(self, fg_color=SURFACE,
                              segmented_button_fg_color=BG,
                              segmented_button_selected_color=ACCENT,
                              segmented_button_selected_hover_color="#4a9de8",
                              segmented_button_unselected_color=BG,
                              segmented_button_unselected_hover_color=HOVER)
        tabs.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        t_apps = tabs.add("Apps")
        ctk.CTkLabel(t_apps, text=f"Apps en registro: {len(core.REGISTRO)}", font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(16, 8))
        scroll = ctk.CTkScrollableFrame(t_apps, fg_color=BG, corner_radius=8, border_width=1, border_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=18, pady=8)
        for e in sorted(core.REGISTRO, key=lambda x: x["nombre"].lower()):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=e['nombre'], font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT, width=190).pack(side="left", padx=(8, 0))
            ctk.CTkLabel(row, text=e['ruta'], font=ctk.CTkFont(size=10), text_color=DIM).pack(side="left", padx=8)
        fila = ctk.CTkFrame(t_apps, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=14)
        self.cmb_apps = ctk.CTkComboBox(fila, values=sorted([e["nombre"] for e in core.REGISTRO]), width=230,
                                        fg_color=BG, button_color=ACCENT, button_hover_color="#4a9de8")
        self.cmb_apps.pack(side="left", padx=(0, 8))
        self.ent_alias = ctk.CTkEntry(fila, placeholder_text="alias nuevo (ej: sting)", width=210, fg_color=BG, border_color=BORDER)
        self.ent_alias.pack(side="left", padx=(0, 8))
        ctk.CTkButton(fila, text="Agregar", width=90, fg_color=ACCENT, hover_color="#4a9de8", text_color="#06101f", command=self.agregar_alias).pack(side="left")
        self.lbl_alias_ok = ctk.CTkLabel(fila, text="", font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.lbl_alias_ok.pack(side="left", padx=8)

        t_audio = tabs.add("Audio")
        ctk.CTkLabel(t_audio, text="Micrófono", font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(16, 8))
        ctk.CTkLabel(t_audio, text="Se aplica al reiniciar Toni", font=ctk.CTkFont(size=12), text_color=DIM).pack(anchor="w", padx=18)
        mics = ["[Default] Micrófono del sistema"]
        for i, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0:
                mics.append(f"[{i}] {d['name']}")
        self.cmb_mic = ctk.CTkComboBox(t_audio, values=mics, width=560, fg_color=BG, button_color=ACCENT, button_hover_color="#4a9de8")
        self.cmb_mic.pack(anchor="w", padx=18, pady=(10, 0))
        if core.DEVICE_ID is not None:
            for m in mics:
                if m.startswith(f"[{core.DEVICE_ID}]"):
                    self.cmb_mic.set(m)
        ctk.CTkButton(t_audio, text="Guardar micrófono", width=190, fg_color=ACCENT, hover_color="#4a9de8", text_color="#06101f", command=self.guardar_mic).pack(anchor="w", padx=18, pady=12)
        self.lbl_mic_ok = ctk.CTkLabel(t_audio, text="", font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.lbl_mic_ok.pack(anchor="w", padx=18)
        ctk.CTkLabel(t_audio, text="Atajo para silenciar el mic (ej: ctrl+alt+m)", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(14, 6))
        self.ent_tecla_mute = ctk.CTkEntry(t_audio, width=280, fg_color=BG, border_color=BORDER)
        self.ent_tecla_mute.pack(anchor="w", padx=18)
        self.ent_tecla_mute.insert(0, core.HOTKEY_MUTE)
        ctk.CTkLabel(t_audio, text="Atajo para pulsar-para-hablar (ej: ctrl+alt+h)", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(12, 6))
        self.ent_tecla_hablar = ctk.CTkEntry(t_audio, width=280, fg_color=BG, border_color=BORDER)
        self.ent_tecla_hablar.pack(anchor="w", padx=18)
        self.ent_tecla_hablar.insert(0, core.HOTKEY_HABLAR)
        ctk.CTkButton(t_audio, text="Guardar atajos", width=160, fg_color=ACCENT, hover_color="#4a9de8", text_color="#06101f", command=self.guardar_atajos).pack(anchor="w", padx=18, pady=12)
        self.lbl_atajos_ok = ctk.CTkLabel(t_audio, text="", font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.lbl_atajos_ok.pack(anchor="w", padx=18)
        ctk.CTkLabel(t_audio, text=f"Modelo de voz actual: {core.WHISPER_MODEL.name}", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(t_audio, text="Para máxima precisión, copiá ggml-medium.bin al lado\nde TONI.exe y reiniciá. Si no, usa el small.", font=ctk.CTkFont(size=11), text_color=DIM, justify="left").pack(anchor="w", padx=18)

        t_pref = tabs.add("Preferencias")
        ctk.CTkLabel(t_pref, text="Servicio de música preferido", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(16, 8))
        self.cmb_musica = ctk.CTkComboBox(t_pref, values=["spotify", "tidal", "apple music", "youtube music", "deezer"], width=280, fg_color=BG, button_color=ACCENT, button_hover_color="#4a9de8")
        self.cmb_musica.pack(anchor="w", padx=18)
        self.cmb_musica.set(core.MUSICA_PREF)
        ctk.CTkLabel(t_pref, text="Servicio de video preferido", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(18, 8))
        self.cmb_video = ctk.CTkComboBox(t_pref, values=["netflix", "disney plus", "prime video", "max", "youtube"], width=280, fg_color=BG, button_color=ACCENT, button_hover_color="#4a9de8")
        self.cmb_video.pack(anchor="w", padx=18)
        self.cmb_video.set(core.VIDEO_PREF)
        ctk.CTkButton(t_pref, text="Guardar preferencias", width=200, fg_color=ACCENT, hover_color="#4a9de8", text_color="#06101f", command=self.guardar_prefs).pack(anchor="w", padx=18, pady=18)
        self.lbl_prefs_ok = ctk.CTkLabel(t_pref, text="", font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.lbl_prefs_ok.pack(anchor="w", padx=18)

        t_conf = tabs.add("Config")
        self.chk_startup = ctk.CTkCheckBox(t_conf, text="Iniciar Toni con Windows (60s después del login)", font=ctk.CTkFont(size=14, weight="bold"), fg_color=ACCENT, hover_color=HOVER, command=self.toggle_startup)
        self.chk_startup.pack(anchor="w", padx=18, pady=(18, 14))
        if self._startup_activo():
            self.chk_startup.select()
        self.chk_letra = ctk.CTkCheckBox(t_conf, text="Modo letra grande (vista cansada)", font=ctk.CTkFont(size=14, weight="bold"), fg_color=ACCENT, hover_color=HOVER, command=self.toggle_letra)
        self.chk_letra.pack(anchor="w", padx=18, pady=(0, 14))
        if core.LETRA_GRANDE:
            self.chk_letra.select()
        self.lbl_letra_ok = ctk.CTkLabel(t_conf, text="", font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.lbl_letra_ok.pack(anchor="w", padx=18)
        ctk.CTkLabel(t_conf, text="Perfil (para usar el mismo Toni en otra PC)", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(18, 8))
        pf = ctk.CTkFrame(t_conf, fg_color="transparent")
        pf.pack(anchor="w", padx=18)
        ctk.CTkButton(pf, text="⬆ Exportar perfil", width=150, height=36, fg_color=ACCENT, hover_color="#4a9de8", text_color="#06101f", command=self.exportar_perfil).pack(side="left", padx=(0, 8))
        ctk.CTkButton(pf, text="⬇ Importar perfil", width=150, height=36, fg_color="transparent", border_width=1, border_color=ACCENT, text_color=ACCENT, hover_color=HOVER, command=self.importar_perfil).pack(side="left")
        self.lbl_perfil = ctk.CTkLabel(t_conf, text="", font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.lbl_perfil.pack(anchor="w", padx=18, pady=(6, 0))
        ctk.CTkLabel(t_conf, text="La voz se activa con el botón de la pantalla principal.\nTodo queda registrado en toni.log.", font=ctk.CTkFont(size=11), text_color=DIM, justify="left").pack(anchor="w", padx=18, pady=(12, 0))

        t_log = tabs.add("Log")
        self.txt_log = ctk.CTkTextbox(t_log, font=ctk.CTkFont(size=11, family="Consolas"), fg_color=BG, corner_radius=8, border_width=1, border_color=BORDER)
        self.txt_log.pack(fill="both", expand=True, padx=18, pady=16)
        core.hook_accion.append(self.log_line)

    def guardar_atajos(self):
        core.guardar_config(tecla_mute=self.ent_tecla_mute.get().strip().lower(),
                            tecla_hablar=self.ent_tecla_hablar.get().strip().lower())
        self.lbl_atajos_ok.configure(text="✓ Guardado. Se aplica al reiniciar Toni.")

    def exportar_perfil(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("Perfil Toni", "*.json")],
                                            initialfile="toni_perfil.json")
        if not ruta:
            return
        perfil = {}
        for nombre in ["toni_config.json", "recordatorios.json", "correcciones.json", "alias_extra.json", "links_extra.json"]:
            p = BASE / nombre
            if p.exists():
                try:
                    perfil[nombre] = json.load(open(p, encoding="utf-8"))
                except Exception:
                    pass
        json.dump(perfil, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        self.lbl_perfil.configure(text="✓ Perfil exportado")

    def importar_perfil(self):
        ruta = filedialog.askopenfilename(filetypes=[("Perfil Toni", "*.json")])
        if not ruta:
            return
        try:
            perfil = json.load(open(ruta, encoding="utf-8"))
        except Exception:
            self.lbl_perfil.configure(text="✗ Archivo inválido")
            return
        for nombre, contenido in perfil.items():
            json.dump(contenido, open(BASE / nombre, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        self.lbl_perfil.configure(text="✓ Perfil importado. Reiniciá Toni.")

    def guardar_prefs(self):
        core.MUSICA_PREF = self.cmb_musica.get()
        core.VIDEO_PREF = self.cmb_video.get()
        core.guardar_config(musica_pref=core.MUSICA_PREF, video_pref=core.VIDEO_PREF)
        self.lbl_prefs_ok.configure(text="✓ Guardado. 'Toni poneme música' ahora abre " + core.MUSICA_PREF)

    def toggle_letra(self):
        core.LETRA_GRANDE = bool(self.chk_letra.get())
        core.guardar_config(letra=core.LETRA_GRANDE)
        ctk.set_widget_scaling(1.25 if core.LETRA_GRANDE else 1.0)
        self.lbl_letra_ok.configure(text="✓ Guardado. Se ve mejor al reiniciar Toni.")

    def log_line(self, msg):
        def _w():
            try:
                self.txt_log.insert("end", msg + "\n")
                self.txt_log.see("end")
            except Exception:
                pass
        self.after(0, _w)

    def agregar_alias(self):
        nombre = self.cmb_apps.get().strip()
        alias = self.ent_alias.get().strip().lower()
        if not nombre or not alias:
            return
        clave = core.normalizar(nombre)
        path = BASE / "alias_extra.json"
        data = {}
        if path.exists():
            data = json.load(open(path, encoding="utf-8"))
        data.setdefault(clave, [])
        if alias not in data[clave]:
            data[clave].append(alias)
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        core.REGISTRO[:] = core.construir_registro()
        self.ent_alias.delete(0, "end")
        self.lbl_alias_ok.configure(text=f"✓ '{alias}' → {nombre}")

    def guardar_mic(self):
        sel = self.cmb_mic.get()
        idx = None
        if sel.startswith("[") and not sel.startswith("[Default]"):
            idx = int(sel.split("]")[0].replace("[", ""))
        core.guardar_config(device=idx)
        self.lbl_mic_ok.configure(text="✓ Guardado. Reiniciá Toni para aplicar.")

    def _startup_activo(self):
        try:
            r = subprocess.run('schtasks /query /tn "TONI"', shell=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return r.returncode == 0
        except Exception:
            return False

    def toggle_startup(self):
        try:
            if self.chk_startup.get():
                if getattr(sys, "frozen", False):
                    tr = f'"{sys.executable}"'
                else:
                    pythonw = Path(sys.executable).with_name("pythonw.exe")
                    if not pythonw.exists():
                        pythonw = Path(sys.executable)
                    tr = f'"{pythonw}" "{BASE / "toni_gui.py"}"'
                subprocess.run(f'schtasks /create /tn "TONI" /tr {tr} /sc onlogon /delay 0001:00 /rl limited /f',
                               shell=True, creationflags=core.CREATE_NO_WINDOW)
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
                        winreg.DeleteValue(k, "TONI")
                except Exception:
                    pass
                core.guardar_config(startup=True)
            else:
                subprocess.run('schtasks /delete /tn "TONI" /f',
                               shell=True, creationflags=core.CREATE_NO_WINDOW,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                core.guardar_config(startup=False)
        except Exception as e:
            print(f"[ERROR startup] {e}")

if __name__ == "__main__":
    import ctypes
    ctypes.windll.kernel32.CreateMutexW(None, False, "TONI_instancia_unica")
    if ctypes.windll.kernel32.GetLastError() == 183:
        _splash.destroy()
        sys.exit(0)

    _splash.destroy()
    app = ToniSimple()
    app.mainloop()