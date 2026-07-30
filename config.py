#!/usr/bin/env python3
"""Трекер задач «Ироничная секретарша» — конфигурация."""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_ID: int = int(os.getenv("TELEGRAM_OWNER_ID", "0"))

VSELLM_API_KEY: str = os.getenv("VSELLM_API_KEY", "")
VSELLM_MODEL: str = os.getenv("VSELLM_MODEL", "xiaomi/mimo-v2.5")
VSELLM_BASE_URL: str = os.getenv("VSELLM_BASE_URL", "https://api.vsellm.ru/v1")

AI_ENABLED: bool = bool(VSELLM_API_KEY)

# Пути к CSV-файлам (в одной папке с ботом)
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
TASKS_CSV: str = os.path.join(BASE_DIR, "tasks.csv")
RECURRING_CSV: str = os.path.join(BASE_DIR, "recurring_tasks.csv")
PROFILE_CSV: str = os.path.join(BASE_DIR, "profile.csv")
