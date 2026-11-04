"""Aplicación principal: pantalla de inicio + Control Center + invernadero virtual.

La ventana principal aloja la pantalla de bienvenida y el Control Center. El invernadero
virtual es una ventana aparte. Las dos comparten una única ``SesionSimulacion``.
"""
import tkinter as tk
from tkinter import ttk

from invernadero.parametros import escenarios
from invernadero.sesion import SesionSimulacion
from .control_center import ControlCenter
from .invernadero_virtual import VentanaInvernadero
from .tema import VERDE_OSCURO


class AplicacionGreenObserver(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Green Observer – Simulación y control de un invernadero")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        ttk.Style(self).theme_use("clam")

        self.sesion = SesionSimulacion(self, escenarios()["Día normal"], "Día normal")
        self._ventana_inv = None

        self._pantalla_inicio = self._crear_inicio()
        self.control_center = ControlCenter(self, self.sesion,
                                            abrir_invernadero=self.abrir_invernadero,
                                            volver_inicio=self.mostrar_inicio)
        self.mostrar_inicio()
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

    # ------------------------------------------------------------------ inicio
    def _crear_inicio(self):
        f = ttk.Frame(self, padding=30)
        ttk.Label(f, text="GREEN OBSERVER", font=("Arial", 28, "bold"), foreground=VERDE_OSCURO).pack(pady=(90, 8))
        ttk.Label(f, text="Simulación y control de un invernadero mediante ecuaciones diferenciales",
                  font=("Arial", 13)).pack(pady=(0, 24))
        ttk.Label(f, justify="center", wraplength=640,
                  text="Temperatura, humedad del suelo, luminosidad y crecimiento del cultivo, calculados con "
                       "el método de Euler y regulados por un control virtual de riego, ventilación e "
                       "iluminación. Observa el invernadero o analiza cada cálculo en el Control Center; "
                       "ambas ventanas muestran la misma simulación.").pack(pady=(0, 30))
        ttk.Button(f, text="📊  Abrir Control Center", command=self.abrir_control_center).pack(pady=8, ipadx=25, ipady=10)
        ttk.Button(f, text="🌱  Abrir invernadero virtual", command=self.abrir_invernadero).pack(pady=8, ipadx=25, ipady=10)
        ttk.Label(f, text="Universidad del Tolima – IDEAD · Ecuaciones Diferenciales", foreground="#777").pack(side="bottom")
        return f

    def mostrar_inicio(self):
        self.control_center.pack_forget()
        self._pantalla_inicio.pack(fill="both", expand=True)

    def abrir_control_center(self):
        self._pantalla_inicio.pack_forget()
        self.control_center.pack(fill="both", expand=True)
        self.deiconify()
        self.lift()

    def abrir_invernadero(self):
        if self._ventana_inv is not None and self._ventana_inv.winfo_exists():
            self._ventana_inv.deiconify()
            self._ventana_inv.lift()
            return
        self._ventana_inv = VentanaInvernadero(self, self.sesion, abrir_control_center=self.abrir_control_center)

    # ------------------------------------------------------------------ cierre
    def cerrar(self):
        self.sesion.pausar()
        self.destroy()


def main():
    AplicacionGreenObserver().mainloop()


if __name__ == "__main__":
    main()
