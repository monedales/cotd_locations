from typing import TypeAlias

from numpy import ndarray

Rect: TypeAlias = tuple[int, int, int, int]
TimestampData: TypeAlias = list[tuple[int, Rect]]
TimestampTextData: TypeAlias = list[tuple[int, Rect, str]]
TimestampImageData: TypeAlias = list[tuple[int, ndarray]]
