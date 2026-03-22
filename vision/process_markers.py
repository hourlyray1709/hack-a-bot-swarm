import cv2
import numpy as np 
import pickle 

def load_calibration(path="camera_calibration.pkl"):
    with open("camera_calibration.pkl", "rb") as f:
        data = pickle.load(f)
        mtx = data["mtx"]
        dist = data["dist"]
    return mtx, dist 

def get_heading(corner): 
    _corner = corner[0]
    top_left = np.array(_corner[0])
    top_right = np.array(_corner[1])
    bottom_right = np.array(_corner[2])
    bottom_left = np.array(_corner[3])
    heading_vector = top_left - bottom_right
    axis = np.array([0,-1])
    pheta = np.arccos(np.dot(heading_vector, axis) / (np.linalg.norm(heading_vector) * np.linalg.norm(axis))) - np.pi / 4
    if pheta < 0: 
        pheta = 2* np.pi + pheta 
    return pheta 

def get_data(corner_data, model):
    cv2.namedWindow("preview")
    vc = cv2.VideoCapture(0)
    vc.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 

    mtx, dist = load_calibration()

    detectorParams = cv2.aruco.DetectorParameters()
    detectorDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(detectorDict, detectorParams)

    if vc.isOpened(): # try to get the first frame
        rval, frame = vc.read()
        background = frame 
    else:
        rval = False
    


    while rval:                        # while we have camera input 
        corners, ids, rejected = detector.detectMarkers(frame)    # corners[i][0] = top left corner of marker i
        if ids is not None:
            for i in range(len(ids)): 
                if ids[i] == 2: 
                    print("Target Hit")
                    print(corners[i])
                    corner_data.target = corners[i]
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)


        # marker processing 
        data = [corner for corner in corners]
        corner_data.data = data 
        top_left_data = [data_i[0] for data_i in data]
        corner_data.top_left_data = top_left_data
        headings = [get_heading(data_i) for data_i in data]
        corner_data.headings = headings 

        # object detection
        od_results = model(frame, conf=0.3, verbose=False)
        od_annotation = od_results[0].plot()

        #cv2.imshow("Canny results", canny_results)


        cv2.imshow("preview", frame)
        cv2.imshow("yolov8frame", od_annotation)
        corner_data.ids = ids
        rval, rawframe = vc.read()
        frame = rawframe
        #frame = cv2.undistort(rawframe, mtx, dist, None)
        #frame = cv2.absdiff(frame, background)
        key = cv2.waitKey(20)
        if key == 27: # exit on ESC
            break

    cv2.destroyWindow("preview")
    vc.release()
