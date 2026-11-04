"""ETAPA 4 – Prototipo matemático SIN interfaz gráfica.

Uso:   python prototipo.py                 (escenario "Día normal")
       python prototipo.py "Baja humedad"
"""
import os
import sys

from invernadero.explicador import explicar_paso
from invernadero.graficas import figura_resultados
from invernadero.parametros import escenarios
from invernadero.simulador import Simulador


def main():
    nombre = sys.argv[1] if len(sys.argv) > 1 else "Día normal"
    esc = escenarios()
    if nombre not in esc:
        print("Escenarios disponibles:", ", ".join(esc))
        sys.exit(1)

    sim = Simulador(esc[nombre]).ejecutar()
    p = sim.p
    print(f"Escenario: {nombre}   (Δt = {p.dt:g} min, duración = {p.duracion:g} min)\n")
    print(f"{'t[min]':>8} {'T[°C]':>8} {'H[%]':>8} {'L[%]':>7} {'P[cm]':>7}  riego vent luz")
    salto = max(1, len(sim.registros) // 24)
    for r in sim.registros[::salto]:
        print(f"{r.t:8.1f} {r.T:8.3f} {r.H:8.3f} {r.L:7.2f} {r.P:7.3f}  "
              f"{'ON ' if r.riego else '-- '}   {'ON ' if r.vent else '-- '}  {'ON' if r.luz else '--'}")

    print("\n--- Primer paso explicado ---")
    print(explicar_paso(sim, 0))
    print("\n--- Eventos ---")
    for t, _, txt in sim.eventos:
        print(f"t = {t:7.1f} min  {txt}")
    print("\n--- Resumen ---")
    for k, v in sim.resumen().items():
        print(f"{k:>10}: {v:.3f}" if isinstance(v, float) else f"{k:>10}: {v}")

    os.makedirs("resultados", exist_ok=True)
    sim.a_csv("resultados/prototipo.csv")
    figura_resultados(sim, titulo=nombre).savefig("resultados/prototipo.png", dpi=120)
    print("\nGuardado: resultados/prototipo.csv y resultados/prototipo.png")


if __name__ == "__main__":
    main()
