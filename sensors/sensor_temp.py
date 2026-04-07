import socket
import time
import random
import os

from shared.protocol import recv_tcp_message, send_tcp_message

BROKER_HOST = os.getenv("BROKER_HOST", "broker")
BROKER_TCP_PORT = 5002
BROKER_UDP_PORT = 5001
SOCKET_TIMEOUT = 5.0

SENSOR_ID = "sensor_temp"
SENSOR_TYPE = "temperatura"


def register_sensor():
    try:
        tcp_sock = socket.create_connection(
            (BROKER_HOST, BROKER_TCP_PORT), timeout=SOCKET_TIMEOUT
        )

        send_tcp_message(tcp_sock, "REGISTER_SENSOR", SENSOR_ID, SENSOR_TYPE)

        response = recv_tcp_message(tcp_sock)
        print(f"[{SENSOR_ID}] Resposta do broker: {response}")

        tcp_sock.close()
    except Exception as e:
        print(f"[{SENSOR_ID}] Erro ao registrar sensor: {e}")


def send_telemetry():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    temperatura = 30.0

    while True:
        variacao = random.uniform(-1.5, 2.0)
        temperatura += variacao

        if temperatura < 20.0:
            temperatura = 20.0
        if temperatura > 120.0:
            temperatura = 120.0

        temperatura = round(temperatura, 1)

        message = f"SENSOR_DATA|{SENSOR_ID}|{SENSOR_TYPE}|{temperatura}"
        udp_sock.sendto(message.encode(), (BROKER_HOST, BROKER_UDP_PORT))

        print(f"[{SENSOR_ID}] Telemetria enviada: {message}")
        # Envio rapido e continuo: em laboratorio usamos 0.5s para manter
        # a saida legivel, mas o caminho UDP aceita taxas maiores.
        time.sleep(0.5)


if __name__ == "__main__":
    print(f"[{SENSOR_ID}] Iniciando sensor de temperatura...")
    register_sensor()
    send_telemetry()
