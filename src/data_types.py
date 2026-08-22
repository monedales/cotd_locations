from typing import TypeAlias

Rect: TypeAlias = tuple[int, int, int, int]
TimestampData: TypeAlias = list[tuple[int, Rect]]
TimestampTextData: TypeAlias = list[tuple[int, Rect, str]]
