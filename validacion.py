"""ETAPA 7 – Validación y generación de informes.

Ejecuta: cálculos manuales vs programa, pruebas de coherencia, estudio de Δt,
todos los escenarios, comparación con/sin control y un informe .docx por escenario.
"""
import os
import re

from invernadero import verificacion
from invernadero.graficas import figura_comparacion, figura_error_dt, figura_resultados
from invernadero.informe import generar_informe
from invernadero.parametros import escenarios
from invernadero.simulador import Simulador

SALIDA = "resultados"


def slug(txt):
    return re.sub(r"[^a-z0-9]+", "_", txt.lower().replace("í", "i").replace("á", "a").replace("é", "e")
                  .replace("ó", "o").replace("ú", "u")).strip("_")


def main():
    os.makedirs(SALIDA, exist_ok=True)
    v = verificacion.ejecutar_todo()

    print("== 1. Humedad: cálculo manual vs programa ==")
    for n, m, c, d in v["humedad_manual"]:
        print(f"  n={n}  manual={m:7.3f}  programa={c:9.5f}  |dif|={d:.1e}")
    print("\n== 2. Temperatura: cálculo manual vs programa ==")
    for caso, n, m, c, d in v["temperatura_manual"]:
        print(f"  {caso:35s} n={n}  manual={m:10.6f}  programa={c:10.6f}  |dif|={d:.1e}")
    print("\n== 3. Pruebas de coherencia ==")
    for desc, ok in v["comportamientos"]:
        print(f"  [{'OK' if ok else 'FALLA'}] {desc}")

    print("\n== 4. Influencia de Δt (error de Euler vs solución exacta) ==")
    errs = verificacion.error_vs_dt()
    for dt, e in errs:
        print(f"  Δt = {dt:5g} min   error máx = {e:.5f} °C")
    figura_error_dt(errs).savefig(f"{SALIDA}/error_vs_dt.png", dpi=120)

    print("\n== 5. Escenarios ==")
    sims = {}
    for nombre, p in escenarios().items():
        s = Simulador(p).ejecutar()
        sims[nombre] = s
        r = s.resumen()
        print(f"  {nombre:34s} T[{r['T_min']:5.1f},{r['T_max']:5.1f}]  H[{r['H_min']:5.1f},{r['H_max']:5.1f}]  "
              f"riego={r['act_riego']} vent={r['act_vent']} luz={r['act_luz']}")
        figura_resultados(s, titulo=nombre).savefig(f"{SALIDA}/{slug(nombre)}.png", dpi=120)
    figura_comparacion({k: sims[k] for k in ("Alta temperatura", "Sin control (referencia)")},
                       "Efecto del control (mismas condiciones, con y sin control)"
                       ).savefig(f"{SALIDA}/comparacion_control.png", dpi=120)

    print("\n== 6. Informes ==")
    for nombre in ("Día normal", "Baja humedad", "Alta temperatura", "Cambio ambiental (ola de calor)"):
        ruta = generar_informe(sims[nombre], f"{SALIDA}/informe_{slug(nombre)}.docx",
                               titulo=f"Informe de simulación – {nombre}")
        print("  ", ruta)

    print("\nRESULTADO GLOBAL:", "TODAS LAS VERIFICACIONES CUMPLEN" if v["ok"] else "HAY VERIFICACIONES QUE FALLAN")


if __name__ == "__main__":
    main()
