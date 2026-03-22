import numpy as np
import cv2 as cv
import glob
from time import sleep 
import pickle 

with open("camera_calibration.pkl", "rb") as f:
    data = pickle.load(f)
    mtx = data["mtx"]
    dist = data["dist"]
    print(mtx)
    print(dist)

camera_index = 0
cv.namedWindow("Undistorted")
vc = cv.VideoCapture(camera_index)
if vc.isOpened(): 
    _rval, _frame = vc.read() 
while _rval: 
    _rval, _frame = vc.read() 
    undistorted = cv.undistort(_frame, mtx, dist, None)
    cv.imshow("Undistorted", undistorted)
    cv.imshow("Raw image", _frame)
    key = cv.waitKey(20)
    if key == 27: # exit on ESC
        break
