import json

from consts import MAP_MONSTER_ORDER, SPOT_TABLE_PATH
from exceptions import SpotTableError


def get_spot_for_map(
    map_index: int,
    date_str: str,
    table_path: str = SPOT_TABLE_PATH,
) -> int:
    with open(table_path, "r") as f:
        table = json.load(f)

    if date_str not in table:
        raise SpotTableError(
            f"Data '{date_str}' não encontrada em '{table_path}'."
        )

    code = table[date_str]
    if len(code) != len(MAP_MONSTER_ORDER):
        raise SpotTableError(
            f"Código de spots de '{date_str}' tem {len(code)} dígitos, "
            f"esperado {len(MAP_MONSTER_ORDER)}: '{code}'."
        )

    digit = code[map_index]
    try:
        return int(digit)
    except ValueError as exc:
        raise SpotTableError(
            f"Dígito inválido na posição {map_index} do código "
            f"'{code}' ({date_str}): '{digit}'."
        ) from exc
