import cv2

VIDEO_PATH = "../media/videos/2026-08-22.mp4"
TEST_TIMESTAMP_MS = 207000

ROI_X1, ROI_Y1 = 150, 100
ROI_X2, ROI_Y2 = 470, 180

capture = cv2.VideoCapture(VIDEO_PATH)
capture.set(cv2.CAP_PROP_POS_MSEC, TEST_TIMESTAMP_MS)
succeed, frame = capture.read()
capture.release()

if succeed:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    roi = gray[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2]

    _ret, thresh = cv2.threshold(roi, 150, 255, cv2.THRESH_BINARY)
    contours, _h = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    print(f"Total de contornos na ROI: {len(contours)}")
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        print(f"bbox=({x},{y},{w},{h}) area={w*h}")

    cv2.imwrite("../media/screenshots/roi_binary_test.png", thresh)
    cv2.imwrite("../media/screenshots/roi_gray_test.png", roi)
else:
    print("Não consegui ler o frame nesse timestamp.")
