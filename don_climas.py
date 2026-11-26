"""Don Climas - Sistema de monitoreo meteorológico para transporte terrestre.

Requisitos: Python 3.9+, pip install pillow psutil reportlab
Ejecutar:   python don_climas.py
Usuario de prueba: admin / 1234     API Key de prueba (sin internet): demo
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import psutil
from PIL import Image, ImageTk

import logica

# ------------------------------------------------------------- constantes ----
NOMBRE_ALUMNO = "Artur Mikhail Lazurenko Mannanov"          # <-- cambia por tu nombre completo
BG = "#161616"
PANEL = "#1f1f1f"
CARD = "#262626"
BORDE = "#3a3a3a"
TXT = "#f2f2f2"
TXT2 = "#a6a6a6"
AZUL = "#4a9eff"
ASSETS = os.path.join(logica.BASE_DIR, "assets")
FUENTE = "Segoe UI"
COLOR_RIESGO = {"bajo": "#3ddc84", "medio": "#ffc233", "alto": "#ff5252"}


def cargar_imagen(nombre, tam=None):
    img = Image.open(os.path.join(ASSETS, nombre)).convert("RGBA")
    if tam:
        img = img.resize(tam, Image.LANCZOS)
    return ImageTk.PhotoImage(img)


def poner_icono(ventana):
    """Aplica el logo como ícono de la ventana (barra de título)."""
    try:
        ventana._icono = cargar_imagen("icon.png")
        ventana.iconphoto(False, ventana._icono)
    except Exception:
        pass


# ------------------------------------------------------- widgets auxiliares ----
class BotonPunteado(tk.Canvas):
    """Botón con borde punteado, como en el wireframe."""

    def __init__(self, master, texto, comando, alto=30):
        super().__init__(master, height=alto, bg=PANEL, highlightthickness=0, cursor="hand2")
        self.texto, self.comando = texto, comando
        self.bind("<Configure>", self._dibujar)
        self.bind("<Button-1>", lambda e: self.comando())
        self.bind("<Enter>", lambda e: self._dibujar(hover=True))
        self.bind("<Leave>", lambda e: self._dibujar())

    def _dibujar(self, e=None, hover=False):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        color = AZUL if hover else TXT2
        self.create_rectangle(1, 1, w - 2, h - 2, outline=color, dash=(3, 3))
        self.create_text(w // 2, h // 2, text=self.texto, fill=TXT, font=(FUENTE, 9))


def insignia(master, n, bg=PANEL):
    c = tk.Canvas(master, width=18, height=18, bg=bg, highlightthickness=0)
    c.create_oval(1, 1, 17, 17, fill=TXT, outline=TXT)
    c.create_text(9, 9, text=str(n), fill="#000", font=(FUENTE, 8, "bold"))
    return c


# ------------------------------------------------------------------ splash ----
class Splash(tk.Toplevel):
    DURACION_MS = 5000
    PASO_MS = 100

    def __init__(self, master, al_terminar):
        super().__init__(master)
        self.al_terminar = al_terminar
        self.overrideredirect(True)
        self.configure(bg="#ffffff", highlightbackground=AZUL, highlightthickness=2)
        w, h = 460, 600
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        poner_icono(self)

        self.logo = cargar_imagen("logo.png", (300, 313))
        tk.Label(self, image=self.logo, bg="#ffffff").pack(pady=(14, 4))
        tk.Label(self, text=NOMBRE_ALUMNO, bg="#ffffff", fg="#1b4f9c",
                 font=(FUENTE, 14, "bold")).pack()

        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("Splash.Horizontal.TProgressbar", troughcolor="#e6eef8",
                         background="#2f7de1", bordercolor="#c9d8ea")

        marco = tk.Frame(self, bg="#ffffff")
        marco.pack(fill="x", padx=40, pady=(14, 0))
        self.barra_carga, self.lbl_carga = self._fila(marco, "Cargando")
        self.barra_cpu, self.lbl_cpu = self._fila(marco, "CPU")
        self.barra_ram, self.lbl_ram = self._fila(marco, "RAM")

        self.transcurrido = 0
        psutil.cpu_percent(None)  # primera lectura de referencia
        self.after(self.PASO_MS, self._tick)

    def _fila(self, marco, nombre):
        tk.Label(marco, text=nombre, bg="#ffffff", fg="#333", font=(FUENTE, 9),
                 anchor="w").pack(fill="x")
        barra = ttk.Progressbar(marco, style="Splash.Horizontal.TProgressbar",
                                maximum=100, length=360)
        barra.pack(fill="x")
        lbl = tk.Label(marco, text="0 %", bg="#ffffff", fg="#555", font=(FUENTE, 8), anchor="e")
        lbl.pack(fill="x", pady=(0, 3))
        return barra, lbl

    def _tick(self):
        self.transcurrido += self.PASO_MS
        pct = min(100, self.transcurrido * 100 / self.DURACION_MS)
        cpu = psutil.cpu_percent(None)
        ram = psutil.virtual_memory().percent
        self.barra_carga["value"], self.lbl_carga["text"] = pct, f"{pct:.0f} %"
        self.barra_cpu["value"], self.lbl_cpu["text"] = cpu, f"{cpu:.0f} %"
        self.barra_ram["value"], self.lbl_ram["text"] = ram, f"{ram:.0f} %"
        if self.transcurrido >= self.DURACION_MS:
            self.destroy()
            self.al_terminar()
        else:
            self.after(self.PASO_MS, self._tick)


# ------------------------------------------------------------------- login ----
class Login(tk.Toplevel):
    def __init__(self, master, al_entrar, al_cancelar):
        super().__init__(master)
        self.al_entrar, self.al_cancelar = al_entrar, al_cancelar
        self.intentos = 0
        self.title("Don Climas - Inicio de sesión")
        self.configure(bg=BG)
        self.resizable(False, False)
        poner_icono(self)
        w, h = 340, 470
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth() - w) // 2}"
                      f"+{(self.winfo_screenheight() - h) // 2}")
        self.protocol("WM_DELETE_WINDOW", self.al_cancelar)

        self.logo = cargar_imagen("logo.png", (150, 157))
        tk.Label(self, image=self.logo, bg=BG).pack(pady=(16, 6))
        tk.Label(self, text="Iniciar sesión", bg=BG, fg=TXT, font=(FUENTE, 13, "bold")).pack()

        marco = tk.Frame(self, bg=BG)
        marco.pack(fill="x", padx=36, pady=10)
        tk.Label(marco, text="Usuario", bg=BG, fg=TXT2, font=(FUENTE, 9)).pack(anchor="w")
        self.e_user = tk.Entry(marco, bg=CARD, fg=TXT, insertbackground=TXT, relief="flat",
                               font=(FUENTE, 10))
        self.e_user.pack(fill="x", ipady=5, pady=(0, 8))
        tk.Label(marco, text="Contraseña", bg=BG, fg=TXT2, font=(FUENTE, 9)).pack(anchor="w")
        self.e_pass = tk.Entry(marco, show="•", bg=CARD, fg=TXT, insertbackground=TXT,
                               relief="flat", font=(FUENTE, 10))
        self.e_pass.pack(fill="x", ipady=5)
        self.lbl_msg = tk.Label(marco, text="", bg=BG, fg="#ff5252", font=(FUENTE, 9))
        self.lbl_msg.pack(pady=(8, 0))

        self.btn = tk.Button(self, text="Entrar", command=self.intentar, bg=BG, fg=TXT,
                             activebackground=CARD, activeforeground=TXT,
                             highlightbackground=TXT, highlightthickness=1, relief="flat",
                             font=(FUENTE, 10, "bold"), cursor="hand2")
        self.btn.pack(fill="x", padx=36, ipady=5)
        tk.Label(self, text=f"Intentos permitidos: {logica.MAX_INTENTOS}", bg=BG, fg=TXT2,
                 font=(FUENTE, 8)).pack(pady=8)
        self.bind("<Return>", lambda e: self.intentar())
        self.e_user.focus_set()

    def intentar(self):
        if logica.validar_login(self.e_user.get(), self.e_pass.get()):
            self.destroy()
            self.al_entrar()
            return
        self.intentos += 1
        restantes = logica.MAX_INTENTOS - self.intentos
        if restantes <= 0:
            self.btn.config(state="disabled")
            messagebox.showerror("Acceso denegado",
                                 "Demasiados intentos fallidos.\nEl inicio de sesión fue "
                                 "cancelado.", parent=self)
            self.al_cancelar()
        else:
            self.lbl_msg.config(text=f"Credenciales incorrectas. Intentos restantes: {restantes}")
            self.e_pass.delete(0, "end")


# --------------------------------------------------- imagen según el clima ----
class VentanaImagen(tk.Toplevel):
    """Escena de carretera que cambia según la categoría del clima."""
    W, H = 460, 270

    CIELO = {"despejado": "#4aa3ff", "nublado": "#8da0b3", "lluvia": "#566678",
             "tormenta": "#2e3440", "niebla": "#b9c0c7", "nieve": "#c8d6e5"}

    def __init__(self, master):
        super().__init__(master)
        self.title("Don Climas - Condiciones en carretera")
        self.configure(bg=BG)
        self.resizable(False, False)
        poner_icono(self)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.logo = cargar_imagen("logo.png", (46, 48))
        cab = tk.Frame(self, bg=BG)
        cab.pack(fill="x", padx=10, pady=8)
        tk.Label(cab, image=self.logo, bg=BG).pack(side="left")
        self.lbl_tit = tk.Label(cab, text="", bg=BG, fg=TXT, font=(FUENTE, 11, "bold"))
        self.lbl_tit.pack(side="left", padx=10)
        self.cv = tk.Canvas(self, width=self.W, height=self.H, highlightthickness=0, bg=BG)
        self.cv.pack(padx=10)
        self.lbl_rec = tk.Label(self, text="", bg=BG, fg=TXT2, wraplength=440,
                                font=(FUENTE, 9), justify="left")
        self.lbl_rec.pack(padx=10, pady=8)

    def mostrar(self, datos):
        cat = datos["categoria"]
        self.lbl_tit.config(text=f"{datos['ciudad']}: {datos['condicion']}")
        self.lbl_rec.config(text="Recomendación al operador: " + logica.RECOMENDACION[cat])
        self._dibujar(cat)
        self.deiconify()
        self.lift()

    def _dibujar(self, cat):
        c, W, H = self.cv, self.W, self.H
        c.delete("all")
        c.create_rectangle(0, 0, W, H, fill=self.CIELO[cat], outline="")
        if cat == "despejado":
            c.create_oval(330, 20, 410, 100, fill="#ffd23f", outline="#ffb300", width=3)
        if cat in ("nublado", "lluvia", "tormenta", "nieve"):
            col = "#4a4f5a" if cat == "tormenta" else "#e8eef5" if cat != "lluvia" else "#9aa5b1"
            for x, y in ((40, 30), (180, 15), (320, 35)):
                for dx, dy, r in ((0, 10, 26), (28, 0, 32), (60, 10, 26)):
                    c.create_oval(x + dx - r, y + dy - r // 2, x + dx + r, y + dy + r // 2 + 14,
                                  fill=col, outline="")
        if cat == "niebla":
            for i in range(6):
                c.create_rectangle(0, 30 + i * 28, W, 50 + i * 28, fill="#e4e8ec",
                                   outline="", stipple="gray50")
        # pasto y carretera
        c.create_rectangle(0, 150, W, H, fill="#4f7d3a" if cat != "nieve" else "#f4f8fb",
                           outline="")
        c.create_polygon(150, 150, 310, 150, W, H, 0, H, fill="#3b3b3f", outline="")
        c.create_polygon(228, 150, 232, 150, 252, H, 208, H, fill="#f2f2f2", outline="")
        # autobús
        c.create_rectangle(70, 175, 215, 225, fill="#2f7de1", outline="#1b4f9c", width=2)
        for x in range(80, 205, 28):
            c.create_rectangle(x, 182, x + 22, 200, fill="#d6ebff", outline="")
        c.create_rectangle(70, 205, 215, 210, fill="#ffffff", outline="")
        for x in (100, 185):
            c.create_oval(x - 11, 215, x + 11, 237, fill="#111", outline="#777", width=2)
        faro = "#fff3a0" if cat in ("lluvia", "tormenta", "niebla", "nublado") else "#ffffff"
        c.create_oval(210, 208, 220, 218, fill=faro, outline="")
        # efectos
        if cat in ("lluvia", "tormenta"):
            for i in range(60):
                x = (i * 37) % W
                y = (i * 53) % 180
                c.create_line(x, y, x - 6, y + 16, fill="#b8d4ff")
        if cat == "tormenta":
            c.create_polygon(380, 10, 350, 70, 372, 70, 355, 125, 405, 55, 382, 55, 400, 10,
                             fill="#ffe14d", outline="#ffb300")
        if cat == "nieve":
            for i in range(70):
                x = (i * 41) % W
                y = (i * 59) % H
                c.create_oval(x, y, x + 5, y + 5, fill="#ffffff", outline="#dbe7f3")


# ---------------------------------------------------------------- SUS ----
class VentanaSUS(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Don Climas - Evaluación de usabilidad (SUS)")
        self.configure(bg=BG)
        poner_icono(self)
        self.logo = cargar_imagen("logo.png", (46, 48))
        cab = tk.Frame(self, bg=BG)
        cab.pack(fill="x", padx=12, pady=8)
        tk.Label(cab, image=self.logo, bg=BG).pack(side="left")
        tk.Label(cab, text="Cuestionario SUS: 1 = totalmente en desacuerdo, "
                           "5 = totalmente de acuerdo", bg=BG, fg=TXT,
                 font=(FUENTE, 10)).pack(side="left", padx=10)
        nom = tk.Frame(self, bg=BG)
        nom.pack(fill="x", padx=12)
        tk.Label(nom, text="Participante:", bg=BG, fg=TXT2).pack(side="left")
        self.e_nombre = tk.Entry(nom, bg=CARD, fg=TXT, insertbackground=TXT, relief="flat")
        self.e_nombre.pack(side="left", padx=6, ipady=3)

        self.vars = []
        cuerpo = tk.Frame(self, bg=BG)
        cuerpo.pack(padx=12, pady=8)
        for i, q in enumerate(logica.SUS_PREGUNTAS):
            tk.Label(cuerpo, text=f"{i + 1}. {q}", bg=BG, fg=TXT, anchor="w", wraplength=480,
                     justify="left", font=(FUENTE, 9)).grid(row=i, column=0, sticky="w", pady=3)
            v = tk.IntVar(value=0)
            self.vars.append(v)
            fila = tk.Frame(cuerpo, bg=BG)
            fila.grid(row=i, column=1, padx=10)
            for n in range(1, 6):
                tk.Radiobutton(fila, text=str(n), variable=v, value=n, bg=BG, fg=TXT,
                               selectcolor=CARD, activebackground=BG,
                               activeforeground=TXT).pack(side="left")
        tk.Button(self, text="Calcular y guardar", command=self.enviar, bg=BG, fg=TXT,
                  highlightbackground=TXT, highlightthickness=1, relief="flat",
                  cursor="hand2").pack(pady=(0, 12), ipadx=12, ipady=4)

    def enviar(self):
        resp = [v.get() for v in self.vars]
        if 0 in resp:
            messagebox.showwarning("Faltan respuestas", "Responde las 10 afirmaciones.",
                                   parent=self)
            return
        p = logica.guardar_sus(self.e_nombre.get().strip(), resp)
        messagebox.showinfo("Resultado SUS",
                            f"Puntaje de usabilidad: {p:.1f} / 100\n{logica.clasificar_sus(p)}",
                            parent=self)
        self.destroy()


# ----------------------------------------------------------- ventana principal ----
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("Don Climas - Monitoreo meteorológico para transporte terrestre")
        self.configure(bg=BG)
        self.geometry("900x520")
        self.minsize(820, 480)
        poner_icono(self)
        self.cola = queue.Queue()
        self.ventana_img = None
        self._estilos()
        self._menu()
        self._interfaz()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.after(100, self._revisar_cola)
        Splash(self, self._mostrar_login)

    # -- flujo splash -> login -> principal
    def _mostrar_login(self):
        Login(self, self._entrar, self.destroy)

    def _entrar(self):
        self.deiconify()

    # -- estilo ttk
    def _estilos(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TXT,
                    rowheight=30, borderwidth=0, font=(FUENTE, 9))
        s.configure("Treeview.Heading", background=PANEL, foreground=TXT, borderwidth=0,
                    font=(FUENTE, 9, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", CARD)])

    def _menu(self):
        mb = tk.Menu(self)
        m1 = tk.Menu(mb, tearoff=0)
        m1.add_command(label="Consultar clima", command=self.consultar)
        m1.add_command(label="Ver imagen del clima", command=self._reabrir_imagen)
        m1.add_separator()
        m1.add_command(label="Salir", command=self.destroy)
        mb.add_cascade(label="Archivo", menu=m1)
        m2 = tk.Menu(mb, tearoff=0)
        m2.add_command(label="Guardar API Key", command=self.guardar_key)
        m2.add_command(label="Limpiar campos", command=self.limpiar)
        mb.add_cascade(label="Configuración", menu=m2)
        m3 = tk.Menu(mb, tearoff=0)
        m3.add_command(label="Evaluar usabilidad (SUS)", command=lambda: VentanaSUS(self))
        m3.add_command(label="Generar PDF de usabilidad", command=self.generar_pdf)
        m3.add_separator()
        m3.add_command(label="Acerca de", command=self.acerca_de)
        mb.add_cascade(label="Ayuda", menu=m3)
        self.config(menu=mb)

    # -- interfaz según wireframe
    def _interfaz(self):
        izq = tk.Frame(self, bg=BG, width=260)
        izq.pack(side="left", fill="y", padx=(12, 6), pady=12)
        izq.pack_propagate(False)

        # Configuración de acceso (2: API Key)
        f1 = tk.LabelFrame(izq, text=" Configuración de acceso ", bg=BG, fg=TXT2,
                           font=(FUENTE, 9), bd=1, relief="solid", highlightbackground=BORDE)
        f1.pack(fill="x")
        fila = tk.Frame(f1, bg=BG)
        fila.pack(fill="x", padx=10, pady=(8, 2))
        insignia(fila, 2, BG).pack(side="left")
        tk.Label(fila, text="API Key", bg=BG, fg=TXT, font=(FUENTE, 9)).pack(side="left", padx=4)
        caja = tk.Frame(f1, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
        caja.pack(fill="x", padx=10, pady=2)
        self.e_key = tk.Entry(caja, show="•", bg=PANEL, fg=TXT, insertbackground=TXT,
                              relief="flat", font=(FUENTE, 10))
        self.e_key.pack(side="left", fill="x", expand=True, ipady=5, padx=4)
        self.ver_key = False
        ojo = tk.Label(caja, text="👁", bg=PANEL, fg=TXT2, cursor="hand2")
        ojo.pack(side="right", padx=6)
        ojo.bind("<Button-1>", self._toggle_key)
        self.e_key.insert(0, logica.cargar_config().get("api_key", ""))
        BotonPunteado(f1, "Guardar API Key", self.guardar_key).pack(fill="x", padx=10, pady=10)

        # Ubicación (1: ciudad, 3: consultar)
        f2 = tk.LabelFrame(izq, text=" Ubicación ", bg=BG, fg=TXT2, font=(FUENTE, 9),
                           bd=1, relief="solid", highlightbackground=BORDE)
        f2.pack(fill="x", pady=12)
        fila = tk.Frame(f2, bg=BG)
        fila.pack(fill="x", padx=10, pady=(8, 2))
        insignia(fila, 1, BG).pack(side="left")
        tk.Label(fila, text="Ciudad o ubicación", bg=BG, fg=TXT,
                 font=(FUENTE, 9)).pack(side="left", padx=4)
        caja2 = tk.Frame(f2, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
        caja2.pack(fill="x", padx=10, pady=2)
        self.e_ciudad = tk.Entry(caja2, bg=PANEL, fg=TXT, insertbackground=TXT, relief="flat",
                                 font=(FUENTE, 10))
        self.e_ciudad.pack(side="left", fill="x", expand=True, ipady=5, padx=4)
        tk.Label(caja2, text="📍", bg=PANEL, fg=TXT2).pack(side="right", padx=6)
        self._placeholder(self.e_ciudad, "Ej. Celaya, Guanajuato")

        fb = tk.Frame(f2, bg=BG)
        fb.pack(fill="x", padx=10, pady=(10, 6))
        self.btn_consultar = tk.Button(
            fb, text="Consultar clima", command=self.consultar, bg=BG, fg=TXT,
            activebackground=CARD, activeforeground=TXT, highlightbackground=TXT,
            highlightcolor=TXT, highlightthickness=2, relief="flat", cursor="hand2",
            font=(FUENTE, 10, "bold"))
        self.btn_consultar.pack(fill="x", ipady=6)
        insignia(fb, 3, BG).place(x=10, rely=0.5, anchor="w")
        BotonPunteado(f2, "Limpiar", self.limpiar).pack(fill="x", padx=10, pady=(4, 12))

        # Panel derecho (4: datos meteorológicos)
        der = tk.Frame(self, bg=BG)
        der.pack(side="left", fill="both", expand=True, padx=(6, 12), pady=12)
        cab = tk.Frame(der, bg=BG)
        cab.pack(fill="x")
        insignia(cab, 4, BG).pack(side="left")
        self.lbl_titulo = tk.Label(cab, text="Datos meteorológicos · Celaya, GTO", bg=BG,
                                   fg=TXT, font=(FUENTE, 11, "bold"))
        self.lbl_titulo.pack(side="left", padx=6)
        self.lbl_riesgo = tk.Label(cab, text="⚠ Riesgo: bajo / medio / alto", bg=BG, fg=TXT,
                                   font=(FUENTE, 9), highlightbackground=TXT2,
                                   highlightthickness=1, padx=10, pady=3)
        self.lbl_riesgo.pack(side="right")

        rejilla = tk.Frame(der, bg=BG)
        rejilla.pack(fill="x", pady=10)
        self.valores = {}
        campos = [("temp", "Temperatura", "-- °C"), ("humedad", "Humedad", "-- %"),
                  ("viento", "Viento", "-- km/h"), ("visibilidad", "Visibilidad", "-- km"),
                  ("lluvia", "Lluvia", "-- mm"), ("condicion", "Condición", "----")]
        for i, (k, nombre, vacio) in enumerate(campos):
            tarjeta = tk.Frame(rejilla, bg=PANEL, highlightbackground=BORDE,
                               highlightthickness=1)
            tarjeta.grid(row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4)
            tk.Label(tarjeta, text=nombre, bg=PANEL, fg=TXT2, font=(FUENTE, 9)).pack(
                anchor="w", padx=10, pady=(8, 0))
            lbl = tk.Label(tarjeta, text=vacio, bg=PANEL, fg=TXT, font=(FUENTE, 14, "bold"),
                           anchor="w")
            lbl.pack(anchor="w", padx=10, pady=(0, 8))
            self.valores[k] = (lbl, vacio)
        for c in range(3):
            rejilla.columnconfigure(c, weight=1, uniform="a")

        marco = tk.Frame(der, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
        marco.pack(fill="both", expand=True, padx=4)
        self.tabla = ttk.Treeview(marco, columns=("hora", "temp", "pron"), show="headings",
                                  height=3, selectmode="none")
        for col, txt, w in (("hora", "Hora", 120), ("temp", "Temp.", 120),
                            ("pron", "Pronóstico", 260)):
            self.tabla.heading(col, text=txt, anchor="w")
            self.tabla.column(col, width=w, anchor="w")
        self.tabla.pack(fill="both", expand=True, padx=6, pady=6)
        self._tabla_vacia()

        self.lbl_estado = tk.Label(der, text="", bg=BG, fg=TXT2, font=(FUENTE, 9), anchor="w")
        self.lbl_estado.pack(fill="x", padx=4, pady=(6, 0))

    # -- utilidades de interfaz
    def _placeholder(self, entry, texto):
        def fuera(e=None):
            if not entry.get():
                entry.insert(0, texto)
                entry.config(fg=TXT2)

        def dentro(e=None):
            if entry.get() == texto and entry.cget("fg") == TXT2:
                entry.delete(0, "end")
                entry.config(fg=TXT)
        entry._ph = texto
        entry.bind("<FocusIn>", dentro)
        entry.bind("<FocusOut>", fuera)
        fuera()

    def _toggle_key(self, e=None):
        self.ver_key = not self.ver_key
        self.e_key.config(show="" if self.ver_key else "•")

    def _tabla_vacia(self):
        self.tabla.delete(*self.tabla.get_children())
        for _ in range(3):
            self.tabla.insert("", "end", values=("--:--", "-- °C", "----"))

    def _ciudad_texto(self):
        t = self.e_ciudad.get().strip()
        return "" if t == getattr(self.e_ciudad, "_ph", None) and self.e_ciudad.cget("fg") == TXT2 else t

    # -- acciones
    def guardar_key(self):
        key = self.e_key.get().strip()
        if not key:
            messagebox.showwarning("API Key", "Escribe tu API Key de OpenWeatherMap "
                                   "(o 'demo' para datos de prueba).")
            return
        cfg = logica.cargar_config()
        cfg["api_key"] = key
        logica.guardar_config(cfg)
        self.lbl_estado.config(text="API Key guardada.", fg="#3ddc84")

    def limpiar(self):
        self.e_ciudad.delete(0, "end")
        self._placeholder(self.e_ciudad, "Ej. Celaya, Guanajuato")
        self.lbl_titulo.config(text="Datos meteorológicos · Celaya, GTO")
        self.lbl_riesgo.config(text="⚠ Riesgo: bajo / medio / alto", fg=TXT,
                               highlightbackground=TXT2)
        for lbl, vacio in self.valores.values():
            lbl.config(text=vacio)
        self._tabla_vacia()
        self.lbl_estado.config(text="")
        if self.ventana_img:
            self.ventana_img.withdraw()

    def consultar(self):
        ciudad, key = self._ciudad_texto(), self.e_key.get().strip()
        if not ciudad:
            messagebox.showwarning("Ubicación", "Escribe una ciudad o ubicación.")
            return
        if not key:
            messagebox.showwarning("API Key", "Captura tu API Key (o 'demo').")
            return
        self.btn_consultar.config(state="disabled")
        self.lbl_estado.config(text="Consultando…", fg=TXT2)

        def tarea():
            try:
                self.cola.put(("ok", logica.consultar_clima(ciudad, key)))
            except logica.ErrorClima as e:
                self.cola.put(("error", str(e)))
            except Exception as e:  # noqa: BLE001
                self.cola.put(("error", f"Error inesperado: {e}"))
        threading.Thread(target=tarea, daemon=True).start()

    def _revisar_cola(self):
        try:
            while True:
                tipo, dato = self.cola.get_nowait()
                self.btn_consultar.config(state="normal")
                if tipo == "ok":
                    self._mostrar(dato)
                else:
                    self.lbl_estado.config(text=dato, fg="#ff5252")
        except queue.Empty:
            pass
        self.after(100, self._revisar_cola)

    def _mostrar(self, d):
        self.ultimo = d
        self.lbl_titulo.config(text=f"Datos meteorológicos · {d['ciudad']}")
        formatos = {"temp": f"{d['temp']:.0f} °C", "humedad": f"{d['humedad']:.0f} %",
                    "viento": f"{d['viento']:.0f} km/h", "visibilidad": f"{d['visibilidad']:.1f} km",
                    "lluvia": f"{d['lluvia']:.1f} mm", "condicion": d["condicion"]}
        for k, v in formatos.items():
            self.valores[k][0].config(text=v)
        col = COLOR_RIESGO[d["riesgo"]]
        self.lbl_riesgo.config(text=f"⚠ Riesgo: {d['riesgo']}", fg=col, highlightbackground=col)
        self.tabla.delete(*self.tabla.get_children())
        for fila in d["pronostico"]:
            self.tabla.insert("", "end", values=fila)
        for _ in range(3 - len(d["pronostico"])):
            self.tabla.insert("", "end", values=("--:--", "-- °C", "----"))
        self.lbl_estado.config(text="Consulta completada.", fg="#3ddc84")
        if not self.ventana_img or not self.ventana_img.winfo_exists():
            self.ventana_img = VentanaImagen(self)
        self.ventana_img.mostrar(d)

    def _reabrir_imagen(self):
        if hasattr(self, "ultimo"):
            if not self.ventana_img or not self.ventana_img.winfo_exists():
                self.ventana_img = VentanaImagen(self)
            self.ventana_img.mostrar(self.ultimo)
        else:
            messagebox.showinfo("Imagen del clima", "Primero consulta el clima de una ciudad.")

    def generar_pdf(self):
        try:
            import usability_report
            ruta = usability_report.generar_pdf(NOMBRE_ALUMNO)
            messagebox.showinfo("PDF generado", f"Reporte guardado en:\n{ruta}")
        except ValueError as e:
            messagebox.showwarning("Sin datos", str(e))
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")

    def acerca_de(self):
        messagebox.showinfo("Acerca de",
                            "Don Climas\nSistema de monitoreo meteorológico para transporte "
                            f"terrestre\n\nAlumno: {NOMBRE_ALUMNO}")


if __name__ == "__main__":
    App().mainloop()
