import json
import socket
from edit_me import SERVER_HOST, SERVER_PORT, handshake, take_turn
from datetime import datetime

class Packet:
    @staticmethod
    def get_time():
        return datetime.now().strftime("%A %d %B %Y %H:%M:%S")

    def __init__(self, header: str, data: str, time=None):
        if time is None:
            time = Packet.get_time()
        self.__time = time
        self.header = header
        self.data = data

    def __str__(self):
        return f"{self.__time}\n{self.header}\n{self.data}"

    @classmethod
    def from_bytes(cls, bytes):
        packet_str = bytes.decode()
        packet_lines = packet_str.split("\n")
        if len(packet_lines) != 3:
            raise ValueError("Bad packet.")
        return cls(packet_lines[1], packet_lines[2], packet_lines[0])

    def get_bytes(self):
        return str(self).encode()

def recv_server(conn):
    while True:
        message = conn.recv(1024)
        packet = Packet.from_bytes(message)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET = internet protocol
    sock.connect((SERVER_HOST, SERVER_PORT))
    sock.send(Packet("HANDSHAKE", handshake()).get_bytes())
    while True:
        message = sock.recv(1024)
        if not message:
            continue
        packet = Packet.from_bytes(message)
        if packet.header == "STOP":
            break
        if packet.header == "PLEASE SEND ME YOUR DIRECTION":
            game_state = json.loads(packet.data)
            direction = take_turn(game_state)
            sock.send(Packet(
                "DIRECTION",
                direction.name
            ).get_bytes())

    sock.close()

if __name__ == "__main__":
    main()

