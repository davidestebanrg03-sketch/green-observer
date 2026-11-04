"""Dibujo del invernadero virtual (solo representación; no calcula nada del modelo).

La escena se diseña en un lienzo lógico de 1000 × 600 y se escala al tamaño real de la
ventana, de modo que se ve bien al cambiar el tamaño. Cada llamada a ``dibujar_escena``
repinta todo a partir de un ``Registro`` del simulador.
"""
import math

from invernadero import modelo
from .tema import AZUL, mezclar

ANCHO, ALTO = 1000, 600
SUELO_Y = 420                      # y lógica de la superficie del suelo
PLANTAS_X = (220, 380, 620, 780)
ESTRELLAS = ((90, 40), (230, 90), (330, 30), (450, 75), (560, 35), (680, 95), (760, 30), (880, 70), (960, 110), (40, 120))


class _Lienzo:
    """Convierte coordenadas lógicas a píxeles conservando la proporción."""

    def __init__(self, cv):
        self.cv = cv
        w, h = max(cv.winfo_width(), 200), max(cv.winfo_height(), 120)
        self.w, self.h = w, h
        self.s = min(w / ANCHO, h / ALTO)
        self.ox, self.oy = (w - ANCHO * self.s) / 2, (h - ALTO * self.s) / 2

    def x(self, v):
        return self.ox + v * self.s

    def y(self, v):
        return self.oy + v * self.s

    def pts(self, *c):
        return [self.x(v) if i % 2 == 0 else self.y(v) for i, v in enumerate(c)]

    def rect(self, x0, y0, x1, y1, **kw):
        return self.cv.create_rectangle(*self.pts(x0, y0, x1, y1), **kw)

    def oval(self, x0, y0, x1, y1, **kw):
        return self.cv.create_oval(*self.pts(x0, y0, x1, y1), **kw)

    def linea(self, *c, **kw):
        if "width" in kw:
            kw["width"] = max(1, kw["width"] * self.s)
        return self.cv.create_line(*self.pts(*c), **kw)

    def poligono(self, *c, **kw):
        if "width" in kw:
            kw["width"] = max(1, kw["width"] * self.s)
        return self.cv.create_polygon(*self.pts(*c), **kw)

    def texto(self, x, y, texto, tam=11, negrita=True, **kw):
        fuente = ("Arial", max(7, int(round(tam * self.s))), "bold" if negrita else "normal")
        return self.cv.create_text(self.x(x), self.y(y), text=texto, font=fuente, **kw)


# ----------------------------------------------------------------------------
def color_cielo(hora, nubosidad=0.0):
    """Color del cielo según la altura del sol (amanecer naranja → día azul → noche) y la nubosidad."""
    altura = math.sin(2 * math.pi * (hora - 6.0) / 24.0)
    if altura <= 0:
        return "#172554"
    a = 100.0 * altura
    if a < 12:
        c = mezclar("#26325F", "#F0A35E", a / 12)
    elif a < 35:
        c = mezclar("#F0A35E", "#5B9BD5", (a - 12) / 23)
    elif a < 70:
        c = mezclar("#5B9BD5", "#87CEEB", (a - 35) / 35)
    else:
        c = "#87CEEB"
    return mezclar(c, "#90A4AE", 0.7 * nubosidad)


def _astro(L, hora):
    """Posición lógica del sol (6–18 h) o de la luna (18–6 h) sobre un arco."""
    prog = (hora - 6.0) / 12.0 if 6.0 <= hora < 18.0 else ((hora - 18.0) if hora >= 18.0 else hora + 6.0) / 12.0
    return 30 + prog * 940, 420 - 380 * math.sin(math.pi * prog)


def dibujar_escena(cv, r, p, fotograma=0):
    """Repinta el invernadero para el registro ``r`` con los parámetros ``p``."""
    cv.delete("all")
    L = _Lienzo(cv)
    hora = modelo.hora_del_dia(r.t, p)
    dia = 6.0 <= hora < 18.0
    oscuro = math.sin(2 * math.pi * (hora - 6.0) / 24.0) < 0.25      # cielo oscuro → texto claro
    calor = (r.T - 18.0) / (40.0 - 18.0)               # 0 = frío, 1 = muy caliente

    # ---- cielo y suelo exterior (cubren todo el lienzo) ----
    cv.create_rectangle(0, 0, L.w, L.y(SUELO_Y), fill=color_cielo(hora, p.nubosidad), outline="")
    cv.create_rectangle(0, L.y(SUELO_Y), L.w, L.h, fill="#DCEFD5", outline="")

    # ---- estructura: el vidrio se tiñe según la temperatura interior ----
    noche = 0.0 if not oscuro else min(1.0, (0.25 - math.sin(2 * math.pi * (hora - 6.0) / 24.0)) / 0.25)
    if r.luz:
        noche *= 0.45                                   # la luz artificial ilumina el interior
    vidrio = mezclar(mezclar("#E3F2FD", "#FFCCBC", calor), "#35495E", 0.55 * noche)
    L.rect(80, 200, 920, SUELO_Y, fill=vidrio, outline="")
    L.poligono(80, 200, 500, 60, 920, 200,
               fill=mezclar(mezclar("#EFF8E9", "#FFE0D0", calor), "#35495E", 0.55 * noche), outline="")

    # ---- sol / luna / estrellas / nubes ----
    ax, ay = _astro(L, hora)
    if dia:
        L.oval(ax - 32, ay - 32, ax + 32, ay + 32, fill="#FFE082", outline="")
        L.oval(ax - 26, ay - 26, ax + 26, ay + 26, fill="#FFD54F", outline="")
    else:
        for ex, ey in ESTRELLAS:
            L.oval(ex, ey, ex + 3, ey + 3, fill="#F5F5F5", outline="")
        L.oval(ax - 27, ay - 27, ax + 27, ay + 27, fill="#F5F5F5", outline="")
        for dx, dy, rr in ((-9, -8, 6), (8, 5, 8), (-4, 12, 4)):                              # cráteres
            L.oval(ax + dx - rr, ay + dy - rr, ax + dx + rr, ay + dy + rr, fill="#CFD8DC", outline="")
    nubes = int(round(p.nubosidad * 4))
    for i in range(nubes):
        cx, cy = 140 + i * 230 + 20 * math.sin(fotograma / 40.0 + i), 70 + 25 * (i % 2)
        color = "#ECEFF1" if dia else "#546E7A"
        for dx, dy, rx in ((-30, 6, 30), (0, -6, 38), (32, 6, 28)):
            L.oval(cx + dx - rx, cy + dy - 18, cx + dx + rx, cy + dy + 18, fill=color, outline="")

    # (el sol y la luna se ven a través del vidrio: se dibujan antes de los marcos)
    L.linea(80, 200, 500, 60, 920, 200, fill="#557C55", width=5)
    L.linea(80, 200, 80, SUELO_Y, fill="#557C55", width=5)
    L.linea(920, 200, 920, SUELO_Y, fill="#557C55", width=5)
    L.linea(500, 60, 500, SUELO_Y, fill="#557C55", width=3)
    L.linea(290, 130, 290, 200, fill="#8BAF8B", width=1)
    L.linea(710, 130, 710, 200, fill="#8BAF8B", width=1)

    # ---- suelo: más oscuro cuanto más húmedo ----
    L.rect(80, SUELO_Y, 920, 520, fill=mezclar("#C2A26B", "#4B3621", r.H / 100.0), outline="")
    L.texto(500, 470, f"Suelo  {r.H:.1f} %", fill="white", tam=13)
    # barra de humedad con los umbrales del riego
    L.rect(110, 495, 890, 507, fill="#37474F", outline="")
    L.rect(110, 495, 110 + 780 * min(1.0, r.H / 100.0), 507, fill=AZUL, outline="")
    if p.control_activo:
        for u in (p.H_min, p.H_max):
            L.linea(110 + 7.8 * u, 491, 110 + 7.8 * u, 511, fill="#FFD54F", width=2)

    # ---- plantas (altura según el tamaño P del modelo) ----
    if p.usar_crecimiento:
        rel = min(1.0, r.P / max(p.K, 1e-9))
        alto = 25 + rel * 100
        pares = 1 + int(rel * 3)
    else:
        alto, pares = 50, 2
    for x in PLANTAS_X:
        L.linea(x, SUELO_Y, x, SUELO_Y - alto, fill="#38783B", width=5)
        for i in range(pares):
            y = SUELO_Y - alto + i * (alto / (pares + 1)) * 0.7
            L.oval(x - 32, y - 14, x - 2, y + 8, fill="#4DAD55", outline="")
            L.oval(x + 2, y - 22, x + 32, y, fill="#388E3C", outline="")

    # ---- riego: depósito, tubería y aspersor ----
    L.rect(110, 235, 145, 280, fill="#78909C", outline="#455A64", width=2)
    L.linea(127, 235, 127, 215, fill="#455A64", width=5)
    L.linea(127, 215, 300, 215, fill="#455A64", width=5)
    L.linea(280, 215, 280, 230, fill="#455A64", width=5)
    if r.riego:
        for k, (gx, gy) in enumerate(((265, 250), (280, 262), (295, 250), (272, 282), (290, 288), (258, 300), (302, 304))):
            gy += (fotograma * 6 + k * 11) % 30                    # las gotas caen
            if gy < SUELO_Y - 10:
                L.oval(gx, gy, gx + 7, gy + 12, fill="#29B6F6", outline="#0288D1")
    L.texto(220, 330, "RIEGO ACTIVO" if r.riego else "RIEGO INACTIVO",
            fill="#0288D1" if r.riego else "#37474F", tam=11)

    # ---- ventilador (las aspas giran mientras está activo) ----
    cx, cy = 850, 270
    L.oval(cx - 35, cy - 35, cx + 35, cy + 35, outline="#455A64", width=4, fill="#ECEFF1")
    ang = math.radians(fotograma * 28) if r.vent else 0.0
    color_aspa = "#43A047" if r.vent else "#90A4AE"
    for k in range(4):
        a = ang + k * math.pi / 2
        ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        L.poligono(cx, cy, cx + 28 * ux - 10 * vx, cy + 28 * uy - 10 * vy,
                   cx + 28 * ux + 10 * vx, cy + 28 * uy + 10 * vy, fill=color_aspa, outline="#455A64")
    L.oval(cx - 7, cy - 7, cx + 7, cy + 7, fill="#37474F", outline="")
    L.texto(cx, cy + 55, "VENTILACIÓN ACTIVA" if r.vent else "VENTILACIÓN INACTIVA",
            fill="#2E7D32" if r.vent else "#37474F", tam=10)
    if r.vent:                                                 # flujo de aire hacia afuera
        for k in range(3):
            off = (fotograma * 5 + k * 20) % 60
            L.linea(890 + off, 245 + k * 25, 925 + off, 245 + k * 25, fill=AZUL, width=3, arrow="last")

    # ---- iluminación artificial ----
    if r.luz:
        L.oval(455, 120, 545, 190, fill="#FFF9C4", outline="")
        L.oval(475, 135, 525, 180, fill="#FFEE58", outline="#F9A825", width=2)
    else:
        L.oval(480, 140, 520, 175, fill="#B0BEC5", outline="#78909C", width=2)
    L.linea(500, 100, 500, 140, fill="#455A64", width=3)
    L.texto(500, 218, "LUZ ARTIFICIAL ON" if r.luz else "luz artificial off",
            fill="#F57F17" if r.luz else "#607D8B", tam=9)

    # ---- rótulos ----
    L.texto(15, 15, f"t = {r.t:g} min   |   {int(hora):02d}:{int((hora % 1) * 60):02d}",
            anchor="nw", fill="white" if oscuro else "#263238", tam=13)
    L.texto(985, 15, f"Exterior {r.Tamb:.1f} °C", anchor="ne",
            fill="white" if oscuro else "#263238", tam=11)
    L.texto(500, 565, "Simulación visual basada en el modelo matemático (EDO + Euler)",
            fill="#37474F", tam=10, negrita=False)
