import math
import time

from control.coordinator import SwarmCoordinator, BotState


# ---------- Simulation ----------

def simulate_step(bot, cmd, dt=0.1, wheelbase=0.2):
    """
    Simple differential drive simulation.
    """
    v = (cmd.left + cmd.right) / 2.0
    omega = (cmd.right - cmd.left) / wheelbase

    bot.heading += omega * dt
    bot.heading = (bot.heading + math.pi) % (2 * math.pi) - math.pi

    bot.x += v * math.cos(bot.heading) * dt
    bot.y += v * math.sin(bot.heading) * dt


def run_simulation(start, target, label, steps=200):
    bot = BotState(id=1, x=start[0], y=start[1], heading=start[2])

    print(f"\n=== {label} ===")
    print(f"Start: ({bot.x:.2f}, {bot.y:.2f}) → Target: {target}")

    path = []

    for i in range(steps):
        cmd = SwarmCoordinator._drive_to(bot, target)
        simulate_step(bot, cmd)

        path.append((bot.x, bot.y))

        # Print every few steps so it's readable
        if i % 10 == 0:
            print(f"Step {i:3d} | x={bot.x:.2f}, y={bot.y:.2f}, "
                  f"L={cmd.left:4d}, R={cmd.right:4d}")

    print(f"Final: ({bot.x:.2f}, {bot.y:.2f})")
    print(f"Error: dx={bot.x - target[0]:.2f}, dy={bot.y - target[1]:.2f}")

    return path


# ---------- Scenarios ----------

start = (0.3, 0.45, 0.0)

run_simulation(start, (1.4, 0.15), "Diagonal up-right")
run_simulation(start, (1.4, 0.75), "Diagonal down-right")
run_simulation(start, (0.1, 0.15), "Diagonal up-left")
run_simulation(start, (0.1, 0.75), "Diagonal down-left")

run_simulation(start, (1.4, 0.45), "Straight ahead")
run_simulation(start, (0.3, 1.2), "Turn left (target above)")
run_simulation(start, (0.3, -0.2), "Turn right (target below)")
run_simulation(start, (-0.5, 0.45), "Behind (should turn)")


print("\nDone.")