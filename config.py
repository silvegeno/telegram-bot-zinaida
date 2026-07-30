#!/usr/bin/env python3
"""Трекер задач «Ироничная секретарша» — конфигурация."""

import os
from datetime import timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = int(os.getenv("TELEGRAM_OWNER_ID", "0"))

VSELLM_API_KEY = os.getenv("VSELLM_API_KEY", "")
VSELLM_MODEL = os.getenv("VSELLM_MODEL", "xiaomi/mimo-v2.5")
VSELLM_BASE_URL = os.getenv("VSELLM_BASE_URL", "https://api.vsellm.ru/v1")

AI_ENABLED = bool(VSELLM_API_KEY)

# Часовой пояс (по умолчанию Москва UTC+3)
TZ_OFFSET_HOURS = int(os.getenv("TZ_OFFSET", "3"))
TZ = timezone(timedelta(hours=TZ_OFFSET_HOURS))

# Пути к CSV-файлам (в одной папке с ботом)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_CSV = os.path.join(BASE_DIR, "tasks.csv")
RECURRING_CSV = os.path.join(BASE_DIR, "recurring_tasks.csv")
PROFILE_CSV = os.path.join(BASE_DIR, "profile.csv")
