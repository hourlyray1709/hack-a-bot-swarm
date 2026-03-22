from vision.process_markers import get_data
from threading import Thread
from ultralytics import YOLO

class CornerData:
    def __init__(self):
        self.data          = None
        self.target        = None
        self.headings      = None
        self.top_left_data = None
        self.ids           = None
        self.obstacles     = []

corner_data = CornerData()
model = YOLO("yolov8n.pt")

thread1 = Thread(target=get_data, args=(corner_data, model))
thread1.start()
thread1.join()
