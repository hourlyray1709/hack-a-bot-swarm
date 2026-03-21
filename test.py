import socket

host = "192.168.0.105"
port = 5000

s = socket.socket()
s.connect((host, port))
s.send(b"F")
s.close()

print("Sent!")