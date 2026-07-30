"""Клавиатуры для телеграм-бота «Ироничная секретарша»."""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from csv_storage import get_active_tasks, get_active_recurring


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню — reply-клавиатура."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить задачу"),
             KeyboardButton(text="Добавить регулярную")],
            [KeyboardButton(text="Мои задачи"),
             KeyboardButton(text="Регулярные задания")],
            [KeyboardButton(text="Профиль"),
             KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True,
    )


def tasks_inline_kb() -> InlineKeyboardMarkup | None:
    """Inline-клавиатура для списка задач: Выполнить / Отменить."""
    tasks = get_active_tasks()
    if not tasks:
        return None
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for t in tasks:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"✅ Выполнить №{t['id']}",
                callback_data=f"done_{t['id']}",
            ),
            InlineKeyboardButton(
                text=f"❌ Отменить №{t['id']}",
                callback_data=f"cancel_{t['id']}",
            ),
        ])
    return kb


def recurring_inline_kb() -> InlineKeyboardMarkup | None:
    """Inline-клавиатура для регулярных заданий."""
    tasks = get_active_recurring()
    if not tasks:
        return None
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for t in tasks:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"✅ Выполнено №{t['id']}",
                callback_data=f"rdone_{t['id']}",
            ),
        ])
    return kb
