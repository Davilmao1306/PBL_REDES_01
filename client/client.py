import socket
import time
import os

from shared.protocol import recv_tcp_message, send_tcp_message

BROKER_HOST = os.getenv("BROKER_HOST", "broker")
BROKER_TCP_PORT = 5002


def send_message(message: str) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((BROKER_HOST, BROKER_TCP_PORT))

    send_tcp_message(sock, message)
    response = recv_tcp_message(sock)

    sock.close()
    return response


def monitor_sensor(sensor_id: str, interval: float = 1.0):
    print("\nPressione CTRL+C para parar o monitoramento.")

    try:
        while True:
            response = send_message(f"GET_SENSOR|{sensor_id}")
            print(f"[TEMPO REAL] {response}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado.")


def menu():
    while True:
        print("\n=== CLIENTE IoT FORNO ===")
        print("1 - Listar sensores")
        print("2 - Listar atuadores")
        print("3 - Consultar sensor")
        print("4 - Consultar atuador")
        print("5 - Enviar comando para atuador")
        print("6 - Monitorar sensor em tempo real")
        print("0 - Sair")

        option = input("Escolha uma opção: ").strip()

        if option == "1":
            response = send_message("LIST_SENSORS")
            print(f"\n[RESPOSTA] {response}")

        elif option == "2":
            response = send_message("LIST_ACTUATORS")
            print(f"\n[RESPOSTA] {response}")

        elif option == "3":
            sensor_id = input("Digite o ID do sensor: ").strip()
            response = send_message(f"GET_SENSOR|{sensor_id}")
            print(f"\n[RESPOSTA] {response}")

        elif option == "4":
            actuator_id = input("Digite o ID do atuador: ").strip()
            response = send_message(f"GET_ACTUATOR|{actuator_id}")
            print(f"\n[RESPOSTA] {response}")

        elif option == "5":
            actuator_id = input("Digite o ID do atuador: ").strip()
            command = input("Digite o comando (ON/OFF/DESLIGAR/ACIONAR_ALARME): ").strip().upper()
            response = send_message(f"COMMAND|{actuator_id}|{command}")
            print(f"\n[RESPOSTA] {response}")

        elif option == "6":
            sensor_id = input("Digite o ID do sensor: ").strip()
            monitor_sensor(sensor_id)

        elif option == "0":
            print("Encerrando cliente...")
            break

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()
