import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
 
 
# ── Arena ─────────────────────────────────────────────────────────────────────
#1.72m x 0.88m
ARENA_WIDTH_M  = 1.748  # metres left→right (start to goal)
ARENA_HEIGHT_M = 0.906   # metres top→bottom
 
# ── Formation ─────────────────────────────────────────────────────────────────
PUSH_OFFSETS_Y  = [-0.10, 0.10]  # 2 pushers: 20cm above and below centre
APPROACH_DIST_M = 0.180          # sit this far behind the trolley
 
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

# ── Obstacle avoidance ────────────────────────────────────────────────────────
OBS_REPULSE_DIST  = 0.40   # start avoiding at this distance in metres
OBS_REPULSE_FORCE = 0.60   # how hard to push the waypoint away


@dataclass
class BotCommand:
    left: int #left motor speed
    right: int #right motor speed

# Fake BotState — just for testing, same fields as the real one
@dataclass
class BotState:
    id:      int
    x:       float
    y:       float
    heading: float

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
    
    @staticmethod
    def _formation_positions(trolley: tuple[float,float]):
        t_x, t_y = trolley

        push_x = t_x - APPROACH_DIST_M  # sit behind the trolley

        return [
            (push_x, t_y + dy)
            for dy in PUSH_OFFSETS_Y    # one position per pusher
        ]

    @staticmethod
    def _assign_bots_positions(bots: dict[int, tuple[float,float]], positions: list[tuple[float,float]]) -> dict[int,tuple[float,float] ]:
        '''
        bots: dictionary where botID is mapped to target position

        RETURNS: a dictionary with bot id to its slot
        '''

        available_bots = list(bots.keys())
        available_pos  = list(range(len(positions)))
        assignment     = {}

        while available_bots and available_pos:
            best_bot  = None
            best_pos  = None
            best_dist = float("inf")

            for bid in available_bots:
                for pi in available_pos:
                    px, py = positions[pi]
                    d = math.hypot(bots[bid].x - px,
                                bots[bid].y - py)
                    if d < best_dist:
                        best_dist = d
                        best_bot  = bid
                        best_pos  = pi

            assignment[best_bot] = positions[best_pos]
            available_bots.remove(best_bot)
            available_pos.remove(best_pos)

        return assignment
    
    @staticmethod
    def _guard_target(trolley: tuple[float, float], obstacles: list[tuple[float,float]]) -> tuple[float,float]:
        tx, ty = trolley

        #get threats in front of the troller in the look ahead zone
        threats = [
            obs for obs in obstacles
            if tx < obs[0] < tx + GUARD_LOOKAHEAD_M
        ]

        if threats:
            # Guard from the more central threats
            target_obs = min(threats, key=lambda o: abs(o[1] - ARENA_HEIGHT_M /2))

             # drive slightly past it to push it clear
            return (target_obs[0] + 0.10, target_obs[1])

        else:
            # no threat — idle ahead of trolley on centreline
            return (tx + GUARD_STANDBY_DIST, ARENA_HEIGHT_M / 2)

    @staticmethod
    def _avoid_obstacles(bot_pos, target: tuple[float,float], obstacles: list[tuple[float, float]]) -> tuple[float, float]:
        tx, ty = target

        for obs in obstacles:
            ox, oy = obs
            dist = math.hypot(tx - ox, ty - oy)

            if dist < OBS_REPULSE_DIST and dist > 0.01:
                #repulse force calculation
                repulse = OBS_REPULSE_FORCE * (1.0 - dist / OBS_REPULSE_DIST)
                angle   = math.atan2(ty - oy, tx - ox)
                tx += repulse * math.cos(angle)
                ty += repulse * math.sin(angle)

        # clamp to arena boundaries
        tx = max(0.05, min(ARENA_WIDTH_M  - 0.05, tx))
        ty = max(0.05, min(ARENA_HEIGHT_M - 0.05, ty))

        return (tx, ty)

    def compute_commands(
            self,
            bots: Dict[int, BotState],
            trolley: Optional[Tuple[float,float]],
            obstacles: List[Tuple[float,float]]
            ) -> Dict[int, BotCommand]:
        
        commands = {
            b_id: BotCommand(left=0, right= 0)
            for b_id in self.bot_ids
        }

        if not bots:
            return commands
        
        if trolley is None:
            trolley = (ARENA_WIDTH_M / 2, ARENA_HEIGHT_M / 2)

        # highest bot ID is the guard, rest are pushers
        pusher_ids = sorted(bots.keys())[:-1]
        guard_id   = sorted(bots.keys())[-1]
 
        # get pusher slot positions
        positions = self._formation_positions(trolley)
 
        # assign pushers to slots
        pusher_bots = {
            bid: bots[bid] for bid in pusher_ids if bid in bots
        }
        assignment = self._assign_bots_positions(pusher_bots, positions)

        # compute pusher commands
        for bot_id, target in assignment.items():
            bot         = bots[bot_id]
            safe_target = self._avoid_obstacles(
                (bot.x, bot.y), target, obstacles
            )
            commands[bot_id] = self._drive_to(bot, safe_target)
 
        # compute guard command
        if guard_id in bots:
            guard_bot    = bots[guard_id]
            guard_target = self._guard_target(trolley, obstacles)
            safe_guard   = self._avoid_obstacles(
                (guard_bot.x, guard_bot.y), guard_target, obstacles
            )
            commands[guard_id] = self._drive_to(guard_bot, safe_guard)
 
        return commands
        
    
        

# outside the class — no indentation
def _deadband(value, dead):
    return 0 if abs(value) < dead else value



if __name__ == "__main__":
    bot = BotState(id=1, x=0.5, y=1.0, heading=0.0)

    tests = [
        ((1.5, 1.0), "straight ahead"),
        ((1.5, 0.6), "ahead and up"),
        ((0.5, 1.0), "already there"),
        ((0.2, 1.0), "behind the bot"),
    ]

    for target, description in tests:
        cmd = SwarmCoordinator._drive_to(bot, target)
        print(f"{description:20s}  ->  L={cmd.left:4d}  R={cmd.right:4d}")

    