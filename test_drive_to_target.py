import socket
import time
import math
from control.coordinator import SwarmCoordinator, BotState

BOT_IP   = "192.168.0.102"
BOT_PORT = 5001
sock     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(cmd):
    payload = f"L{cmd.left} R{cmd.right}\n".encode()
    sock.sendto(payload, (BOT_IP, BOT_PORT))
    print(f"L={cmd.left:4d}  R={cmd.right:4d}")

# pretend the bot is at 0.3m, 0.5m facing right
# and the target is 1.0m, 0.5m (straight ahead)
bot    = BotState(id=1, x=0.3, y=0.5, heading=0.0)
target = (1.0, 0.5)

print("Driving to target for 3 seconds...")
start = time.time()
while time.time() - start < 3.0:
    cmd = SwarmCoordinator._drive_to(bot, target)
    send(cmd)
    time.sleep(0.067)   # 15hz

print("Stop")
sock.sendto(b"L0 R0\n", (BOT_IP, BOT_PORT))
sock.close()