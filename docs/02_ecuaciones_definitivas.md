# Etapa 2 – Ecuaciones definitivas

Unidades: tiempo en **minutos**; T en °C; H, L en %; P en cm. Hora del día h = hora_inicio + t/60.

## Variables
| Variable | Tipo | Unidad | Origen |
|---|---|---|---|
| T(t) | estado (EDO) | °C | dT/dt |
| H(t) | estado (EDO) | % | dH/dt |
| P(t) | estado (EDO, opcional) | cm | dP/dt |
| L(t) | entrada (función del tiempo) | % | sinusoide recortada |
| Tamb(t) | entrada | °C | sinusoide |
| u_riego, v (ventilación), u_luz | control (0/1) | – | histéresis |

## Sistema de ecuaciones
**Humedad** (del documento, con E dependiente de T):

    dH/dt = R(t) − E(T)          R = R_on·u_riego          E = E0·(1 + β(T − Tref))

**Temperatura** (del documento; Q(t) se concreta como radiación + efecto de la ventilación):

    dT/dt = (k + kv·v(t))·(Tamb(t) − T) + a·L(t)

**Luminosidad** (entrada):

    L(t) = Lmax·(1 − nub)·max(0, sin(2π(h − 6)/24)) + L_art·u_luz

**Temperatura exterior** (entrada):

    Tamb(t) = Tmed + A·sin(2π(h − 9)/24)        (máx. 15 h, mín. 3 h)

**Crecimiento** (ampliación opcional, logístico modulado):

    dP/dt = r·fT·fH·fL·P·(1 − P/K)
    fT = exp(−((T − Topt)/wT)²)   fH = exp(−((H − Hopt)/wH)²)   fL = L/100

**Método numérico (Euler explícito):**  y(n+1) = y(n) + Δt·f(t_n, y_n)

## Control con histéresis
| Acción | Se enciende | Se apaga | Efecto en el modelo |
|---|---|---|---|
| Riego | H ≤ H_min (40) | H ≥ H_max (70) | R = 0 → R_on (dH/dt pasa de negativo a positivo) |
| Ventilación | T ≥ T_max (30) | T ≤ T_ok (27) | k → k + kv (la T tiende más rápido a Tamb) |
| Iluminación | L_nat < L_min y 6 h ≤ h < 20 h | al salir de la condición | L → L + L_art |

La histéresis (dos umbrales distintos) evita que el actuador se encienda y apague en cada paso.

## Parámetros por defecto
| Parámetro | Valor | Significado |
|---|---|---|
| Δt | 1 min | paso de Euler |
| T0, H0, P0 | 22 °C, 60 %, 2 cm | condiciones iniciales |
| Tmed, A | 24 °C, 5 °C | temperatura exterior |
| R_on, E0, β, Tref | 0.20 %/min, 0.03 %/min, 0.04 1/°C, 25 °C | humedad |
| k, kv, a | 0.02, 0.06 1/min, 0.0016 °C/min/% | temperatura |
| r, K, Topt, Hopt | 0.002 1/min, 50 cm, 25 °C, 60 % | crecimiento |

**Justificación de a:** sin ventilación la temperatura de equilibrio con luz máxima es
Tamb + a·L/k = Tamb + 0.0016·100/0.02 = Tamb + 8 °C; con ventilación, Tamb + 0.16/0.08 = Tamb + 2 °C.
Es un comportamiento cualitativamente razonable (un invernadero se calienta por encima del exterior).

## Estabilidad numérica de Euler
Para dT/dt = k_ef(Tamb − T) + … el método de Euler da T(n+1) − Tamb = (1 − k_ef·Δt)·(T(n) − Tamb):
- si k_ef·Δt < 1 la aproximación decae suavemente (comportamiento correcto);
- si 1 < k_ef·Δt < 2 aparecen oscilaciones amortiguadas (resultado incorrecto cualitativamente);
- si k_ef·Δt > 2 la solución numérica diverge (inestable).

Con k_ef = 0.08 (ventilación) y Δt = 1 min, k_ef·Δt = 0.08: muy seguro. Se vuelve oscilatorio con
Δt > 12.5 min e inestable con Δt > 25 min. Por eso la interfaz permite cambiar Δt y el informe incluye el estudio del error.

El modelo tiene **tres EDO de primer orden** (H, T y, opcionalmente, P). Las de humedad y temperatura son lineales
con coeficientes constantes por tramos, por lo que tienen solución analítica (ver `03_calculos_manuales.md`).
