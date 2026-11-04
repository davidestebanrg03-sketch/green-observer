"""Gráficas de resultados (Matplotlib, sin pyplot para que funcione dentro de Tkinter)."""
from matplotlib.figure import Figure

COLORES = {"T": "#d9534f", "H": "#2e86c1", "L": "#e6a817", "P": "#2e8b57"}


def _sombrear(ax, t, flags, color, etiqueta):
    ax.fill_between(t, 0, 1, where=flags, transform=ax.get_xaxis_transform(),
                    color=color, alpha=0.18, label=etiqueta, linewidth=0)


def figura_resultados(sim, titulo=None, figsize=(10, 9)):
    """Figura con T, H, L y P frente al tiempo, con las acciones de control sombreadas."""
    p, rs = sim.p, sim.registros
    t = [r.t / 60.0 for r in rs]           # eje en horas
    fig = Figure(figsize=figsize, dpi=100)
    n_ax = 4 if p.usar_crecimiento else 3
    axs = fig.subplots(n_ax, 1, sharex=True)

    ax = axs[0]
    ax.plot(t, [r.T for r in rs], color=COLORES["T"], label="T interior")
    ax.plot(t, [r.Tamb for r in rs], color="gray", ls=":", label="T exterior")
    if p.control_activo:
        ax.axhline(p.T_max, color=COLORES["T"], ls="--", lw=0.8, label=f"T_max = {p.T_max:g}")
    _sombrear(ax, t, [r.vent for r in rs], "#5bc0de", "ventilación")
    ax.set_ylabel("Temperatura [°C]")

    ax = axs[1]
    ax.plot(t, [r.H for r in rs], color=COLORES["H"], label="H suelo")
    if p.control_activo:
        ax.axhline(p.H_min, color=COLORES["H"], ls="--", lw=0.8, label=f"H_min = {p.H_min:g}")
        ax.axhline(p.H_max, color=COLORES["H"], ls="--", lw=0.8, label=f"H_max = {p.H_max:g}")
    _sombrear(ax, t, [r.riego for r in rs], "#7fb3d5", "riego")
    ax.set_ylabel("Humedad [%]")

    ax = axs[2]
    ax.plot(t, [r.Lnat for r in rs], color=COLORES["L"], label="luz natural")
    if p.usar_iluminacion:
        ax.plot(t, [r.L for r in rs], color="#8e44ad", ls="--", label="luz efectiva")
        _sombrear(ax, t, [r.luz for r in rs], "#f7dc6f", "iluminación")
    ax.set_ylabel("Luminosidad [%]")

    if p.usar_crecimiento:
        ax = axs[3]
        ax.plot(t, [r.P for r in rs], color=COLORES["P"], label="P planta")
        ax.set_ylabel("Tamaño [cm]")

    for a in axs:
        a.grid(alpha=0.3)
        a.legend(loc="upper right", fontsize=7, ncol=3)
    axs[-1].set_xlabel("Tiempo [h]")
    fig.suptitle(titulo or "Simulación del invernadero (método de Euler)")
    fig.tight_layout()
    return fig


def figura_error_dt(resultados):
    """Error máximo de Euler vs Δt (escala log-log)."""
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.subplots()
    dts = [r[0] for r in resultados]
    errs = [r[1] for r in resultados]
    ax.loglog(dts, errs, "o-", color="#c0392b")
    ax.set_xlabel("Paso de tiempo Δt [min]")
    ax.set_ylabel("Error máximo vs solución exacta [°C]")
    ax.set_title("Influencia de Δt en el método de Euler")
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    return fig


def figura_comparacion(simulaciones, titulo="Comparación de escenarios"):
    """Compara T y H de varias simulaciones {nombre: Simulador}."""
    fig = Figure(figsize=(10, 6), dpi=100)
    ax1, ax2 = fig.subplots(2, 1, sharex=True)
    for nombre, s in simulaciones.items():
        t = [r.t / 60.0 for r in s.registros]
        ax1.plot(t, [r.T for r in s.registros], label=nombre)
        ax2.plot(t, [r.H for r in s.registros], label=nombre)
    ax1.set_ylabel("Temperatura [°C]")
    ax2.set_ylabel("Humedad [%]")
    ax2.set_xlabel("Tiempo [h]")
    for a in (ax1, ax2):
        a.grid(alpha=0.3)
    ax1.legend(fontsize=7, ncol=2)
    fig.suptitle(titulo)
    fig.tight_layout()
    return fig
