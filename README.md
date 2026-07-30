# 📋 Зинаида — Telegram-бот трекер задач

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-orange)](https://aiogram.dev)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Зинаида** — строгая, но добрая виртуальная секретарша в вашем Telegram. Помогает вести список задач, напоминает о дедлайнах, начисляет очки за выполненные дела и комментирует вашу продуктивность с тёплой иронией.

<p align="center">
  <img src="logo.png" alt="Зинаида" width="180">
</p>

---

## Что умеет

| 📝 Разовые задачи | 🔁 Регулярные задания | ⏰ Напоминания |
|---|---|---|
| Дедлайн, название, очки | Каждый день / неделю / N дней | За час до дедлайна |
| Inline-кнопки ✅ ❌ | Защита от повторов | Ежедневная сводка в 10:00 |

| 📊 Геймификация | 🤖 AI-комментарии | 🔒 Доступ |
|---|---|---|
| Очки + 4 уровня | Через VseLLM API | Только владелец |
| Повышение с поздравлением | Fallback на встроенные фразы | Проверка по Telegram ID |

---

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/silvegeno/telegram-bot-zinaida.git
cd telegram-bot-zinaida

# 2. Виртуальное окружение
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux

# 3. Зависимости
pip install -r requirements.txt

# 4. Настроить .env (создать из .env.example)
cp .env.example .env

# 5. Запустить
python bot.py
```

### Переменные окружения (`.env`)

| Переменная | Обязательно | Описание |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен от [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_OWNER_ID` | ✅ | Ваш Telegram ID (через [@userinfobot](https://t.me/userinfobot)) |
| `VSELLM_API_KEY` | ❌ | Ключ API [VseLLM](https://vsellm.ru) для AI-комментариев |
| `VSELLM_MODEL` | ❌ | Модель (по умолчанию `anthropic/claude-fable-5`) |
| `TZ_OFFSET` | ❌ | Смещение часового пояса от UTC (по умолчанию `3` = Москва) |

---

## Команды

| Команда | Действие |
|---|---|
| `/start` | Приветствие от Зинаиды |
| `/menu` | Главное меню |
| `/add` | Добавить задачу (число + время через точку `10.00`) |
| `/add_regular` | Добавить регулярное задание |
| `/tasks` | Список задач + кнопки ✅ Выполнить / ❌ Отменить |
| `/regular` | Регулярные задания + ✅ Выполнено |
| `/profile` | Очки, выполнено задач, уровень |
| `/help` | Справка |

---

## Геймификация

<div align="center">

| Уровень | Очки | Награда за задачу |
|---|---|---|
| 1 | 0–49 | Разовая: **10**, Ежедневная: **5** |
| 2 | 50–99 | Еженедельная: **8** |
| 3 | 100–199 | Интервальная: **10** |
| 4 | 200+ | 💎 Элита |

</div>

---

## Деплой

### Railway (бесплатный тир)
Просто подключите репозиторий — бот запустится автоматически. Порт 8080 уже настроен.

### VPS (screen)
```bash
screen -S zinaida
python bot.py
# Ctrl+A D — отключиться
```

### VPS (systemd)
[Пример unit-файла](deploy/zinaida.service) в папке `deploy/`.

---

## Структура

```
├── bot.py              # Главный файл — aiogram 3, FSM, хендлеры
├── config.py           # .env, токены, TZ
├── csv_storage.py      # CRUD для трёх CSV-файлов
├── keyboards.py        # Reply + inline клавиатуры
├── scheduler.py        # APScheduler: напоминания + ежедневная сводка
├── phrases.py          # 7 категорий fallback-фраз
├── ai_comments.py      # AI через VseLLM API
├── index.html          # Публичная страница проекта
├── brandbook.html      # Брендбук: логотип, цвета, голос
├── logo.png            # Логотип Зинаиды
├── requirements.txt    # 4 зависимости
└── .env.example        # Шаблон переменных окружения
```

## Лицензия

MIT — делайте что хотите, Зинаида не против.
