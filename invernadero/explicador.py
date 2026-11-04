"""Genera el texto con las ecuaciones y los cálculos paso a paso (ventana de cálculos)."""
import math

from . import modelo


def texto_ecuaciones(p):
    return f"""MODELO MATEMÁTICO DEL INVERNADERO
Unidades: tiempo [min], T [°C], H [%], L [%], P [cm]

1) HUMEDAD DEL SUELO
   dH/dt = R(t) − E(T)                       [%/min]
   R(t)  = R_on·u_riego(t)    con R_on = {p.R_on:g}
   E(T)  = E0·(1 + β·(T − Tref))   con E0 = {p.E0:g}, β = {p.beta_E:g}, Tref = {p.T_ref:g}
           {'(acoplada a la temperatura)' if p.acoplar_evaporacion else '(constante: E = E0)'}

2) TEMPERATURA INTERIOR
   dT/dt = (k + kv·v(t))·(Tamb(t) − T) + a·L(t)    [°C/min]
   k = {p.k:g}, kv = {p.k_vent:g}, a = {p.a_sol:g}
   v(t) = 1 si la ventilación está activa, 0 si no.
   Tamb(t) = Tmed + A·sin(2π(h − 9)/24)    Tmed = {p.Tmed:g}, A = {p.Amp_T:g}

3) LUMINOSIDAD (función del tiempo)
   L(t) = Lmax·(1 − nub)·max(0, sin(2π(h − 6)/24)) + L_art·u_luz(t)
   Lmax = {p.Lmax:g}, nub = {p.nubosidad:g}, L_art = {p.L_art:g}
   h = hora del día = hora_inicio + t/60

4) CRECIMIENTO DEL CULTIVO {'(activo)' if p.usar_crecimiento else '(desactivado)'}
   dP/dt = r·fT·fH·fL·P·(1 − P/K)           [cm/min]
   fT = exp(−((T − {p.T_opt:g})/{p.w_T:g})²)   fH = exp(−((H − {p.H_opt:g})/{p.w_H:g})²)   fL = L/100
   r = {p.r_max:g}, K = {p.K:g}

MÉTODO NUMÉRICO — EULER EXPLÍCITO (Δt = {p.dt:g} min)
   y(n+1) = y(n) + Δt · f(t_n, y_n)

CONTROL (histéresis)
   Riego:        ON si H ≤ {p.H_min:g}  |  OFF si H ≥ {p.H_max:g}
   Ventilación:  ON si T ≥ {p.T_max:g}  |  OFF si T ≤ {p.T_ok:g}
   Iluminación:  {'ON si L_natural < ' + format(p.L_min, 'g') + ' entre ' + format(p.ilum_hora_ini, 'g') + ' h y ' + format(p.ilum_hora_fin, 'g') + ' h' if p.usar_iluminacion else 'desactivada'}
   Control automático: {'activo' if p.control_activo else 'DESACTIVADO'}
"""


def _hhmm(h):
    return f"{int(h):02d}:{int(round((h - int(h)) * 60)) % 60:02d}"


def explicar_paso(sim, n):
    """Explica el paso n → n+1 con todos los valores sustituidos."""
    p, rs = sim.p, sim.registros
    if n < 0 or n >= len(rs) - 1:
        return "Todavía no hay un paso calculado en esta posición."
    a, b = rs[n], rs[n + 1]
    dt = b.t - a.t
    hora = modelo.hora_del_dia(a.t, p)
    onoff = lambda x: "ENCENDIDO" if x else "apagado"
    L = []
    L.append(f"PASO {n} → {n + 1}     t: {a.t:g} min → {b.t:g} min     (Δt = {dt:g} min)     hora del día: {_hhmm(hora)}")
    L.append("=" * 78)
    L.append(f"Estado actual:  T = {a.T:.4f} °C   H = {a.H:.4f} %   L = {a.L:.2f} %   P = {a.P:.4f} cm")
    L.append(f"Actuadores:     riego {onoff(a.riego)}, ventilación {onoff(a.vent)}, iluminación {onoff(a.luz)}")
    L.append("")

    # ---- humedad ----
    L.append("1) HUMEDAD DEL SUELO        dH/dt = R − E")
    if p.acoplar_evaporacion:
        L.append(f"   E = E0·(1 + β(T − Tref)) = {p.E0:g}·(1 + {p.beta_E:g}·({a.T:.4f} − {p.T_ref:g})) = {a.E:.6f}")
    else:
        L.append(f"   E = E0 = {a.E:.6f}")
    L.append(f"   R = {a.R:g}   ({'riego encendido: R = R_on' if a.riego else 'riego apagado'})")
    L.append(f"   dH/dt = {a.R:g} − {a.E:.6f} = {a.dH:+.6f} %/min   "
             f"→ la humedad {'aumenta' if a.dH > 0 else 'disminuye' if a.dH < 0 else 'no cambia'}")
    H_raw = a.H + dt * a.dH
    L.append(f"   Euler: H(n+1) = {a.H:.4f} + {dt:g}·({a.dH:+.6f}) = {H_raw:.4f} %")
    if abs(H_raw - b.H) > 1e-9:
        L.append(f"   (se limita al rango físico [0, 100] %  →  H(n+1) = {b.H:.4f} %)")
    L.append("")

    # ---- temperatura ----
    k_ef = p.k + (p.k_vent if a.vent else 0.0)
    L.append("2) TEMPERATURA INTERIOR     dT/dt = (k + kv·v)(Tamb − T) + a·L")
    L.append(f"   Tamb = {a.Tamb:.4f} °C     L = {a.L:.4f} %     v = {int(a.vent)}")
    L.append(f"   k_ef = k + kv·v = {p.k:g} + {p.k_vent:g}·{int(a.vent)} = {k_ef:g}")
    L.append(f"   dT/dt = {k_ef:g}·({a.Tamb:.4f} − {a.T:.4f}) + {p.a_sol:g}·{a.L:.4f}")
    L.append(f"         = {k_ef * (a.Tamb - a.T):+.6f} + {p.a_sol * a.L:.6f} = {a.dT:+.6f} °C/min")
    L.append(f"   Euler: T(n+1) = {a.T:.4f} + {dt:g}·({a.dT:+.6f}) = {a.T + dt * a.dT:.4f} °C")
    L.append("")

    # ---- luminosidad ----
    L.append("3) LUMINOSIDAD              L(t) = Lmax(1 − nub)·max(0, sin(2π(h − 6)/24)) + L_art·u")
    s = math.sin(2 * math.pi * (hora - 6.0) / 24.0)
    L.append(f"   h = {hora:.4f}   sin(2π({hora:.4f} − 6)/24) = {s:.4f}")
    L.append(f"   L_natural = {p.Lmax:g}·(1 − {p.nubosidad:g})·{max(0.0, s):.4f} = {a.Lnat:.4f} %"
             + (f"   + luz artificial {p.L_art:g}  →  L = {a.L:.4f} % (máx. 100)" if a.luz else ""))
    L.append("")

    # ---- crecimiento ----
    if p.usar_crecimiento:
        fT, fH, fL = modelo.factores_crecimiento(a.T, a.H, a.L, p)
        L.append("4) CRECIMIENTO              dP/dt = r·fT·fH·fL·P·(1 − P/K)")
        L.append(f"   fT = {fT:.4f}   fH = {fH:.4f}   fL = {fL:.4f}")
        L.append(f"   dP/dt = {p.r_max:g}·{fT:.4f}·{fH:.4f}·{fL:.4f}·{a.P:.4f}·(1 − {a.P:.4f}/{p.K:g}) = {a.dP:.8f} cm/min")
        L.append(f"   Euler: P(n+1) = {a.P:.4f} + {dt:g}·{a.dP:.8f} = {a.P + dt * a.dP:.4f} cm")
        if abs(a.P + dt * a.dP - b.P) > 1e-9:
            L.append(f"   (se limita al máximo K  →  P(n+1) = {b.P:.4f} cm)")
        L.append("")

    # ---- control ----
    L.append("5) EVALUACIÓN DEL CONTROL con el nuevo estado")
    L.append(f"   H(n+1) = {b.H:.4f} % (límites {p.H_min:g}–{p.H_max:g})  →  riego {onoff(b.riego)}")
    L.append(f"   T(n+1) = {b.T:.4f} °C (límites {p.T_ok:g}–{p.T_max:g})  →  ventilación {onoff(b.vent)}")
    if not p.control_activo:
        L.append("   (control automático desactivado)")
    return "\n".join(L)
