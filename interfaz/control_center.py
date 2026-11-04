"""Control Center: análisis de la simulación compartida.

Pestañas: Panel · Gráficas · Cálculos paso a paso · Control y eventos · Datos · Parámetros.
No contiene lógica de simulación: lee de la ``SesionSimulacion`` y le pide acciones.
"""
import tkinter as tk
from dataclasses import fields
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from invernadero import verificacion
from invernadero.campos import BOOLEANOS, CAMPOS
from invernadero.explicador import explicar_paso, texto_ecuaciones
from invernadero.graficas import COLORES
from invernadero.informe import generar_informe
from invernadero.parametros import Parametros, escenarios
from invernadero.sesion import VELOCIDADES, etiqueta_velocidad
from .tema import AZUL, GRIS, NARANJA, ROJO, VERDE, fuente_mono, hora_de

NOMBRES_EVENTO = {
    "inicio": "Inicio", "fin": "Fin",
    "riego_on": "Riego activado", "riego_off": "Riego desactivado",
    "vent_on": "Ventilación activada", "vent_off": "Ventilación desactivada",
    "luz_on": "Iluminación activada", "luz_off": "Iluminación desactivada",
}


class ControlCenter(ttk.Frame):
    def __init__(self, maestro, sesion, abrir_invernadero=None, volver_inicio=None):
        super().__init__(maestro)
        self.sesion = sesion
        self.abrir_invernadero = abrir_invernadero
        self.volver_inicio = volver_inicio
        self.fuente_mono = fuente_mono(self)
        self.vars = {}
        self._ev_mostrados = 0
        self._ultimo_calc = None
        self._sombras = []
        self._pendiente = {"graficas": True, "calculos": True, "datos": True}

        self._crear_barra()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self._crear_panel()
        self._crear_graficas()
        self._crear_calculos()
        self._crear_control()
        self._crear_datos()
        self._crear_parametros()
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self._refrescar_visible())

        self._al_cambiar("nueva")
        self.sesion.suscribir(self._al_cambiar)

    # ================================================================== barra
    def _crear_barra(self):
        barra = ttk.Frame(self, padding=6)
        barra.pack(fill="x")
        ttk.Label(barra, text="Escenario:").pack(side="left")
        self.cb_escenario = ttk.Combobox(barra, state="readonly", width=32)
        self.cb_escenario.pack(side="left", padx=4)
        self.cb_escenario.bind("<<ComboboxSelected>>", self._elegir_escenario)

        self.btn_play = ttk.Button(barra, text="▶ Iniciar", width=11, command=self.sesion.alternar)
        self.btn_play.pack(side="left", padx=2)
        ttk.Button(barra, text="⏭ Paso", command=self.sesion.un_paso).pack(side="left", padx=2)
        ttk.Button(barra, text="⏩ Ejecutar todo", command=self.sesion.ejecutar_todo).pack(side="left", padx=2)
        ttk.Button(barra, text="⟲ Reiniciar", command=self.sesion.reiniciar).pack(side="left", padx=2)

        ttk.Label(barra, text="  Velocidad:").pack(side="left")
        self.cb_vel = ttk.Combobox(barra, state="readonly", width=11,
                                   values=[etiqueta_velocidad(v) for v in VELOCIDADES])
        self.cb_vel.pack(side="left", padx=4)
        self.cb_vel.bind("<<ComboboxSelected>>",
                         lambda e: self.sesion.set_velocidad(VELOCIDADES[self.cb_vel.current()]))

        # segunda fila: salidas y navegación (así la barra cabe en pantallas pequeñas)
        barra2 = ttk.Frame(self, padding=(6, 0, 6, 4))
        barra2.pack(fill="x")
        if self.abrir_invernadero:
            ttk.Button(barra2, text="🌱 Invernadero virtual", command=self.abrir_invernadero).pack(side="left", padx=2)
        ttk.Button(barra2, text="Verificar modelo", command=self.verificar).pack(side="left", padx=2)
        ttk.Button(barra2, text="Exportar CSV", command=self.exportar_csv).pack(side="left", padx=2)
        ttk.Button(barra2, text="Informe (.docx)", command=self.generar_informe).pack(side="left", padx=2)
        if self.volver_inicio:
            ttk.Button(barra2, text="⌂ Inicio", command=self.volver_inicio).pack(side="right", padx=2)

        self.progreso = ttk.Progressbar(self, mode="determinate")
        self.progreso.pack(fill="x", padx=8)
        self.lbl_tiempo = ttk.Label(self, text="", anchor="w")
        self.lbl_tiempo.pack(fill="x", padx=8)

    # ================================================================== panel
    def _crear_panel(self):
        f = ttk.Frame(self.nb, padding=15)
        self.nb.add(f, text=" Panel ")
        ttk.Label(f, text="Estado del invernadero", font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 12))

        grandes = ttk.Frame(f)
        grandes.pack(fill="x", pady=(0, 14))
        self.grande = {}
        for clave, texto in (("T", "Temperatura interior"), ("H", "Humedad del suelo"),
                             ("L", "Luminosidad"), ("P", "Tamaño de la planta")):
            marco = ttk.Frame(grandes)
            marco.pack(side="left", expand=True, fill="x", padx=5)
            ttk.Label(marco, text=texto, font=("Arial", 10)).pack()
            lbl = tk.Label(marco, text="–", fg="white", bg=GRIS, font=("Arial", 18, "bold"), pady=10)
            lbl.pack(fill="x")
            self.grande[clave] = lbl

        det = ttk.LabelFrame(f, text="Detalle", padding=10)
        det.pack(fill="x")
        self.ind = {}
        for i, (clave, texto) in enumerate((("Tamb", "Temp. exterior"), ("hora", "Hora del día"),
                                            ("riego", "Riego"), ("vent", "Ventilación"),
                                            ("luz", "Iluminación artificial"))):
            ttk.Label(det, text=texto + ":", width=22).grid(row=i, column=0, sticky="w", pady=2)
            lbl = tk.Label(det, text="–", width=16, fg="white", bg=GRIS, font=("TkDefaultFont", 10, "bold"))
            lbl.grid(row=i, column=1, sticky="w", pady=2)
            self.ind[clave] = lbl
        ttk.Label(f, text="Verde = dentro del rango · Naranja/Rojo = fuera del rango · "
                          "Azul = por encima del rango (humedad) o frío",
                  foreground="#555").pack(anchor="w", pady=(10, 0))
        if self.abrir_invernadero:
            ttk.Button(f, text="🌱 Ver el invernadero virtual", command=self.abrir_invernadero).pack(anchor="w", pady=14)

    def _actualizar_panel(self):
        sim = self.sesion.sim
        r, p = sim.actual, sim.p
        ct = ROJO if r.T >= p.T_max else AZUL if r.T < 15 else VERDE
        ch = NARANJA if r.H <= p.H_min else AZUL if r.H >= p.H_max else VERDE
        for lbl, txt, col in ((self.grande["T"], f"{r.T:.2f} °C", ct), (self.grande["H"], f"{r.H:.2f} %", ch),
                              (self.grande["L"], f"{r.L:.1f} %", "#c99a12"),
                              (self.grande["P"], f"{r.P:.2f} cm" if p.usar_crecimiento else "no simulado", "#2e8b57"),
                              (self.ind["Tamb"], f"{r.Tamb:.2f} °C", "#777"),
                              (self.ind["hora"], hora_de(r.t, p), "#777")):
            lbl.config(text=txt, bg=col)
        for clave in ("riego", "vent", "luz"):
            activo = getattr(r, clave)
            self.ind[clave].config(text="ACTIVO" if activo else "inactivo", bg=VERDE if activo else GRIS)

    # ================================================================ gráficas
    def _crear_graficas(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text=" Gráficas ")
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
        for ax, attr, color in ((self.axs[0], "vent", "#5bc0de"), (self.axs[1], "riego", "#7fb3d5"),
                                (self.axs[2], "luz", "#f7dc6f")):
            flags = [getattr(r, attr) for r in rs]
            if any(flags):
                self._sombras.append(ax.fill_between(t, 0, 1, where=flags, color=color, alpha=0.25,
                                                     transform=ax.get_xaxis_transform(), linewidth=0))
        for i, ax in enumerate(self.axs):
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=(i != 1))
        self.canvas_fig.draw_idle()

    # ================================================================ cálculos
    def _crear_calculos(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text=" Cálculos paso a paso ")
        panel = ttk.PanedWindow(f, orient="horizontal")
        panel.pack(fill="both", expand=True, padx=6, pady=6)

        izq = ttk.LabelFrame(panel, text="Ecuaciones del modelo", padding=4)
        self.txt_ecu = tk.Text(izq, width=62, font=self.fuente_mono, wrap="none", bg="#fbfbf4")
        self.txt_ecu.pack(fill="both", expand=True)
        panel.add(izq, weight=2)

        der = ttk.LabelFrame(panel, text="Cálculo del paso seleccionado", padding=4)
        nav = ttk.Frame(der)
        nav.pack(fill="x")
        ttk.Button(nav, text="◀", width=3, command=lambda: self._mover_paso(-1)).pack(side="left")
        self.paso_sel = tk.IntVar(value=0)
        self.spin = ttk.Spinbox(nav, from_=0, to=0, textvariable=self.paso_sel, width=8,
                                command=self._mostrar_calculo)
        self.spin.pack(side="left", padx=4)
        self.spin.bind("<Return>", lambda e: self._mostrar_calculo())
        ttk.Button(nav, text="▶", width=3, command=lambda: self._mover_paso(+1)).pack(side="left")
        self.seguir = tk.BooleanVar(value=True)
        ttk.Checkbutton(nav, text="Seguir el último paso calculado", variable=self.seguir,
                        command=self._mostrar_calculo).pack(side="left", padx=10)
        self.txt_calc = tk.Text(der, font=self.fuente_mono, wrap="none", bg="#fbfbf4")
        self.txt_calc.pack(fill="both", expand=True, pady=(4, 0))
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

    # ============================================================== control
    def _crear_control(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text=" Control y eventos ")
        top = ttk.LabelFrame(f, text="Mecanismos de control virtual", padding=10)
        top.pack(fill="x", padx=8, pady=8)
        self.lbl_ctrl = {}
        for i, (clave, texto) in enumerate((("riego", "Sistema de riego"), ("vent", "Ventilación"),
                                            ("luz", "Iluminación artificial"))):
            ttk.Label(top, text=texto, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=i, padx=20)
            lbl = tk.Label(top, text="inactivo", width=14, fg="white", bg=GRIS, font=("TkDefaultFont", 11, "bold"))
            lbl.grid(row=1, column=i, padx=20, pady=4)
            self.lbl_ctrl[clave] = lbl
        self.lbl_cont = ttk.Label(top, text="")
        self.lbl_cont.grid(row=3, column=0, columnspan=3, pady=(8, 0))

        cuadro = ttk.LabelFrame(f, text="Historial de eventos", padding=4)
        cuadro.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.txt_ev = tk.Text(cuadro, font=self.fuente_mono, state="disabled")
        sb = ttk.Scrollbar(cuadro, command=self.txt_ev.yview)
        self.txt_ev.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_ev.pack(fill="both", expand=True)

    def _actualizar_control(self):
        sim, p = self.sesion.sim, self.sesion.p
        r = sim.actual
        for clave in ("riego", "vent", "luz"):
            activo = getattr(r, clave)
            self.lbl_ctrl[clave].config(text="ACTIVO" if activo else "inactivo", bg=VERDE if activo else GRIS)
        res = sim.resumen()
        self.lbl_cont.config(text=f"Activaciones – riego: {res['act_riego']} ({res['min_riego']:g} min)   |   "
                                  f"ventilación: {res['act_vent']} ({res['min_vent']:g} min)   |   "
                                  f"iluminación: {res['act_luz']} ({res['min_luz']:g} min)")
        nuevos = sim.eventos[self._ev_mostrados:]
        if nuevos:
            self.txt_ev.config(state="normal")
            for t, tipo, txt in nuevos:
                self.txt_ev.insert("end", f"t = {t:8.1f} min | {hora_de(t, p)} | "
                                          f"{NOMBRES_EVENTO.get(tipo, tipo):22s} | {txt}\n")
            self.txt_ev.see("end")
            self.txt_ev.config(state="disabled")
            self._ev_mostrados = len(sim.eventos)

    # ================================================================== datos
    def _crear_datos(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text=" Datos ")
        cols = ("t", "hora", "T", "H", "L", "P", "R", "E", "riego", "vent", "luz")
        nombres = ("t [min]", "hora", "T [°C]", "H [%]", "L [%]", "P [cm]", "R", "E", "riego", "vent.", "luz")
        self.tabla = ttk.Treeview(f, columns=cols, show="headings", height=20)
        for c, n in zip(cols, nombres):
            self.tabla.heading(c, text=n)
            self.tabla.column(c, width=80, anchor="center")
        sb = ttk.Scrollbar(f, command=self.tabla.yview)
        self.tabla.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tabla.pack(fill="both", expand=True, padx=6, pady=6)

    def _actualizar_tabla(self):
        sim = self.sesion.sim
        self.tabla.delete(*self.tabla.get_children())
        onoff = lambda x: "ON" if x else "–"
        for r in sim.registros[-300:]:
            self.tabla.insert("", "end", values=(f"{r.t:g}", hora_de(r.t, sim.p), f"{r.T:.3f}", f"{r.H:.3f}",
                                                 f"{r.L:.2f}", f"{r.P:.3f}", f"{r.R:g}", f"{r.E:.4f}",
                                                 onoff(r.riego), onoff(r.vent), onoff(r.luz)))
        hijos = self.tabla.get_children()
        if hijos:
            self.tabla.see(hijos[-1])

    # ============================================================== parámetros
    def _crear_parametros(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text=" Parámetros ")
        marco = ttk.Frame(f)
        marco.pack(fill="both", expand=True, padx=8, pady=8)
        for i, (grupo, lista) in enumerate(CAMPOS):
            lf = ttk.LabelFrame(marco, text=grupo, padding=6)
            lf.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
            for r, (campo, etiqueta, unidad) in enumerate(lista):
                ttk.Label(lf, text=etiqueta).grid(row=r, column=0, sticky="w")
                v = tk.StringVar()
                ttk.Entry(lf, textvariable=v, width=10).grid(row=r, column=1, padx=4, pady=1)
                ttk.Label(lf, text=unidad, foreground="#666").grid(row=r, column=2, sticky="w")
                self.vars[campo] = v
        lf = ttk.LabelFrame(marco, text="Opciones", padding=6)
        lf.grid(row=len(CAMPOS) // 3, column=len(CAMPOS) % 3, sticky="nsew", padx=5, pady=5)
        for campo, etiqueta in BOOLEANOS:
            v = tk.BooleanVar()
            ttk.Checkbutton(lf, text=etiqueta, variable=v).pack(anchor="w")
            self.vars[campo] = v
        ttk.Button(marco, text="Aplicar parámetros y reiniciar simulación",
                   command=self.aplicar_parametros).grid(row=4, column=0, columnspan=3, pady=12)

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
        """Aplica el formulario: crea una simulación nueva en la sesión (la ven todas las ventanas)."""
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

    # ============================================================ observador
    def _al_cambiar(self, evento):
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

        # --- barra común
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
        self.btn_play.config(text="⏸ Pausar" if s.corriendo else "▶ Iniciar")
        r = sim.actual
        estado = "FINALIZADA" if sim.terminado else ("en ejecución" if s.corriendo else "en pausa")
        self.progreso.config(value=len(sim.registros) - 1)
        self.lbl_tiempo.config(text=f"Simulación {estado}  –  t = {r.t:g} min de {sim.p.duracion:g} min  "
                                    f"({hora_de(r.t, sim.p)})  –  paso {len(sim.registros) - 1} de {sim.n_pasos}")

        # --- contenido: lo barato siempre; lo costoso solo si su pestaña está a la vista
        self._actualizar_panel()
        self._actualizar_control()
        for clave in self._pendiente:
            self._pendiente[clave] = True
        pesada = sim.terminado or evento != "actualizacion" or s.ticks % 10 == 0
        self._refrescar_visible(tabla=pesada)

    def _refrescar_visible(self, tabla=True):
        """Redibuja solo la pestaña visible (las demás quedan pendientes hasta que se abran)."""
        try:
            pestaña = self.nb.tab(self.nb.select(), "text").strip()
        except tk.TclError:
            return
        if pestaña == "Gráficas" and self._pendiente["graficas"]:
            self._actualizar_graficas()
            self._pendiente["graficas"] = False
        elif pestaña == "Cálculos paso a paso":
            self._mostrar_calculo()
        elif pestaña == "Datos" and tabla and self._pendiente["datos"]:
            self._actualizar_tabla()
            self._pendiente["datos"] = False

    # ============================================================== salidas
    def exportar_csv(self):
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile="simulacion.csv")
        if ruta:
            self.sesion.sim.a_csv(ruta)
            messagebox.showinfo("Exportado", f"Datos guardados en:\n{ruta}", parent=self)

    def generar_informe(self):
        s = self.sesion
        s.pausar()
        if not s.sim.terminado and messagebox.askyesno(
                "Simulación incompleta",
                "La simulación no ha terminado. ¿Ejecutarla completa antes de generar el informe?", parent=self):
            s.ejecutar_todo()
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension=".docx", filetypes=[("Word", "*.docx")],
                                            initialfile="informe_invernadero.docx")
        if not ruta:
            return
        try:
            generar_informe(s.sim, ruta, titulo=f"Informe de simulación – {s.nombre}")
            messagebox.showinfo("Informe generado", f"Informe guardado en:\n{ruta}", parent=self)
        except Exception as e:  # noqa: BLE001 - mostrar cualquier problema al usuario
            messagebox.showerror("No se pudo generar el informe", str(e), parent=self)

    def verificar(self):
        v = verificacion.ejecutar_todo()
        L = ["VERIFICACIÓN DEL MODELO", "=" * 60, "", "Humedad – cálculo manual vs programa (ejemplo del documento)"]
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
