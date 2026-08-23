from consts import TIME_LIMIT_MS
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
    extract_monsters_locations,
    save_monster_locations,
)


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
    video_path = download_video("https://www.youtube.com/watch?v=1ihlsS2nX48")
    print(video_path)
    found_frames = find_monsters_frames(video_path, 80500, 500)
    save_debug_crops(video_path, found_frames)
    filtered_frames = filter_frames_with_text(video_path, found_frames)
    print(f"Antes do filtro: {len(found_frames)}")
    print(f"Depois do filtro: {len(filtered_frames)}")

    reduced_frames = reduce_duplicates(filtered_frames, TIME_LIMIT_MS)
    print(f"Depois do agrupamento: {len(reduced_frames)}")

    reduced_for_crop = []
    for item in reduced_frames:
        reduced_for_crop.append((item[0], item[1]))
    save_debug_crops(video_path, reduced_for_crop, subfolder="final")

    monster_locations = extract_monsters_locations(video_path, reduced_frames)
    save_monster_locations(video_path, monster_locations, subfolder="screenshots")

    for item in reduced_frames:
        print(item)
