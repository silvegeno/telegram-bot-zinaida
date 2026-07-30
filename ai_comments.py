"""AI-генератор ироничных комментариев Зинаиды через VseLLM API."""

import datetime as dt
import httpx

from config import VSELLM_API_KEY, VSELLM_MODEL, VSELLM_BASE_URL, AI_ENABLED
from phrases import random_phrase

_WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
_TODAY = dt.date.today()

SYSTEM_PROMPT = (
    f"Ты — Зинаида, виртуальная секретарша в Telegram-боте трекера задач. "
    f"Тебя зовут Зинаида. Ты — строгая, но добрая женщина в возрасте, "
    f"которая ведёт картотеку дел своего подопечного. "
    f"Сегодня {_TODAY.strftime('%d.%m.%Y')}, {_WEEKDAYS[_TODAY.weekday()]}. "
    "Твои сообщения — короткие, остроумные, с лёгкой иронией и доброжелательностью. "
    "Никаких оскорблений, грубости, давления или насмешек над личностью пользователя. "
    "Ирония должна быть тёплой, как у старого друга, который немного устал "
    "напоминать тебе про дела. Отвечай на русском языке, 1-3 предложения."
)


async def generate_comment(ctx: str, fallback_category: str) -> str:
    """Сгенерировать AI-комментарий или вернуть fallback-фразу.
    
    ctx — описание ситуации (например, «задача выполнена, 10 очков»).
    fallback_category — категория фраз на случай недоступности AI.
    """
    if not AI_ENABLED:
        return random_phrase(fallback_category)

    print(f"[AI] Запрос к {VSELLM_MODEL}...")
    try:
        async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
            resp = await client.post(
                f"{VSELLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {VSELLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": VSELLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": ctx},
                    ],
                    "max_tokens": 120,
                    "temperature": 0.9,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                print(f"[AI] Ответ: {content[:80]}...")
                return content.strip()
            else:
                print(f"[AI] HTTP {resp.status_code}: {resp.text[:300]}")
                return random_phrase(fallback_category)
    except Exception as e:
        print(f"[AI] Ошибка ({type(e).__name__}): {e}")
        return random_phrase(fallback_category)
