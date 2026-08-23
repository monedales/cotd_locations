import cv2  # type: ignore
import yt_dlp
from datetime import datetime
import os
import re
import shutil

from consts import (
    MS_PER_SECOND,
    MIN_TEXT_LENGTH,
    BALLOON_ROI_X1,
    BALLOON_ROI_Y1,
    BALLOON_ROI_X2,
    BALLOON_ROI_Y2,
    SCREENSHOTS_DIR,
    VIDEO_FOLDER_NAME_PATTERN,
)
from data_types import TimestampData, TimestampTextData, TimestampImageData
from image_ops import (
    crop_fixed_region,
    find_contours_from_grayscale,
    find_balloon_rect,
    extract_balloon_text,
)


def clean_debug_screenshots(base_dir: str = SCREENSHOTS_DIR) -> None:
    if not os.path.isdir(base_dir):
        return
    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        is_video_folder = re.fullmatch(VIDEO_FOLDER_NAME_PATTERN, entry)
        if os.path.isdir(entry_path) and is_video_folder:
            shutil.rmtree(entry_path)
            os.makedirs(entry_path)


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
            gray_frame,
            BALLOON_ROI_Y1, BALLOON_ROI_Y2,
            BALLOON_ROI_X1, BALLOON_ROI_X2,
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
            rect = (
                roi_x + BALLOON_ROI_X1,
                roi_y + BALLOON_ROI_Y1,
                width, height,
            )
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
        found_frames: TimestampData,
        subfolder: str = ""
        ) -> None:
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = f"../media/screenshots/{video_name}"
    if subfolder:
        output_dir = f"{output_dir}/{subfolder}"
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


def extract_monsters_locations(
        video_path: str,
        frames: TimestampTextData
        ) -> TimestampImageData:
    capture = cv2.VideoCapture(video_path)
    locations = []
    for timestamp_ms, _rect, _text in frames:
        capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
        succeed, frame = capture.read()
        if not succeed:
            continue
        locations.append((timestamp_ms, frame))
    capture.release()
    return locations


def save_monster_locations(
        video_path: str,
        locations: TimestampImageData,
        subfolder: str = ""
        ) -> None:
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = f"../media/screenshots/{video_name}"
    if subfolder:
        output_dir = f"{output_dir}/{subfolder}"
    os.makedirs(output_dir, exist_ok=True)

    for timestamp_ms, frame in locations:
        filename = f"{output_dir}/{timestamp_ms}.png"
        cv2.imwrite(filename, frame)


def reduce_duplicates(
        frames: TimestampTextData,
        time_limit_ms: int
        ) -> TimestampTextData:
    groups = []
    current_group = [frames[0]]

    for item in frames[1:]:
        last_timestamp = current_group[-1][0]
        if item[0] - last_timestamp <= time_limit_ms:
            current_group.append(item)
        else:
            groups.append(current_group)
            current_group = [item]

    groups.append(current_group)

    reduced_frames = []
    for group in groups:
        reduced_frames.append(group[-1])

    return reduced_frames
