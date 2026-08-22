from image_ops import (
    load_image_grayscale,
    find_contours_from_grayscale,
    find_balloon_rect,
    show_image,
    extract_balloon_text,
)
from video_ops import (
    download_video,
    find_monsters_frames,
    save_debug_crops,
    filter_frames_with_text,
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
    video_path = download_video("https://www.youtube.com/watch?v=tdHbQSbinhs")
    print(video_path)
    found_frames = find_monsters_frames(video_path, 80500, 500)
    save_debug_crops(video_path, found_frames)
    filtered_frames = filter_frames_with_text(video_path, found_frames)
    print(f"Antes do filtro: {len(found_frames)}")
    print(f"Depois do filtro: {len(filtered_frames)}")
    for item in filtered_frames:
        print(item)
