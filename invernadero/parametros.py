"""Parámetros del modelo, condiciones iniciales y escenarios predefinidos.

Unidades (tiempo base = minutos):
    temperatura  -> °C          humedad del suelo -> %
    luminosidad  -> % (0-100)   tamaño de la planta -> cm
"""
from dataclasses import dataclass, replace


@dataclass
class Parametros:
    # ---- Tiempo ----
    dt: float = 1.0            # paso de Euler [min]
    duracion: float = 1440.0   # duración total [min] (24 h)
    hora_inicio: float = 6.0   # hora del día en t = 0 [h]

    # ---- Condiciones iniciales ----
    T0: float = 22.0           # temperatura interior inicial [°C]
    H0: float = 60.0           # humedad inicial del suelo [%]
    P0: float = 2.0            # tamaño inicial de la planta [cm]

    # ---- Ambiente exterior (entradas) ----
    Tmed: float = 24.0         # temperatura exterior media [°C]
    Amp_T: float = 5.0         # amplitud del ciclo diario [°C]
    Lmax: float = 100.0        # luminosidad máxima al mediodía [%]
    nubosidad: float = 0.0     # 0 = despejado, 1 = totalmente nublado
    perturbacion_dT: float = 0.0       # cambio ambiental: +ΔT sobre Tamb [°C]
    perturbacion_inicio: float = 0.0   # instante de inicio [min]
    perturbacion_fin: float = 0.0      # instante de fin [min]

    # ---- Modelo de humedad: dH/dt = R - E ----
    R_on: float = 0.20         # aporte de agua con el riego encendido [%/min]
    E0: float = 0.03           # pérdida base de agua [%/min]
    beta_E: float = 0.04       # sensibilidad de E a la temperatura [1/°C]
    T_ref: float = 25.0        # temperatura de referencia [°C]
    acoplar_evaporacion: bool = True

    # ---- Modelo de temperatura: dT/dt = (k + kv*v)(Tamb - T) + a L ----
    k: float = 0.02            # intercambio térmico con el exterior [1/min]
    k_vent: float = 0.06       # intercambio extra con ventilación [1/min]
    a_sol: float = 0.0016      # calentamiento por luz [°C/min por % de luz]

    # ---- Modelo de crecimiento logístico modulado ----
    usar_crecimiento: bool = True
    r_max: float = 0.002       # tasa máxima de crecimiento [1/min]
    K: float = 50.0            # tamaño máximo [cm]
    T_opt: float = 25.0        # temperatura óptima [°C]
    w_T: float = 8.0           # tolerancia térmica [°C]
    H_opt: float = 60.0        # humedad óptima [%]
    w_H: float = 25.0          # tolerancia a la humedad [%]

    # ---- Control virtual (con histéresis) ----
    control_activo: bool = True
    H_min: float = 40.0        # se enciende el riego si H <= H_min
    H_max: float = 70.0        # se apaga el riego si H >= H_max
    T_max: float = 30.0        # se enciende la ventilación si T >= T_max
    T_ok: float = 27.0         # se apaga la ventilación si T <= T_ok
    usar_iluminacion: bool = False
    L_min: float = 20.0        # luz natural mínima aceptable [%]
    L_art: float = 40.0        # aporte de la luz artificial [%]
    ilum_hora_ini: float = 6.0
    ilum_hora_fin: float = 20.0

    def validar(self):
        """Lanza ValueError si los parámetros no son coherentes."""
        if self.dt <= 0 or self.duracion <= 0:
            raise ValueError("Δt y la duración deben ser positivos.")
        if self.dt > self.duracion:
            raise ValueError("Δt no puede ser mayor que la duración.")
        if self.duracion / self.dt > 200_000:
            raise ValueError("Demasiados pasos (máx. 200 000). Aumente Δt.")
        if not (0 <= self.H0 <= 100):
            raise ValueError("La humedad inicial debe estar entre 0 y 100 %.")
        if not (0 <= self.nubosidad <= 1):
            raise ValueError("La nubosidad debe estar entre 0 y 1.")
        if self.H_min >= self.H_max:
            raise ValueError("H_min debe ser menor que H_max.")
        if self.T_ok >= self.T_max:
            raise ValueError("T_ok debe ser menor que T_max.")
        if self.K <= 0 or self.P0 < 0:
            raise ValueError("K debe ser positivo y P0 no negativo.")
        if self.P0 > self.K:
            raise ValueError("El tamaño inicial P0 no puede superar el máximo K.")
        if self.w_T <= 0 or self.w_H <= 0:
            raise ValueError("Las tolerancias de temperatura y humedad deben ser positivas.")
        if self.Lmax < 0:
            raise ValueError("La luminosidad máxima no puede ser negativa.")
        if not (0 <= self.L_min <= 100) or not (0 <= self.L_art <= 100):
            raise ValueError("La luz mínima y la artificial deben estar entre 0 y 100 %.")
        if not (0 <= self.ilum_hora_ini < 24) or not (0 <= self.ilum_hora_fin <= 24):
            raise ValueError("Las horas de iluminación deben estar entre 0 y 24.")
        if self.R_on < 0 or self.E0 < 0:
            raise ValueError("El aporte de riego y la pérdida de agua no pueden ser negativos.")


def escenarios():
    """Escenarios predefinidos (los de la sección de validación del documento)."""
    base = Parametros()
    return {
        "Día normal": base,
        "Ejemplo manual del documento": replace(
            base, duracion=10, usar_crecimiento=False, acoplar_evaporacion=False,
            E0=0.8, R_on=2.5, H_min=56.0, H_max=100.0),
        "Baja humedad": replace(base, H0=45.0, E0=0.06, R_on=0.30),
        "Alta temperatura": replace(base, Tmed=29.0, T0=27.0),
        "Poca luz / nublado": replace(base, nubosidad=0.75, usar_iluminacion=True),
        "Cambio ambiental (ola de calor)": replace(
            base, perturbacion_dT=6.0, perturbacion_inicio=360.0, perturbacion_fin=720.0),
        "Sin control (referencia)": replace(
            base, Tmed=29.0, T0=27.0, H0=45.0, E0=0.06, control_activo=False),
    }
