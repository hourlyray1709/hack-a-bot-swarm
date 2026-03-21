"""
test_keyboard.py  —  Manual keyboard control for MONA bot
Press arrow keys to drive, Q to quit.
 
Make sure your laptop and bot are on the same WiFi network.
"""
 
import socket
import sys
 
BOT_IP   = "192.168.0.102"  # your bot's IP
BOT_PORT = 5001              # port for bot 1
SPEED    = 150               # 0-255, change this to go faster or slower
 
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
 
def send(left, right):
    payload = f"L{left} R{right}\n".encode()
    sock.sendto(payload, (BOT_IP, BOT_PORT))
    print(f"L={left:4d}  R={right:4d}")
 
# ── Windows (msvcrt) ──────────────────────────────────────────────────────────
if sys.platform == "win32":
    import msvcrt
 
    print("Arrow keys to drive, Q to quit")
    print("UP=forward  DOWN=backward  LEFT=spin left  RIGHT=spin right")
    print("--------------------------------------------------------------")
 
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
 
            if key == b'q' or key == b'Q':
                print("Stopping bot and quitting...")
                send(0, 0)
                break
 
            elif key == b'\xe0' or key == b'\x00':   # arrow key prefix
                arrow = msvcrt.getch()
 
                if arrow == b'H':    # up arrow
                    print("Forward")
                    send(SPEED, SPEED)
 
                elif arrow == b'P':  # down arrow
                    print("Backward")
                    send(-SPEED, -SPEED)
 
                elif arrow == b'K':  # left arrow
                    print("Spin left")
                    send(-SPEED, SPEED)
 
                elif arrow == b'M':  # right arrow
                    print("Spin right")
                    send(SPEED, -SPEED)
 
            else:
                # any other key = stop
                print("Stop")
                send(0, 0)
 
# ── Mac / Linux (curses) ──────────────────────────────────────────────────────
else:
    import curses
 
    def main(screen):
        curses.noecho()
        curses.cbreak()
        screen.keypad(True)
        screen.nodelay(True)   # non-blocking key reads
 
        screen.addstr(0, 0, "Arrow keys to drive, Q to quit")
        screen.addstr(1, 0, "UP=forward  DOWN=backward  LEFT=spin left  RIGHT=spin right")
        screen.addstr(2, 0, "--------------------------------------------------------------")
 
        while True:
            key = screen.getch()
 
            if key == ord('q') or key == ord('Q'):
                send(0, 0)
                break
            elif key == curses.KEY_UP:
                screen.addstr(4, 0, "Forward      ")
                send(SPEED, SPEED)
            elif key == curses.KEY_DOWN:
                screen.addstr(4, 0, "Backward     ")
                send(-SPEED, -SPEED)
            elif key == curses.KEY_LEFT:
                screen.addstr(4, 0, "Spin left    ")
                send(-SPEED, SPEED)
            elif key == curses.KEY_RIGHT:
                screen.addstr(4, 0, "Spin right   ")
                send(SPEED, -SPEED)
            elif key != -1:
                screen.addstr(4, 0, "Stop         ")
                send(0, 0)
 
    curses.wrapper(main)
 
sock.close()
print("Done!")