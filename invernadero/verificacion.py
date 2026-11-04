"""Verificaciones: cálculos manuales, solución analítica, paso de tiempo y coherencia."""
import math
from dataclasses import replace

from . import modelo
from .parametros import Parametros, escenarios
from .simulador import Simulador

TOL = 1e-9

# Valores calculados a mano en el documento de la propuesta (humedad, Δt = 1 min)
H_MANUAL = [60.0, 59.2, 58.4, 57.6, 56.8, 56.0, 57.7, 59.4]


def comparar_humedad_manual():
    """Ejemplo del documento: E = 0.8, sin riego 5 min y luego R = 2.5."""
    sim = Simulador(escenarios()["Ejemplo manual del documento"])
    sim.ejecutar()
    filas = []
    for n, h_man in enumerate(H_MANUAL):
        h_prog = sim.registros[n].H
        filas.append((n, h_man, h_prog, abs(h_man - h_prog)))
    return filas


def _euler_T(T0, Tamb, L, vent, p, pasos):
    """Euler directo sobre dT/dt con entradas constantes (para ejemplos a mano)."""
    T, out = T0, [T0]
    for _ in range(pasos):
        T = T + p.dt * modelo.tasa_temperatura(T, Tamb, L, vent, p)
        out.append(T)
    return out


def comparar_temperatura_manual():
    """Casos de temperatura calculados a mano (ver docs/03_calculos_manuales.md)."""
    p = Parametros(dt=1.0, k=0.02, k_vent=0.06, a_sol=0.0)
    casos = [
        ("T0=24, Tamb=30, sin ventilación", 24.0, 30.0, False, [24.0, 24.12, 24.2376, 24.352848]),
        ("T0=34, Tamb=30, con ventilación", 34.0, 30.0, True, [34.0, 33.68, 33.3856, 33.114752]),
    ]
    filas = []
    for nombre, T0, Tamb, vent, manual in casos:
        prog = _euler_T(T0, Tamb, 0.0, vent, p, len(manual) - 1)
        for n, (m, c) in enumerate(zip(manual, prog)):
            filas.append((nombre, n, m, c, abs(m - c)))
    return filas


def error_vs_dt(dts=(0.5, 1, 5, 10, 30, 60), T0=20.0, Tamb=30.0, k=0.02, t_fin=240.0):
    """Error máximo de Euler frente a la solución analítica de dT/dt = k(Tamb - T).

    Solución exacta:  T(t) = Tamb + (T0 - Tamb)·e^(-k t)
    """
    p = Parametros(k=k, a_sol=0.0)
    resultados = []
    for dt in dts:
        n = int(round(t_fin / dt))
        T, err = T0, 0.0
        for i in range(1, n + 1):
            T = T + dt * modelo.tasa_temperatura(T, Tamb, 0.0, False, p)
            exacta = Tamb + (T0 - Tamb) * math.exp(-k * i * dt)
            err = max(err, abs(T - exacta))
        resultados.append((dt, err))
    return resultados


def verificar_comportamientos():
    """Pruebas de coherencia física y de control. Devuelve [(descripción, ok)]."""
    base = Parametros()
    res = []

    # 1. Sin riego y con pérdida, la humedad baja siempre
    s = Simulador(replace(base, control_activo=False, duracion=300)).ejecutar()
    Hs = [r.H for r in s.registros]
    res.append(("Sin riego y E > 0, la humedad disminuye en todo momento",
                all(Hs[i + 1] < Hs[i] for i in range(len(Hs) - 1))))

    # 2. Con riego mayor que la pérdida, la humedad sube
    s = Simulador(replace(base, H0=30.0, duracion=30)).ejecutar()
    res.append(("Con R > E (riego activo) la humedad aumenta", s.registros[5].H > s.registros[0].H))

    # 3. El riego se activa exactamente cuando H <= H_min
    s = Simulador(replace(base, H0=45.0, E0=0.06)).ejecutar()
    primero = next((r for r in s.registros if r.H <= base.H_min + 1e-9), None)
    ev = next((e for e in s.eventos if e[1] == "riego_on"), None)
    res.append(("El riego se activa en el primer instante con H ≤ H_min",
                bool(primero and ev and abs(primero.t - ev[0]) < 1e-9)))

    # 4. El riego mantiene la humedad cerca del rango objetivo
    s = Simulador(replace(base, H0=45.0, E0=0.06)).ejecutar()
    res.append(("Con control, la humedad nunca baja de H_min − 1 %",
                min(r.H for r in s.registros) >= base.H_min - 1.0))

    # 5. Si Tamb > T (sin luz ni ventilación), T sube hacia Tamb
    p = Parametros(a_sol=0.0)
    res.append(("Si Tamb > T, dT/dt > 0 (la temperatura tiende a subir)",
                modelo.tasa_temperatura(20.0, 30.0, 0.0, False, p) > 0))
    res.append(("Si Tamb < T, dT/dt < 0 (la temperatura tiende a bajar)",
                modelo.tasa_temperatura(35.0, 30.0, 0.0, False, p) < 0))

    # 6. La ventilación acelera el enfriamiento
    res.append(("Con ventilación el enfriamiento es más rápido que sin ella",
                modelo.tasa_temperatura(35.0, 30.0, 0.0, True, p) <
                modelo.tasa_temperatura(35.0, 30.0, 0.0, False, p)))

    # 7. En un día caluroso el control reduce la temperatura máxima
    caluroso = replace(base, Tmed=29.0, T0=27.0)
    con = Simulador(caluroso).ejecutar().resumen()["T_max"]
    sin = Simulador(replace(caluroso, control_activo=False)).ejecutar().resumen()["T_max"]
    res.append((f"La ventilación reduce la T máxima ({sin:.1f} → {con:.1f} °C)", con < sin))

    # 8. La humedad se mantiene en el rango físico
    s = Simulador(replace(base, control_activo=False, duracion=4000)).ejecutar()
    res.append(("La humedad permanece en [0, 100] %", all(0 <= r.H <= 100 for r in s.registros)))

    # 9. La planta nunca supera K ni decrece
    s = Simulador(replace(base, duracion=4320)).ejecutar()
    Ps = [r.P for r in s.registros]
    res.append(("El crecimiento es no decreciente y acotado por K",
                all(Ps[i + 1] >= Ps[i] - 1e-12 for i in range(len(Ps) - 1)) and max(Ps) <= base.K))

    # 10. Euler converge al reducir Δt
    e = dict(error_vs_dt(dts=(10, 1, 0.1)))
    res.append(("El error de Euler disminuye al reducir Δt (10 → 1 → 0.1 min)",
                e[10] > e[1] > e[0.1]))
    return res


def ejecutar_todo():
    """Devuelve un diccionario con todas las verificaciones y si pasaron."""
    h = comparar_humedad_manual()
    t = comparar_temperatura_manual()
    c = verificar_comportamientos()
    return {
        "humedad_manual": h, "temperatura_manual": t, "comportamientos": c,
        "ok": all(f[3] < TOL for f in h) and all(f[4] < TOL for f in t) and all(ok for _, ok in c),
    }
