import json
import os

from consts import SENT_LOG_PATH


def load_sent_log() -> dict:
    if not os.path.exists(SENT_LOG_PATH):
        return {}
    with open(SENT_LOG_PATH, "r") as f:
        return json.load(f)


def is_already_sent(date_str: str, map_index: int) -> bool:
    log = load_sent_log()
    sent_indexes = log.get(date_str, [])
    return map_index in sent_indexes


def mark_as_sent(date_str: str, map_index: int) -> None:
    log = load_sent_log()
    sent_indexes = log.get(date_str, [])
    if map_index not in sent_indexes:
        sent_indexes.append(map_index)
    log[date_str] = sent_indexes
    with open(SENT_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)
