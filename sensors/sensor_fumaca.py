import socket
import time
import random
import os

from shared.protocol import recv_tcp_message, send_tcp_message

BROKER_HOST = os.getenv("BROKER_HOST", "broker")
BROKER_TCP_PORT = 5002
BROKER_UDP_PORT = 5001
SOCKET_TIMEOUT = 5.0

SENSOR_ID = "sensor_fumaca"
SENSOR_TYPE = "fumaca"


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

    fumaca = 5.0

    while True:
        variacao = random.uniform(-0.8, 1.8)
        fumaca += variacao

        if fumaca < 0.0:
            fumaca = 0.0
        if fumaca > 100.0:
            fumaca = 100.0

        fumaca = round(fumaca, 1)

        message = f"SENSOR_DATA|{SENSOR_ID}|{SENSOR_TYPE}|{fumaca}"
        udp_sock.sendto(message.encode(), (BROKER_HOST, BROKER_UDP_PORT))

        print(f"[{SENSOR_ID}] Telemetria enviada: {message}")
        # Telemetria continua via UDP. O intervalo curto evidencia o fluxo
        # em tempo real sem inundar o terminal da apresentacao.
        time.sleep(0.7)


if __name__ == "__main__":
    print(f"[{SENSOR_ID}] Iniciando sensor de fumaça...")
    register_sensor()
    send_telemetry()
