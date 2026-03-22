import cv2
import numpy as np

cap = cv2.VideoCapture(0)  # 0 = default webcam

while True:
    ret, frame = cap.read()
    if not ret:
        break

    orig = frame.copy()

    # 1. Grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 2. Blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Edge detection
    edges = cv2.Canny(blur, 50, 150)

    # 4. Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 2000:  # filter noise
            continue

        # 5. Approximate shape
        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        # 6. Check for quadrilateral
        if len(approx) == 4:
            # Optional: check aspect ratio (square-ish)
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)

            if 0.8 < aspect_ratio < 1.2:  # roughly square
                cv2.drawContours(orig, [approx], -1, (0, 255, 0), 3)
                cv2.putText(orig, "Paper", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Show outputs
    cv2.imshow("Edges", edges)
    cv2.imshow("Detection", orig)

    # Press ESC to quit
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()