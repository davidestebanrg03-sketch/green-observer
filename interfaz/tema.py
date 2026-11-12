#Colores y utilidades visuales compartidas por todas las ventanas.

import tkinter.font as tkfont

# Colores utilizados para representar estados y elementos de la interfaz.
VERDE, NARANJA, ROJO, AZUL, GRIS = "#2e9e5b", "#e08a1e", "#d9534f", "#2e86c1", "#888888"
VERDE_OSCURO = "#1b5e20"


def mezclar(c1, c2, f):
    # Mezclar dos colores según un factor entre 0 y 1.
    f = min(1.0, max(0.0, f))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * f) for x, y in zip(a, b))


def fuente_mono(ventana, tam=10):
    f = tkfont.nametofont("TkFixedFont").copy()
    f.configure(size=tam)
    return f


def hhmm(hora):
    # Convertir una hora decimal a formato de 24 horas (HH:MM).
    minutos = int(round(hora * 60)) % (24 * 60)
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def hora_de(t_min, p):
    # Obtener la hora del día correspondiente a un instante de la simulación.
    return hhmm(p.hora_inicio + t_min / 60.0)
