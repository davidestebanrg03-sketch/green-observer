
import os
import asyncio
import json

from integracion_azure.iot.device.aio import IoTHubDeviceClient


async def main():
    cadena = os.getenv("AZURE_IOT_DEVICE_CONNECTION_STRING")

    print("Variable encontrada:", cadena is not None)
    print("Longitud:", len(cadena) if cadena else 0)

    if not cadena:
        print("No se encontró la cadena de conexión.")
        return

    cliente = IoTHubDeviceClient.create_from_connection_string(
        cadena
    )

    try:
        print("Conectando con Azure...")

        await cliente.connect()

        print("¡Conexión establecida!")

        datos = {
            "temperatura": 28.5,
            "humedad_suelo": 42.0,
            "luminosidad": 750,
            "riego": False,
            "ventilacion": True
        }

        mensaje = json.dumps(datos)

        await cliente.send_message(mensaje)

        print("Datos enviados correctamente:")
        print(mensaje)

    except Exception as error:
        print("Error durante la comunicación:", error)

    finally:
        await cliente.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
