import socket
import curses

#Create the socket object
sock = socket.socket()
#Modify the next line, and add the IP of your MONA ESP
host = "192.168.0.10" #MONA ESP IP in local network
port = 80             #Server Port
#Connect to host
sock.connect((host, port))

def speed_check(speed):
    if speed < 0:
        speed = 0
    if speed > 225:
        speed = 225
    return(speed)

def move_forward(speed):
    speed_check(speed)
    sock.send("F"+str(speed)+'\n')

def move_back(speed):
    speed_check(speed)
    sock.send("B"+str(speed)+'\n')

def move_left(speed):
    speed_check(speed)
    sock.send("L"+str(speed)+'\n')

def move_right(speed):
    speed_check(speed)
    sock.send("R"+str(speed)+'\n')

