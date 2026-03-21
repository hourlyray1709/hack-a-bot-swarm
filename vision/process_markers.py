import cv2

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
    corners, ids, rejected = detector.detectMarkers(frame)    # corners[0] = top left corner of marker 
    if ids is not None: 
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

    cv2.imshow("preview", frame)
    rval, frame = vc.read()
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break

cv2.destroyWindow("preview")
vc.release()