import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.protocol import recv_tcp_message, send_tcp_message


def wait_for_broker(timeout=5.0):
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            probe = socket.create_connection(("127.0.0.1", 5002), timeout=0.2)
            probe.close()
            return
        except OSError:
            time.sleep(0.1)

    raise RuntimeError("broker nao iniciou dentro do tempo esperado")


def simulated_actuator(ready_event):
    sock = socket.create_connection(("127.0.0.1", 5002), timeout=2)
    send_tcp_message(sock, "REGISTER_ACTUATOR", "atuador_teste", "rele")
    assert recv_tcp_message(sock) == "REGISTERED|atuador_teste"
    ready_event.set()

    command = recv_tcp_message(sock)
    assert command == "EXECUTE|ON"
    send_tcp_message(sock, "OK", "ON")
    sock.close()


def main():
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    broker = subprocess.Popen(
        [sys.executable, "-B", "-m", "broker.broker"],
        cwd=".",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_for_broker()

        ready_event = threading.Event()
        actuator_thread = threading.Thread(
            target=simulated_actuator, args=(ready_event,), daemon=True
        )
        actuator_thread.start()
        assert ready_event.wait(2), "atuador de teste nao registrou"

        sensor_sock = socket.create_connection(("127.0.0.1", 5002), timeout=2)
        send_tcp_message(sensor_sock, "REGISTER_SENSOR", "sensor_teste", "temperatura")
        assert recv_tcp_message(sensor_sock) == "REGISTERED|sensor_teste"
        sensor_sock.close()

        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.sendto(
            b"SENSOR_DATA|sensor_teste|temperatura|42.5", ("127.0.0.1", 5001)
        )
        udp_sock.close()
        time.sleep(0.2)

        client = socket.create_connection(("127.0.0.1", 5002), timeout=2)
        send_tcp_message(client, "GET_SENSOR|sensor_teste")
        assert (
            recv_tcp_message(client)
            == "SENSOR|sensor_teste|temperatura|42.5|ONLINE"
        )
        client.close()

        client = socket.create_connection(("127.0.0.1", 5002), timeout=2)
        send_tcp_message(client, "COMMAND|atuador_teste|ON")
        assert recv_tcp_message(client) == "COMMAND_OK|atuador_teste|ON"
        client.close()

        print("integration ok")
    finally:
        broker.terminate()
        try:
            broker.wait(timeout=2)
        except subprocess.TimeoutExpired:
            broker.kill()


if __name__ == "__main__":
    main()
