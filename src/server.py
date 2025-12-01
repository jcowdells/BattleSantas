from common import Game, Direction, SantaID
from edit_me import handshake, take_turn
from threading import Thread, Event
import socket
import time
from multiplayer import Packet

class Connection:
    def __init__(self, connection, address, running):
        self.__connection = connection
        self.__address = address
        self.__running_event = running
        self.__name = ""
        self.__direction = None
        self.__thread  = Thread(target=self.__thread_target)
        self.__thread.start()

    def __thread_target(self):
        while self.__running_event.is_set():
            try:
                data = self.__connection.recv(1024)
                packet = Packet.from_bytes(data)
                print(packet)
                if packet.header == "DIRECTION":
                    self.__direction = getattr(Direction, packet.data)
                elif packet.header == "HANDSHAKE":
                    self.__name = packet.data
            except Exception as e:
                print(f"Exception: {e}")
                packet = Packet("EXCEPTION", f"An error occured. Your connection has been terminated. error={type(e)}".encode())
                try:
                    self.__connection.send(packet.get_bytes())
                    self.__connection.shutdown(socket.SHUT_RDWR)
                    self.__connection.close()
                except OSError:
                    pass
                break

    def get_name(self):
        return self.__name

    def get_direction(self):
        direction = self.__direction
        self.__direction = None
        return direction

    def get_address(self):
        return f"{self.__address[0]}:{self.__address[1]}"

class Server(Game):
    def __init__(self):
        super().__init__()
        self.__accepting_event = Event()
        self.__running_event = Event()
        self.__await_event = Event()
        self.__accepter = Thread(target=self.__accept_target)
        self.__thread = Thread(target=self.__thread_target)
        self.__connections = list()
        self.__direction_dict = dict()
        self.__connection_names = dict()
        self.__host = "0.0.0.0"
        self.__port = 33279

    def __accept_target(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET = internet protocol
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.__host, self.__port))
        sock.listen(64)
        while self.__running_event.is_set():
            try:
                conn, addr = sock.accept()
                if self.__accepting_event.is_set():
                    self.__connections.append(Connection(conn, addr, self.__running_event))
            except Exception as e:
                print(e)

    def __thread_target(self):
        self.__direction_dict = dict()
        while self.__running_event.is_set():
            try:
                
                for connection in self.__connections:
                    direction = connection.get_direction()
                    address = connection.get_address()
                    self.__connection_names[address] = connection.get_name()
                    if self.__await_event.is_set():
                        if direction is not None:
                            self.__direction_dict[address] = direction
                        if len(self.__direction_dict) == len(self.__connections):
                            self.__await_event.clear()
            except Exception as e:
                print(e)

    def start_server(self):
        self.__running_event.set()
        self.__accepting_event.set()
        self.__await_event.clear()
        self.__accepter.start()
        self.__thread.start()

    def lock_server(self):
        self.__accepting_event.clear()

    def stop_server(self):
        self.__running_event.clear()
        self.__thread.join()
        self.__accepter.join()

    def get_server_ip(self) -> str:
        return f"{self.__host}:{self.__port}"

    def get_santa_ids(self) -> list[SantaID]:
        santa_ids = list()
        for address, name in self.__connection_names.items():
            santa_ids.append(SantaID(address, name))
        return santa_ids

    def request_santas(self) -> None:
        self.__await_event.set()

    def received_santas(self) -> bool:
        return not self.__await_event.is_set()

    def get_santas(self) -> list[tuple[str, Direction]]:
        items = self.__direction_dict.items()
        self.__direction_dict = dict()
        return items

def main():
    game = Server()
    game.run()

if __name__ == "__main__":
    main()
