"""Aplicación principal de Green Observer.

Pantalla de inicio, Control Center e invernadero virtual.
La simulación es compartida entre las dos ventanas.
"""

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from invernadero.parametros import escenarios
from invernadero.sesion import SesionSimulacion
from .control_center import ControlCenterPanel
from .invernadero_virtual import VentanaInvernadero


# ------------------------------------------------------------
# PALETA DE COLORES Y CONSTANTES DE DISEÑO
# ------------------------------------------------------------

TEAL = "#0C6F73"
TEAL_TEXTO = "#07858A"
LAVANDA = "#E8EAF6"
BLANCO = "#FFFFFF"
TURQUESA = "#5CE1E6"
VERDE = "#00C853"
LIMA = "#80FF39"
GRIS_TEXTO = "#52616B"
COLOR_HOVER = "#DCE1F0"


class AplicacionGreenObserver(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Green Observer – Simulación y control de un invernadero")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.configure(bg=BLANCO)
        ttk.Style(self).theme_use("clam")

        # Cargar recursos gráficos
        self._imagenes_inicio = {
            "logo": self._cargar_imagen("logo_green_observer.png", 400, 300),
            "green_house": self._cargar_imagen("green_house.png", 220, 180),
            "control_center": self._cargar_imagen("control_center.png", 220, 180),
        }

        # Sesión compartida del simulador
        self.sesion = SesionSimulacion(
            self, escenarios()["Día normal"], "Día normal"
        )

        self._ventana_inv = None

        # Pantalla de inicio y Control Center
        self._pantalla_inicio = self._crear_inicio()
        self.control_center = ControlCenterPanel(
            self,
            self.sesion,
            abrir_invernadero=self.abrir_invernadero,
            volver_inicio=self.mostrar_inicio,
        )

        self.mostrar_inicio()
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

    # ========================================================
    # PANTALLA DE INICIO
    # ========================================================

    def _crear_inicio(self):
        f = tk.Frame(self, bg=BLANCO)

        self.canvas_inicio = tk.Canvas(f, bg=BLANCO, highlightthickness=0)
        self.canvas_inicio.pack(fill="both", expand=True)

        self.canvas_inicio.bind("<Configure>", self._dibujar_inicio)

        return f

    # ========================================================
    # DIBUJO Y RENDERIZADO DE LA INTERFAZ
    # ========================================================

    def _dibujar_inicio(self, event=None):
        c = self.canvas_inicio
        c.delete("all")

        ancho = c.winfo_width()
        alto = c.winfo_height()

        if ancho <= 1 or alto <= 1:
            return

        # Barra de encabezado
        alto_barra = 39
        c.create_rectangle(0, 0, ancho, alto_barra, fill=TEAL, outline="")

        # Geometría y márgenes
        margen = max(20, ancho * 0.016)
        espacio = max(22, ancho * 0.025)
        contenido_y = alto_barra + 22
        contenido_alto = alto - contenido_y - 20

        # Panel izquierdo (Logotipo y bienvenida)
        panel_ancho = ancho * 0.435
        panel_x = margen
        panel_y = contenido_y

        self._rectangulo_redondeado(
            c,
            panel_x,
            panel_y,
            panel_x + panel_ancho,
            panel_y + contenido_alto,
            30,
            LAVANDA,
        )

        centro_x = panel_x + panel_ancho / 2
        zona_logo_y = panel_y + contenido_alto * 0.05
        zona_logo_alto = contenido_alto * 0.60

        c.create_image(
            centro_x,
            zona_logo_y + zona_logo_alto / 2,
            image=self._imagenes_inicio["logo"],
            anchor="center",
            tags="logo_principal",
        )

        titulo_y = panel_y + contenido_alto * 0.75
        c.create_text(
            centro_x,
            titulo_y,
            text="Green Observer",
            fill=TEAL_TEXTO,
            font=("Segoe UI", max(22, int(ancho * 0.024)), "bold"),
        )

        eslogan = (
            "Explora las condiciones ambientales, observa los\n"
            "resultados y analiza el comportamiento del invernadero."
        )
        c.create_text(
            centro_x,
            panel_y + contenido_alto * 0.865,
            text=eslogan,
            fill=TEAL,
            font=("Segoe UI", max(11, int(ancho * 0.012)), "bold"),
            justify="center",
            width=panel_ancho - 40,
        )

        # Panel derecho (Tarjetas de acceso)
        tarjetas_x = panel_x + panel_ancho + espacio
        espacio_derecho = ancho - margen - tarjetas_x
        separacion_tarjetas = max(20, ancho * 0.021)

        tarjeta_ancho = ((espacio_derecho - separacion_tarjetas) / 2) * 0.90
        tarjeta_alto = contenido_alto * 0.47
        ancho_total = (tarjeta_ancho * 2) + separacion_tarjetas

        tarjetas_x += (espacio_derecho - ancho_total) / 2
        tarjeta_y = contenido_y + (contenido_alto - tarjeta_alto) / 2

        # Tarjeta 1: Green House
        self._dibujar_tarjeta(
            c,
            tarjetas_x,
            tarjeta_y,
            tarjeta_ancho,
            tarjeta_alto,
            "Green House",
            "green_house",
            "GREEN_HOUSE_TAG",
        )

        # Tarjeta 2: Control Center
        control_x = tarjetas_x + tarjeta_ancho + separacion_tarjetas
        self._dibujar_tarjeta(
            c,
            control_x,
            tarjeta_y,
            tarjeta_ancho,
            tarjeta_alto,
            "Control Center",
            "control_center",
            "CONTROL_CENTER_TAG",
        )

    def _dibujar_tarjeta(
        self, canvas, x, y, ancho, alto, titulo, identificador, etiqueta
    ):
        centro_x = x + ancho / 2

        self._rectangulo_redondeado(
            canvas,
            x,
            y,
            x + ancho,
            y + alto,
            20,
            LAVANDA,
            tags=(etiqueta, "tarjeta"),
        )

        canvas.create_text(
            centro_x,
            y + alto * 0.14,
            text=titulo,
            fill="#479E98",
            font=("Segoe UI", max(16, int(ancho * 0.08)), "bold"),
            tags=(etiqueta,),
        )

        centro_y = y + alto * 0.59
        imagen = self._imagenes_inicio[identificador]
        canvas.create_image(
            centro_x,
            centro_y,
            image=imagen,
            anchor="center",
            tags=(etiqueta,),
        )

        # Eventos de interacción
        canvas.tag_bind(
            etiqueta,
            "<Button-1>",
            lambda e: (
                self.abrir_invernadero()
                if identificador == "green_house"
                else self.abrir_control_center()
            ),
        )

        canvas.tag_bind(
            etiqueta,
            "<Enter>",
            lambda e: self._hover_tarjeta(etiqueta, True),
        )
        canvas.tag_bind(
            etiqueta,
            "<Leave>",
            lambda e: self._hover_tarjeta(etiqueta, False),
        )

    # ========================================================
    # GEOMETRÍA AUXILIAR
    # ========================================================

    def _rectangulo_redondeado(
        self, canvas, x1, y1, x2, y2, radio, color, tags=()
    ):
        puntos = [
            x1 + radio, y1,
            x2 - radio, y1,
            x2 - radio, y1,
            x2, y1,
            x2, y1 + radio,
            x2, y1 + radio,
            x2, y2 - radio,
            x2, y2 - radio,
            x2, y2,
            x2 - radio, y2,
            x2 - radio, y2,
            x1 + radio, y2,
            x1 + radio, y2,
            x1, y2,
            x1, y2 - radio,
            x1, y2 - radio,
            x1, y1 + radio,
            x1, y1 + radio,
            x1, y1,
            x1 + radio, y1,
        ]

        return canvas.create_polygon(
            puntos,
            smooth=True,
            splinesteps=16,
            fill=color,
            outline="",
            tags=tags,
        )

    # ========================================================
    # EFECTOS VISUALES
    # ========================================================

    def _hover_tarjeta(self, etiqueta, activo):
        color = COLOR_HOVER if activo else LAVANDA

        for item in self.canvas_inicio.find_withtag(etiqueta):
            if self.canvas_inicio.type(item) == "polygon":
                self.canvas_inicio.itemconfigure(item, fill=color)

        self.canvas_inicio.config(cursor="hand2" if activo else "")

    # ========================================================
    # NAVEGACIÓN ENTRE VISTAS
    # ========================================================

    def mostrar_inicio(self):
        self.control_center.pack_forget()
        self._pantalla_inicio.pack(fill="both", expand=True)

    def abrir_control_center(self):
        self._pantalla_inicio.pack_forget()
        self.control_center.pack(fill="both", expand=True)
        self.deiconify()
        self.lift()

    def abrir_invernadero(self):
        if (
            self._ventana_inv is not None
            and self._ventana_inv.winfo_exists()
        ):
            self._ventana_inv.deiconify()
            self._ventana_inv.lift()
            return

        self._ventana_inv = VentanaInvernadero(
            self,
            self.sesion,
            abrir_control_center=self.abrir_control_center,
        )

    def _cargar_imagen(self, nombre, ancho, alto):
        carpeta = Path(__file__).resolve().parent.parent / "assets"
        archivo = carpeta / nombre

        imagen = Image.open(archivo)
        imagen.thumbnail((ancho, alto), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(imagen, master=self)

    # ========================================================
    # GESTIÓN DE CIERRE DE LA APLICACIÓN
    # ========================================================

    def cerrar(self):
        if hasattr(self, "sesion") and self.sesion:
            self.sesion.pausar()
        self.destroy()


def main():
    app = AplicacionGreenObserver()
    app.mainloop()


if __name__ == "__main__":
    main()