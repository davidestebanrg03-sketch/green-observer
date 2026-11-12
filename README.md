# Green Observer

Simulación y control de un invernadero mediante ecuaciones diferenciales.

Proyecto de Ecuaciones Diferenciales desarrollado en la Universidad del Tolima (IDEAD), Ingeniería de Sistemas.

## Descripción

Green Observer simula la evolución de la temperatura interior, la humedad del suelo, la luminosidad y, de forma opcional, el crecimiento de un cultivo dentro de un invernadero virtual. El modelo se plantea como un sistema de ecuaciones diferenciales ordinarias que se resuelve con el método de Euler explícito. Sobre la simulación actúa un control por histéresis del riego, la ventilación y la iluminación artificial.

La aplicación ofrece dos ventanas que comparten la misma simulación:

- **Control Center:** gráficas, cálculo paso a paso, eventos de control, datos y edición de parámetros.
- **Invernadero virtual:** vista animada del invernadero (ciclo día y noche, riego, ventilador, iluminación y cultivo).

Además, permite exportar los datos a CSV, generar informes en formato Word y, de manera opcional, enviar telemetría a Azure IoT Hub.

## Requisitos

- Python 3.10 o superior.
- Tkinter. Viene incluido con Python en Windows y macOS; en Linux se instala con `sudo apt install python3-tk`.
- Las dependencias de Python que se listan a continuación (se instalan con `requirements.txt`).

| Paquete | Versión mínima | Uso |
|---|---|---|
| matplotlib | 3.7 | Gráficas del Control Center y de los informes |
| python-docx | 1.0 | Generación de informes en formato `.docx` |
| Pillow | 10.0 | Carga de imágenes e íconos de la interfaz |
| azure-iot-device | 2.14 | Envío de telemetría a Azure IoT Hub |
| azure-eventhub | 5.11 | Solo para `integracion_azure/leer_telemetria.py` (opcional, no incluido en `requirements.txt`) |

NumPy se instala automáticamente como dependencia de Matplotlib.

## Instalación

Desde la carpeta del proyecto:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux y macOS
source .venv/bin/activate

pip install -r requirements.txt
```

En Visual Studio Code, seleccionar el intérprete del entorno virtual con `Ctrl+Shift+P`, opción *Python: Select Interpreter*.

## Ejecución

| Elemento | Comando | Descripción |
|---|---|---|
| Aplicación | `python main.py` | Abre la pantalla de inicio, desde la que se accede al Control Center y al invernadero virtual |
| Prototipo | `python prototipo.py ["Baja humedad"]` | Simulación por consola; guarda `prototipo.csv` y `prototipo.png` en `resultados/` |
| Validación | `python validacion.py` | Compara los cálculos manuales con el programa, estudia la influencia de Δt, ejecuta todos los escenarios y genera los informes |
| Pruebas | `python -m unittest -v` | Ejecuta las pruebas automáticas |

El archivo `.vscode/launch.json` incluye configuraciones equivalentes para la pestaña *Run and Debug* de Visual Studio Code.

## Uso de la interfaz

1. En la pantalla de inicio se abre el Control Center, el invernadero virtual o ambas ventanas.
2. Se elige un escenario desde cualquiera de las ventanas, o se editan los valores en la pestaña *Parámetros* y se pulsa *Aplicar parámetros y reiniciar simulación*.
3. La simulación se controla con los botones *Iniciar* o *Pausar*, *Paso* (avanza un paso de Euler), *Todo* (ejecuta hasta el final) y *Reiniciar*. La velocidad puede ser de 1, 5, 25, 125, 500 o 2000 pasos por segundo; el valor inicial es 125.
4. En la pestaña *Cálculos* se muestra la ecuación con los valores sustituidos y el resultado del paso de Euler. Al desmarcar *Seguir el último paso calculado* es posible revisar cualquier paso anterior.
5. El botón *Verificar modelo* compara el programa con los cálculos manuales. Los botones *CSV* y *DOCX* de la sección *Exportar* guardan los datos y el informe, respectivamente.

Los cambios de escenario, la pausa y la edición de parámetros realizados en una ventana se reflejan en la otra, porque ambas utilizan la misma sesión de simulación.

### Escenarios disponibles

- Día normal
- Ejemplo manual del documento
- Baja humedad
- Alta temperatura
- Poca luz / nublado
- Cambio ambiental (ola de calor)
- Sin control (referencia)

## Modelo matemático

El tiempo se expresa en minutos, la temperatura T en °C, la humedad H y la luminosidad L en %, y el crecimiento P en cm.

```
Humedad       dH/dt = R(t) − E(T)               R = R_on·u_riego     E = E0·(1 + β·(T − Tref))
Temperatura   dT/dt = (k + kv·v(t))·(Tamb − T) + a·L(t)
Crecimiento   dP/dt = r·fT·fH·fL·P·(1 − P/K)    (opcional, modelo logístico modulado)
Euler         y(n+1) = y(n) + Δt·f(t_n, y_n)
```

La luminosidad L(t) y la temperatura exterior Tamb(t) son funciones del tiempo (entradas del modelo). El riego, la ventilación y la iluminación se activan mediante control por histéresis con dos umbrales por actuador.

La deducción completa, los parámetros por defecto y el análisis de estabilidad numérica se encuentran en:

- [`docs/02_ecuaciones_definitivas.md`](docs/02_ecuaciones_definitivas.md)
- [`docs/03_calculos_manuales.md`](docs/03_calculos_manuales.md)

### Consideraciones de modelado

- La ventilación y la iluminación se incorporan en el término Q(t) de la ecuación de temperatura: Q = a·L, y el coeficiente de intercambio k pasa a k + kv cuando la ventilación está activa.
- La pérdida de agua E puede depender de la temperatura; esta opción se activa o desactiva desde los parámetros.
- Para simular 24 horas se emplean tasas más lentas que las del ejemplo didáctico de la propuesta. Dicho ejemplo se conserva como escenario («Ejemplo manual del documento»).

## Integración con Azure IoT Hub (opcional)

Al iniciar la aplicación se crea un cliente que envía telemetría a Azure IoT Hub mientras la simulación está en marcha. Si la variable de entorno de conexión no está definida, el cliente informa por consola que no puede conectarse y la aplicación continúa funcionando con normalidad.

### Configuración

La cadena de conexión del dispositivo se lee de la variable de entorno `AZURE_IOT_DEVICE_CONNECTION_STRING`.

```bash
# Windows (PowerShell), solo para la sesión actual
$env:AZURE_IOT_DEVICE_CONNECTION_STRING = "<cadena de conexión del dispositivo>"

# Linux y macOS
export AZURE_IOT_DEVICE_CONNECTION_STRING="<cadena de conexión del dispositivo>"
```

> Las cadenas de conexión son credenciales. No deben escribirse en el código ni subirse al repositorio.

### Mensajes enviados

Se envía un mensaje JSON como máximo cada 15 segundos de tiempo real, con los campos `device_id` (`green-observer-simulator`), `tiempo_simulacion_min`, `temperatura_interior`, `temperatura_exterior`, `humedad_suelo`, `planta_cm`, `luminosidad_natural`, `luminosidad_efectiva`, `riego`, `ventilacion` e `iluminacion`.

### Scripts auxiliares

| Script | Descripción |
|---|---|
| `integracion_azure/prueba_azure.py` | Envía un mensaje de prueba para comprobar que la cadena de conexión es válida |
| `integracion_azure/leer_telemetria.py` | Muestra por consola los mensajes que llegan al IoT Hub. Requiere `pip install azure-eventhub` y la variable `AZURE_EVENTHUB_CONNECTION_STRING`, con la cadena del endpoint compatible con Event Hubs, que debe incluir `EntityPath` |

## Estructura del proyecto

```
main.py                  Punto de entrada de la aplicación
prototipo.py             Simulación por consola
validacion.py            Validación del modelo y generación de informes
requirements.txt         Dependencias

invernadero/             Núcleo de la simulación (no depende de Tkinter)
  parametros.py          Parámetros, condiciones iniciales y escenarios
  modelo.py              Ecuaciones diferenciales y entradas (Tamb, L)
  control.py             Control por histéresis
  simulador.py           Método de Euler y registro de resultados
  sesion.py              Sesión compartida: reloj, velocidad y notificación a las ventanas
  explicador.py          Texto de las ecuaciones y cálculo paso a paso
  verificacion.py        Cálculos manuales, solución analítica y error frente a Δt
  graficas.py            Gráficas de Matplotlib
  informe.py             Informe en formato Word
  campos.py              Descripción del formulario de parámetros

interfaz/                Ventanas (solo dibujan y solicitan acciones a la sesión)
  app.py                 Pantalla de inicio y ventana principal
  control_center.py      Panel, gráficas, cálculos, control y eventos, datos y parámetros
  invernadero_virtual.py Ventana con la escena animada y sus controles
  escena.py              Dibujo del invernadero
  tema.py                Colores y utilidades

integracion_azure/       Envío y lectura de telemetría (Azure IoT Hub)
assets/                  Imágenes e íconos de la interfaz
docs/                    Ecuaciones definitivas y cálculos manuales
resultados/              Gráficas e informes de ejemplo generados por validacion.py
tests/                   Pruebas unitarias
```

La arquitectura separa el cálculo de la presentación: `Simulador` (Euler y control) es utilizado por `SesionSimulacion` (reloj, velocidad, inicio y pausa), a la que se suscriben las ventanas y el cliente de Azure.

## Pruebas

```bash
python -m unittest -v
```

Se ejecutan 37 pruebas automáticas. Las 5 pruebas de interfaz se omiten cuando no hay Tkinter o entorno gráfico disponible.

## Autores

- David Esteban Rodríguez García
- Jesús Eliécer Portela Córdoba