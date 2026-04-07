import socket
import os

from shared.protocol import parse_message, recv_tcp_message, send_tcp_message

BROKER_HOST = os.getenv("BROKER_HOST", "broker")
BROKER_TCP_PORT = 5002
SOCKET_TIMEOUT = 5.0

ACTUATOR_ID = "atuador_exaustor"
ACTUATOR_TYPE = "exaustor"


def main():
    state = "OFF"

    sock = socket.create_connection((BROKER_HOST, BROKER_TCP_PORT), timeout=SOCKET_TIMEOUT)
    sock.settimeout(None)

    send_tcp_message(sock, "REGISTER_ACTUATOR", ACTUATOR_ID, ACTUATOR_TYPE)

    response = recv_tcp_message(sock)
    print(f"[{ACTUATOR_ID}] Resposta do broker: {response}")
    print(f"[{ACTUATOR_ID}] Estado inicial: {state}")

    try:
        while True:
            message = recv_tcp_message(sock)
            if not message:
                print(f"[{ACTUATOR_ID}] Conexão encerrada pelo broker.")
                break

            print(f"[{ACTUATOR_ID}] Comando recebido: {message}")

            parts = parse_message(message)

            if len(parts) == 2 and parts[0] == "EXECUTE":
                command = parts[1]

                if command in ("ON", "OFF", "ACIONAR_ALARME"):
                    if command == "ACIONAR_ALARME":
                        command = "ON"
                    state = command
                    print(f"[{ACTUATOR_ID}] Novo estado: {state}")
                    send_tcp_message(sock, "OK", state)
                else:
                    send_tcp_message(sock, "ERROR", "comando_invalido")
            else:
                send_tcp_message(sock, "ERROR", "mensagem_invalida")

    except Exception as e:
        print(f"[{ACTUATOR_ID}] Erro: {e}")

    finally:
        sock.close()
        print(f"[{ACTUATOR_ID}] Encerrado.")


if __name__ == "__main__":
    main()
