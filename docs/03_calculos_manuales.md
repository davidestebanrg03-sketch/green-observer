# Etapa 3 – Cálculos manuales (referencia para validar el programa)

Todos estos valores se comprueban automáticamente con `python validacion.py` y con
`python -m unittest -v`.

## 1. Humedad – ejemplo del documento
Datos: H0 = 60 %, E = 0.8 %/min, Δt = 1 min. Sin riego: dH/dt = 0 − 0.8 = −0.8 %/min.

| n | t [min] | R | dH/dt | H(n+1) = H(n) + Δt·dH/dt |
|---|---|---|---|---|
| 0 | 0 | 0 | −0.8 | 60 − 0.8 = **59.2** |
| 1 | 1 | 0 | −0.8 | **58.4** |
| 2 | 2 | 0 | −0.8 | **57.6** |
| 3 | 3 | 0 | −0.8 | **56.8** |
| 4 | 4 | 0 | −0.8 | **56.0** |
| 5 | 5 | 2.5 | +1.7 | 56.0 + 1.7 = **57.7** (se activa el riego) |
| 6 | 6 | 2.5 | +1.7 | **59.4** |

*Interpretación:* la pendiente cambia de signo en t = 5 min porque R (2.5) supera a E (0.8).
En el programa: escenario «Ejemplo manual del documento» (con H_min = 56 el riego se activa exactamente en n = 5).

**Solución analítica:** con R y E constantes, dH/dt = R − E ⇒ H(t) = H0 + (R − E)t.
La solución es una recta, así que **Euler es exacto** en cada tramo (error = 0, salvo redondeo).

## 2. Temperatura – dos casos (a = 0, k = 0.02, kv = 0.06, Δt = 1 min)

**Caso A: T0 = 24, Tamb = 30, sin ventilación** (k_ef = 0.02)

| n | dT/dt = k_ef(Tamb − T) | T(n+1) |
|---|---|---|
| 0 | 0.02·(30 − 24) = 0.12 | **24.12** |
| 1 | 0.02·(30 − 24.12) = 0.1176 | **24.2376** |
| 2 | 0.02·(30 − 24.2376) = 0.115248 | **24.352848** |

**Caso B: T0 = 34, Tamb = 30, con ventilación** (k_ef = 0.02 + 0.06 = 0.08)

| n | dT/dt | T(n+1) |
|---|---|---|
| 0 | 0.08·(30 − 34) = −0.32 | **33.68** |
| 1 | 0.08·(30 − 33.68) = −0.2944 | **33.3856** |
| 2 | 0.08·(30 − 33.3856) = −0.270848 | **33.114752** |

Comparando A y B se ve el efecto de la ventilación: para una misma diferencia (Tamb − T) la tasa de cambio es 4 veces mayor con ventilación, porque k_ef pasa de 0.02 a 0.08. Por eso en el caso B la temperatura se acerca al exterior mucho más rápido.

**Solución analítica** (Tamb y L constantes). La ecuación lineal dT/dt = k(Tamb − T) tiene solución

    T(t) = Tamb + (T0 − Tamb)·e^(−k t)

Ejemplo con T0 = 20, Tamb = 30, k = 0.02:

| t [min] | Euler (Δt = 1) | Exacta | Error |
|---|---|---|---|
| 1 | 20.2000 | 20.1980 | 0.0020 |
| 2 | 20.3960 | 20.3921 | 0.0039 |
| 3 | 20.5881 | 20.5824 | 0.0057 |

El error de Euler es proporcional a Δt (método de primer orden): al reducir Δt a la mitad, el error máximo
se reduce aproximadamente a la mitad (`validacion.py` lo muestra para Δt de 0.5 a 60 min).

## 3. Entradas ambientales (hora_inicio = 0)
- Tamb(15 h) = 24 + 5·sin(2π·6/24) = 24 + 5 = **29 °C**; Tamb(3 h) = 24 − 5 = **19 °C**.
- L(12 h) = 100·sin(2π·6/24) = **100 %**; L(9 h) = 100·sin(π/4) = **70.71 %**; L(20 h) = max(0, sin(…)) = **0 %**.

## 4. Un paso del crecimiento
Con T = 25, H = 60, L = 100, P = 2, r = 0.002, K = 50: fT = fH = fL = 1
dP/dt = 0.002·1·1·1·2·(1 − 2/50) = 0.002·2·0.96 = 0.00384 cm/min  ⇒  P(1) = 2 + 0.00384 = **2.00384 cm**.

## 5. Pérdida de agua acoplada a la temperatura
E(30 °C) = 0.03·(1 + 0.04·(30 − 25)) = 0.03·1.2 = **0.036 %/min** (a 25 °C vale 0.03): más calor ⇒ más pérdida.
