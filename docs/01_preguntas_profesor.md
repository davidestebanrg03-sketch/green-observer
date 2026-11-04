# Etapa 1 – Revisión de la propuesta con el profesor

Lleve esta lista a la reunión y anote las respuestas al lado.

## Confirmaciones
- [ ] ¿Acepta el **invernadero virtual** (sin sensores ni Arduino) como proyecto?
- [ ] ¿Acepta usar **Python** con **Tkinter + Matplotlib** (y NumPy/SymPy si hace falta)?
- [ ] ¿Está bien que el tiempo se simule en **minutos** con paso Δt = 1 min?

## Nivel matemático
- [ ] ¿Exige resolver **alguna ecuación analíticamente** o basta el método numérico (Euler)?
      *Ya tenemos preparadas las soluciones analíticas de dH/dt = R − E y dT/dt = k(Tamb − T)
      para comparar con Euler (ver `docs/03_calculos_manuales.md`).*
- [ ] ¿Es suficiente **Euler** o espera también Euler mejorado / Runge-Kutta?
- [ ] ¿Cuenta como contenido del curso el **modelo logístico** dP/dt = rP(1 − P/K)?
- [ ] ¿Espera análisis cualitativo (puntos de equilibrio, estabilidad, campo de direcciones)?

## Decisiones de modelado que conviene que apruebe
1. La **luminosidad** es una *función del tiempo* (entrada), no una EDO.
2. La **ventilación** aumenta el coeficiente de intercambio: k pasa a k + kv.
3. La **pérdida de agua E** puede depender de la temperatura (modelo acoplado) o ser constante.
4. El **crecimiento** es opcional; ¿lo incluimos o lo dejamos como ampliación?
5. Los valores del ejemplo del documento (E = 0.8 %/min) son didácticos; para simular 24 h usamos
   valores más lentos (E0 = 0.03 %/min). ¿Está de acuerdo?

## Entregables
- [ ] ¿Formato del informe (Word/PDF), extensión y fecha de entrega?
- [ ] ¿Sustentación con demostración del programa? ¿Cuánto tiempo?
