import socket
import time

BOT_IP   = "192.168.1.105"  # your bot's IP
BOT_PORT = 5001              # port for bot 1

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Forward...")
sock.sendto(b"L150 R150\n", (BOT_IP, BOT_PORT))
time.sleep(2)

print("Stop...")
sock.sendto(b"L0 R0\n", (BOT_IP, BOT_PORT))
time.sleep(1)

print("Turn right...")
sock.sendto(b"L150 R60\n", (BOT_IP, BOT_PORT))
time.sleep(2)

print("Stop...")
sock.sendto(b"L0 R0\n", (BOT_IP, BOT_PORT))

sock.close()
print("Done!")