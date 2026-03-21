import cv2
import numpy as np 

def get_heading(corner): 
    _corner = corner[0]
    top_left = np.array(_corner[0])
    top_right = np.array(_corner[1])
    bottom_right = np.array(_corner[2])
    bottom_left = np.array(_corner[3])
    heading_vector = top_left - bottom_right
    axis = np.array([0,-1])
    pheta = np.acos(np.dot(heading_vector, axis) / (np.linalg.norm(heading_vector) * np.linalg.norm(axis)))
    return pheta 

def get_data(corner_data, model):
    cv2.namedWindow("preview")
    vc = cv2.VideoCapture(0)

    detectorParams = cv2.aruco.DetectorParameters()
    detectorDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(detectorDict, detectorParams)


    if vc.isOpened(): # try to get the first frame
        rval, frame = vc.read()
    else:
        rval = False

    while rval:                        # while we have camera input 
        corners, ids, rejected = detector.detectMarkers(frame)    # corners[i][0] = top left corner of marker i
        if ids is not None: 
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)


        # marker processing 
        data = [corner for corner in corners]
        corner_data.data = data 
        top_left_data = [data_i[0] for data_i in data]
        corner_data.top_left_data = top_left_data
        headings = [get_heading(data_i) for data_i in data]
        corner_data.headings = headings 

        # object detection
        clache = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = clache.apply(gray_frame)
        gray_frame = cv2.merge([gray_frame, gray_frame, gray_frame])
        od_results = model(gray_frame, conf=0.3)
        od_annotation = od_results[0].plot()
        canny_results = cv2.Canny(gray_frame, 50, 150, apertureSize=3)
        cv2.imshow("Canny results", canny_results)


        cv2.imshow("preview", frame)
        cv2.imshow("yolov8frame", od_annotation)
        corner_data.ids = ids
        rval, frame = vc.read()
        key = cv2.waitKey(20)
        if key == 27: # exit on ESC
            break

    cv2.destroyWindow("preview")
    vc.release()
