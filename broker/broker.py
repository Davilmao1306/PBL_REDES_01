import socket
import threading
import time

from shared.protocol import parse_message, build_message, recv_tcp_message, send_tcp_message

UDP_HOST = "0.0.0.0"
UDP_PORT = 5001

TCP_HOST = "0.0.0.0"
TCP_PORT = 5002

# Estruturas em memória
sensors = {}
actuators = {}

# Lock para evitar problemas de concorrência
data_lock = threading.Lock()


def register_sensor(sensor_id, sensor_type, addr):
    with data_lock:
        sensors[sensor_id] = {
            "type": sensor_type,
            "value": None,
            "last_update": None,
            "status": "ONLINE",
            "addr": addr,
        }
    print(f"[BROKER] Sensor registrado: {sensor_id} ({sensor_type})")


def register_actuator(actuator_id, actuator_type, conn, addr):
    with data_lock:
        actuators[actuator_id] = {
            "type": actuator_type,
            "state": "OFF",
            "status": "ONLINE",
            "conn": conn,
            "lock": threading.Lock(),
            "addr": addr,
        }
    print(f"[BROKER] Atuador registrado: {actuator_id} ({actuator_type})")


def update_sensor_data(sensor_id, sensor_type, value):
    with data_lock:
        if sensor_id not in sensors:
            sensors[sensor_id] = {
                "type": sensor_type,
                "value": value,
                "last_update": time.time(),
                "status": "ONLINE",
                "addr": None,
            }
        else:
            sensors[sensor_id]["type"] = sensor_type
            sensors[sensor_id]["value"] = value
            sensors[sensor_id]["last_update"] = time.time()
            sensors[sensor_id]["status"] = "ONLINE"

    print(f"[BROKER] Telemetria: {sensor_id} -> {sensor_type} = {value}")


def list_sensors():
    with data_lock:
        if not sensors:
            return "SENSORS|NONE"

        items = []
        for sensor_id, info in sensors.items():
            items.append(
                f"{sensor_id},{info['type']},{info['value']},{info['status']}"
            )
        return "SENSORS|" + ";".join(items)


def list_actuators():
    with data_lock:
        if not actuators:
            return "ACTUATORS|NONE"

        items = []
        for actuator_id, info in actuators.items():
            items.append(
                f"{actuator_id},{info['type']},{info['state']},{info['status']}"
            )
        return "ACTUATORS|" + ";".join(items)


def get_sensor(sensor_id):
    with data_lock:
        if sensor_id not in sensors:
            return build_message("ERROR", "sensor_nao_encontrado")

        info = sensors[sensor_id]
        return build_message(
            "SENSOR",
            sensor_id,
            info["type"],
            info["value"],
            info["status"]
        )


def get_actuator(actuator_id):
    with data_lock:
        if actuator_id not in actuators:
            return build_message("ERROR", "atuador_nao_encontrado")

        info = actuators[actuator_id]
        return build_message(
            "ACTUATOR",
            actuator_id,
            info["type"],
            info["state"],
            info["status"]
        )


def send_command_to_actuator(actuator_id, command):
    command = command.upper()

    if command not in ("ON", "OFF", "DESLIGAR", "ACIONAR_ALARME"):
        return build_message("ERROR", "comando_nao_suportado")

    with data_lock:
        if actuator_id not in actuators:
            return build_message("ERROR", "atuador_nao_encontrado")

        actuator = actuators[actuator_id]
        conn = actuator["conn"]
        actuator_lock = actuator["lock"]

    try:
        with actuator_lock:
            send_tcp_message(conn, "EXECUTE", command)
            response = recv_tcp_message(conn)
        parts = parse_message(response)

        if len(parts) >= 2 and parts[0] == "OK":
            new_state = parts[1]
            with data_lock:
                actuators[actuator_id]["state"] = new_state
            return build_message("COMMAND_OK", actuator_id, new_state)

        return build_message("ERROR", "falha_execucao")

    except Exception as e:
        print(f"[BROKER] Erro ao enviar comando ao atuador {actuator_id}: {e}")
        with data_lock:
            actuators[actuator_id]["status"] = "OFFLINE"
        return build_message("ERROR", "atuador_offline")


def udp_server():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((UDP_HOST, UDP_PORT))

    print(f"[UDP] Broker escutando telemetria em {UDP_HOST}:{UDP_PORT}")

    while True:
        data, addr = udp_sock.recvfrom(1024)
        message = data.decode().strip()
        print(f"[UDP] Recebido de {addr}: {message}")

        parts = parse_message(message)

        if len(parts) == 4 and parts[0] == "SENSOR_DATA":
            _, sensor_id, sensor_type, value = parts
            update_sensor_data(sensor_id, sensor_type, value)
        else:
            print("[UDP] Mensagem inválida")


def handle_actuator_connection(conn, addr, actuator_id):
    try:
        while True:
            time.sleep(1)
            # Mantém a conexão viva enquanto o atuador estiver conectado
            # Os comandos serão enviados a partir de outras threads
            if conn.fileno() == -1:
                break
    except Exception:
        pass
    finally:
        with data_lock:
            if actuator_id in actuators:
                actuators[actuator_id]["status"] = "OFFLINE"
        conn.close()
        print(f"[TCP] Atuador desconectado: {actuator_id}")


def handle_tcp_client(conn, addr):
    print(f"[TCP] Nova conexão: {addr}")

    actuator_id_registered = None

    try:
        first_message = recv_tcp_message(conn)
        if not first_message:
            conn.close()
            return

        print(f"[TCP] Primeira mensagem de {addr}: {first_message}")

        parts = parse_message(first_message)

        # Registro de sensor
        if len(parts) == 3 and parts[0] == "REGISTER_SENSOR":
            _, sensor_id, sensor_type = parts
            register_sensor(sensor_id, sensor_type, addr)
            send_tcp_message(conn, "REGISTERED", sensor_id)
            conn.close()
            return

        # Registro de atuador
        if len(parts) == 3 and parts[0] == "REGISTER_ACTUATOR":
            _, actuator_id, actuator_type = parts
            register_actuator(actuator_id, actuator_type, conn, addr)
            actuator_id_registered = actuator_id
            send_tcp_message(conn, "REGISTERED", actuator_id)

            handle_actuator_connection(conn, addr, actuator_id)
            return

        # Cliente comum
        while True:
            message = first_message if first_message else None
            if message is None:
                message = recv_tcp_message(conn)
                if not message:
                    break

            print(f"[TCP] Cliente {addr} enviou: {message}")
            parts = parse_message(message)

            response = build_message("ERROR", "comando_invalido")

            if len(parts) == 1 and parts[0] == "LIST_SENSORS":
                response = list_sensors()

            elif len(parts) == 1 and parts[0] == "LIST_ACTUATORS":
                response = list_actuators()

            elif len(parts) == 2 and parts[0] == "GET_SENSOR":
                response = get_sensor(parts[1])

            elif len(parts) == 2 and parts[0] == "GET_ACTUATOR":
                response = get_actuator(parts[1])

            elif len(parts) == 3 and parts[0] == "COMMAND":
                _, actuator_id, command = parts
                response = send_command_to_actuator(actuator_id, command)

            send_tcp_message(conn, response)

            first_message = None

    except Exception as e:
        print(f"[TCP] Erro na conexão {addr}: {e}")

    finally:
        if actuator_id_registered:
            with data_lock:
                if actuator_id_registered in actuators:
                    actuators[actuator_id_registered]["status"] = "OFFLINE"

        try:
            conn.close()
        except Exception:
            pass

        print(f"[TCP] Conexão encerrada: {addr}")


def tcp_server():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind((TCP_HOST, TCP_PORT))
    tcp_sock.listen(10)

    print(f"[TCP] Broker escutando em {TCP_HOST}:{TCP_PORT}")

    while True:
        conn, addr = tcp_sock.accept()
        thread = threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True)
        thread.start()


def main():
    print("[SYSTEM] Iniciando broker...")

    udp_thread = threading.Thread(target=udp_server, daemon=True)
    tcp_thread = threading.Thread(target=tcp_server, daemon=True)

    udp_thread.start()
    tcp_thread.start()

    print("[SYSTEM] Broker iniciado com sucesso.")
    print(f"[SYSTEM] UDP telemetria: {UDP_PORT}")
    print(f"[SYSTEM] TCP controle: {TCP_PORT}")

    udp_thread.join()
    tcp_thread.join()


if __name__ == "__main__":
    main()
