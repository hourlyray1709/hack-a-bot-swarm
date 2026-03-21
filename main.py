# the file we run when we connect to the camera 
import cv2
from vision.process_markers import get_data 
from threading import Thread 
from time import sleep 
import math
from control.coordinator import SwarmCoordinator, BotState, BotCommand

import socket

# ── Bot IP addresses ───────────────────────────────────────────────────────────
# Update these once each bot connects and prints its IP in Serial Monitor
BOT_IPS = {
    1: ("192.168.1.101", 5001),
    2: ("192.168.1.102", 5002),
    3: ("192.168.1.103", 5003),
}


# ── these must match your actual camera + arena setup ─────────────────────────
#1080p camera
IMAGE_WIDTH_PX  = 1920   # your camera resolution width
IMAGE_HEIGHT_PX = 1080    # your camera resolution height
ARENA_WIDTH_M   = 1.748    # real arena width in metres
ARENA_HEIGHT_M  =  0.906 # real arena height in metres

# create one UDP socket — reused for all bots
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_command(bot_id, cmd):
    if bot_id not in BOT_IPS:
        return
    ip, port = BOT_IPS[bot_id]
    payload  = f"L{cmd.left} R{cmd.right}\n".encode()
    try:
        udp_sock.sendto(payload, (ip, port))
    except OSError as e:
        print(f"UDP error bot {bot_id}: {e}")

def corners_to_botstates(corner_data):
    """
    Converts raw corner list into a dict of BotState objects.
    corner_data is a list of 3 tuples, each with 4 (x,y) pixel coords.
    Returns {1: BotState, 2: BotState, 3: BotState}
    """
    bots = {}

    for i, corners in enumerate(corner_data):
        bot_id = i + 1   # list index 0 = bot 1, index 1 = bot 2 etc.

        # unpack the 4 corners
        try:
            (x1,y1), (x2,y2), (x3,y3), (x4,y4) = corners[0]
        except (ValueError, IndexError):
            continue 
        # centre = average of all 4 corners
        cx = (x1 + x2 + x3 + x4) / 4
        cy = (y1 + y2 + y3 + y4) / 4

        # heading = direction from corner 0 to corner 1
        heading = math.atan2(y2 - y1, x2 - x1)

        # convert pixels to metres
        mx = (cx / IMAGE_WIDTH_PX)  * ARENA_WIDTH_M
        my = (cy / IMAGE_HEIGHT_PX) * ARENA_HEIGHT_M

        bots[bot_id] = BotState(id=bot_id, x=mx, y=my, heading=heading)

    return bots

class CornerData: 
    def __init__(self): 
        self.data = None 


if __name__ == "__main__":
    corner_data = CornerData()
    coordinator = SwarmCoordinator(bot_ids=[1, 2, 3])
    thread1 = Thread(target=get_data, args=(corner_data,))
    thread1.start()

    while True:
        if corner_data.data is not None and len(corner_data.data) > 0:

            # convert raw corners to BotState objects
            bots = corners_to_botstates(corner_data.data)

            # for now no trolley or obstacles — we'll add those later
            trolley   = None
            obstacles = []

            # get motor commands
            commands = coordinator.compute_commands(bots, trolley, obstacles)

            # print them for now — later we'll send over UDP
            for bot_id, cmd in commands.items():
                print(f"Bot {bot_id}  ->  L={cmd.left:4d}  R={cmd.right:4d}")  # keep for debug
                send_command(bot_id, cmd)

        print("----------------------")
        sleep(0.067) 
        # print(corner_data.data)
        # print("----------------------")
        # sleep(1)