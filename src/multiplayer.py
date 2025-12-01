import socket
import threading
from edit_me import SERVER_HOST, SERVER_PORT, handshake, take_turn
from datetime import datetime

class Packet:
    @staticmethod
    def get_time():
        return datetime.now().strftime("%A %-d %B %Y %H:%M:%S")

    def __init__(self, header: str, data: str, time=get_time()):
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
        if message:
            print(message.decode())

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET = internet protocol
    sock.connect((SERVER_HOST, SERVER_PORT))
    sock.send(Packet("HANDSHAKE", handshake()).get_bytes())
    while True:
        packet = sock.recv(1024)
        if packet:
            print(packet)
    sock.close()

if __name__ == "__main__":
    main()

