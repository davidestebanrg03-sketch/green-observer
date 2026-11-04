# Qué tomé de cada versión

**Base: `invernadero_ed` (v1)** — es la que tenía el modelo, los cálculos paso a paso, la verificación
y los informes funcionando. Todo eso se conserva igual (mismos nombres de parámetros y ecuaciones, así
`docs/` y los cálculos manuales siguen valiendo).

**Cambios tomados de `Green-Observer` (v2)**

| Idea de la v2 | Cómo quedó |
|---|---|
| Simulación separada del invernadero | `invernadero/sesion.py` (sesión compartida, patrón observador) + ventanas en `interfaz/` |
| Pantalla de inicio «Green Observer» | `interfaz/app.py` |
| Invernadero virtual en ventana propia (sol/luna, aspersor, ventilador, plantas, cielo) | `interfaz/escena.py` + `invernadero_virtual.py`; ahora además: nubes, estrellas, lámpara, gotas y aspas animadas, vidrio que se tiñe con la temperatura, barra de humedad con umbrales |
| Control Center con pestañas | `interfaz/control_center.py` (con las pestañas de la v1) |
| Escenario / velocidad elegibles desde el invernadero | ambas ventanas controlan la misma sesión |
| Hora del día en el historial de eventos | columna `hora` en eventos y datos |
| Luz total limitada a 100 %, planta limitada a K, último paso recortado | `simulador.py` |
| Validaciones extra de parámetros | `parametros.py` |

**Lo que NO traje de la v2 (y por qué)**

- Nombres largos de parámetros (`temperatura_ventilacion_activar`, …): rompían la correspondencia con las ecuaciones del documento.
- Un `main()` de 1 600 líneas con funciones anidadas: se reemplazó por clases pequeñas.
- Informe `.txt`: se mantiene el informe Word de la v1 (con gráficas y verificación).
- Se había perdido «Verificar modelo», los cálculos manuales, el escenario «Ejemplo manual» y el de referencia sin control: vuelven.
- Archivos `*_respaldo.py`, `.idea/` y los `prueba_*.py` sueltos (reemplazados por `tests/`).
- `sympy` de `requirements.txt`: no se usaba en ningún archivo.

**Diferencia de comportamiento a tener en cuenta:** en la v2 la simulación avanzaba 1 paso por segundo
(1x) y al abrir el invernadero había que pulsar «Ejecutar simulación». Ahora la simulación ya existe al
abrir y la velocidad se elige en *pasos/s* (1 a 2000; por defecto 125 ≈ un día en 12 s).
