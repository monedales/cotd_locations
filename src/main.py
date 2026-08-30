from consts import TIME_LIMIT_MS, CONTEXT_MS, VIDEO_URL
from image_ops import (
    load_image_grayscale,
    find_contours_from_grayscale,
    find_balloon_rect,
    show_image,
    extract_balloon_text,
)
from video_ops import (
    clean_debug_screenshots,
    download_video,
    find_monsters_frames,
    save_debug_crops,
    filter_frames_with_text,
    reduce_duplicates,
    separate_monsters_group,
    assign_monsters_map,
    extract_monsters_locations,
    save_monster_locations,
)
from notifier import notify_monster
import os


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


if __name__ == "__main__":
    # run_pipeline("../media/screenshots/message-coco.png")
    clean_debug_screenshots()
    video_path = download_video(VIDEO_URL)
    print(video_path)
    found_frames = find_monsters_frames(video_path, 80500, 500)
    save_debug_crops(video_path, found_frames)
    filtered_frames = filter_frames_with_text(video_path, found_frames)
    print(f"Antes do filtro: {len(found_frames)}")
    print(f"Depois do filtro: {len(filtered_frames)}")

    reduced_frames = reduce_duplicates(filtered_frames, TIME_LIMIT_MS)
    print(f"Depois do agrupamento: {len(reduced_frames)}")

    separated_frames = separate_monsters_group(reduced_frames, 8)
    print(f"Depois da separação por mapa: {len(separated_frames)}")

    mapped_frames = assign_monsters_map(separated_frames)
    print("Associação mapa/monstro:")
    for item in mapped_frames:
        print(item)

    reduced_for_crop = []
    for item in separated_frames:
        reduced_for_crop.append((item[0], item[1]))
    save_debug_crops(video_path, reduced_for_crop, subfolder="final")

    monster_locations = extract_monsters_locations(
        video_path, separated_frames, CONTEXT_MS
    )
    save_monster_locations(video_path, monster_locations,
                           subfolder="screenshots")

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    screenshots_dir = f"../media/screenshots/{video_name}/screenshots"

    for index, item in enumerate(mapped_frames):
        timestamp, rect, text, map_data = item

        context_pos = index * 2
        main_pos = index * 2 + 1

        context_timestamp = monster_locations[context_pos][0]
        main_timestamp = monster_locations[main_pos][0]

        context_path = f"{screenshots_dir}/{context_timestamp}.png"
        main_path = f"{screenshots_dir}/{main_timestamp}.png"

        notify_monster(map_data, [context_path, main_path], index, video_name)
