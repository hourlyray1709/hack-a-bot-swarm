# the file we run when we connect to the camera 
import cv2
from vision.process_markers import get_data 
from threading import Thread 
from time import sleep 

class CornerData: 
    def __init__(self): 
        self.data = None 

corner_data = CornerData()
thread1 = Thread(target=get_data, args=(corner_data,))
thread1.start()

while True: 
    print(corner_data.data)
    print("----------------------")
    sleep(1)