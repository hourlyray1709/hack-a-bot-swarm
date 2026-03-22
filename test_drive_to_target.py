import socket
import time
import math
from dataclasses import dataclass

# ---------- config ----------
BOT_IP = "192.168.0.102"
BOT_PORT = 5001
DT = 0.067

ARENA_WIDTH_M = 1.748
ARENA_HEIGHT_M = 0.906
ARRIVE_THRESH_M = 0.06

MAX_SPEED = 220
MIN_SPEED = 40
KP_DIST = 1.0
KP_SIDE = 180.0   # steering from lateral error (tune 120..260)
# ---------------------------

@dataclass
class BotCommand:
    left: int
    right: int

@dataclass
class BotState:
    x: float
    y: float

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def clamp_target(x, y):
    x = max(0.05, min(ARENA_WIDTH_M - 0.05, x))
    y = max(0.05, min(ARENA_HEIGHT_M - 0.05, y))
    return x, y

def sat(v, lo, hi):
    return max(lo, min(hi, v))

def deadband(v, d):
    return 0 if abs(v) < d else v

def send_cmd(cmd: BotCommand):
    payload = f"L{cmd.left} R{cmd.right}\n".encode()
    sock.sendto(payload, (BOT_IP, BOT_PORT))
    print(payload.decode().strip())

def stop():
    sock.sendto(b"L0 R0\n", (BOT_IP, BOT_PORT))
    print("L0 R0")

def get_latest_bot_state() -> BotState:
    # TODO: replace with real tracker each cycle
    # must return UPDATED x,y
    return BotState(x=0.8, y=0.5)

def drive_no_heading(bot: BotState, target):
    tx, ty = clamp_target(*target)
    dx, dy = tx - bot.x, ty - bot.y
    dist = math.hypot(dx, dy)

    if dist < ARRIVE_THRESH_M:
        return BotCommand(0, 0), dist

    # forward speed from distance
    fwd = int(sat(KP_DIST * dist * MAX_SPEED, MIN_SPEED, MAX_SPEED))

    # lateral steering using world-frame y error
    steer = int(sat(KP_SIDE * dy, -MAX_SPEED, MAX_SPEED))

    left = int(sat(fwd - steer, -MAX_SPEED, MAX_SPEED))
    right = int(sat(fwd + steer, -MAX_SPEED, MAX_SPEED))

    left = deadband(left, MIN_SPEED)
    right = deadband(right, MIN_SPEED)
    return BotCommand(left, right), dist

def run_to_target(target):
    try:
        while True:
            bot = get_latest_bot_state()
            cmd, dist = drive_no_heading(bot, target)
            send_cmd(cmd)

            if dist < ARRIVE_THRESH_M:
                break

            time.sleep(DT)
    finally:
        stop()
        sock.close()

if __name__ == "__main__":
    run_to_target((1.4, 0))  # diagonal target