#Control MONA ESP from a terminal using socketes over the network
#
#Created by Bart Garcia, January 2021.
#bart.garcia.nathan@gmail.com

import socket
import curses

#Create the socket object

#Modify the next line, and add the IP of your MONA ESP
host = "192.168.0.105" #MONA ESP IP in local network
port = 5000             #Server Port
#Connect to host

def send_command(cmd):
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect((host, port))
        s.send(cmd.encode())
        s.close()
    except Exception as e:
        print("Error:", e)

# Create a screen for curses
screen = curses.initscr()
# turn off input echoing
curses.noecho()
# respond to keys immediately (don't wait for enter)
curses.cbreak()
# map arrow keys to special values
screen.keypad(True)
screen.addstr(0, 0, 'MONA ESP CONTROL')
screen.addstr(1, 0, 'Press "q" to exit the program')
screen.addstr(2, 0, 'Use the arrow keys to move')

try:
    while True:
        char = screen.getch()
        if char == ord('q'): #Use the letter 'q' to exit the program
            break
        elif char == curses.KEY_RIGHT:
            # print doesn't work with curses, use addstr instead
            screen.addstr(3, 0, 'Right arrow -> Turn Right   ')
            send_command("R")
        elif char == curses.KEY_LEFT:
            screen.addstr(3, 0, 'Left arrow -> Turn Left    ')
            send_command("L")
        elif char == curses.KEY_UP:
            screen.addstr(3, 0, 'Up arrow -> Move Fordward   ')
            send_command("F")
        elif char == curses.KEY_DOWN:
            screen.addstr(3, 0, 'Down arrow -> Move Backward   ')
            send_command("B")
finally:
    # shut down cleanly
    curses.nocbreak(); screen.keypad(0); curses.echo()
    curses.endwin()

#Close the socketet and finalize the program
#socket.close()