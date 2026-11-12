
import traceback

from .parametros import Parametros, escenarios
from .simulador import Simulador

# Intervalo del reloj para organizar la ejecución [ms].
TICK_MS = 40

# Velocidades expresadas en pasos de simulación por segundo real.
VELOCIDADES = (1, 5, 25, 125, 500, 2000)
VELOCIDAD_INICIAL = 125


def etiqueta_velocidad(v):
    return f"{v:g} paso/s" if v == 1 else f"{v:g} pasos/s"


class SesionSimulacion:
    # Coordina el simulador y mantiene sincronizadas las ventanas.
    def __init__(self, planificador, parametros=None, nombre="Día normal"):
        self._plan = planificador
        self._tarea = None
        self._observadores = []
        self.velocidad = VELOCIDAD_INICIAL
        self.nombre = nombre

        # La sesión crea y conserva el único simulador compartido.
        self.sim = Simulador(parametros if parametros is not None else escenarios()[nombre])
        self._ticks = 0

    # ---------------------------------------------------------- Consultas
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
        #Cantidad de avisos de avance enviados a las ventanas.
        return self._ticks

    # -------------------------------------------------------- Observadores
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

    # -------------------------------------------------------------- Reloj
    def _parametros_reloj(self):
        # Calcula el intervalo del reloj y los pasos por cada aviso.
        pasos_por_tick = self.velocidad * TICK_MS / 1000.0

        # A velocidades bajas se aumenta el intervalo entre avisos.
        if pasos_por_tick < 1:
            return max(1, round(1000.0 / self.velocidad)), 1

        # A velocidades altas se ejecutan varios pasos en cada aviso.
        return TICK_MS, max(1, round(pasos_por_tick))

    def iniciar(self):
        # Programa la ejecución si está pausada y aún no ha terminado.
        if self._tarea is None and not self.sim.terminado:
            self._programar()
            self._avisar("estado")

    def _programar(self):
        # Programa el siguiente avance utilizando el planificador.
        intervalo, _ = self._parametros_reloj()
        self._tarea = self._plan.after(intervalo, self._tick)

    def _tick(self):
        # Ejecuta los pasos correspondientes a un aviso del reloj.
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
        # Cancela el siguiente avance programado.
        if self._tarea is not None:
            self._plan.after_cancel(self._tarea)
            self._tarea = None
            self._avisar("estado")

    def alternar(self):
        # Cambia entre iniciar y pausar la simulación.
        if self.corriendo:
            self.pausar()
        else:
            self.iniciar()

    def set_velocidad(self, pasos_por_segundo):
        v = float(pasos_por_segundo)
        if v <= 0:
            raise ValueError("La velocidad debe ser positiva.")
        self.velocidad = v

        # Si está ejecutándose, programa el siguiente avance con el nuevo ritmo.
        if self._tarea is not None:
            self._plan.after_cancel(self._tarea)
            self._programar()
        self._avisar("estado")

    # ------------------------------------------------------------- Acciones
    def un_paso(self):
        # Pausa el reloj y avanza exactamente un paso de simulación.
        self.pausar()
        self.sim.paso()
        self._ticks += 1
        self._avisar("actualizacion")
        self._avisar("estado")

    def ejecutar_todo(self):
        # Ejecuta los pasos restantes hasta completar la simulación.
        self.pausar()
        self.sim.ejecutar()
        self._ticks += 1
        self._avisar("actualizacion")
        self._avisar("estado")

    def reiniciar(self):
        # Vuelve al instante inicial conservando los mismos parámetros.
        self.pausar()
        self.sim.reiniciar()
        self._avisar("reinicio")

    def cargar(self, parametros, nombre=None):
        # Reemplaza la simulación después de validar los nuevos parámetros.
        nuevo = Simulador(parametros)

        # Primero se construye el nuevo simulador; si falla la validación, sesión actual permanece intacta.
        self.pausar()
        self.sim = nuevo

        if nombre is not None:
            self.nombre = nombre

        self._avisar("nueva")

    # Carga uno de los escenarios predefinidos.
    def cargar_escenario(self, nombre):
        self.cargar(escenarios()[nombre], nombre)
