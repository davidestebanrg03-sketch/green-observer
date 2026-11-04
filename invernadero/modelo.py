"""Ecuaciones diferenciales del invernadero y funciones de entrada.

Cada función es una expresión matemática pura (sin estado) para que pueda
verificarse a mano y reutilizarse en las pruebas y en la ventana de cálculos.
"""
import math


# ------------------------------------------------------------------ entradas
def hora_del_dia(t, p):
    """Hora del día [0, 24) para el instante t [min]."""
    return (p.hora_inicio + t / 60.0) % 24.0


def temperatura_ambiente(t, p):
    """Tamb(t) = Tmed + A·sin(2π(h-9)/24)  (máximo a las 15 h, mínimo a las 3 h)."""
    h = hora_del_dia(t, p)
    Tamb = p.Tmed + p.Amp_T * math.sin(2 * math.pi * (h - 9.0) / 24.0)
    if p.perturbacion_inicio <= t < p.perturbacion_fin:
        Tamb += p.perturbacion_dT
    return Tamb


def luz_natural(t, p):
    """L(t) = Lmax·(1-nub)·max(0, sin(2π(h-6)/24))  (día de 6 h a 18 h)."""
    h = hora_del_dia(t, p)
    return p.Lmax * (1.0 - p.nubosidad) * max(0.0, math.sin(2 * math.pi * (h - 6.0) / 24.0))


# ------------------------------------------------------------- humedad (EDO)
def evaporacion(T, p):
    """E(T) = E0·(1 + β(T - Tref)); constante E0 si no hay acoplamiento."""
    if p.acoplar_evaporacion:
        return max(0.0, p.E0 * (1.0 + p.beta_E * (T - p.T_ref)))
    return p.E0


def tasa_humedad(R, E):
    """dH/dt = R - E   [%/min]"""
    return R - E


# --------------------------------------------------------- temperatura (EDO)
def tasa_temperatura(T, Tamb, L, ventilando, p):
    """dT/dt = (k + kv·v)(Tamb - T) + a·L   [°C/min]

    v = 1 si la ventilación está activa (aumenta el intercambio con el exterior).
    """
    k_ef = p.k + (p.k_vent if ventilando else 0.0)
    return k_ef * (Tamb - T) + p.a_sol * L


# ----------------------------------------------------------- crecimiento (EDO)
def factores_crecimiento(T, H, L, p):
    """Factores de 0 a 1: fT (temperatura), fH (humedad), fL (luz)."""
    fT = math.exp(-((T - p.T_opt) / p.w_T) ** 2)
    fH = math.exp(-((H - p.H_opt) / p.w_H) ** 2)
    fL = min(1.0, max(0.0, L / 100.0))
    return fT, fH, fL


def tasa_crecimiento(P, T, H, L, p):
    """dP/dt = r·fT·fH·fL·P·(1 - P/K)   [cm/min]  (logístico modulado)."""
    fT, fH, fL = factores_crecimiento(T, H, L, p)
    return p.r_max * fT * fH * fL * P * (1.0 - P / p.K)
