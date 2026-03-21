import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
 
 
# ── Arena ─────────────────────────────────────────────────────────────────────
ARENA_WIDTH_M  = 3.0   # metres left→right (start to goal)
ARENA_HEIGHT_M = 2.0   # metres top→bottom
 
# ── Formation ─────────────────────────────────────────────────────────────────
PUSH_OFFSETS_Y  = [-0.20, 0.20]  # 2 pushers: 20cm above and below centre
APPROACH_DIST_M = 0.18           # sit this far behind the trolley
 
# ── Guard ─────────────────────────────────────────────────────────────────────
GUARD_LOOKAHEAD_M  = 0.60  # scan this far ahead of the trolley for obstacles
GUARD_STANDBY_DIST = 0.40  # idle this far ahead when no threat exists
 
# ── Controller ────────────────────────────────────────────────────────────────
KP_LINEAR  = 1.2   # forward speed gain  — raise if bots feel sluggish
KP_ANGULAR = 2.5   # turning gain        — lower if bots wobble side to side
MAX_SPEED  = 220   # max motor PWM (0–255), leave headroom below 255
MIN_SPEED  = 40    # dead-band: values below this won't spin the motors
 
# ── Safety ────────────────────────────────────────────────────────────────────
ARRIVE_THRESH_M = 0.06

@dataclass
class BotCommand:
    left: int #left motor speed
    right: int #right motor speed


class SwarmCoordinator:
    def __init__(self, bot_ids: list):
        self.bot_ids = bot_ids

    @staticmethod
    def _drive_to(bot, target):
        dx = target[0] - bot.x
        dy = target[1] - bot.y
        dist = math.hypot(dx, dy)

        if dist < ARRIVE_THRESH_M:
            return BotCommand(left=0, right=0)

        target_heading = math.atan2(dy, dx)
        heading_err = target_heading - bot.heading
        heading_err = (heading_err + math.pi) % (2 * math.pi) - math.pi

        base_speed = min(KP_LINEAR * dist * MAX_SPEED, MAX_SPEED)
        base_speed *= max(0.0, 1.0 - abs(heading_err) / math.pi)

        turn  = KP_ANGULAR * heading_err * MAX_SPEED / math.pi
        left  = int(base_speed - turn)
        right = int(base_speed + turn)

        left  = _deadband(max(-MAX_SPEED, min(MAX_SPEED, left)),  MIN_SPEED)
        right = _deadband(max(-MAX_SPEED, min(MAX_SPEED, right)), MIN_SPEED)

        return BotCommand(left=left, right=right)


# outside the class — no indentation
def _deadband(value, dead):
    return 0 if abs(value) < dead else value