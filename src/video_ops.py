import cv2  # type: ignore
import yt_dlp
from datetime import datetime, timedelta
import os
import re
from loguru import logger

from consts import (
    MS_PER_SECOND,
    MIN_TEXT_LENGTH,
    BALLOON_ROI_X1,
    BALLOON_ROI_Y1,
    BALLOON_ROI_X2,
    BALLOON_ROI_Y2,
    SCREENSHOTS_DIR,
    VIDEO_FOLDER_NAME_PATTERN,
    MAP_MONSTER_ORDER
)
from data_types import TimestampData, TimestampTextData, TimestampImageData, TimestampMapData
from exceptions import InsufficientEventsError, VideoDownloadError
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
            for inner_entry in os.listdir(entry_path):
                inner_path = os.path.join(entry_path, inner_entry)
                if os.path.isfile(inner_path):
                    os.remove(inner_path)


def download_video(url: str) -> str:
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise VideoDownloadError(
            f"Falha ao consultar metadados do vídeo '{url}'.\n"
            f"Erro original: {exc}"
        ) from exc

    original_data = info.get("upload_date")
    if original_data is None:
        raise VideoDownloadError(
            f"O vídeo '{url}' não possui data de upload disponível nos "
            f"metadados retornados pelo yt-dlp."
        )
    format_data = datetime.strptime(original_data, "%Y%m%d")
    new_data = format_data + timedelta(days=1)
    date_str = new_data.strftime("%Y-%m-%d")

    output_path = ("../media/videos/" + date_str + ".mp4")

    options = {
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "merge_output_format": "mp4",
        "outtmpl": "../media/videos/" + date_str + ".%(ext)s",
    }
    if not os.path.exists(output_path):
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except yt_dlp.utils.DownloadError as exc:
            raise VideoDownloadError(
                f"Falha ao baixar o vídeo '{url}'.\n"
                f"Erro original: {exc}"
            ) from exc

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
        if not succeed:
            logger.warning(
                f"Falha ao ler o frame em {current_ms}ms do vídeo "
                f"'{video_path}' durante a varredura. Pulando."
            )
            current_ms = current_ms + intval_ms
            continue
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
            logger.warning(
                f"Falha ao ler o frame em {timestamp_ms}ms do vídeo "
                f"'{video_path}' durante o filtro de texto. Pulando."
            )
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
            logger.warning(
                f"Falha ao ler o frame em {timestamp_ms}ms do vídeo "
                f"'{video_path}' ao salvar recorte de debug. Pulando."
            )
            continue
        x, y, width, height = rect
        crop = crop_fixed_region(frame, y, y + height, x, x + width)
        filename = f"{output_dir}/{timestamp_ms}.png"
        cv2.imwrite(filename, crop)
    capture.release()


def extract_monsters_locations(
        video_path: str,
        frames: TimestampTextData,
        context_ms: int
        ) -> TimestampImageData:
    capture = cv2.VideoCapture(video_path)
    locations = []
    for timestamp_ms, _rect, _text in frames:
        context_timestamp_ms = timestamp_ms - context_ms
        capture.set(cv2.CAP_PROP_POS_MSEC, context_timestamp_ms)
        succeed, context_frame = capture.read()
        if succeed:
            locations.append((context_timestamp_ms, context_frame))
        else:
            logger.warning(
                f"Falha ao ler o frame de contexto em "
                f"{context_timestamp_ms}ms do vídeo '{video_path}'. "
                f"Notificação seguirá sem a imagem de contexto deste evento."
            )
        capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
        succeed, frame = capture.read()
        if not succeed:
            logger.error(
                f"Falha ao ler o frame principal em {timestamp_ms}ms do "
                f"vídeo '{video_path}'. Este evento não terá screenshot "
                f"final para notificação."
            )
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


def separate_monsters_group(frames: TimestampTextData,
                            monsters: int) -> TimestampTextData:
    len_list = len(frames)
    if len_list < monsters:
        raise InsufficientEventsError(
            f"Eram esperados pelo menos {monsters} eventos para separar "
            f"por mapa, mas só {len_list} foram encontrados após o "
            f"filtro e a deduplicação."
        )
    time_gap = []
    for i in range(1, len_list):
        gap = frames[i][0] - frames[i-1][0]
        time_gap.append((gap, i))
    sorted_gaps = sorted(time_gap, reverse=True)
    cuts = monsters - 1
    top_gaps = sorted_gaps[:cuts]
    cut_pos = []
    for item in top_gaps:
        cut_pos.append(item[1])
    sorted_cut_pos = sorted(cut_pos)
    boundaries = [0] + sorted_cut_pos + [len_list]
    groups = []
    for idx in range(monsters):
        start = boundaries[idx]
        end = boundaries[idx + 1]
        piece = frames[start:end]
        groups.append(piece)
    final_frames = []
    for group in groups:
        final_frames.append(group[-1])
    return final_frames


def assign_monsters_map(frames: TimestampTextData) -> TimestampMapData:
    result = []
    for i, item in enumerate(frames):
        map_data = MAP_MONSTER_ORDER[i]
        timestamp, rect, text = item
        result.append((timestamp, rect, text, map_data))
    return result
