from dotenv import load_dotenv
import os
import json
import httpx

from consts import MONSTER_LOCATIONS_DIR, MONSTER_REFERENCE_IMAGE
from data_types import MapData


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
        with open(image_path, "rb") as f:
            image_bytes = f.read()
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


def notify_monster(map_data: MapData, event_image_paths: list[str]) -> httpx.Response:
    map_name, monster_name = map_data

    sorted_paths = sorted(event_image_paths)
    context_path, main_path = sorted_paths

    reference_filename = MONSTER_REFERENCE_IMAGE[monster_name]
    reference_path = f"{MONSTER_LOCATIONS_DIR}/{reference_filename}"

    message = f"{map_name} - {monster_name}"
    image_paths = [reference_path, context_path, main_path]

    return send_notification(message, image_paths)


if __name__ == "__main__":
    result = send_notification(
        "Testando o webhook!",
        ["../media/screenshots/2026-08-28/screenshots/71000.png"],
    )
    print(f"Enviado com sucesso! Status: {result.status_code}")
