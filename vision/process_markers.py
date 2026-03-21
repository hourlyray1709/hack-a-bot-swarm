import cv2


def get_data(corner_data):
    cv2.namedWindow("preview")
    vc = cv2.VideoCapture(0)

    detectorParams = cv2.aruco.DetectorParameters()
    detectorDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000)
    detector = cv2.aruco.ArucoDetector(detectorDict, detectorParams)


    if vc.isOpened(): # try to get the first frame
        rval, frame = vc.read()
    else:
        rval = False

    while rval:                        # while we have camera input 
        corners, ids, rejected = detector.detectMarkers(frame)    # corners[i][0] = top left corner of marker i
        if ids is not None: 
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        data = [corner for corner in corners]
        corner_data.data = data 
        top_left_data = [data_i[0] for data_i in data]
        cv2.imshow("preview", frame)
        rval, frame = vc.read()
        key = cv2.waitKey(20)
        if key == 27: # exit on ESC
            break

    cv2.destroyWindow("preview")
    vc.release()