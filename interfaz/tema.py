"""Colores y utilidades visuales compartidas por todas las ventanas."""
import tkinter.font as tkfont

VERDE, NARANJA, ROJO, AZUL, GRIS = "#2e9e5b", "#e08a1e", "#d9534f", "#2e86c1", "#888888"
VERDE_OSCURO = "#1b5e20"


def mezclar(c1, c2, f):
    """Interpola dos colores '#rrggbb' (f = 0 → c1, f = 1 → c2) y devuelve '#rrggbb'."""
    f = min(1.0, max(0.0, f))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * f) for x, y in zip(a, b))


def fuente_mono(ventana, tam=10):
    f = tkfont.nametofont("TkFixedFont").copy()
    f.configure(size=tam)
    return f


def hhmm(hora):
    """Hora decimal (6.5) → '06:30'."""
    minutos = int(round(hora * 60)) % (24 * 60)
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def hora_de(t_min, p):
    """Hora del día 'hh:mm' para el instante t [min] de una simulación."""
    return hhmm(p.hora_inicio + t_min / 60.0)
