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
    top_left  = np.array(_corner[0])
    top_right = np.array(_corner[1])

    heading_vector = top_right - top_left
    heading = np.arctan2(heading_vector[1], heading_vector[0])
    return heading

def detect_red_obstacles(frame, arena_width_m, arena_height_m):
    """
    Finds red objects in the frame and returns their centres in metres.
    Returns a list of (x, y) tuples.
    """
    # convert to HSV — much easier to filter colours than BGR
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # red wraps around in HSV so we need two ranges
    lower_red1 = np.array([0,   120, 70])
    upper_red1 = np.array([10,  255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    # combine both red ranges into one mask
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask  = cv2.bitwise_or(mask1, mask2)

    # clean up the mask
    kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask    = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask    = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)

    # find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    obstacles = []
    h, w = frame.shape[:2]

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500:   # ignore tiny blobs — noise
            continue

        # get centre
        M  = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]

        # convert pixels to metres
        mx = (cx / w) * arena_width_m
        my = (cy / h) * arena_height_m

        obstacles.append((mx, my))

        # draw on frame for debug
        cv2.circle(frame, (int(cx), int(cy)), 12, (0, 0, 255), 2)
        cv2.putText(frame, "obstacle", (int(cx)-20, int(cy)-16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    return obstacles

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
            #for i in range(len(ids)): 
                #if ids[i] == 4: 
                    #print("Target Hit")
                    #print(corners[i])
                    #corner_data.target = corners[i]
            corner_data.target=[[0.8, 0.45], [0.8, 0.45], [0.8, 0.45], [0.8, 0.45]]
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)


        # marker processing 
        data = [corner for corner in corners]
        corner_data.data = data 
        top_left_data = [data_i[0] for data_i in data]
        corner_data.top_left_data = top_left_data
        headings = [get_heading(data_i) for data_i in data]
        corner_data.headings = headings 

        obstacles = detect_red_obstacles(frame, 1.748, 0.906)
        corner_data.obstacles = obstacles
        
        # object detection
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray_frame, (5,5), 0)
        edges = cv2.Canny(blur, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 2000:  # filter noise
                continue

            # 5. Approximate shape
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)

            # 6. Check for quadrilateral
            if len(approx) < 7:
                # Optional: check aspect ratio (square-ish)
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)

                cv2.drawContours(frame, [approx], -1, (0, 255, 0), 3)
                cv2.putText(frame, "Paper", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        #cv2.imshow("Canny results", canny_results)


        cv2.imshow("preview", frame)
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
