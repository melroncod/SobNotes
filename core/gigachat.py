import httpx
from config import creds, client_secret

API_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

async def generate_note_with_gigachat(query: str) -> tuple[str, str]:
    """
    Генерирует развернутый Markdown-ответ по запросу через GigaChat.
    Возвращает (title, body), где title == query, body == Markdown-текст.
    """
    if not creds or not client_secret:
        raise RuntimeError(
            "Не заданы параметры в config.py: creds и client_secret обязательны."
        )

    # Промпт
    user_prompt = (
        "Ты эксперт в области IT-технологий и программирования. "
        f"Дай кратко и по делу ответ, что это такое, где применяется и тд в формате Markdown на запрос: «{query}»"
    )

    # 1) Получаем OAuth-токен
    payload = 'scope=GIGACHAT_API_PERS'
    oauth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': client_secret,
        'Authorization': f'Basic {creds}',
    }
    async with httpx.AsyncClient(verify=False) as client:
        auth = await client.post(API_OAUTH_URL, headers=oauth_headers, data=payload, timeout=30.0)
        auth.raise_for_status()
        token = auth.json().get('access_token')
        if not token:
            raise RuntimeError("GigaChat: не удалось получить access_token")

        # 2) Запрашиваем генерацию текста
        chat_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'RqUID': client_secret,
            'Authorization': f'Bearer {token}',
        }
        payload_json = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": user_prompt}]
        }
        resp = await client.post(API_CHAT_URL, headers=chat_headers, json=payload_json, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()

    # Берём весь ответ как Markdown
    content = data.get('choices', [])[0].get('message', {}).get('content', '')
    title = query.strip()
    body = content.strip()

    return title, body
