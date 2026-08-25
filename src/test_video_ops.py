import os

from video_ops import clean_debug_screenshots


def test_removes_files_from_existing_video_folder(tmp_path):
    video_folder = tmp_path / "2026-08-20"
    video_folder.mkdir()
    (video_folder / "80500.png").write_text("fake image data")

    clean_debug_screenshots(str(tmp_path))

    assert video_folder.is_dir()
    assert os.listdir(video_folder) == []


def test_leaves_already_empty_video_folder_untouched(tmp_path):
    video_folder = tmp_path / "2026-08-20"
    video_folder.mkdir()

    clean_debug_screenshots(str(tmp_path))

    assert video_folder.is_dir()
    assert os.listdir(video_folder) == []


def test_does_nothing_when_base_dir_does_not_exist(tmp_path):
    missing_dir = tmp_path / "screenshots"

    clean_debug_screenshots(str(missing_dir))

    assert not missing_dir.exists()


def test_preserves_entries_that_are_not_video_folders(tmp_path):
    video_folder = tmp_path / "2026-08-20"
    video_folder.mkdir()
    (video_folder / "80500.png").write_text("fake image data")

    fixture_file = tmp_path / "message-coco.png"
    fixture_file.write_text("static fixture, not debug output")

    roi_scan_folder = tmp_path / "roi_scan"
    roi_scan_folder.mkdir()
    (roi_scan_folder / "205000.png").write_text("debug_roi.py output")

    clean_debug_screenshots(str(tmp_path))

    assert os.listdir(video_folder) == []
    assert fixture_file.read_text() == "static fixture, not debug output"
    assert os.listdir(roi_scan_folder) == ["205000.png"]


def test_preserves_subfolders_inside_video_folder(tmp_path):
    video_folder = tmp_path / "2026-08-20"
    video_folder.mkdir()
    (video_folder / "80500.png").write_text("raw debug crop")

    final_folder = video_folder / "final"
    final_folder.mkdir()
    (final_folder / "80500.png").write_text("final debug crop")

    screenshots_folder = video_folder / "screenshots"
    screenshots_folder.mkdir()
    (screenshots_folder / "80500.png").write_text("final monster location")

    clean_debug_screenshots(str(tmp_path))

    assert sorted(os.listdir(video_folder)) == ["final", "screenshots"]
    assert (final_folder / "80500.png").read_text() == "final debug crop"
    assert (screenshots_folder / "80500.png").read_text() == \
        "final monster location"
