import cv2  # type: ignore
from numpy import ndarray
import pytesseract
import yt_dlp
from datetime import datetime
from typing import TypeAlias
import os

MS_PER_SECOND = 1000
ROI_X1, ROI_Y1 = 150, 100
ROI_X2, ROI_Y2 = 470, 170
MIN_TEXT_LENGTH = 10
Rect: TypeAlias = tuple[int, int, int, int]
TimestampData: TypeAlias = list[tuple[int, Rect]]
TimestampTextData: TypeAlias = list[tuple[int, Rect, str]]


def load_image_grayscale(path: str) -> ndarray:
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return image


def crop_fixed_region(
    image: ndarray, y1: int, y2: int, x1: int, x2: int
) -> ndarray:
    return image[y1:y2, x1:x2]


def find_contours_from_grayscale(
    image: ndarray, thresh_val: int, max_val: int
) -> list:
    _ret, thresh_img = cv2.threshold(
        image, thresh_val, max_val, cv2.THRESH_BINARY
    )
    contours, _hierarchy = cv2.findContours(
        thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    return contours, thresh_img


def find_balloon_rect(
    contours: list,
    w_min: int,
    w_max: int,
    h_min: int,
    h_max: int,
) -> tuple | None:
    for contour in contours:
        x, y, largura, altura = cv2.boundingRect(contour)
        if w_min <= largura <= w_max and \
           h_min <= altura <= h_max:
            return (x, y, largura, altura)
    return None


def show_image(image: ndarray, window_name: str) -> None:
    cv2.imshow(window_name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def run_pipeline(path: str) -> tuple | None:
    image = load_image_grayscale(path)
    contours, thresh_img = find_contours_from_grayscale(
        image, thresh_val=150, max_val=255
    )
    rect = find_balloon_rect(
        contours,
        w_min=350, w_max=420,
        h_min=80, h_max=120,
    )
    show_image(thresh_img, "Binary Image")
    print(rect)

    if rect is not None:
        balloon_text = extract_balloon_text(image, rect)
        print(balloon_text)

    return rect


def extract_balloon_text(image: ndarray, rect: tuple) -> str:
    x, y, width, height = rect
    x1, y1 = x, y
    x2, y2 = x + width, y + height
    balloon_crop = crop_fixed_region(image, y1, y2, x1, x2)
    text = pytesseract.image_to_string(balloon_crop)
    return text


def download_video(url: str) -> str:
    today = datetime.now()
    output_path = ("../media/videos/" + today.strftime("%Y-%m-%d") + ".mp4")

    options = {
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "merge_output_format": "mp4",
        "outtmpl": "../media/videos/"
        + today.strftime("%Y-%m-%d") + ".%(ext)s",
    }
    if not os.path.exists(output_path):
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

    return output_path


def find_monsters_frames(
        video_path: str,
        first_ms: int,
        intval_ms: int
        ) -> TimestampData:
    capture = cv2.VideoCapture(video_path)
    frame_width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    frame_height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Frame size (width x height): {frame_width} x {frame_height}")
    total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = capture.get(cv2.CAP_PROP_FPS)
    duration_sec = total_frames / fps
    duration_ms = duration_sec * MS_PER_SECOND
    print(f"Accurate Frame Count: {total_frames}")
    print(f"Accurate second count: {duration_sec}")
    current_ms = first_ms
    found_frames = []
    while (current_ms < duration_ms):
        capture.set(cv2.CAP_PROP_POS_MSEC, current_ms)
        succeed, frame = capture.read()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        roi_frame = crop_fixed_region(
            gray_frame, ROI_Y1, ROI_Y2, ROI_X1, ROI_X2
        )
        contours, thresh_img = find_contours_from_grayscale(
            roi_frame, thresh_val=150, max_val=255
        )
        roi_rect = find_balloon_rect(
            contours,
            w_min=220, w_max=300,
            h_min=45, h_max=80,
        )
        if roi_rect is not None:
            roi_x, roi_y, width, height = roi_rect
            rect = (roi_x + ROI_X1, roi_y + ROI_Y1, width, height)
            found_frames.append((current_ms, rect))
        current_ms = current_ms + intval_ms
    capture.release()
    print(found_frames)
    return found_frames


def filter_frames_with_text(
        video_path: str,
        found_frames: TimestampData
        ) -> TimestampTextData:
    capture = cv2.VideoCapture(video_path)
    filtered_frames = []
    for timestamp_ms, rect in found_frames:
        capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
        succeed, frame = capture.read()
        if not succeed:
            continue
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = extract_balloon_text(gray_frame, rect)
        cleaned_text = text.strip()
        if len(cleaned_text) >= MIN_TEXT_LENGTH:
            filtered_frames.append((timestamp_ms, rect, cleaned_text))
    capture.release()
    return filtered_frames


def save_debug_crops(
        video_path: str,
        found_frames: TimestampData
        ) -> None:
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = f"../media/screenshots/{video_name}"
    os.makedirs(output_dir, exist_ok=True)

    capture = cv2.VideoCapture(video_path)
    for timestamp_ms, rect in found_frames:
        capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
        succeed, frame = capture.read()
        if not succeed:
            continue
        x, y, width, height = rect
        crop = crop_fixed_region(frame, y, y + height, x, x + width)
        filename = f"{output_dir}/{timestamp_ms}.png"
        cv2.imwrite(filename, crop)
    capture.release()


if __name__ == "__main__":
    # run_pipeline("../media/screenshots/message-coco.png")
    video_path = download_video("https://www.youtube.com/watch?v=tdHbQSbinhs")
    print(video_path)
    found_frames = find_monsters_frames(video_path, 80500, 500)
    save_debug_crops(video_path, found_frames)
    filtered_frames = filter_frames_with_text(video_path, found_frames)
    print(f"Antes do filtro: {len(found_frames)}")
    print(f"Depois do filtro: {len(filtered_frames)}")
    for item in filtered_frames:
        print(item)
