# 🐟 Creatures of the Deep: Monster Location Notifier

## Description

Python pipeline that detects the monster reveal moment on each of the
game's 8 maps from the daily video posted on Browind's YouTube channel,
and prepares ready-to-send screenshots plus map and monster
identification for a Discord notification to a game clan, without
anyone needing to watch the full video.

## Instructions

### Dependencies

- Python 3.14
- Homebrew packages: `tesseract`, `ffmpeg`

### Setup

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install tesseract ffmpeg
cp .env.example .env
```

Fill in `DISCORD_WEBHOOK_URL` in `.env` with your webhook URL.

### Running

```bash
cd src
python3.14 main.py
```

## Project Structure

```
cotd_locations/
├── src/
│   ├── main.py            entry point: runs the full pipeline
│   ├── video_ops.py       download, scanning, dedup, map assignment
│   ├── image_ops.py       generic image ops (crop, contours, OCR)
│   ├── notifier.py        Discord webhook notification
│   ├── spot_table.py      daily spot lookup from community data
│   ├── exceptions.py      pipeline-specific exception hierarchy
│   ├── data_types.py      shared type aliases
│   └── consts.py          calibration constants
│
├── tools/
│   ├── debug_roi.py       ROI/contour calibration helper
│   └── debug_video_info.py   inspects yt-dlp metadata without
│                              downloading the video
│
└── data/
    └── spot_table.json    daily monster-spot codes shared by the
                            community
```

## Pipeline

### Detection & extraction

```mermaid
flowchart TD
    A["download_video(url)"] --> B["find_monsters_frames<br/>(geometric detection in the ROI)"]
    B --> C["filter_frames_with_text<br/>(OCR text filter)"]
    C --> D["reduce_duplicates<br/>(time-proximity dedup)"]
    D --> E["separate_monsters_group<br/>(split at the largest gaps)"]
    E --> F["assign_monsters_map<br/>(sequential map/monster assignment)"]
    F --> G["extract_monsters_locations<br/>(balloon + context screenshot)"]
    G --> H["save_monster_locations<br/>(saved to disk)"]

    style A fill:#ece4f7,color:#3b2a54
    style H fill:#ece4f7,color:#3b2a54
```

### Notification

```mermaid
flowchart TD
    I["notify_monster<br/>(map, monster, screenshots)"] --> J["get_spot_for_map<br/>(daily spot lookup)"]
    J --> K["send_notification<br/>(posts to Discord webhook)"]

    style I fill:#ece4f7,color:#3b2a54
    style K fill:#ece4f7,color:#3b2a54
```

## Glossary

- **yt-dlp**: command-line tool (used here as a Python library) to
  download videos from YouTube; also used to fetch video metadata,
  like the upload date, without downloading the file
- **OCR (Optical Character Recognition)**: technology that reads text
  from images (used here via Tesseract, to read the balloon message)
- **ROI (Region of Interest)**: a fixed region of the screen where the
  search is restricted, to avoid false positives from unrelated areas
- **Geometric detection**: finding shapes in an image based on contour
  size and proportion, without relying on fixed pixel coordinates
- **Threshold (binary thresholding)**: converting a grayscale image
  into pure black-and-white, based on a brightness cutoff, to simplify
  shape detection
- **Deduplication**: removing repeated detections of the same
  real-world event, so only one representative screenshot per map is
  kept
- **Webhook**: a URL that lets an external app post directly into a
  specific Discord channel, without needing a full bot setup

## Resources

- [OpenCV](https://opencv.org/): geometric detection, image processing
- [Tesseract](https://github.com/tesseract-ocr/tesseract) /
  [pytesseract](https://github.com/madmaze/pytesseract): OCR
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): video download
- [ffmpeg](https://ffmpeg.org/): video and audio handling
- [httpx](https://www.python-httpx.org/): Discord webhook requests
- [python-dotenv](https://github.com/theskumar/python-dotenv): loads
  secrets (webhook URL) from a local `.env` file
- [loguru](https://github.com/Delgan/loguru): structured logging

## Status

- [x] Environment setup
- [x] Balloon detection (manual crop to geometric detection)
- [x] Video automation (download, OCR filter, deduplication)
- [x] Map/monster assignment by sequential order
- [ ] Refinements (nightly automation)
- [x] Discord integration (validated end-to-end with test server;
      swapping to the clan's real webhook)
- [ ] Automated test suite
