# the file we run when we connect to the camera 
from vision.process_markers import get_data 
from threading import Thread 
from time import sleep 
import math
from control.coordinator import SwarmCoordinator, BotState, BotCommand
import ultralytics
import supervision
import torch
import cv2
from collections import defaultdict
import supervision as sv
from ultralytics import YOLO
import os 

import socket

# ── Bot IP addresses ───────────────────────────────────────────────────────────
# Update these once each bot connects and prints its IP in Serial Monitor
BOT_IPS = {
    1: ("192.168.0.102", 5001),
    2: ("192.168.0.103", 5002),
    3: ("192.168.0.104", 5003),
}


# ── these must match your actual camera + arena setup ─────────────────────────
#1080p camera
IMAGE_WIDTH_PX  = 640   # your camera resolution width
IMAGE_HEIGHT_PX = 480    # your camera resolution height
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

    if corner_data.data is None or corner_data.headings is None:
        return bots
    
    for i, corners in enumerate(corner_data.data):
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
        #heading = math.atan2(y2 - y1, x2 - x1)
        heading = corner_data.headings[i]

        


        # convert
        #  pixels to metres
        mx = (cx / IMAGE_WIDTH_PX)  * ARENA_WIDTH_M
        my = (cy / IMAGE_HEIGHT_PX) * ARENA_HEIGHT_M

        bots[bot_id] = BotState(id=bot_id, x=mx, y=my, heading=heading)

    return bots


def corners_to_trolley(corner_data):
    if not hasattr(corner_data, 'target') or corner_data.target is None:
        return None
    try:
        (x1,y1), (x2,y2), (x3,y3), (x4,y4) = corner_data.target[0]
    except (ValueError, IndexError):
        return None

    cx = (x1 + x2 + x3 + x4) / 4
    cy = (y1 + y2 + y3 + y4) / 4
    mx = (cx / IMAGE_WIDTH_PX) * ARENA_WIDTH_M
    my = (cy / IMAGE_HEIGHT_PX) * ARENA_HEIGHT_M
    return (mx, my)

class CornerData: 
    def __init__(self): 
        self.data = None 
        self.top_left_data = None 
        self.headings = None 
        self.ids = None 
        self.target = None


if __name__ == "__main__":
    model = YOLO('yolov8n.pt')
    corner_data = CornerData()
    coordinator = SwarmCoordinator(bot_ids=[1, 2, 3])
    thread1 = Thread(target=get_data, args=(corner_data,model))
    thread1.start()

    while True:
        if corner_data.data is not None and len(corner_data.data) > 0:

            # convert raw corners to BotState objects
            bots = corners_to_botstates(corner_data)
            print(f"Visible bots: {list(bots.keys())}")

            # for now no trolley or obstacles — we'll add those later
            trolley   = corners_to_trolley(corner_data.target)
            obstacles = []

            for bot_id, bot in bots.items():
                print(f"x={bot.x:.3f}  y={bot.y:.3f}  heading={bot.heading:.2f} rad  ({math.degrees(bot.heading):.1f} deg)")

            # get motor commands
            commands = coordinator.compute_commands(bots, trolley, obstacles)

            # print them for now — later we'll send over UDP
            for bot_id, cmd in commands.items():
                print(f"Bot {bot_id}  ->  L={cmd.left:4d}  R={cmd.right:4d}")  # keep for debug
                send_command(bot_id, cmd)
            
            for bot_key in bots.keys(): 
                bot = bots[bot_key]
                print(f"bot position {bot.x}, {bot.y}")
            print(f"target position {corner_data.target[0][0], corner_data.target[0][1]}")
        print("--------")
        sleep(0.5)    
        #os.system("cls")
        # print(corner_data.data)
        # print("----------------------")
        # sleep(1)
