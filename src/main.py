from .database import Database
import socket


UDP_IP = ""
UDP_PORT = 8000
MESSAGE = "lol"

database = Database("./sqlite3.db")

print("UDP target IP:", UDP_IP)
print("UDP target port:", UDP_PORT)
print("message:", MESSAGE)


def main():
    print("Welcome")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock.sendto(bytes(MESSAGE, "utf-8"), (UDP_IP, UDP_PORT))


if __name__ == "__main__":
    main()
