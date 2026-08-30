from dotenv import load_dotenv
import os
import json
import httpx
from loguru import logger

from consts import MONSTER_LOCATIONS_DIR, MONSTER_REFERENCE_IMAGE
from data_types import MapData
from exceptions import MissingImageError, SpotTableError
from spot_table import get_spot_for_map


def get_webhook_url() -> str:
    load_dotenv()
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url is None:
        raise ValueError("The value for DISCORD_WEBHOOK_URL variable is missing.")
    return webhook_url


def send_notification(message: str, image_paths: list[str]) -> httpx.Response:
    data = {"content": message}
    text = json.dumps(data)
    url = get_webhook_url()

    files = {}
    for index, image_path in enumerate(image_paths):
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        except FileNotFoundError as exc:
            raise MissingImageError(
                f"Imagem não encontrada para a notificação: '{image_path}'."
            ) from exc
        filename = os.path.basename(image_path)
        files[f"files[{index}]"] = (filename, image_bytes, "image/png")

    try:
        response = httpx.post(url, data={"payload_json": text}, files=files)
        response.raise_for_status()
        return response

    except httpx.HTTPStatusError as exc:
        raise ValueError(
            f"Erro de Webhook (HTTP {exc.response.status_code}).\n"
            f"Mensagem enviada: {message}\n"
            f"Resposta do servidor: {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise ValueError(
            f"Falha de conexão com o Webhook.\n"
            f"Mensagem que tentou enviar: {message}\n"
            f"Erro original: {exc}"
        ) from exc


def notify_monster(
    map_data: MapData,
    event_image_paths: list[str],
    map_index: int,
    date_str: str,
) -> httpx.Response:
    map_name, monster_name = map_data

    # quem chama passa na ordem: [contexto, principal]
    context_path, main_path = event_image_paths

    reference_filename = MONSTER_REFERENCE_IMAGE[monster_name]
    reference_path = f"{MONSTER_LOCATIONS_DIR}/{reference_filename}"

    message = f"{map_name} - {monster_name}"
    try:
        spot = get_spot_for_map(map_index, date_str)
        message = f"{message}\nSpot: {spot}"
    except SpotTableError as exc:
        logger.warning(
            f"Não foi possível obter o spot para '{map_name}' em "
            f"'{date_str}'. Notificação seguirá sem subtítulo.\n"
            f"Motivo: {exc.message}"
        )

    image_paths = [main_path, context_path, reference_path]

    return send_notification(message, image_paths)


if __name__ == "__main__":
    result = send_notification(
        "Testando o webhook!",
        ["../media/screenshots/2026-08-28/screenshots/71000.png"],
    )
    print(f"Enviado com sucesso! Status: {result.status_code}")
