import os
from azure.eventhub import EventHubConsumerClient


def recibir_mensaje(partition_context, event):

    if event is None:
        return

    print("\n" + "=" * 50)
    print("Mensaje recibido desde Azure IoT Hub")
    print("Partición:", partition_context.partition_id)

    print("Contenido:")

    print(event.body_as_str(encoding="UTF-8"))

    print("=" * 50)

    partition_context.update_checkpoint(event)


def main():

    cadena = os.getenv("AZURE_EVENTHUB_CONNECTION_STRING")

    if not cadena:
        print("No se encontró la cadena de conexión de Event Hubs.")
        return

    cliente = EventHubConsumerClient.from_connection_string(
        conn_str=cadena,
        consumer_group="$Default"
    )

    try:

        print("Conectando con el endpoint de Azure...")
        print("Esperando mensajes de telemetría...")
        print("Presiona Ctrl + C para detener la lectura.")

        with cliente:

            cliente.receive(
                on_event=recibir_mensaje,
                starting_position="@latest"
            )

    except KeyboardInterrupt:

        print("\nLectura de telemetría detenida.")

    except Exception as error:

        print("Error al recibir mensajes:", error)


if __name__ == "__main__":
    main()