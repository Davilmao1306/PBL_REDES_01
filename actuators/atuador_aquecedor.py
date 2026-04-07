import socket
import os

from shared.protocol import parse_message, recv_tcp_message, send_tcp_message

BROKER_HOST = os.getenv("BROKER_HOST", "broker")
BROKER_TCP_PORT = 5002

ACTUATOR_ID = "atuador_aquecedor"
ACTUATOR_TYPE = "aquecedor"


def main():
    state = "OFF"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((BROKER_HOST, BROKER_TCP_PORT))

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

                if command in ("ON", "OFF", "DESLIGAR"):
                    if command == "DESLIGAR":
                        command = "OFF"
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
