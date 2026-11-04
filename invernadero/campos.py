"""Descripción de los campos del formulario de parámetros (independiente de Tkinter)."""

# (grupo, [(campo, etiqueta, unidad), ...])
CAMPOS = [
    ("Tiempo", [("duracion", "Duración", "min"), ("dt", "Paso Δt", "min"),
                ("hora_inicio", "Hora de inicio", "h")]),
    ("Condiciones iniciales", [("T0", "Temperatura inicial T0", "°C"), ("H0", "Humedad inicial H0", "%"),
                               ("P0", "Tamaño inicial P0", "cm")]),
    ("Ambiente exterior", [("Tmed", "Temp. exterior media", "°C"), ("Amp_T", "Amplitud térmica A", "°C"),
                           ("Lmax", "Luz máxima Lmax", "%"), ("nubosidad", "Nubosidad (0–1)", ""),
                           ("perturbacion_dT", "Cambio ambiental ΔT", "°C"),
                           ("perturbacion_inicio", "  inicio del cambio", "min"),
                           ("perturbacion_fin", "  fin del cambio", "min")]),
    ("Modelo de humedad", [("R_on", "Riego R (encendido)", "%/min"), ("E0", "Pérdida base E0", "%/min"),
                           ("beta_E", "Sensibilidad β", "1/°C"), ("T_ref", "Temp. referencia", "°C")]),
    ("Modelo de temperatura", [("k", "Intercambio k", "1/min"), ("k_vent", "Extra ventilación kv", "1/min"),
                               ("a_sol", "Ganancia por luz a", "°C/min/%")]),
    ("Crecimiento", [("r_max", "Tasa máxima r", "1/min"), ("K", "Tamaño máximo K", "cm"),
                     ("T_opt", "Temp. óptima", "°C"), ("w_T", "Tolerancia térmica", "°C"),
                     ("H_opt", "Humedad óptima", "%"), ("w_H", "Tolerancia humedad", "%")]),
    ("Control", [("H_min", "Riego ON si H ≤", "%"), ("H_max", "Riego OFF si H ≥", "%"),
                 ("T_max", "Ventilación ON si T ≥", "°C"), ("T_ok", "Ventilación OFF si T ≤", "°C"),
                 ("L_min", "Luz mínima natural", "%"), ("L_art", "Aporte luz artificial", "%"),
                 ("ilum_hora_ini", "Iluminar desde", "h"), ("ilum_hora_fin", "Iluminar hasta", "h")]),
]

BOOLEANOS = [
    ("acoplar_evaporacion", "Acoplar la pérdida E a la temperatura"),
    ("usar_crecimiento", "Simular crecimiento del cultivo"),
    ("control_activo", "Control automático activo"),
    ("usar_iluminacion", "Iluminación artificial"),
]
