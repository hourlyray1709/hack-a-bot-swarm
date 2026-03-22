import numpy as np
import cv2 as cv
import glob
from time import sleep 
import pickle 

frames_to_capture = 60 
counter = 0 
camera_index = 0
 # 0 for webcam, 1 for arena cam 
 
# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
 
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
checker_coords = [11,7]
objp = np.zeros((checker_coords[0] * checker_coords[1],3), np.float32)
objp[:,:2] = np.mgrid[0:checker_coords[0],0:checker_coords[1]].T.reshape(-1,2)
 
# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.
 
cv.namedWindow("Test Calibration")
vc = cv.VideoCapture(camera_index)
vc.set(cv.CAP_PROP_FRAME_WIDTH, 640)
vc.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

if vc.isOpened():
    rval, frame = vc.read()
    background = frame 
else:
    rval = False

while rval: 
    cv.imshow("Test Calibration", frame)

    grey_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    ret, corners = cv.findChessboardCorners(grey_frame, (checker_coords[0],checker_coords[1]), None)

    if ret == True and len(corners) == checker_coords[0] * checker_coords[1] and counter < frames_to_capture:
        counter += 1  
        objpoints.append(objp)
 
        corners2 = cv.cornerSubPix(grey_frame,corners, (11,11), (-1,-1), criteria)
        imgpoints.append(corners2)
 
        # Draw and display the corners
        cv.drawChessboardCorners(frame, (checker_coords[0], checker_coords[1]), corners2, ret)
        cv.imshow('Test Calibration', frame)
        print(f"captured {counter} out of {frames_to_capture}")
        print("Press space to continue")
        sleep(1)
        key=cv.waitKey(0)
    key = cv.waitKey(20)
    if key == 27: # exit on ESC
        break
    rval, frame = vc.read()
    cv.waitKey(20)

cv.destroyAllWindows()

print("Beginning calibration")
print(f"Number of frames detected: {len(objpoints)}")
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, grey_frame.shape[::-1], None, None)

print("Calibration successful:", ret)
print("Camera matrix:\n", mtx)
print("Distortion coefficients:\n", dist)

print("Showing undistort image")

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


cv.destroyAllWindows()
overwrite = input("Overwrite calibration files?y/n")
if overwrite == 'y': 
    # Save camera matrix and distortion coefficients
    calibration_data = {"mtx": mtx, "dist": dist}

    with open("camera_calibration.pkl", "wb") as f:
        pickle.dump(calibration_data, f)

    print("Calibration saved to camera_calibration.pkl")
