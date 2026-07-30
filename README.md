# Telegram-бот «Ироничная секретарша»

Трекер задач с геймификацией для Telegram. Бот помогает добавлять задачи, отмечать выполнение, получать очки и уровни — всё с ироничными комментариями виртуальной секретарши.

## Возможности

- 📝 Добавление разовых задач с дедлайном
- 🔁 Регулярные задания: каждый день, раз в неделю, раз в N дней
- ✅ Отметка выполнения с начислением очков
- 📊 Система уровней (1–4) в зависимости от набранных очков
- ⏰ Напоминание за час до дедлайна
- 📋 Ежедневная рассылка регулярных заданий в 10:00
- 🤖 Ироничные комментарии через ИИ (VseLLM API)
- 🔒 Доступ только для владельца (по Telegram ID)

## Требования

- Python 3.12 или новее
- Telegram-токен от [BotFather](https://t.me/BotFather)

## Установка

### 1. Клонирование / копирование проекта

Скопируйте папку `simple_secretary_bot/` на компьютер или VPS.

### 2. Создание виртуального окружения

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Создание Telegram-бота через BotFather

1. Откройте [BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Придумайте имя бота (например: «Ироничная секретарша»)
4. Придумайте username бота (должен заканчиваться на `bot`)
5. **Сохраните полученный токен** — он понадобится для `.env`

Узнать свой Telegram ID можно через бота [@userinfobot](https://t.me/userinfobot).

### 5. Настройка `.env`

Создайте файл `.env` на основе `.env.example`:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_OWNER_ID=795375565
VSELLM_API_KEY=your_api_key
VSELLM_MODEL=anthropic/claude-fable-5
VSELLM_BASE_URL=https://api.vsellm.ru/v1
```

- `TELEGRAM_BOT_TOKEN` — токен, полученный от BotFather
- `TELEGRAM_OWNER_ID` — ваш Telegram ID
- `VSELLM_API_KEY` — ключ API VseLLM для AI-комментариев (опционально; если не указан, используются встроенные фразы)

### 6. Запуск

```bash
python bot.py
```

Бот запустится и будет работать пока открыт терминал. На VPS используйте `screen` или `systemd` для фонового запуска.

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота, приветствие |
| `/menu` | Главное меню |
| `/add` | Добавить разовую задачу |
| `/add_regular` | Добавить регулярное задание |
| `/tasks` | Список активных задач |
| `/regular` | Список регулярных заданий |
| `/profile` | Профиль, очки, уровень |
| `/help` | Справка |

## Геймификация

- За выполнение разовой задачи: **10 очков**
- За выполнение ежедневного задания: **5 очков**
- За выполнение еженедельного: **8 очков**
- За выполнение с интервалом: **10 очков**

Уровни:
- Уровень 1: 0–49 очков
- Уровень 2: 50–99 очков
- Уровень 3: 100–199 очков
- Уровень 4: 200+ очков

## Формат CSV-файлов

### tasks.csv
```
id,title,deadline,status,created_at,completed_at,reward,reminder_sent
```

### recurring_tasks.csv
```
id,title,period_type,period_value,last_completed,status,reward
```

### profile.csv
```
telegram_id,name,points,completed_tasks
```

Все файлы создаются автоматически при первом запуске.

## Структура проекта

```
today/
├── bot.py              # Главный файл бота
├── config.py           # Конфигурация (токены, пути)
├── csv_storage.py      # Работа с CSV-хранилищем
├── keyboards.py        # Клавиатуры (reply + inline)
├── scheduler.py        # Планировщик напоминаний (APScheduler)
├── phrases.py          # Встроенные ироничные фразы
├── ai_comments.py      # AI-генерация комментариев (VseLLM)
├── requirements.txt    # Зависимости Python
├── .env.example        # Пример файла .env
└── README.md           # Этот файл
```
