"""Хранилище данных на CSV-файлах."""

import csv
import os
import datetime
from collections.abc import Sequence
from typing import Any

from config import TASKS_CSV, RECURRING_CSV, PROFILE_CSV

# ─── поля CSV ────────────────────────────────────────────────
TASK_FIELDS = ["id", "title", "deadline", "status", "created_at",
               "completed_at", "reward", "reminder_sent"]
RECURRING_FIELDS = ["id", "title", "period_type", "period_value",
                    "last_completed", "status", "reward"]
PROFILE_FIELDS = ["telegram_id", "name", "points", "completed_tasks"]


def _ensure_file(path: str, header: Sequence[str]) -> None:
    """Создать файл с заголовком, если его нет."""
    if not os.path.isfile(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()


def _read_all(path: str, fields: Sequence[str]) -> list[dict[str, str]]:
    """Прочитать все строки CSV-файла."""
    _ensure_file(path, fields)
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_all(path: str, fields: Sequence[str],
               rows: list[dict[str, str]]) -> None:
    """Полностью перезаписать CSV-файл."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _next_id(rows: list[dict[str, str]]) -> int:
    if not rows:
        return 1
    return max(int(r.get("id", 0)) for r in rows) + 1


# ═══════════════  Разовые задачи  ═══════════════════════════

def add_task(title: str, deadline_str: str, reward: int = 10) -> dict[str, str]:
    """Добавить разовую задачу."""
    rows = _read_all(TASKS_CSV, TASK_FIELDS)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    task = {
        "id": str(_next_id(rows)),
        "title": title,
        "deadline": deadline_str,
        "status": "active",
        "created_at": now,
        "completed_at": "",
        "reward": str(reward),
        "reminder_sent": "0",
    }
    rows.append(task)
    _write_all(TASKS_CSV, TASK_FIELDS, rows)
    return task


def get_active_tasks() -> list[dict[str, str]]:
    """Получить список активных задач."""
    return [r for r in _read_all(TASKS_CSV, TASK_FIELDS)
            if r.get("status") == "active"]


def get_all_tasks() -> list[dict[str, str]]:
    return _read_all(TASKS_CSV, TASK_FIELDS)


def complete_task(task_id: int) -> dict[str, str] | None:
    """Отметить задачу выполненной. Возвращает None если уже выполнена."""
    rows = _read_all(TASKS_CSV, TASK_FIELDS)
    for row in rows:
        if int(row["id"]) == task_id:
            if row["status"] == "completed":
                return None
            row["status"] = "completed"
            row["completed_at"] = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M")
            _write_all(TASKS_CSV, TASK_FIELDS, rows)
            return row
    return None


def cancel_task(task_id: int) -> dict[str, str] | None:
    """Отменить задачу."""
    rows = _read_all(TASKS_CSV, TASK_FIELDS)
    for row in rows:
        if int(row["id"]) == task_id:
            if row["status"] in ("completed", "cancelled"):
                return None
            row["status"] = "cancelled"
            _write_all(TASKS_CSV, TASK_FIELDS, rows)
            return row
    return None


def get_tasks_needing_reminder() -> list[dict[str, str]]:
    """Задачи, у которых дедлайн < 1 час и reminder_sent == 0."""
    now = datetime.datetime.now()
    threshold = now + datetime.timedelta(hours=1)
    tasks: list[dict[str, str]] = []
    rows = _read_all(TASKS_CSV, TASK_FIELDS)
    for row in rows:
        if row["status"] != "active":
            continue
        if row.get("reminder_sent") == "1":
            continue
        try:
            dl = datetime.datetime.strptime(row["deadline"],
                                            "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if now < dl <= threshold:
            tasks.append(row)
    return tasks


def mark_reminder_sent(task_id: str) -> None:
    rows = _read_all(TASKS_CSV, TASK_FIELDS)
    for row in rows:
        if row["id"] == task_id:
            row["reminder_sent"] = "1"
    _write_all(TASKS_CSV, TASK_FIELDS, rows)


# ═══════════════  Регулярные задачи  ═══════════════════════

def add_recurring(title: str, period_type: str, period_value: str,
                  reward: int = 5) -> dict[str, str]:
    """Добавить регулярную задачу."""
    rows = _read_all(RECURRING_CSV, RECURRING_FIELDS)
    task = {
        "id": str(_next_id(rows)),
        "title": title,
        "period_type": period_type,
        "period_value": period_value,
        "last_completed": "",
        "status": "active",
        "reward": str(reward),
    }
    rows.append(task)
    _write_all(RECURRING_CSV, RECURRING_FIELDS, rows)
    return task


def get_active_recurring() -> list[dict[str, str]]:
    return [r for r in _read_all(RECURRING_CSV, RECURRING_FIELDS)
            if r.get("status") == "active"]


def complete_recurring(task_id: int) -> dict[str, str] | None:
    """Выполнить регулярную задачу.
    Возвращает None если уже выполнена в текущем периоде.
    """
    rows = _read_all(RECURRING_CSV, RECURRING_FIELDS)
    today = datetime.date.today().isoformat()
    for row in rows:
        if int(row["id"]) == task_id:
            pt = row["period_type"]

            # Проверка: нельзя выполнить повторно в тот же период
            if pt == "daily" and row.get("last_completed") == today:
                return None
            if pt == "weekly":
                weekday = datetime.date.today().strftime("%A").lower()
                target = row["period_value"].strip().lower()
                if weekday != target:
                    return None  # сегодня не тот день
                if row.get("last_completed") == today:
                    return None
            if pt == "interval_days":
                if row.get("last_completed") == today:
                    return None
                # interval_days: можно выполнить, если прошло >= N дней
                if row.get("last_completed"):
                    try:
                        last = datetime.date.fromisoformat(
                            row["last_completed"])
                        gap = (datetime.date.today() - last).days
                        if gap < int(row["period_value"]):
                            return None
                    except (ValueError, TypeError):
                        pass

            row["last_completed"] = today
            _write_all(RECURRING_CSV, RECURRING_FIELDS, rows)
            return row
    return None


def get_today_recurring() -> list[dict[str, str]]:
    """Регулярные задания, актуальные на сегодня."""
    today = datetime.date.today()
    weekday = today.strftime("%A").lower()
    result: list[dict[str, str]] = []
    for row in get_active_recurring():
        pt = row["period_type"]
        if pt == "daily":
            result.append(row)
        elif pt == "weekly":
            if row["period_value"].strip().lower() == weekday:
                result.append(row)
        elif pt == "interval_days":
            result.append(row)
    return result


# ═══════════════  Профиль  ═══════════════════════════════

def get_profile(telegram_id: int) -> dict[str, str]:
    """Получить профиль. Создать, если нет."""
    rows = _read_all(PROFILE_CSV, PROFILE_FIELDS)
    for row in rows:
        if row.get("telegram_id") == str(telegram_id):
            return row
    profile = {
        "telegram_id": str(telegram_id),
        "name": "Пользователь",
        "points": "0",
        "completed_tasks": "0",
    }
    rows.append(profile)
    _write_all(PROFILE_CSV, PROFILE_FIELDS, rows)
    return profile


def add_points(telegram_id: int, amount: int) -> dict[str, str]:
    """Начислить очки. Возвращает обновлённый профиль."""
    rows = _read_all(PROFILE_CSV, PROFILE_FIELDS)
    for row in rows:
        if row["telegram_id"] == str(telegram_id):
            row["points"] = str(int(row.get("points", 0)) + amount)
            row["completed_tasks"] = str(
                int(row.get("completed_tasks", 0)) + 1)
            _write_all(PROFILE_CSV, PROFILE_FIELDS, rows)
            return row
    return get_profile(telegram_id)


def get_level(points: int) -> int:
    """Рассчитать уровень по очкам."""
    if points < 50:
        return 1
    if points < 100:
        return 2
    if points < 200:
        return 3
    return 4


def ensure_files() -> None:
    """Создать все CSV-файлы при старте."""
    _ensure_file(TASKS_CSV, TASK_FIELDS)
    _ensure_file(RECURRING_CSV, RECURRING_FIELDS)
    _ensure_file(PROFILE_CSV, PROFILE_FIELDS)
