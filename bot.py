#!/usr/bin/env python3
"""Telegram-бот «Зинаида» — трекер задач с геймификацией и ироничной секретаршей."""

import sys
import os
import asyncio
import calendar
import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, BotCommand,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, OWNER_ID
from csv_storage import (
    ensure_files, get_profile, add_task, get_active_tasks,
    complete_task, cancel_task,
    add_recurring, get_active_recurring, complete_recurring,
    add_points, get_level,
)
from keyboards import (
    main_menu_kb, cancel_kb, tasks_inline_kb, recurring_inline_kb,
)
from phrases import random_phrase, WELCOME_PHRASES
from ai_comments import generate_comment
from scheduler import start_scheduler

# ─── Проверка токена ─────────────────────────────────────
if not BOT_TOKEN:
    print("Ошибка: TELEGRAM_BOT_TOKEN не задан в .env")
    sys.exit(1)

# ─── Инициализация ─────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ─── Состояния FSM ─────────────────────────────────────
class AddTask(StatesGroup):
    waiting_title = State()
    waiting_date = State()
    waiting_time = State()

class AddRegular(StatesGroup):
    waiting_title = State()
    waiting_type = State()
    waiting_day = State()
    waiting_interval = State()

# ─── Проверка владельца ────────────────────────────────
async def is_owner(message: Message) -> bool:
    if message.from_user and message.from_user.id == OWNER_ID:
        return True
    await message.answer("Этот бот работает в закрытом режиме.")
    return False

# ─── Команды бота для меню ─────────────────────────────
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="add", description="Добавить задачу"),
        BotCommand(command="add_regular", description="Добавить регулярную"),
        BotCommand(command="tasks", description="Мои задачи"),
        BotCommand(command="regular", description="Регулярные задания"),
        BotCommand(command="done", description="Выполнить задачу"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)

# ═══════════════  /start  ═════════════════════════════
@dp.message(Command("start"))
async def cmd_start(message: Message):
    if not await is_owner(message):
        return
    ensure_files()
    get_profile(OWNER_ID)
    await message.answer(
        random_phrase("welcome"),
        reply_markup=main_menu_kb(),
    )

# ═══════════════  /menu + кнопка Главное меню ═════════
@dp.message(Command("menu"))
@dp.message(F.text.lower() == "главное меню")
async def cmd_menu(message: Message):
    if not await is_owner(message):
        return
    await message.answer("Главное меню:", reply_markup=main_menu_kb())

# ═══════════════  /help + кнопка Помощь ═══════════════
@dp.message(Command("help"))
@dp.message(F.text.lower() == "помощь")
async def cmd_help(message: Message):
    if not await is_owner(message):
        return
    text = (
        "📖 *Справка*\n\n"
        "*/add* — добавить разовую задачу\n"
        "*/add\\_regular* — добавить регулярное задание\n"
        "*/tasks* — список активных задач\n"
        "*/regular* — регулярные задания\n"
        "*/profile* — профиль и уровень\n"
        "*/help* — эта справка\n\n"
        "*Геймификация:*\n"
        "За выполнение задач начисляются очки.\n"
        "Уровень 1: 0–49 | Уровень 2: 50–99 | "
        "Уровень 3: 100–199 | Уровень 4: 200+\n\n"
        "*Напоминания:*\n"
        "Напоминание за час до дедлайна.\n"
        "Регулярные задания приходят каждый день в 10:00."
    )
    await message.answer(text, parse_mode="Markdown",
                         reply_markup=main_menu_kb())

# ═══════════════  Добавление разовой задачи ════════════
@dp.message(Command("add"))
@dp.message(F.text.lower() == "добавить задачу")
async def add_task_start(message: Message, state: FSMContext):
    if not await is_owner(message):
        return
    await state.set_state(AddTask.waiting_title)
    await message.answer("Что нужно сделать?", reply_markup=cancel_kb())

@dp.message(AddTask.waiting_title, F.text.lower() == "отмена")
async def add_task_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление отменено.", reply_markup=main_menu_kb())

@dp.message(AddTask.waiting_title)
async def add_task_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Что нужно сделать?")
        return
    await state.update_data(title=title)
    await state.set_state(AddTask.waiting_date)
    await message.answer(
        "На какую дату поставить задачу? Введите в формате 30.07.2026.",
        reply_markup=cancel_kb(),
    )

@dp.message(AddTask.waiting_date, F.text.lower() == "отмена")
async def add_task_date_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление отменено.", reply_markup=main_menu_kb())

@dp.message(AddTask.waiting_date)
async def add_task_date(message: Message, state: FSMContext):
    raw = message.text.strip()
    today = datetime.date.today()

    # Полная дата: 30.07.2026
    try:
        dt = datetime.datetime.strptime(raw, "%d.%m.%Y")
    except ValueError:
        # Только число: 30
        try:
            day = int(raw)
        except ValueError:
            await message.answer(
                "Не удалось распознать дату. Введите число (например, 30) "
                "или полную дату в формате 30.07.2026.",
            )
            return

        if day < 1 or day > 31:
            await message.answer("Введите число от 1 до 31.")
            return

        # Ищем подходящий месяц: текущий или следующий
        _, days_cur = calendar.monthrange(today.year, today.month)
        if day >= today.day and day <= days_cur:
            dt = datetime.datetime(today.year, today.month, day)
        else:
            next_m = today.month + 1 if today.month < 12 else 1
            next_y = today.year if today.month < 12 else today.year + 1
            _, days_next = calendar.monthrange(next_y, next_m)
            if day > days_next:
                await message.answer(
                    f"Число {day} не существует в ближайших месяцах. Введите другую дату."
                )
                return
            dt = datetime.datetime(next_y, next_m, day)

    # Не более 30 дней вперёд
    diff = (dt.date() - today).days
    if diff < 0:
        await message.answer("Эта дата уже прошла. Введите будущую дату.")
        return
    if diff > 30:
        await message.answer(
            "Планирование не более чем на 30 дней. Введите дату поближе."
        )
        return

    await state.update_data(deadline_date=dt.strftime("%Y-%m-%d"))
    await state.set_state(AddTask.waiting_time)
    await message.answer(
        f"Дата: {dt.strftime('%d.%m.%Y')}. Во сколько напомнить? Введите в формате 10.00.",
        reply_markup=cancel_kb(),
    )

@dp.message(AddTask.waiting_time, F.text.lower() == "отмена")
async def add_task_time_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление отменено.", reply_markup=main_menu_kb())

@dp.message(AddTask.waiting_time)
async def add_task_time(message: Message, state: FSMContext):
    raw = message.text.strip()
    # Принимаем и двоеточие (10:00) и точку (10.00)
    raw_clean = raw.replace(".", ":")
    try:
        tm = datetime.datetime.strptime(raw_clean, "%H:%M")
    except ValueError:
        await message.answer("Не удалось распознать время. Используйте формат 10.00 или 10:00.")
        return
    data = await state.get_data()
    deadline = f"{data['deadline_date']} {tm.strftime('%H:%M')}"
    task = add_task(data["title"], deadline, reward=10)
    await state.clear()

    comment = await generate_comment(
        f"Пользователь добавил задачу «{task['title']}» до {data['deadline_date']} {raw}",
        "task_created",
    )
    await message.answer(
        f"Задача добавлена.\n"
        f"«{task['title']}» — до {raw}, {data['deadline_date']}.\n\n"
        f"{comment}",
        reply_markup=main_menu_kb(),
    )

# ═══════════════  Добавление регулярной задачи ════════
@dp.message(Command("add_regular"))
@dp.message(F.text.lower() == "добавить регулярную")
async def add_regular_start(message: Message, state: FSMContext):
    if not await is_owner(message):
        return
    await state.set_state(AddRegular.waiting_title)
    await message.answer("Какое регулярное задание добавить?", reply_markup=cancel_kb())

@dp.message(AddRegular.waiting_title, F.text.lower() == "отмена")
async def reg_title_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление отменено.", reply_markup=main_menu_kb())

@dp.message(AddRegular.waiting_title)
async def reg_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Какое задание?")
        return
    await state.update_data(title=title)
    await state.set_state(AddRegular.waiting_type)
    await message.answer(
        "Выберите тип повторения:\n"
        "1 — Каждый день\n"
        "2 — Раз в неделю\n"
        "3 — Раз в несколько дней\n\n"
        "Введите номер варианта:",
        reply_markup=cancel_kb(),
    )

@dp.message(AddRegular.waiting_type, F.text.lower() == "отмена")
async def reg_type_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление отменено.", reply_markup=main_menu_kb())

@dp.message(AddRegular.waiting_type)
async def reg_type(message: Message, state: FSMContext):
    choice = message.text.strip()
    if choice == "1":
        await state.update_data(period_type="daily", period_value="1")
        data = await state.get_data()
        task = add_recurring(data["title"], "daily", "1", reward=5)
        await state.clear()
        comment = await generate_comment(
            f"Добавлено ежедневное задание «{task['title']}»", "task_created")
        await message.answer(
            f"Регулярное задание добавлено: «{task['title']}».\n"
            f"Повторение — каждый день.\n\n{comment}",
            reply_markup=main_menu_kb(),
        )
    elif choice == "2":
        await state.set_state(AddRegular.waiting_day)
        await message.answer(
            "Введите день недели (понедельник, вторник, среда, четверг, пятница, "
            "суббота, воскресенье):",
            reply_markup=cancel_kb(),
        )
    elif choice == "3":
        await state.set_state(AddRegular.waiting_interval)
        await message.answer(
            "Введите число дней (от 2 до 30):",
            reply_markup=cancel_kb(),
        )
    else:
        await message.answer("Введите 1, 2 или 3.")

@dp.message(AddRegular.waiting_day, F.text.lower() == "отмена")
async def reg_day_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление отменено.", reply_markup=main_menu_kb())

@dp.message(AddRegular.waiting_day)
async def reg_day(message: Message, state: FSMContext):
    day = message.text.strip().lower()
    day_map = {
        "понедельник": "monday",
        "вторник": "tuesday",
        "среда": "wednesday",
        "четверг": "thursday",
        "пятница": "friday",
        "суббота": "saturday",
        "воскресенье": "sunday",
    }
    eng = day_map.get(day)
    if not eng:
        await message.answer("Не распознан день недели. Введите, например, «понедельник».")
        return
    data = await state.get_data()
    task = add_recurring(data["title"], "weekly", eng, reward=8)
    await state.clear()
    comment = await generate_comment(
        f"Добавлено еженедельное задание «{task['title']}» на {day}", "task_created")
    await message.answer(
        f"Регулярное задание добавлено: «{task['title']}».\n"
        f"Повторение — каждый {day}.\n\n{comment}",
        reply_markup=main_menu_kb(),
    )

@dp.message(AddRegular.waiting_interval, F.text.lower() == "отмена")
async def reg_interval_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление отменено.", reply_markup=main_menu_kb())

@dp.message(AddRegular.waiting_interval)
async def reg_interval(message: Message, state: FSMContext):
    raw = message.text.strip()
    try:
        days = int(raw)
    except ValueError:
        await message.answer("Введите число от 2 до 30.")
        return
    if days < 2 or days > 30:
        await message.answer("Введите число от 2 до 30.")
        return
    data = await state.get_data()
    task = add_recurring(data["title"], "interval_days", str(days), reward=10)
    await state.clear()
    comment = await generate_comment(
        f"Добавлено задание «{task['title']}» раз в {days} дней", "task_created")
    await message.answer(
        f"Регулярное задание добавлено: «{task['title']}».\n"
        f"Повторение — раз в {days} дней.\n\n{comment}",
        reply_markup=main_menu_kb(),
    )

# ═══════════════  Список задач  ═══════════════════════
@dp.message(Command("tasks"))
@dp.message(F.text.lower() == "мои задачи")
async def cmd_tasks(message: Message):
    if not await is_owner(message):
        return
    tasks = get_active_tasks()
    if not tasks:
        comment = await generate_comment("У пользователя нет активных задач", "empty_list")
        await message.answer(f"Активных задач нет.\n{comment}")
        return
    lines = ["*Активные задачи:*\n"]
    for t in tasks:
        try:
            dl = datetime.datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
            dl_str = dl.strftime("%d.%m.%Y, %H:%M")
        except ValueError:
            dl_str = t["deadline"]
        lines.append(f"*{t['id']}.* {t['title']}\n    До {dl_str}\n")
    text = "\n".join(lines)
    kb = tasks_inline_kb()
    await message.answer(text, parse_mode="Markdown",
                         reply_markup=kb or None)

# ═══════════════  Регулярные задания  ══════════════════
@dp.message(Command("regular"))
@dp.message(F.text.lower() == "регулярные задания")
async def cmd_regular(message: Message):
    if not await is_owner(message):
        return
    regulars = get_active_recurring()
    if not regulars:
        comment = await generate_comment("Нет активных регулярных заданий", "empty_list")
        await message.answer(f"Регулярных заданий нет.\n{comment}")
        return
    lines = ["*Регулярные задания:*\n"]
    for r in regulars:
        pt = r["period_type"]
        if pt == "daily":
            freq = "Каждый день"
        elif pt == "weekly":
            day_map_rev = {
                "monday": "понедельник", "tuesday": "вторник",
                "wednesday": "среда", "thursday": "четверг",
                "friday": "пятница", "saturday": "суббота",
                "sunday": "воскресенье",
            }
            day_name = day_map_rev.get(r["period_value"], r["period_value"])
            freq = f"Каждый {day_name}"
        else:
            freq = f"Раз в {r['period_value']} дней"
        lines.append(
            f"*{r['id']}.* {r['title']}\n"
            f"    {freq}\n"
            f"    Награда: {r['reward']} очков\n"
        )
    text = "\n".join(lines)
    kb = recurring_inline_kb()
    await message.answer(text, parse_mode="Markdown",
                         reply_markup=kb or None)

# ═══════════════  Профиль  ═════════════════════════════
@dp.message(Command("profile"))
@dp.message(F.text.lower() == "профиль")
async def cmd_profile(message: Message):
    if not await is_owner(message):
        return
    profile = get_profile(OWNER_ID)
    points = int(profile.get("points", 0))
    n_completed = int(profile.get("completed_tasks", 0))
    level = get_level(points)

    level_ranges = {
        1: "0–49",
        2: "50–99",
        3: "100–199",
        4: "200+",
    }

    text = (
        f"👤 *Ваш профиль*\n\n"
        f"⭐ Очки: {points}\n"
        f"✅ Выполнено задач: {n_completed}\n"
        f"📊 Уровень: {level} ({level_ranges[level]})\n"
    )
    await message.answer(text, parse_mode="Markdown")

# ═══════════════  Callbacks: задачи ════════════════════
@dp.callback_query(F.data.startswith("done_"))
async def cb_done(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    task_id = int(callback.data.split("_")[1])
    task = complete_task(task_id)
    if task is None:
        await callback.answer("Задача уже выполнена.", show_alert=True)
        return
    reward = int(task.get("reward", 10))
    old_points = int(get_profile(OWNER_ID).get("points", 0))
    old_level = get_level(old_points)
    profile = add_points(OWNER_ID, reward)
    new_points = int(profile.get("points", 0))
    new_level = get_level(new_points)

    comment = await generate_comment(
        f"Задача «{task['title']}» выполнена, начислено {reward} очков", "success")
    text = (
        f"Задача выполнена.\n"
        f"Получено {reward} очков.\n\n"
        f"{comment}"
    )

    if new_level > old_level:
        lvl_comment = await generate_comment(
            f"Пользователь достиг уровня {new_level}", "level_up")
        text += f"\n\n🎉 Новый уровень — {new_level}.\n{lvl_comment}"

    # Обновить сообщение: перегенерировать список
    tasks = get_active_tasks()
    if tasks:
        lines = ["*Активные задачи:*\n"]
        for t in tasks:
            try:
                dl = datetime.datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
                dl_str = dl.strftime("%d.%m.%Y, %H:%M")
            except ValueError:
                dl_str = t["deadline"]
            lines.append(f"*{t['id']}.* {t['title']}\n    До {dl_str}\n")
        new_text = "\n".join(lines)
    else:
        new_text = "Активных задач нет."

    kb = tasks_inline_kb()
    await callback.message.edit_text(
        new_text,
        parse_mode="Markdown",
        reply_markup=kb,
    )
    await callback.answer(text)

@dp.callback_query(F.data.startswith("cancel_"))
async def cb_cancel(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    task_id = int(callback.data.split("_")[1])
    task = cancel_task(task_id)
    if task is None:
        await callback.answer("Задача уже отменена или выполнена.", show_alert=True)
        return

    # Обновить список
    tasks = get_active_tasks()
    if tasks:
        lines = ["*Активные задачи:*\n"]
        for t in tasks:
            try:
                dl = datetime.datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
                dl_str = dl.strftime("%d.%m.%Y, %H:%M")
            except ValueError:
                dl_str = t["deadline"]
            lines.append(f"*{t['id']}.* {t['title']}\n    До {dl_str}\n")
        new_text = "\n".join(lines)
    else:
        new_text = "Активных задач нет."

    kb = tasks_inline_kb()
    await callback.message.edit_text(
        new_text,
        parse_mode="Markdown",
        reply_markup=kb,
    )
    await callback.answer(random_phrase("cancelled"))

# ═══════════════  Callbacks: регулярные ═════════════════
@dp.callback_query(F.data.startswith("rdone_"))
async def cb_rdone(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    task_id = int(callback.data.split("_")[1])
    task = complete_recurring(task_id)
    if task is None:
        await callback.answer(
            "Уже выполнено в этом периоде или не подходит день.",
            show_alert=True,
        )
        return
    reward = int(task.get("reward", 5))
    old_points = int(get_profile(OWNER_ID).get("points", 0))
    old_level = get_level(old_points)
    profile = add_points(OWNER_ID, reward)
    new_points = int(profile.get("points", 0))
    new_level = get_level(new_points)

    comment = await generate_comment(
        f"Регулярное задание «{task['title']}» выполнено, +{reward} очков", "success")
    text = (
        f"«{task['title']}» отмечено как выполненное.\n"
        f"Получено {reward} очков.\n\n"
        f"{comment}"
    )

    if new_level > old_level:
        lvl_comment = await generate_comment(
            f"Пользователь достиг уровня {new_level}", "level_up")
        text += f"\n\n🎉 Новый уровень — {new_level}.\n{lvl_comment}"

    await callback.answer(text)
    # Обновить сообщение со списком регулярных
    remaining = get_active_recurring()
    if remaining:
        lines = ["*Регулярные задания:*\n"]
        for r in remaining:
            pt = r["period_type"]
            if pt == "daily":
                freq = "Каждый день"
            elif pt == "weekly":
                day_map_rev = {
                    "monday": "понедельник", "tuesday": "вторник",
                    "wednesday": "среда", "thursday": "четверг",
                    "friday": "пятница", "saturday": "суббота",
                    "sunday": "воскресенье",
                }
                day_name = day_map_rev.get(r["period_value"], r["period_value"])
                freq = f"Каждый {day_name}"
            else:
                freq = f"Раз в {r['period_value']} дней"
            lines.append(
                f"*{r['id']}.* {r['title']}\n"
                f"    {freq}\n"
                f"    Награда: {r['reward']} очков\n"
            )
        new_text = "\n".join(lines)
    else:
        new_text = "Регулярных заданий нет."

    kb = recurring_inline_kb()
    await callback.message.edit_text(
        new_text,
        parse_mode="Markdown",
        reply_markup=kb,
    )

# ═══════════════  Отмена FSM глобально ═════════════════
@dp.message(F.text.lower() == "отмена")
async def global_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=main_menu_kb())
        return
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_kb())

# ═══════════════  Неизвестные команды ══════════════════
@dp.message()
async def unknown_message(message: Message):
    if not await is_owner(message):
        return
    await message.answer(
        "Я не знаю такой команды. Используйте /help или кнопки меню.",
        reply_markup=main_menu_kb(),
    )

# ═══════════════════════════════════════════════════════
async def main():
    print("[Bot] Запуск «Зинаида»...")
    ensure_files()
    await set_commands(bot)

    # Запускаем планировщик
    start_scheduler(bot)

    # HTTP-сервер для Railway (отдаёт index.html, health-check и favicon)
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.isfile(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index_html = f.read()
    else:
        index_html = "<html><body><h1>Зинаида</h1><p>Трекер задач в Telegram.</p></body></html>"

    async def http_handler(reader, writer):
        try:
            data = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=5)
            request_line = data.split(b"\r\n")[0].decode("utf-8", errors="replace")
            parts = request_line.split(" ")
            path = parts[1] if len(parts) > 1 else "/"

            if path == "/" or path == "/index.html":
                body = index_html
                content_type = "text/html; charset=utf-8"
                status = "200 OK"
            elif path == "/favicon.ico":
                body = ""
                content_type = "image/x-icon"
                status = "204 No Content"
            elif path == "/health":
                body = "OK"
                content_type = "text/plain"
                status = "200 OK"
            else:
                body = index_html
                content_type = "text/html; charset=utf-8"
                status = "200 OK"

            resp = (
                f"HTTP/1.1 {status}\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(body.encode('utf-8'))}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{body}"
            )
            writer.write(resp.encode("utf-8"))
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    http_port = int(os.getenv("PORT", "8080"))
    server = await asyncio.start_server(http_handler, "0.0.0.0", http_port)
    print(f"[HTTP] Страница бота на http://0.0.0.0:{http_port}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
