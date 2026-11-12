import tkinter as tk
from dataclasses import fields
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, ImageTk

from invernadero import verificacion
from invernadero.campos import BOOLEANOS, CAMPOS
from invernadero.explicador import explicar_paso, texto_ecuaciones
from invernadero.graficas import COLORES
from invernadero.informe import generar_informe
from invernadero.parametros import Parametros, escenarios
from invernadero.sesion import VELOCIDADES, etiqueta_velocidad
from .tema import AZUL, GRIS, NARANJA, ROJO, VERDE, fuente_mono, hora_de


NOMBRES_EVENTO = {
    "inicio": "Inicio",
    "fin": "Fin",
    "riego_on": "Riego activado",
    "riego_off": "Riego desactivado",
    "vent_on": "Ventilación activada",
    "vent_off": "Ventilación desactivada",
    "luz_on": "Iluminación activada",
    "luz_off": "Iluminación desactivada",
}

# Construye el panel principal y sus herramientas de simulación.
class ControlCenterPanel(tk.Frame):

    def __init__(
            self,
            parent,
            sesion_simulacion,
            cambiar_pantalla_callback=None,
            abrir_invernadero=None,
            volver_inicio=None,
            **kwargs,
    ):
        super().__init__(parent, bg="#F8FAFC")
        self.sesion = sesion_simulacion
        self.cambiar_pantalla = cambiar_pantalla_callback
        self.abrir_invernadero = abrir_invernadero
        self.volver_inicio = volver_inicio

        self.fuente_mono = fuente_mono(self)
        self.vars = {}
        self._ev_mostrados = 0
        self._ultimo_calc = None
        self._sombras = []
        self._pendiente = {"graficas": True, "calculos": True, "datos": True}
        self.indice_actual = 0
        self.vistas = []

        # Colores utilizados en el menú lateral, las tarjetas y el contenido.
        self.PALETA = {
            "bg_sidebar": "#FFFFFF",
            "bg_content": "#F8FAFC",
            "bg_card": "#FFFFFF",
            "border_card": "#E2E8F0",
            "verde_primary": "#008075",
            "verde_card_title": "#007A29",
            "verde_boton_menu": "#F1F5F9",
            "verde_activo": "#22C55E",
            "rojo_inactivo": "#EF4444",
            "cyan_agua": "#00E5FF",
            "verde_destacado": "#10B981",
            "texto_dark": "#1E293B",
            "texto_light": "#64748B",
        }

        self._crear_interfaz()

        if hasattr(self.sesion, "suscribir"):
            self.sesion.suscribir(self._al_cambiar)
        elif hasattr(self.sesion, "registrar_observador"):
            self.sesion.registrar_observador(self._al_cambiar)
        elif hasattr(self.sesion, "agregar_observador"):
            self.sesion.agregar_observador(self._al_cambiar)

        self._al_cambiar("nueva")

    def _crear_interfaz(self):
        self.columnconfigure(0, weight=0, minsize=240)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._crear_sidebar()

        self.area_derecha = tk.Frame(self, bg=self.PALETA["bg_content"])
        self.area_derecha.grid(row=0, column=1, sticky="nsew")

        self._crear_barra_superior(self.area_derecha)

        # Contenedor donde se crean las seis secciones del Control Center.
        self.contenedor_vistas = tk.Frame(self.area_derecha, bg=self.PALETA["bg_content"])
        self.contenedor_vistas.pack(fill="both", expand=True, padx=20, pady=10)

        # Las vistas ocupan la misma posición y se muestra una a la vez.
        self.contenedor_vistas.grid_rowconfigure(0, weight=1)
        self.contenedor_vistas.grid_columnconfigure(0, weight=1)

        self._crear_panel_dashboard()
        self._crear_graficas()
        self._crear_calculos()
        self._crear_control()
        self._crear_datos()
        self._crear_parametros()

        self._cambiar_vista(0)

    # ----------------------------------------------------------------- Barra lateral
    def _crear_sidebar(self):
        sidebar = tk.Frame(self, bg=self.PALETA["bg_sidebar"], width=240)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        tk.Frame(self, bg=self.PALETA["border_card"], width=1).place(x=239, y=0, relheight=1)

        frame_logo = tk.Frame(sidebar, bg=self.PALETA["bg_sidebar"])
        frame_logo.pack(fill="x", padx=20, pady=(25, 30))

        # Buscar el logotipo en la carpeta de recursos gráficos.
        ruta_logo = Path(__file__).resolve().parent.parent / "assets" / "logo_green_observer.png"

        if ruta_logo.is_file():
            img_pil = Image.open(ruta_logo).convert("RGBA")
            img_pil.thumbnail((50, 50), Image.Resampling.LANCZOS)
            self.img_logo = ImageTk.PhotoImage(img_pil, master=self)
            lbl_img = tk.Label(frame_logo, image=self.img_logo, bg=self.PALETA["bg_sidebar"])
            lbl_img.pack(side="left", padx=(0, 10))
        # Mostrar un texto alternativo si no se encuentra el archivo.
        else:
            lbl_img = tk.Label(frame_logo, text="[GO]", font=("Segoe UI", 12, "bold"), fg=self.PALETA["verde_primary"],
                               bg=self.PALETA["bg_sidebar"])
            lbl_img.pack(side="left", padx=(0, 10))

        lbl_titulo = tk.Label(frame_logo, text="Green\nObserver", font=("Segoe UI", 14, "bold"),
                              fg=self.PALETA["verde_primary"], bg=self.PALETA["bg_sidebar"], justify="left")
        lbl_titulo.pack(side="left")

        # Cargar los iconos del menú; si falta alguno, se utiliza la opción sin imagen.
        self.opciones_menu = [
            ("Panel", 0, "icon_panel.png"),
            ("Gráficas", 1, "icon_graficas.png"),
            ("Cálculos", 2, "icon_calculos.png"),
            ("Control y eventos", 3, "icon_control.png"),
            ("Datos", 4, "icon_datos.png"),
            ("Parámetros", 5, "icon_parametros.png"),
        ]

        self.iconos_menu = {}
        carpeta_assets = Path(__file__).resolve().parent.parent / "assets"

        for texto, idx, archivo in self.opciones_menu:
            ruta_icono = carpeta_assets / archivo
            if ruta_icono.is_file():
                imagen = Image.open(ruta_icono).convert("RGBA")
                imagen.thumbnail((20, 20), Image.Resampling.LANCZOS)
                self.iconos_menu[idx] = ImageTk.PhotoImage(imagen, master=self)
            else:
                self.iconos_menu[idx] = None

        self.botones_menu = []

        for texto, idx, archivo in self.opciones_menu:
            btn = tk.Button(
                sidebar,
                text="  " + texto,
                image=self.iconos_menu[idx],
                compound="left",
                font=("Segoe UI", 10, "bold"),
                fg=self.PALETA["texto_light"],
                bg=self.PALETA["bg_sidebar"],
                activebackground=self.PALETA["verde_boton_menu"],
                activeforeground=self.PALETA["verde_primary"],
                bd=0,
                anchor="w",
                padx=20,
                pady=12,
                cursor="hand2",
                relief="flat",
                command=lambda i=idx: self._cambiar_vista(i),
            )
            btn.pack(fill="x")
            self.botones_menu.append(btn)

        frame_bottom = tk.Frame(sidebar, bg=self.PALETA["bg_sidebar"])
        frame_bottom.pack(side="bottom", fill="x", padx=20, pady=20)

        frame_exp = tk.Frame(frame_bottom, bg=self.PALETA["bg_sidebar"])
        frame_exp.pack(fill="x", pady=(0, 10))

        tk.Label(frame_exp, text="Exportar", font=("Segoe UI", 9, "bold"), fg=self.PALETA["texto_light"],
                 bg=self.PALETA["bg_sidebar"]).pack(side="left", padx=(0, 6))
        tk.Button(frame_exp, text="CSV", font=("Segoe UI", 8, "bold"), fg="white", bg="#10B981", bd=0, padx=10, pady=4,
                  cursor="hand2", relief="flat", command=self.exportar_csv).pack(side="left", padx=2)
        tk.Button(frame_exp, text="DOCX", font=("Segoe UI", 8, "bold"), fg="white", bg="#10B981", bd=0, padx=10, pady=4,
                  cursor="hand2", relief="flat", command=self.generar_informe).pack(side="left", padx=2)

        tk.Button(frame_bottom, text="Verificar modelo", font=("Segoe UI", 9, "bold"), fg="white",
                  bg=self.PALETA["verde_primary"], bd=0, pady=6, cursor="hand2", relief="flat",
                  command=self.verificar).pack(fill="x", pady=(0, 8))

        if self.abrir_invernadero:
            tk.Button(frame_bottom, text="Abrir Invernadero", font=("Segoe UI", 9, "bold"), fg="white",
                      bg=self.PALETA["verde_destacado"], bd=0, pady=6, cursor="hand2", relief="flat",
                      command=self.abrir_invernadero).pack(fill="x", pady=(0, 8))

        if self.volver_inicio:
            tk.Button(frame_bottom, text="⌂ Inicio", font=("Segoe UI", 9, "bold"), fg=self.PALETA["texto_dark"],
                      bg=self.PALETA["verde_boton_menu"], bd=0, pady=6, cursor="hand2", relief="flat",
                      command=self.volver_inicio).pack(fill="x")

    def _crear_barra_superior(self, parent):
        barra = tk.Frame(parent, bg="#FFFFFF", padx=15, pady=10)
        barra.pack(fill="x", side="top")

        tk.Frame(parent, bg=self.PALETA["border_card"], height=1).pack(fill="x", side="top")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", padding=5, relief="flat", background="#F1F5F9")

        tk.Label(barra, text="Escenario:", bg="#FFFFFF", fg=self.PALETA["texto_dark"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self.cb_escenario = ttk.Combobox(barra, state="readonly", width=25, font=("Segoe UI", 9))
        self.cb_escenario.pack(side="left", padx=8)
        self.cb_escenario.bind("<<ComboboxSelected>>", self._elegir_escenario)

        btn_style = {"font": ("Segoe UI", 9, "bold"), "bd": 0, "padx": 12, "pady": 5, "cursor": "hand2",
                     "relief": "flat"}

        self.btn_play = tk.Button(barra, text="▶ Iniciar", bg="#10B981", fg="white", command=self.sesion.alternar,
                                  **btn_style)
        self.btn_play.pack(side="left", padx=4)

        tk.Button(barra, text="⏭ Paso", bg="#F1F5F9", fg=self.PALETA["texto_dark"], command=self.sesion.un_paso,
                  **btn_style).pack(side="left", padx=4)
        tk.Button(barra, text="⏩ Todo", bg="#F1F5F9", fg=self.PALETA["texto_dark"], command=self.sesion.ejecutar_todo,
                  **btn_style).pack(side="left", padx=4)
        tk.Button(barra, text="⟲ Reiniciar", bg="#F1F5F9", fg=self.PALETA["texto_dark"], command=self.sesion.reiniciar,
                  **btn_style).pack(side="left", padx=4)

        tk.Label(barra, text="Velocidad:", bg="#FFFFFF", fg=self.PALETA["texto_dark"],
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(15, 0))
        self.cb_vel = ttk.Combobox(barra, state="readonly", width=12,
                                   values=[etiqueta_velocidad(v) for v in VELOCIDADES], font=("Segoe UI", 9))
        self.cb_vel.pack(side="left", padx=8)
        self.cb_vel.bind("<<ComboboxSelected>>",
                         lambda e: self.sesion.set_velocidad(VELOCIDADES[self.cb_vel.current()]))

        style.configure("TProgressbar", thickness=8, background="#10B981", troughcolor="#E2E8F0")
        self.progreso = ttk.Progressbar(parent, mode="determinate")
        self.progreso.pack(fill="x", padx=15, pady=(10, 2))

        self.lbl_tiempo = tk.Label(parent, text="", anchor="w", font=("Segoe UI", 9), bg=self.PALETA["bg_content"],
                                   fg=self.PALETA["texto_light"])
        self.lbl_tiempo.pack(fill="x", padx=15, pady=(2, 10))

    def _cambiar_vista(self, index):
        self.indice_actual = index
        for i, vista in enumerate(self.vistas):
            if i == index:
                vista.tkraise()

        for i, btn in enumerate(self.botones_menu):
            if i == index:
                btn.config(bg=self.PALETA["verde_boton_menu"], fg=self.PALETA["verde_primary"])
            else:
                btn.config(bg=self.PALETA["bg_sidebar"], fg=self.PALETA["texto_light"])

        self._refrescar_visible()

    # ================================================================= TAB 1: PANEL
    def _crear_panel_dashboard(self):
        f = tk.Frame(self.contenedor_vistas, bg=self.PALETA["bg_content"])
        f.grid(row=0, column=0, sticky="nsew")  # SUPERPUESTO
        self.vistas.append(f)

        lbl_header = tk.Label(f, text="Estado del invernadero", font=("Segoe UI", 18, "bold"),
                              fg=self.PALETA["texto_dark"], bg=self.PALETA["bg_content"])
        lbl_header.pack(pady=(10, 20))

        frame_cards = tk.Frame(f, bg=self.PALETA["bg_content"])
        frame_cards.pack(fill="x", padx=10)

        for col in range(4):
            frame_cards.columnconfigure(col, weight=1, uniform="tarjetas")

        def crear_tarjeta(col, titulo, archivo_img, var_texto):
            card = tk.Frame(frame_cards, bg=self.PALETA["bg_card"], highlightbackground=self.PALETA["border_card"],
                            highlightthickness=1)
            card.grid(row=0, column=col, sticky="nsew", padx=8, pady=8)

            tk.Label(card, text=titulo, font=("Segoe UI", 11, "bold"), fg=self.PALETA["texto_light"],
                     bg=self.PALETA["bg_card"]).pack(pady=(15, 10))

            frame_val = tk.Frame(card, bg=self.PALETA["bg_card"])
            frame_val.pack(pady=(0, 15))

            # Cargar el icono correspondiente a cada indicador.
            ruta_img = Path(__file__).resolve().parent.parent / "assets" / archivo_img
            if ruta_img.is_file():
                img_pil = Image.open(ruta_img).convert("RGBA")
                img_pil.thumbnail((35, 35), Image.Resampling.LANCZOS)  # Ajusta el tamaño (ancho, alto)
                img_tk = ImageTk.PhotoImage(img_pil, master=self)

                lbl_icono = tk.Label(frame_val, image=img_tk, bg=self.PALETA["bg_card"])

                # Mantener una referencia a la imagen para evitar que Tkinter la elimine.
                lbl_icono.image = img_tk
                lbl_icono.pack(side="left", padx=10)
            else:
                # Mostrar un aviso si no se encuentra el icono.
                tk.Label(frame_val, text="[Falta Img]", bg=self.PALETA["bg_card"], font=("Segoe UI", 9),
                         fg="gray").pack(side="left", padx=10)
            # ------------------------------------------

            lbl = tk.Label(frame_val, text=var_texto, font=("Segoe UI", 16, "bold"), bg=self.PALETA["bg_card"],
                           fg=self.PALETA["texto_dark"])
            lbl.pack(side="left")
            return lbl

        # Llamadas actualizadas
        self.lbl_card_temp = crear_tarjeta(0, "Temperatura", "icon_temp.png", "-- °C")
        self.lbl_card_hum = crear_tarjeta(1, "Humedad del suelo", "icon_hum.png", "-- %")
        self.lbl_card_luz = crear_tarjeta(2, "Iluminación", "icon_luz.png", "-- %")
        self.lbl_card_bio = crear_tarjeta(3, "Crecimiento", "icon_bio.png", "-- cm")

        # Indicadores visuales del estado de los actuadores.
        frame_actuadores = tk.Frame(f, bg=self.PALETA["bg_content"])
        frame_actuadores.pack(fill="x", pady=(30, 0), padx=10)

        for col in range(3):
            frame_actuadores.columnconfigure(col, weight=1)

        _, self.canvas_ind_riego = self._crear_badge_actuador(frame_actuadores, "Riego", 0)
        _, self.canvas_ind_vent = self._crear_badge_actuador(frame_actuadores, "Ventilación", 1)
        _, self.canvas_ind_ilum = self._crear_badge_actuador(frame_actuadores, "Iluminación artificial", 2)

    def _crear_badge_actuador(self, parent, texto, col):
        container = tk.Frame(parent, bg=self.PALETA["bg_content"])
        container.grid(row=0, column=col, padx=5)

        pill = tk.Frame(container, bg=self.PALETA["bg_card"], highlightbackground=self.PALETA["border_card"],
                        highlightthickness=1, padx=15, pady=8)
        pill.pack()

        canvas_ind = tk.Canvas(pill, width=14, height=14, bg=self.PALETA["bg_card"], highlightthickness=0)
        canvas_ind.pack(side="left", padx=(0, 8))
        canvas_ind.create_oval(2, 2, 12, 12, fill=self.PALETA["rojo_inactivo"], outline="")

        lbl = tk.Label(pill, text=texto, font=("Segoe UI", 10, "bold"), fg=self.PALETA["texto_dark"],
                       bg=self.PALETA["bg_card"])
        lbl.pack(side="left")
        return pill, canvas_ind


    def _actualizar_panel(self):
        sim = self.sesion.sim
        r, p = sim.actual, sim.p

        ct = "#EF4444" if r.T >= p.T_max else "#3B82F6" if r.T < 15 else "#10B981"
        ch = "#F59E0B" if r.H <= p.H_min else "#3B82F6" if r.H >= p.H_max else "#10B981"

        self.lbl_card_temp.config(text=f"{r.T:.1f} °C", fg=ct)
        self.lbl_card_hum.config(text=f"{r.H:.1f} %", fg=ch)
        self.lbl_card_luz.config(text=f"{r.L:.1f} %", fg="#D97706")
        self.lbl_card_bio.config(text=f"{r.P:.2f} cm" if getattr(p, "usar_crecimiento", True) else "N/A")

        self._set_estado_badge(self.canvas_ind_riego, r.riego)
        self._set_estado_badge(self.canvas_ind_vent, r.vent)
        self._set_estado_badge(self.canvas_ind_ilum, r.luz)

    def _set_estado_badge(self, canvas, activo):
        color = self.PALETA["verde_activo"] if activo else self.PALETA["rojo_inactivo"]
        canvas.delete("all")
        canvas.create_oval(2, 2, 12, 12, fill=color, outline="")

    # ================================================================= TAB 2: GRÁFICAS
    def _crear_graficas(self):
        f = tk.Frame(self.contenedor_vistas, bg=self.PALETA["bg_content"])
        f.grid(row=0, column=0, sticky="nsew")
        self.vistas.append(f)
        self.fig = Figure(figsize=(9, 7), dpi=100)
        self.canvas_fig = FigureCanvasTkAgg(self.fig, master=f)
        self.canvas_fig.get_tk_widget().pack(fill="both", expand=True)

    def _configurar_graficas(self):
        p = self.sesion.p
        self.fig.clear()
        n = 4 if p.usar_crecimiento else 3
        self.axs = a = self.fig.subplots(n, 1, sharex=True)
        self.ln = {}
        self.ln["T"], = a[0].plot([], [], color=COLORES["T"], label="T interior")
        self.ln["Tamb"], = a[0].plot([], [], color="gray", ls=":", label="T exterior")
        a[0].set_ylabel("Temperatura [°C]")
        self.ln["H"], = a[1].plot([], [], color=COLORES["H"], label="Humedad")
        a[1].set_ylabel("Humedad [%]")
        self.ln["Lnat"], = a[2].plot([], [], color=COLORES["L"], label="luz natural")
        self.ln["L"], = a[2].plot([], [], color="#8e44ad", ls="--", label="luz efectiva")
        a[2].set_ylabel("Luminosidad [%]")
        if p.usar_crecimiento:
            self.ln["P"], = a[3].plot([], [], color=COLORES["P"], label="Planta")
            a[3].set_ylabel("Tamaño [cm]")
        if p.control_activo:
            a[0].axhline(p.T_max, color=COLORES["T"], ls="--", lw=0.8, label="T_max (ventilar)")
            a[0].axhline(p.T_ok, color=COLORES["T"], ls=":", lw=0.8, label="T_ok (apagar)")
            a[1].axhline(p.H_min, color=COLORES["H"], ls="--", lw=0.8, label="H_min (regar)")
            a[1].axhline(p.H_max, color=COLORES["H"], ls=":", lw=0.8, label="H_max (apagar)")
            if p.usar_iluminacion:
                a[2].axhline(p.L_min, color="#8e44ad", ls=":", lw=0.8, label="L_min")
        for ax in a:
            ax.grid(alpha=0.3)
            ax.set_xlim(0, p.duracion / 60.0)
            ax.legend(loc="upper right", fontsize=7, ncol=3)
        a[1].set_ylim(0, 100)
        a[-1].set_xlabel("Tiempo [h]")
        self.fig.tight_layout()
        self._sombras = []

    def _actualizar_graficas(self):
        rs = self.sesion.sim.registros
        t = [r.t / 60.0 for r in rs]
        self.ln["T"].set_data(t, [r.T for r in rs])
        self.ln["Tamb"].set_data(t, [r.Tamb for r in rs])
        self.ln["H"].set_data(t, [r.H for r in rs])
        self.ln["Lnat"].set_data(t, [r.Lnat for r in rs])
        self.ln["L"].set_data(t, [r.L for r in rs])
        if "P" in self.ln:
            self.ln["P"].set_data(t, [r.P for r in rs])
        for s in self._sombras:
            s.remove()
        self._sombras = []
        for ax, attr, color in (
                (self.axs[0], "vent", "#5bc0de"),
                (self.axs[1], "riego", "#7fb3d5"),
                (self.axs[2], "luz", "#f7dc6f"),
        ):
            flags = [getattr(r, attr) for r in rs]
            if any(flags):
                self._sombras.append(
                    ax.fill_between(
                        t, 0, 1, where=flags, color=color, alpha=0.25, transform=ax.get_xaxis_transform(), linewidth=0,
                    )
                )
        for i, ax in enumerate(self.axs):
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=(i != 1))
        self.canvas_fig.draw_idle()

    # ================================================================= TAB 3: CÁLCULOS
    def _crear_calculos(self):
        f = tk.Frame(self.contenedor_vistas, bg=self.PALETA["bg_content"])
        f.grid(row=0, column=0, sticky="nsew")
        self.vistas.append(f)

        panel = ttk.PanedWindow(f, orient="horizontal")
        panel.pack(fill="both", expand=True)

        izq = tk.LabelFrame(panel, text="Ecuaciones del modelo", bg=self.PALETA["bg_card"],
                            fg=self.PALETA["texto_dark"], bd=1, relief="solid", padx=10, pady=10)
        self.txt_ecu = tk.Text(izq, width=55, font=self.fuente_mono, wrap="none", bg="#F8FAFC", bd=0,
                               highlightthickness=0)
        self.txt_ecu.pack(fill="both", expand=True)
        panel.add(izq, weight=2)

        der = tk.LabelFrame(panel, text="Cálculo del paso seleccionado", bg=self.PALETA["bg_card"],
                            fg=self.PALETA["texto_dark"], bd=1, relief="solid", padx=10, pady=10)
        nav = tk.Frame(der, bg=self.PALETA["bg_card"])
        nav.pack(fill="x")

        style = ttk.Style()
        style.configure("TButton", padding=3)

        ttk.Button(nav, text="◀", width=3, command=lambda: self._mover_paso(-1)).pack(side="left")
        self.paso_sel = tk.IntVar(value=0)
        self.spin = ttk.Spinbox(nav, from_=0, to=0, textvariable=self.paso_sel, width=8, command=self._mostrar_calculo)
        self.spin.pack(side="left", padx=4)
        self.spin.bind("<Return>", lambda e: self._mostrar_calculo())
        ttk.Button(nav, text="▶", width=3, command=lambda: self._mover_paso(+1)).pack(side="left")

        self.seguir = tk.BooleanVar(value=True)
        ttk.Checkbutton(nav, text="Seguir el último paso calculado", variable=self.seguir,
                        command=self._mostrar_calculo).pack(side="left", padx=10)

        self.txt_calc = tk.Text(der, font=self.fuente_mono, wrap="none", bg="#F8FAFC", bd=0, highlightthickness=0)
        self.txt_calc.pack(fill="both", expand=True, pady=(10, 0))
        panel.add(der, weight=3)

    def _mover_paso(self, d):
        self.seguir.set(False)
        try:
            actual = int(self.paso_sel.get())
        except (tk.TclError, ValueError):
            actual = 0
        n = max(0, min(len(self.sesion.sim.registros) - 2, actual + d))
        self.paso_sel.set(n)
        self._mostrar_calculo()

    def _mostrar_calculo(self):
        sim = self.sesion.sim
        rs = sim.registros
        if len(rs) < 2:
            texto, clave = "Presione «⏭ Paso» o «▶ Iniciar» para calcular el primer paso.", None
        else:
            maxn = len(rs) - 2
            self.spin.config(to=maxn)
            if self.seguir.get():
                self.paso_sel.set(maxn)
            try:
                n = max(0, min(maxn, int(self.paso_sel.get())))
            except (tk.TclError, ValueError):
                n = maxn
            self.paso_sel.set(n)
            clave = (n, len(rs))
            if clave == self._ultimo_calc:
                return
            texto = explicar_paso(sim, n)
        self._ultimo_calc = clave
        self.txt_calc.config(state="normal")
        self.txt_calc.delete("1.0", "end")
        self.txt_calc.insert("1.0", texto)
        self.txt_calc.config(state="disabled")

    # ================================================================= TAB 4: CONTROL Y EVENTOS
    def _crear_control(self):
        f = tk.Frame(self.contenedor_vistas, bg=self.PALETA["bg_content"])
        f.grid(row=0, column=0, sticky="nsew")
        self.vistas.append(f)

        top = tk.LabelFrame(f, text="Mecanismos de control virtual", bg=self.PALETA["bg_card"],
                            fg=self.PALETA["texto_dark"], bd=1, relief="solid", padx=15, pady=15)
        top.pack(fill="x", pady=(0, 10))

        self.lbl_ctrl = {}
        for i, (clave, texto) in enumerate(
                (("riego", "Sistema de riego"), ("vent", "Ventilación"), ("luz", "Iluminación artificial"))
        ):
            tk.Label(top, text=texto, font=("Segoe UI", 10, "bold"), bg=self.PALETA["bg_card"],
                     fg=self.PALETA["texto_dark"]).grid(row=0, column=i, padx=20)
            lbl = tk.Label(top, text="inactivo", width=14, fg="white", bg=self.PALETA["rojo_inactivo"],
                           font=("Segoe UI", 11, "bold"), pady=5)
            lbl.grid(row=1, column=i, padx=20, pady=8)
            self.lbl_ctrl[clave] = lbl

        self.lbl_cont = tk.Label(top, text="", bg=self.PALETA["bg_card"], fg=self.PALETA["texto_light"],
                                 font=("Segoe UI", 9))
        self.lbl_cont.grid(row=2, column=0, columnspan=3, pady=(15, 0))

        cuadro = tk.LabelFrame(f, text="Historial de eventos", bg=self.PALETA["bg_card"], fg=self.PALETA["texto_dark"],
                               bd=1, relief="solid", padx=10, pady=10)
        cuadro.pack(fill="both", expand=True)

        self.txt_ev = tk.Text(cuadro, font=self.fuente_mono, state="disabled", bg="#F8FAFC", bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(cuadro, command=self.txt_ev.yview)
        self.txt_ev.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_ev.pack(fill="both", expand=True)

    def _actualizar_control(self):
        sim, p = self.sesion.sim, self.sesion.p
        r = sim.actual
        for clave in ("riego", "vent", "luz"):
            activo = getattr(r, clave)
            self.lbl_ctrl[clave].config(
                text="ACTIVO" if activo else "inactivo",
                bg=self.PALETA["verde_activo"] if activo else self.PALETA["rojo_inactivo"]
            )
        res = sim.resumen()
        self.lbl_cont.config(
            text=f"Activaciones – riego: {res['act_riego']} ({res['min_riego']:g} min)   |   "
                 f"ventilación: {res['act_vent']} ({res['min_vent']:g} min)   |   "
                 f"iluminación: {res['act_luz']} ({res['min_luz']:g} min)"
        )
        nuevos = sim.eventos[self._ev_mostrados:]
        if nuevos:
            self.txt_ev.config(state="normal")
            for t, tipo, txt in nuevos:
                self.txt_ev.insert(
                    "end",
                    f"t = {t:8.1f} min | {hora_de(t, p)} | "
                    f"{NOMBRES_EVENTO.get(tipo, tipo):22s} | {txt}\n",
                )
            self.txt_ev.see("end")
            self.txt_ev.config(state="disabled")
            self._ev_mostrados = len(sim.eventos)

    # ================================================================= TAB 5: DATOS
    def _crear_datos(self):
        f = tk.Frame(self.contenedor_vistas, bg=self.PALETA["bg_content"])
        f.grid(row=0, column=0, sticky="nsew")
        self.vistas.append(f)

        cols = ("t", "hora", "T", "H", "L", "P", "R", "E", "riego", "vent", "luz")
        nombres = ("t [min]", "hora", "T [°C]", "H [%]", "L [%]", "P [cm]", "R", "E", "riego", "vent.", "luz")

        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#F1F5F9", relief="flat")

        self.tabla = ttk.Treeview(f, columns=cols, show="headings")
        for c, n in zip(cols, nombres):
            self.tabla.heading(c, text=n)
            self.tabla.column(c, width=80, anchor="center")
        sb = ttk.Scrollbar(f, command=self.tabla.yview)
        self.tabla.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tabla.pack(fill="both", expand=True)

    def _actualizar_tabla(self):
        sim = self.sesion.sim
        self.tabla.delete(*self.tabla.get_children())
        onoff = lambda x: "ON" if x else "–"
        for r in sim.registros[-300:]:
            self.tabla.insert(
                "", "end",
                values=(
                    f"{r.t:g}", hora_de(r.t, sim.p), f"{r.T:.3f}", f"{r.H:.3f}", f"{r.L:.2f}", f"{r.P:.3f}", f"{r.R:g}",
                    f"{r.E:.4f}",
                    onoff(r.riego), onoff(r.vent), onoff(r.luz),
                ),
            )
        hijos = self.tabla.get_children()
        if hijos:
            self.tabla.see(hijos[-1])

    # ================================================================= TAB 6: PARÁMETROS
    def _crear_parametros(self):
        f = tk.Frame(self.contenedor_vistas, bg=self.PALETA["bg_content"])
        f.grid(row=0, column=0, sticky="nsew")
        self.vistas.append(f)

        # Crear el área desplazable para mostrar todos los parámetros.
        canvas = tk.Canvas(f, bg=self.PALETA["bg_content"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)

        # Frame que contiene los grupos de parámetros.
        marco_scrollable = tk.Frame(canvas, bg=self.PALETA["bg_content"])

        # Ajustar el área de desplazamiento cuando cambie el tamaño del contenido.
        marco_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Insertar el frame dentro del Canvas y ajustar su ancho.
        canvas_window = canvas.create_window((0, 0), window=marco_scrollable, anchor="nw")

        # Hacer que el frame se expanda para ocupar_todo el ancho del canvas
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))

        canvas.configure(yscrollcommand=scrollbar.set)

        # Mostrar el área de parámetros y su barra de desplazamiento.
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Permitir desplazarse por el formulario con la rueda del ratón.
        f.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        # -------------------------------------------------------

        # Crear los campos agrupados según la configuración de invernadero.campos.
        for i, (grupo, lista) in enumerate(CAMPOS):
            lf = tk.LabelFrame(marco_scrollable, text=grupo, bg=self.PALETA["bg_card"], fg=self.PALETA["texto_dark"],
                               bd=1,
                               relief="solid", padx=15, pady=15)
            lf.grid(row=i // 3, column=i % 3, sticky="nsew", padx=8, pady=8)
            for r, (campo, etiqueta, unidad) in enumerate(lista):
                tk.Label(lf, text=etiqueta, bg=self.PALETA["bg_card"], fg=self.PALETA["texto_dark"],
                         font=("Segoe UI", 9)).grid(row=r, column=0, sticky="w", pady=2)
                v = tk.StringVar()
                ttk.Entry(lf, textvariable=v, width=10, font=("Segoe UI", 9)).grid(row=r, column=1, padx=5, pady=2)
                tk.Label(lf, text=unidad, fg=self.PALETA["texto_light"], bg=self.PALETA["bg_card"],
                         font=("Segoe UI", 9)).grid(row=r, column=2, sticky="w")
                self.vars[campo] = v

        # Opciones
        lf = tk.LabelFrame(marco_scrollable, text="Opciones", bg=self.PALETA["bg_card"], fg=self.PALETA["texto_dark"],
                           bd=1,
                           relief="solid", padx=15, pady=15)
        lf.grid(row=len(CAMPOS) // 3, column=len(CAMPOS) % 3, sticky="nsew", padx=8, pady=8)

        # Agregar las opciones que se activan o desactivan mediante casillas.
        for campo, etiqueta in BOOLEANOS:
            v = tk.BooleanVar()
            tk.Checkbutton(lf, text=etiqueta, variable=v, bg=self.PALETA["bg_card"], fg=self.PALETA["texto_dark"],
                           activebackground=self.PALETA["bg_card"], font=("Segoe UI", 9)).pack(anchor="w", pady=2)
            self.vars[campo] = v

        # Botón Aplicar
        tk.Button(
            marco_scrollable,
            text="Aplicar parámetros y reiniciar simulación",
            bg=self.PALETA["verde_primary"], fg="white", bd=0, pady=8, font=("Segoe UI", 10, "bold"), cursor="hand2",
            relief="flat",
            command=self.aplicar_parametros,
        ).grid(row=4, column=0, columnspan=4, pady=20)

    def _cargar_formulario(self, p):
        for f in fields(p):
            v = self.vars[f.name]
            val = getattr(p, f.name)
            v.set(bool(val) if isinstance(val, bool) else f"{val:g}")

    def _leer_formulario(self):
        kw = {}
        for f in fields(Parametros):
            v = self.vars[f.name].get()
            if isinstance(f.default, bool):
                kw[f.name] = bool(v)
            else:
                try:
                    kw[f.name] = float(str(v).replace(",", "."))
                except ValueError:
                    raise ValueError(f"El valor de «{f.name}» no es un número: {v!r}")
        return Parametros(**kw)

    def aplicar_parametros(self):
        try:
            p = self._leer_formulario()
            base = self.sesion.nombre.replace(" (editado)", "")
            self.sesion.cargar(p, f"{base} (editado)")
        except ValueError as e:
            messagebox.showerror("Parámetros no válidos", str(e), parent=self)

    def _elegir_escenario(self, _e=None):
        nombre = self.cb_escenario.get()
        if nombre in escenarios():
            self.sesion.cargar_escenario(nombre)

    # Recibir las notificaciones de la sesión y actualizar los elementos del panel.
    def _al_cambiar(self, evento="actualizacion"):
        if not self.winfo_exists():
            return
        s, sim = self.sesion, self.sesion.sim
        if evento in ("nueva", "reinicio"):
            self._ev_mostrados = 0
            self._ultimo_calc = None
            self.txt_ev.config(state="normal")
            self.txt_ev.delete("1.0", "end")
            self.txt_ev.config(state="disabled")
            self.seguir.set(True)
            self.progreso.config(maximum=max(1, sim.n_pasos))
            if evento == "nueva":
                self._cargar_formulario(sim.p)
                self.txt_ecu.config(state="normal")
                self.txt_ecu.delete("1.0", "end")
                self.txt_ecu.insert("1.0", texto_ecuaciones(sim.p))
                self.txt_ecu.config(state="disabled")
            self._configurar_graficas()
            self._pendiente.update(graficas=True, calculos=True, datos=True)

        nombres = list(escenarios())
        if s.nombre not in nombres:
            nombres.append(s.nombre)
        if tuple(self.cb_escenario["values"]) != tuple(nombres):
            self.cb_escenario.config(values=nombres)
        if self.cb_escenario.get() != s.nombre:
            self.cb_escenario.set(s.nombre)

        etiqueta = etiqueta_velocidad(s.velocidad)
        if self.cb_vel.get() != etiqueta:
            self.cb_vel.set(etiqueta)

        self.btn_play.config(
            text="⏸ Pausar" if s.corriendo else "▶ Iniciar",
            bg=self.PALETA["rojo_inactivo"] if s.corriendo else self.PALETA["verde_destacado"]
        )

        r = sim.actual
        estado = "FINALIZADA" if sim.terminado else ("en ejecución" if s.corriendo else "en pausa")
        self.progreso.config(value=len(sim.registros) - 1)
        self.lbl_tiempo.config(
            text=f"Simulación {estado}  –  t = {r.t:g} min de {sim.p.duracion:g} min  "
                 f"({hora_de(r.t, sim.p)})  –  paso {len(sim.registros) - 1} de {sim.n_pasos}"
        )

        self._actualizar_panel()
        self._actualizar_control()

        for clave in self._pendiente:
            self._pendiente[clave] = True
        pesada = sim.terminado or evento != "actualizacion" or s.ticks % 10 == 0
        self._refrescar_visible(tabla=pesada)

    # Actualizar los elementos de la vista seleccionada cuando sea necesario.
    def _refrescar_visible(self, tabla=True):
        if self.indice_actual == 1 and self._pendiente["graficas"]:
            self._actualizar_graficas()
            self._pendiente["graficas"] = False
        elif self.indice_actual == 2:
            self._mostrar_calculo()
        elif self.indice_actual == 4 and tabla and self._pendiente["datos"]:
            self._actualizar_tabla()
            self._pendiente["datos"] = False

    # Exportar los registros de la simulación a un archivo CSV.
    def exportar_csv(self):
        ruta = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="simulacion.csv",
        )
        if ruta:
            self.sesion.sim.a_csv(ruta)
            messagebox.showinfo("Exportado", f"Datos guardados en:\n{ruta}", parent=self)

    # Ejecutar las pruebas del modelo y mostrar sus resultados.
    def generar_informe(self):
        s = self.sesion
        s.pausar()
        if not s.sim.terminado and messagebox.askyesno(
                "Simulación incompleta",
                "La simulación no ha terminado. ¿Ejecutarla completa antes de generar el informe?", parent=self,
        ):
            s.ejecutar_todo()
        ruta = filedialog.asksaveasfilename(
            parent=self, defaultextension=".docx", filetypes=[("Word", "*.docx")],
            initialfile="informe_invernadero.docx",
        )
        if not ruta:
            return
        try:
            generar_informe(s.sim, ruta, titulo=f"Informe de simulación – {s.nombre}")
            messagebox.showinfo("Informe generado", f"Informe guardado en:\n{ruta}", parent=self)
        except Exception as e:
            messagebox.showerror("No se pudo generar el informe", str(e), parent=self)

    def verificar(self):
        v = verificacion.ejecutar_todo()
        L = [
            "VERIFICACIÓN DEL MODELO", "=" * 60, "",
            "Humedad – cálculo manual vs programa (ejemplo del documento)",
        ]
        for n, m, c, d in v["humedad_manual"]:
            L.append(f"  n={n}   manual={m:8.3f}   programa={c:10.5f}   |dif|={d:.1e}")
        L += ["", "Temperatura – cálculo manual vs programa"]
        for caso, n, m, c, d in v["temperatura_manual"]:
            L.append(f"  {caso:34s} n={n}  manual={m:10.6f}  programa={c:10.6f}")
        L += ["", "Pruebas de coherencia"]
        L += [f"  [{'OK' if ok else 'FALLA'}] {d}" for d, ok in v["comportamientos"]]
        L += ["", "Error de Euler vs solución exacta según Δt"]
        L += [f"  Δt = {dt:5g} min   error máx = {e:.5f} °C" for dt, e in verificacion.error_vs_dt()]
        L += ["", "RESULTADO: " + ("TODO CUMPLE" if v["ok"] else "HAY PRUEBAS QUE FALLAN")]

        win = tk.Toplevel(self)
        win.title("Verificación del modelo")
        win.geometry("760x620")
        t = tk.Text(win, font=self.fuente_mono)
        t.pack(fill="both", expand=True)
        t.insert("1.0", "\n".join(L))
        t.config(state="disabled")


# Alias para mantener la retrocompatibilidad
ControlCenter = ControlCenterPanel
