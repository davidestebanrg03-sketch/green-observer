"""Sesión de simulación compartida entre varias ventanas (patrón observador).

La sesión es la ÚNICA dueña del simulador y del reloj. Las ventanas (el invernadero
virtual, el Control Center, ...) no calculan nada: se suscriben a la sesión, reciben
un aviso cada vez que algo cambia y leen el estado desde ``sesion.sim``.

Esto separa la simulación matemática de su representación visual:

    SesionSimulacion  ──avisa──▶  Invernadero virtual   (dibujo)
         │                  └───▶  Control Center        (gráficas, tablas, cálculos)
         └── Simulador (Euler + control)  →  modelo (ecuaciones)

No depende de Tkinter: solo necesita un «planificador» con ``after(ms, f)`` y
``after_cancel(id)`` (cualquier ventana de Tkinter lo cumple; las pruebas usan uno falso).

Eventos que reciben los observadores (``observador(evento)``):
    "actualizacion"  se calcularon pasos nuevos
    "estado"         cambió iniciar/pausar/velocidad (los datos no cambiaron)
    "nueva"          hay una simulación nueva (otro escenario o parámetros distintos)
    "reinicio"       se volvió a t = 0 con los mismos parámetros
"""
import traceback

from .parametros import Parametros, escenarios
from .simulador import Simulador

TICK_MS = 40            # periodo del reloj cuando se simula rápido [ms]

# Velocidades disponibles: pasos de simulación por segundo real.
VELOCIDADES = (1, 5, 25, 125, 500, 2000)
VELOCIDAD_INICIAL = 125


def etiqueta_velocidad(v):
    return f"{v:g} paso/s" if v == 1 else f"{v:g} pasos/s"


class SesionSimulacion:
    def __init__(self, planificador, parametros=None, nombre="Día normal"):
        self._plan = planificador
        self._tarea = None
        self._observadores = []
        self.velocidad = VELOCIDAD_INICIAL
        self.nombre = nombre
        self.sim = Simulador(parametros if parametros is not None else escenarios()[nombre])
        self._ticks = 0

    # ----------------------------------------------------------- consulta
    @property
    def p(self):
        return self.sim.p

    @property
    def corriendo(self):
        return self._tarea is not None

    @property
    def terminado(self):
        return self.sim.terminado

    @property
    def ticks(self):
        """Cantidad de avisos de avance emitidos (sirve para refrescar tablas pesadas de vez en cuando)."""
        return self._ticks

    # ------------------------------------------------------- observadores
    def suscribir(self, observador, notificar=True):
        if observador not in self._observadores:
            self._observadores.append(observador)
        if notificar:
            observador("actualizacion")

    def desuscribir(self, observador):
        if observador in self._observadores:
            self._observadores.remove(observador)

    def _avisar(self, evento):
        for obs in tuple(self._observadores):
            try:
                obs(evento)
            except Exception:  # noqa: BLE001 - una ventana defectuosa no debe detener a las demás
                traceback.print_exc()

    # ------------------------------------------------------------- reloj
    def _parametros_reloj(self):
        """(intervalo en ms, pasos por aviso) para la velocidad actual."""
        pasos_por_tick = self.velocidad * TICK_MS / 1000.0
        if pasos_por_tick < 1:
            return max(1, round(1000.0 / self.velocidad)), 1
        return TICK_MS, max(1, round(pasos_por_tick))

    def iniciar(self):
        if self._tarea is None and not self.sim.terminado:
            self._programar()
            self._avisar("estado")

    def _programar(self):
        intervalo, _ = self._parametros_reloj()
        self._tarea = self._plan.after(intervalo, self._tick)

    def _tick(self):
        self._tarea = None
        _, n = self._parametros_reloj()
        for _ in range(n):
            if not self.sim.paso():
                break
        self._ticks += 1
        if self.sim.terminado:
            self._avisar("actualizacion")
            self._avisar("estado")
        else:
            self._programar()
            self._avisar("actualizacion")

    def pausar(self):
        if self._tarea is not None:
            self._plan.after_cancel(self._tarea)
            self._tarea = None
            self._avisar("estado")

    def alternar(self):
        if self.corriendo:
            self.pausar()
        else:
            self.iniciar()

    def set_velocidad(self, pasos_por_segundo):
        v = float(pasos_por_segundo)
        if v <= 0:
            raise ValueError("La velocidad debe ser positiva.")
        self.velocidad = v
        if self._tarea is not None:           # reprogramar con el nuevo ritmo
            self._plan.after_cancel(self._tarea)
            self._programar()
        self._avisar("estado")

    # ---------------------------------------------------------- acciones
    def un_paso(self):
        """Avanza exactamente un paso (pausa el reloj si estaba en marcha)."""
        self.pausar()
        self.sim.paso()
        self._ticks += 1
        self._avisar("actualizacion")
        self._avisar("estado")

    def ejecutar_todo(self):
        self.pausar()
        self.sim.ejecutar()
        self._ticks += 1
        self._avisar("actualizacion")
        self._avisar("estado")

    def reiniciar(self):
        """Vuelve a t = 0 con los mismos parámetros."""
        self.pausar()
        self.sim.reiniciar()
        self._avisar("reinicio")

    def cargar(self, parametros, nombre=None):
        """Sustituye la simulación por otra con nuevos parámetros (lanza ValueError si no son válidos)."""
        nuevo = Simulador(parametros)       # valida antes de tocar nada
        self.pausar()
        self.sim = nuevo
        if nombre is not None:
            self.nombre = nombre
        self._avisar("nueva")

    def cargar_escenario(self, nombre):
        self.cargar(escenarios()[nombre], nombre)
