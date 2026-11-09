
import os
import json
import asyncio
import queue
import threading
import time

from azure.iot.device.aio import IoTHubDeviceClient


class ClienteIoT:

    def __init__(self, sesion, intervalo=15):

        self.sesion = sesion
        self.intervalo = intervalo

        self.cola = queue.Queue()
        self.detener = object()

        self.ultimo_envio = 0

        self.hilo = None

    def iniciar(self):

        if self.hilo is not None:
            return

        self.hilo = threading.Thread(
            target=self._ejecutar,
            daemon=True
        )

        self.hilo.start()

    def observar(self, evento):

        if evento != "actualizacion":
            return

        ahora = time.monotonic()

        if ahora - self.ultimo_envio < self.intervalo:
            return

        self.ultimo_envio = ahora

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

        asyncio.run(self._procesar())

    async def _procesar(self):

        cadena = os.getenv(
            "AZURE_IOT_DEVICE_CONNECTION_STRING"
        )

        if not cadena:
            print("Azure IoT: no se encontró la cadena de conexión.")
            return

        cliente = IoTHubDeviceClient.create_from_connection_string(
            cadena
        )

        conectado = False

        try:

            print("Azure IoT: conectando...")

            await cliente.connect()

            conectado = True

            print("Azure IoT: conexión establecida.")

            while True:

                datos = await asyncio.to_thread(
                    self.cola.get
                )

                if datos is self.detener:
                    break

                mensaje = json.dumps(datos)

                try:

                    await cliente.send_message(mensaje)

                    print("Azure IoT: telemetría enviada.")

                except Exception as error:

                    print("Azure IoT: error al enviar:", error)

        except Exception as error:

            print("Azure IoT: error de conexión:", error)

        finally:

            if conectado:

                try:
                    await cliente.disconnect()
                    print("Azure IoT: conexión cerrada.")

                except Exception as error:
                    print("Azure IoT: error al desconectar:", error)

    def cerrar(self):

        if self.hilo is None:
            return

        if self.hilo.is_alive():

            self.cola.put(self.detener)

            self.hilo.join(timeout=5)

        self.hilo = None
