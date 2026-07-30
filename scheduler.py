"""Планировщик: напоминания и ежедневная рассылка."""

import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import OWNER_ID
from csv_storage import (
    get_tasks_needing_reminder,
    mark_reminder_sent,
    get_today_recurring,
)
from phrases import random_phrase
import ai_comments

scheduler = AsyncIOScheduler()


async def _send_to_bot(bot, text: str) -> None:
    """Отправить сообщение владельцу."""
    try:
        await bot.send_message(OWNER_ID, text)
    except Exception as e:
        print(f"[Scheduler] Ошибка отправки: {e}")


async def _check_reminders(bot):
    """Проверить задачи с дедлайном < 1 час."""
    tasks = get_tasks_needing_reminder()
    for task in tasks:
        task_name = task["title"]
        comment = await ai_comments.generate_comment(
            f"До задачи «{task_name}» осталось меньше часа.",
            "reminder",
        )
        msg = f"⏰ До задачи «{task_name}» осталось меньше часа.\n{comment}"
        await _send_to_bot(bot, msg)
        mark_reminder_sent(task["id"])


async def _daily_recurring(bot):
    """Ежедневная рассылка регулярных заданий в 10:00."""
    tasks = get_today_recurring()
    if not tasks:
        return
    task_list = "\n".join(f"— {t['title']}" for t in tasks)
    comment = await ai_comments.generate_comment(
        f"Регулярные задания на сегодня: {', '.join(t['title'] for t in tasks)}",
        "daily_recurring",
    )
    msg = (
        f"📋 Регулярные задания на сегодня:\n{task_list}\n\n{comment}"
    )
    await _send_to_bot(bot, msg)


def start_scheduler(bot):
    """Запустить планировщик с задачами."""
    # Проверка напоминаний каждую минуту
    scheduler.add_job(
        _check_reminders,
        "interval",
        minutes=1,
        args=[bot],
        id="reminders",
        replace_existing=True,
    )
    # Ежедневная рассылка в 10:00
    scheduler.add_job(
        _daily_recurring,
        "cron",
        hour=10,
        minute=0,
        args=[bot],
        id="daily_recurring",
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] Запущен (интервал 1 мин + ежедневно в 10:00)")
