"""Ventana «Invernadero virtual»: muestra la escena y controla la simulación compartida."""
import tkinter as tk
from tkinter import messagebox, ttk

from invernadero.parametros import escenarios
from invernadero.sesion import VELOCIDADES, etiqueta_velocidad
from . import escena
from .tema import AZUL, GRIS, NARANJA, ROJO, VERDE, hora_de


class VentanaInvernadero(tk.Toplevel):
    def __init__(self, maestro, sesion, abrir_control_center=None):
        super().__init__(maestro)
        self.sesion = sesion
        self.abrir_control_center = abrir_control_center
        self._fotograma = 0
        self.title("Green Observer – Invernadero virtual")
        self.geometry("1100x760")
        self.minsize(760, 560)

        self._crear_indicadores()
        self._crear_escena()
        self._crear_controles()

        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.bind("<Destroy>", self._al_destruir)
        self.sesion.suscribir(self._al_cambiar)

    # ------------------------------------------------------------ construcción
    def _crear_indicadores(self):
        barra = ttk.Frame(self, padding=(8, 8, 8, 0))
        barra.pack(fill="x")
        ttk.Label(barra, text="Invernadero virtual", font=("Arial", 18, "bold")).pack(side="left")
        self.lbl_estado = ttk.Label(barra, text="", foreground="#555")
        self.lbl_estado.pack(side="right")

        fila = ttk.Frame(self, padding=(8, 6))
        fila.pack(fill="x")
        self.ind = {}
        for clave, texto in (("T", "Temperatura"), ("H", "Humedad del suelo"), ("L", "Luminosidad"), ("P", "Planta")):
            marco = ttk.Frame(fila)
            marco.pack(side="left", expand=True, fill="x", padx=4)
            ttk.Label(marco, text=texto, font=("Arial", 9)).pack()
            lbl = tk.Label(marco, text="–", fg="white", bg=GRIS, font=("Arial", 13, "bold"), padx=8, pady=3)
            lbl.pack(fill="x")
            self.ind[clave] = lbl

    def _crear_escena(self):
        self.cv = tk.Canvas(self, bg="#DCEFD5", highlightthickness=0, width=1000, height=520)
        self.cv.pack(fill="both", expand=True, padx=8, pady=4)
        self.cv.bind("<Configure>", lambda e: self._dibujar())

    def _crear_controles(self):
        self.progreso = ttk.Progressbar(self, mode="determinate")
        self.progreso.pack(fill="x", padx=8)

        barra = ttk.Frame(self, padding=8)
        barra.pack(fill="x")
        ttk.Label(barra, text="Escenario:").pack(side="left")
        self.cb_escenario = ttk.Combobox(barra, state="readonly", width=30)
        self.cb_escenario.pack(side="left", padx=4)
        self.cb_escenario.bind("<<ComboboxSelected>>", self._elegir_escenario)

        self.btn_play = ttk.Button(barra, text="▶ Iniciar", width=11, command=self.sesion.alternar)
        self.btn_play.pack(side="left", padx=2)
        ttk.Button(barra, text="⏭ Paso", command=self.sesion.un_paso).pack(side="left", padx=2)
        ttk.Button(barra, text="⏩ Todo", command=self.sesion.ejecutar_todo).pack(side="left", padx=2)
        ttk.Button(barra, text="⟲ Reiniciar", command=self.sesion.reiniciar).pack(side="left", padx=2)

        ttk.Label(barra, text="  Velocidad:").pack(side="left")
        self.cb_vel = ttk.Combobox(barra, state="readonly", width=11,
                                   values=[etiqueta_velocidad(v) for v in VELOCIDADES])
        self.cb_vel.pack(side="left", padx=4)
        self.cb_vel.bind("<<ComboboxSelected>>", self._elegir_velocidad)

        if self.abrir_control_center:
            ttk.Button(barra, text="📊 Control Center", command=self.abrir_control_center).pack(side="right")

    # ---------------------------------------------------------------- acciones
    def _elegir_escenario(self, _e=None):
        nombre = self.cb_escenario.get()
        if nombre in escenarios():
            try:
                self.sesion.cargar_escenario(nombre)
            except ValueError as e:
                messagebox.showerror("Escenario no válido", str(e), parent=self)

    def _elegir_velocidad(self, _e=None):
        self.sesion.set_velocidad(VELOCIDADES[self.cb_vel.current()])

    def cerrar(self):
        self.destroy()

    def _al_destruir(self, evento):
        if evento.widget is self:
            self.sesion.desuscribir(self._al_cambiar)

    # -------------------------------------------------------------- observador
    def _al_cambiar(self, evento):
        if not self.winfo_exists():
            return
        self._sincronizar_controles()
        self._fotograma += 1
        self._dibujar()

    def _sincronizar_controles(self):
        s = self.sesion
        nombres = list(escenarios())
        if s.nombre not in nombres:
            nombres.append(s.nombre)                 # parámetros editados en el Control Center
        if tuple(self.cb_escenario["values"]) != tuple(nombres):
            self.cb_escenario.config(values=nombres)
        if self.cb_escenario.get() != s.nombre:
            self.cb_escenario.set(s.nombre)
        etiqueta = etiqueta_velocidad(s.velocidad)
        if self.cb_vel.get() != etiqueta:
            self.cb_vel.set(etiqueta)
        self.btn_play.config(text="⏸ Pausar" if s.corriendo else "▶ Iniciar")

    def _dibujar(self):
        s = self.sesion
        sim = s.sim
        r, p = sim.actual, sim.p
        escena.dibujar_escena(self.cv, r, p, self._fotograma)

        ct = ROJO if r.T >= p.T_max else AZUL if r.T < 15 else VERDE
        ch = NARANJA if r.H <= p.H_min else AZUL if r.H >= p.H_max else VERDE
        self._poner("T", f"{r.T:.2f} °C", ct)
        self._poner("H", f"{r.H:.2f} %", ch)
        self._poner("L", f"{r.L:.1f} %", "#c99a12")
        self._poner("P", f"{r.P:.2f} cm" if p.usar_crecimiento else "no simulada", "#2e8b57")

        paso = len(sim.registros) - 1
        self.progreso.config(maximum=max(1, sim.n_pasos), value=paso)
        estado = "FINALIZADA" if sim.terminado else ("en ejecución" if s.corriendo else "en pausa")
        self.lbl_estado.config(text=f"Simulación {estado} – {hora_de(r.t, p)} – paso {paso}/{sim.n_pasos}")

    def _poner(self, clave, texto, color):
        self.ind[clave].config(text=texto, bg=color)
