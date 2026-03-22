from vision.process_markers import get_data
from threading import Thread
from time import sleep
import math
import time
import socket
import os
from dataclasses import dataclass, field
from typing import Optional, Tuple

from control.coordinator import SwarmCoordinator, BotState, BotCommand
from ultralytics import YOLO

# ── Config ────────────────────────────────────────────────────────────────────
BOT_IPS = {
    1: ("192.168.0.102", 5001),
    2: ("192.168.0.103", 5002),
    3: ("192.168.0.104", 5003),
}

IMAGE_WIDTH_PX = 640
IMAGE_HEIGHT_PX = 480
ARENA_WIDTH_M = 1.748
ARENA_HEIGHT_M = 0.906
GOAL_POS = (ARENA_WIDTH_M, ARENA_HEIGHT_M / 2)

VISION_TIMEOUT_S = 0.5
COLLISION_DIST_M = 0.12
KP_LINEAR = 1.2
KP_ANGULAR = 2.5
MAX_SPEED = 200
MIN_SPEED = 40
ARRIVE_THRESH = 0.06

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ── Tracker (dead-reckoning when trolley leaves camera view) ──────────────────


@dataclass
class TrackedObject:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    last_seen: float = field(default_factory=time.time)

    def update(self, x: float, y: float):
        dt = time.time() - self.last_seen
        if 0 < dt < 1.0:
            self.vx = (x - self.x) / dt
            self.vy = (y - self.y) / dt
        self.x, self.y = x, y
        self.last_seen = time.time()

    def predict(self) -> Tuple[float, float]:
        dt = time.time() - self.last_seen
        px = max(0.05, min(ARENA_WIDTH_M - 0.05, self.x + self.vx * dt))
        py = max(0.05, min(ARENA_HEIGHT_M - 0.05, self.y + self.vy * dt))
        return (px, py)

    @property
    def vision_fresh(self) -> bool:
        return (time.time() - self.last_seen) < VISION_TIMEOUT_S


# ── Motor maths ───────────────────────────────────────────────────────────────
def deadband(v):
    return 0 if abs(v) < MIN_SPEED else v


def drive_to(bot: BotState, target: Tuple[float, float]):
    dx = target[0] - bot.x
    dy = target[1] - bot.y
    dist = math.hypot(dx, dy)
    if dist < ARRIVE_THRESH:
        return 0, 0
    err = (math.atan2(dy, dx) - bot.heading +
           math.pi) % (2 * math.pi) - math.pi
    base = min(KP_LINEAR * dist * MAX_SPEED, MAX_SPEED)
    base *= max(0.0, 1.0 - abs(err) / math.pi)
    turn = KP_ANGULAR * err * MAX_SPEED / math.pi
    left = deadband(max(-MAX_SPEED, min(MAX_SPEED, int(base - turn))))
    right = deadband(max(-MAX_SPEED, min(MAX_SPEED, int(base + turn))))
    return left, right


# ── Coordinate helpers ────────────────────────────────────────────────────────
def corners_to_botstates(corner_data) -> dict:
    bots = {}
    if corner_data.data is None or corner_data.headings is None:
        return bots
    for i, corners in enumerate(corner_data.data):
        bot_id = i + 1
        try:
            (x1, y1), (x2, y2), (x3, y3), (x4, y4) = corners[0]
        except (ValueError, IndexError):
            continue
        cx = (x1 + x2 + x3 + x4) / 4
        cy = (y1 + y2 + y3 + y4) / 4
        mx = (cx / IMAGE_WIDTH_PX) * ARENA_WIDTH_M
        my = (cy / IMAGE_HEIGHT_PX) * ARENA_HEIGHT_M
        bots[bot_id] = BotState(id=bot_id, x=mx, y=my,
                                heading=corner_data.headings[i])
    return bots


def corners_to_trolley(corner_data) -> Optional[Tuple[float, float]]:
    # FIX: was corners_to_trolley(corner_data.target) in main — wrong, pass full object
    if not hasattr(corner_data, 'target') or corner_data.target is None:
        return None
    try:
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = corner_data.target[0]
    except (ValueError, IndexError):
        return None
    cx = (x1 + x2 + x3 + x4) / 4
    cy = (y1 + y2 + y3 + y4) / 4
    return (cx / IMAGE_WIDTH_PX) * ARENA_WIDTH_M, \
           (cy / IMAGE_HEIGHT_PX) * ARENA_HEIGHT_M


# ── Build full Arduino payload ────────────────────────────────────────────────
def build_payload(bot: BotState,
                  trolley_pos: Optional[Tuple[float, float]],
                  tracker: Optional[TrackedObject]):
    """
    Returns (payload_string, updated_tracker).
    Format: "L:{n},R:{n},PL:{n},PR:{n},VL:{0|1}"
    Arduino parse_command() reads all five fields.
    """
    if trolley_pos is not None:
        if tracker is None:
            tracker = TrackedObject(x=trolley_pos[0], y=trolley_pos[1])
        else:
            tracker.update(*trolley_pos)

    if tracker is None:
        return "L:0,R:0,PL:0,PR:0,VL:1", tracker

    vision_lost = not tracker.vision_fresh
    obj_pos = (tracker.x, tracker.y) if not vision_lost else tracker
