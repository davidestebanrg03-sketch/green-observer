# Green Observer – Simulación y control de un invernadero mediante ecuaciones diferenciales

Proyecto de Ecuaciones Diferenciales – Universidad del Tolima (IDEAD), Ingeniería de Sistemas.
Simula temperatura, humedad del suelo, luminosidad y (opcional) crecimiento de un cultivo con **EDO + método de Euler**,
con control virtual de riego, ventilación e iluminación, un **invernadero virtual animado**, un **Control Center** (gráficas, cálculos paso a paso, eventos, datos) e informes .docx.

## 1. Preparar el entorno en VS Code
```bash
# En la carpeta del proyecto (terminal de VS Code)
python -m venv .venv
.venv\Scripts\activate          # Windows      (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```
Luego `Ctrl+Shift+P → Python: Select Interpreter → .venv`.
> Tkinter viene con Python en Windows/macOS. En Linux: `sudo apt install python3-tk`.

## 2. Ejecutar
| Qué | Comando | Qué hace |
|---|---|---|
| **Aplicación** | `python main.py` | Pantalla de inicio → **Control Center** e **Invernadero virtual** (misma simulación en ambas ventanas) |
| Prototipo | `python prototipo.py ["Baja humedad"]` | Simulación por consola, CSV y PNG en `resultados/` |
| Validación | `python validacion.py` | Manual vs programa, Δt, escenarios, informes .docx |
| Pruebas | `python -m unittest -v` | 37 pruebas automáticas (las de interfaz se omiten si no hay pantalla/Tkinter) |

También hay configuraciones de ejecución en `.vscode/launch.json` (pestaña *Run and Debug*).

## 3. Estructura
```
main.py  prototipo.py  validacion.py
invernadero/            ← NÚCLEO (sin interfaz; todo se puede probar sin Tkinter)
  parametros.py   parámetros, condiciones iniciales y 7 escenarios
  modelo.py       las ecuaciones diferenciales y las entradas (Tamb, L)
  control.py      control con histéresis
  simulador.py    método de Euler + registro de resultados
  sesion.py       SESIÓN COMPARTIDA: dueña del simulador y del reloj; avisa a las ventanas
  explicador.py   texto de ecuaciones y cálculo paso a paso
  verificacion.py cálculos manuales, solución analítica, error vs Δt
  graficas.py     gráficas Matplotlib (informes)
  informe.py      informe Word
  campos.py       descripción del formulario de parámetros
interfaz/               ← VENTANAS (solo dibujan y piden acciones a la sesión)
  app.py                  pantalla de inicio y ventana principal
  control_center.py       Panel · Gráficas · Cálculos · Control y eventos · Datos · Parámetros
  invernadero_virtual.py  ventana con la escena animada y los controles
  escena.py               dibujo del invernadero (sol/luna, riego, ventilador, plantas...)
  tema.py                 colores y utilidades
tests/            pruebas unitarias
docs/             etapas 1-3 (preguntas al profesor, ecuaciones, cálculos manuales)
resultados/       salidas de ejemplo
```
Arquitectura: `Simulador` (Euler + control) ← `SesionSimulacion` (reloj, velocidad, iniciar/pausar)
← ventanas suscritas. Cambiar de escenario, pausar o editar parámetros en una ventana se refleja en la otra.

## 4. Cómo usar la interfaz
1. En la pantalla de inicio abra el **Control Center**, el **invernadero virtual** o ambos.
2. Elija un **escenario** (en cualquiera de las dos ventanas) o edite la pestaña *Parámetros* y pulse «Aplicar».
3. **▶ Iniciar** (velocidad ajustable), **⏭ Paso** para avanzar de uno en uno, **⏩ Ejecutar todo**, **⟲ Reiniciar**.
4. En **Cálculos paso a paso** verá la ecuación con los valores sustituidos y el resultado de Euler;
   desmarque «Seguir el último paso» para revisar cualquier paso anterior.
5. **Verificar modelo** muestra la comparación con los cálculos manuales; **Informe (.docx)** genera el informe.

## 5. Hoja de ruta
- [ ] 1. Revisar con el profesor → `docs/01_preguntas_profesor.md`
- [x] 2. Ecuaciones definitivas → `docs/02_ecuaciones_definitivas.md`  *(pendiente de su aprobación)*
- [x] 3. Cálculos manuales → `docs/03_calculos_manuales.md`
- [x] 4. Prototipo → `prototipo.py`
- [x] 5. Control virtual → `invernadero/control.py`
- [x] 6. Interfaz → `interfaz/` (Control Center + invernadero virtual)
- [x] 7. Validación e informe → `validacion.py`

## 6. Cambios respecto a la propuesta (coméntelos con el profesor)
- La ventilación y la luz se concretan en el término Q(t): `Q = a·L` y `k → k + kv` al ventilar.
- E (pérdida de agua) puede depender de la temperatura (opción activable).
- Para simular 24 h se usan tasas más lentas que las del ejemplo didáctico (que sí está como escenario).
