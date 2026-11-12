"""Motor de simulación mediante Euler explícito y control virtual"""

import csv
import math
from dataclasses import dataclass

from . import modelo
from .control import Controlador


@dataclass
class Registro:
    """Almacena los valores de las variables en un instante de la simulación."""
    t: float        # tiempo [min]
    T: float        # temperatura interior [°C]
    H: float        # humedad del suelo [%]
    P: float        # tamaño de la planta [cm]
    Tamb: float     # temperatura exterior [°C]
    Lnat: float     # luz natural [%]
    L: float        # luz efectiva (natural + artificial) [%]
    riego: bool          # Estado del sistema de riego
    vent: bool           # Estado de la ventilación
    luz: bool            # Estado de la iluminación artificial
    R: float        # aporte de riego [%/min]
    E: float        # pérdida de agua [%/min]
    dT: float       # dT/dt
    dH: float       # dH/dt
    dP: float       # dP/dt


class Simulador:
    def __init__(self, parametros):
        parametros.validar()
        self.p = parametros
        self.reiniciar()

    # ------------------------------------------------------------------ Inicialización
    def reiniciar(self):
        self.ctrl = Controlador(self.p)
        self.registros = []
        self.eventos = [(0.0, "inicio", "Inicio de la simulación")]

        # Se calcula la cantidad de pasos necesaria para alcanzar la duración.
        # El último paso puede ser más corto si la duración no es múltiplo de Δt.
        self.n_pasos = max(1, math.ceil(self.p.duracion / self.p.dt - 1e-9))

        # Guarda las condiciones iniciales y calcula sus primeras tasas de cambio.
        self._registrar(0.0, self.p.T0, self.p.H0, self.p.P0)

    @property
    def terminado(self):
        return len(self.registros) - 1 >= self.n_pasos

    @property
    def actual(self):
        return self.registros[-1]

    # ------------------------------------------------------------------ Registro de datos
    def _registrar(self, t, T, H, P):
        p = self.p

        # Obtiene las condiciones ambientales para el instante actual.
        Tamb = modelo.temperatura_ambiente(t, p)
        Lnat = modelo.luz_natural(t, p)
        hora = modelo.hora_del_dia(t, p)

        # El controlador evalúa las condiciones y actualiza los actuadores.
        self.eventos.extend(self.ctrl.evaluar(t, T, H, Lnat, hora))

        # Calcula la luz disponible, sin superar el límite del 100 %.
        L = min(100.0, Lnat + (p.L_art if self.ctrl.luz else 0.0))

        # Determina el aporte de agua y la pérdida por evaporación.
        R = p.R_on if self.ctrl.riego else 0.0
        E = modelo.evaporacion(T, p)

        # Calcula las tasas de cambio de las tres variables del modelo.
        dH = modelo.tasa_humedad(R, E)
        dT = modelo.tasa_temperatura(T, Tamb, L, self.ctrl.vent, p)
        dP = modelo.tasa_crecimiento(P, T, H, L, p) if p.usar_crecimiento else 0.0

        # Guarda el estado, las entradas aplicadas y las tasas calculadas.
        self.registros.append(Registro(t, T, H, P, Tamb, Lnat, L,
                                       self.ctrl.riego, self.ctrl.vent, self.ctrl.luz,
                                       R, E, dT, dH, dP))

    # --------------------------------------------------------- Avance de Euler
    def paso(self):
        """Avanza un paso de Euler. Devuelve False si ya terminó."""
        if self.terminado:
            return False
        r = self.registros[-1]
        n = len(self.registros)
        t = min(self.p.duracion, n * self.p.dt)

        # El intervalo real puede ser menor que Δt en el último paso.
        dt = t - r.t

        # Método_de_Euler: nuevo valor = valor actual + intervalo * tasa actual.
        T = r.T + dt * r.dT
        H = min(100.0, max(0.0, r.H + dt * r.dH))
        P = min(self.p.K, max(0.0, r.P + dt * r.dP))

        # Registra el nuevo estado y calcula sus tasas para el siguiente paso.
        self._registrar(t, T, H, P)

        # Registra el evento de finalización al alcanzar la duración establecida.
        if self.terminado:
            self.eventos.append((t, "fin", "Fin de la simulación"))
        return True

    def ejecutar(self):
        while self.paso():
            pass
        return self

    # --------------------------------------------------------- Resumen de resultados
    def resumen(self):
        rs = self.registros

        # Cada estado de un actuador se mantiene hasta el siguiente registro.
        minutos = lambda attr: sum(rs[i + 1].t - rs[i].t for i in range(len(rs) - 1) if getattr(rs[i], attr))

        # Cuenta cuántas veces se activó cada actuador.
        cuenta = lambda tipo: sum(1 for e in self.eventos if e[1] == tipo)

        return {
            "pasos": len(rs) - 1,
            "T_min": min(r.T for r in rs), "T_max": max(r.T for r in rs),
            "T_prom": sum(r.T for r in rs) / len(rs),
            "H_min": min(r.H for r in rs), "H_max": max(r.H for r in rs),
            "H_prom": sum(r.H for r in rs) / len(rs),
            "P_final": rs[-1].P,
            "act_riego": cuenta("riego_on"), "act_vent": cuenta("vent_on"),
            "act_luz": cuenta("luz_on"),
            "min_riego": minutos("riego"),
            "min_vent": minutos("vent"),
            "min_luz": minutos("luz"),
        }

    # --------------------------------------------------------- Exportación
    def a_csv(self, ruta):
        campos = ["t_min", "T_C", "H_pct", "P_cm", "Tamb_C", "L_nat_pct", "L_pct",
                  "riego", "ventilacion", "iluminacion", "R", "E", "dTdt", "dHdt", "dPdt"]
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(campos)
            for r in self.registros:
                w.writerow([r.t, r.T, r.H, r.P, r.Tamb, r.Lnat, r.L, int(r.riego),
                            int(r.vent), int(r.luz), r.R, r.E, r.dT, r.dH, r.dP])
