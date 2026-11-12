
import os
import json
import asyncio
import queue
import threading
import time

from azure.iot.device.aio import IoTHubDeviceClient


class ClienteIoT:
    # Envía a Azure IoT Hub los datos de la simulación.
    def __init__(self, sesion, intervalo=15):

        self.sesion = sesion
        self.intervalo = intervalo

        # Cola que permite pasar los datos de la simulación al hilo de envío.
        self.cola = queue.Queue()

        # Objeto utilizado para indicar que el hilo debe finalizar.
        self.detener = object()

        # Momento del último envío, utilizado para controlar el intervalo.
        self.ultimo_envio = 0

        # Hilo independiente para realizar la comunicación con Azure.
        self.hilo = None

    def iniciar(self):

        # Evitar que se inicie más de un hilo de comunicación.
        if self.hilo is not None:
            return

        self.hilo = threading.Thread(
            target=self._ejecutar,
            daemon=True
        )

        self.hilo.start()

    def observar(self, evento):

        # Solo se envían datos cuando la sesión informa una actualización.
        if evento != "actualizacion":
            return

        # Limitar los envíos para no transmitir datos en cada actualización.
        ahora = time.monotonic()

        if ahora - self.ultimo_envio < self.intervalo:
            return

        self.ultimo_envio = ahora

        # Tomar el último registro de la simulación y preparar los datos que se enviarán a Azure IoT Hub.
        registro = self.sesion.sim.actual

        datos = {
            "device_id": "green-observer-simulator",
            "tiempo_simulacion_min": registro.t,
            "temperatura_interior": registro.T,
            "temperatura_exterior": registro.Tamb,
            "humedad_suelo": registro.H,
            "planta_cm": registro.P,
            "luminosidad_natural": registro.Lnat,
            "luminosidad_efectiva": registro.L,
            "riego": registro.riego,
            "ventilacion": registro.vent,
            "iluminacion": registro.luz
        }

        self.cola.put(datos)

    def _ejecutar(self):
        # Iniciar el ciclo asíncrono de comunicación con Azure.
        asyncio.run(self._procesar())

    async def _procesar(self):

        # Leer la cadena de conexión desde las variables de entorno.
        cadena = os.getenv(
            "AZURE_IOT_DEVICE_CONNECTION_STRING"
        )

        if not cadena:
            print("Azure IoT: no se encontró la cadena de conexión.")
            return

        # Crear el cliente que representa al dispositivo en Azure IoT Hub.
        cliente = IoTHubDeviceClient.create_from_connection_string(
            cadena
        )

        conectado = False

        try:

            print("Azure IoT: conectando...")

            await cliente.connect()

            conectado = True

            print("Azure IoT: conexión establecida.")

            # Esperar datos en la cola y enviarlos mientras el cliente esté activo.
            while True:

                datos = await asyncio.to_thread(
                    self.cola.get
                )

                if datos is self.detener:
                    break

                # Convertir el registro de la simulación al formato JSON requerido para transmitirlo como mensaje.
                mensaje = json.dumps(datos)

                try:

                    await cliente.send_message(mensaje)

                    print("Azure IoT: telemetría enviada.")

                except Exception as error:

                    print("Azure IoT: error al enviar:", error)

        except Exception as error:

            print("Azure IoT: error de conexión:", error)

        finally:

            # Cerrar la conexión antes de finalizar el proceso.
            if conectado:

                try:
                    await cliente.disconnect()
                    print("Azure IoT: conexión cerrada.")

                except Exception as error:
                    print("Azure IoT: error al desconectar:", error)

    # Detener el envío y esperar a que termine el hilo de comunicación.
    def cerrar(self):

        if self.hilo is None:
            return

        if self.hilo.is_alive():
            # Enviar una señal a la cola para que el hilo termine su ciclo.
            self.cola.put(self.detener)

            self.hilo.join(timeout=5)

        self.hilo = None
