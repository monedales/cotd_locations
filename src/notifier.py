from dotenv import load_dotenv
import os
import json
import httpx


def get_webhook_url() -> str:
    load_dotenv()
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url is None:
        raise ValueError("The value for DISCORD_WEBHOOK_URL variable is missing.")
    return webhook_url


def send_notification(message: str, image_path: str) -> httpx.Response:
    data = {"content": message}
    text = json.dumps(data)
    url = get_webhook_url()

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    files = {"file": ("screenshot.png", image_bytes, "image/png")}

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


if __name__ == "__main__":
    result = send_notification("Testando o webhook!", "../media/screenshots/2026-08-28/screenshots/71000.png")
    print(f"Enviado com sucesso! Status: {result.status_code}")
