"""Protocolo textual simples usado pelos componentes do projeto.

O projeto nao usa MQTT, AMQP, Kafka ou qualquer framework de mensageria.
As mensagens trafegam diretamente sobre sockets TCP/UDP, que sao a forma
nativa de comunicacao da arquitetura da Internet.
"""

ENCODING = "utf-8"
SEPARATOR = "|"
END_OF_MESSAGE = "\n"


def parse_message(message: str):
    """Divide uma mensagem textual no formato COMANDO|campo1|campo2."""
    return message.strip().split(SEPARATOR)


def build_message(*parts):
    """Monta uma mensagem sem o terminador de linha."""
    return SEPARATOR.join(str(part) for part in parts)


def send_tcp_message(conn, *parts):
    """Envia uma mensagem TCP delimitada por linha.

    TCP e um fluxo de bytes: uma chamada recv() nao equivale a uma mensagem.
    O terminador de linha cria um enquadramento simples para o receptor saber
    onde a mensagem termina.
    """
    frame = build_message(*parts) + END_OF_MESSAGE
    conn.sendall(frame.encode(ENCODING))


def recv_tcp_message(conn, max_bytes=4096):
    """Recebe uma unica mensagem TCP delimitada por linha."""
    data = bytearray()

    while len(data) < max_bytes:
        chunk = conn.recv(1)
        if not chunk:
            break
        if chunk == END_OF_MESSAGE.encode(ENCODING):
            break
        data.extend(chunk)

    return data.decode(ENCODING).strip()
