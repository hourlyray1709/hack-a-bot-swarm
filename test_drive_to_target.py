import socket
import time
from control.coordinator import SwarmCoordinator, BotState

BOT_IP   = "192.168.0.102"
BOT_PORT = 5001
sock     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(cmd):
    payload = f"L{cmd.left} R{cmd.right}\n".encode()
    sock.sendto(payload, (BOT_IP, BOT_PORT))
    print(f"L={cmd.left:4d}  R={cmd.right:4d}")

def stop():
    sock.sendto(b"L0 R0\n", (BOT_IP, BOT_PORT))
    print("--- STOP ---")
    time.sleep(1)

def drive_to_target(bot, target, label, duration=10.0):
    print(f"\n{label}")
    start = time.time()#

    while time.time() - start < duration:
        cmd = SwarmCoordinator._drive_to(bot, target)
        send(cmd)
        time.sleep(0.067)
    stop()

# bot starts at centre of arena facing right
bot = BotState(id=1, x=0, y=0, heading=0.0)

# diagonal up-right
x = bot.x 
y = bot.y
drive_to_target(bot, (x+1, y-1), "Diagonal up-right")

# # diagonal down-right  
# x = bot.x 
# y = bot.y
# drive_to_target(bot, (x+1, y+1), "Diagonal down-right")

# # diagonal up-left
# x = bot.x 
# y = bot.y
# drive_to_target(bot, (x-1, y-1), "Diagonal up-left")

# # diagonal down-left
# x = bot.x 
# y = bot.y
# drive_to_target(bot, (x-1, y+1), "Diagonal down-left")


# # straight ahead — target is directly to the right
# drive_to_target(bot, (1.4, 10), "Straight ahead")

# # target above — bot needs to turn left
# drive_to_target(bot, (0.8, 0.1), "Turn left (target above)")

# # target below — bot needs to turn right
# drive_to_target(bot, (0.8, 0.9), "Turn right (target below)")

# # target behind — bot needs to reverse/spin
# drive_to_target(bot, (0.2, 0.5), "Behind (should spin)")

print("\nAll done!")
sock.close()