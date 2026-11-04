"""Control virtual con histéresis (no hay dispositivos físicos).

Riego:        ON si H <= H_min,  OFF si H >= H_max
Ventilación:  ON si T >= T_max,  OFF si T <= T_ok
Iluminación:  ON si la luz natural < L_min dentro del fotoperiodo
La histéresis evita que los actuadores se enciendan y apaguen en cada paso.
"""

EPS = 1e-9  # tolerancia para comparaciones con números flotantes


class Controlador:
    def __init__(self, p):
        self.p = p
        self.riego = False
        self.vent = False
        self.luz = False

    def evaluar(self, t, T, H, L_nat, hora):
        """Evalúa el estado y devuelve la lista de eventos (t, tipo, texto)."""
        p, ev = self.p, []
        if not p.control_activo:
            return ev

        # --- riego ---
        if not self.riego and H <= p.H_min + EPS:
            self.riego = True
            ev.append((t, "riego_on", f"Riego ACTIVADO: H = {H:.2f} % ≤ H_min = {p.H_min:g} %"))
        elif self.riego and H >= p.H_max - EPS:
            self.riego = False
            ev.append((t, "riego_off", f"Riego DESACTIVADO: H = {H:.2f} % ≥ H_max = {p.H_max:g} %"))

        # --- ventilación ---
        if not self.vent and T >= p.T_max - EPS:
            self.vent = True
            ev.append((t, "vent_on", f"Ventilación ACTIVADA: T = {T:.2f} °C ≥ T_max = {p.T_max:g} °C"))
        elif self.vent and T <= p.T_ok + EPS:
            self.vent = False
            ev.append((t, "vent_off", f"Ventilación DESACTIVADA: T = {T:.2f} °C ≤ T_ok = {p.T_ok:g} °C"))

        # --- iluminación artificial ---
        if p.usar_iluminacion:
            necesita = (L_nat < p.L_min) and (p.ilum_hora_ini <= hora < p.ilum_hora_fin)
            if necesita and not self.luz:
                self.luz = True
                ev.append((t, "luz_on", f"Iluminación ACTIVADA: luz natural = {L_nat:.1f} % < L_min = {p.L_min:g} %"))
            elif not necesita and self.luz:
                self.luz = False
                ev.append((t, "luz_off", f"Iluminación DESACTIVADA: luz natural = {L_nat:.1f} %"))
        return ev
