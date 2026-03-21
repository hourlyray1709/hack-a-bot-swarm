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