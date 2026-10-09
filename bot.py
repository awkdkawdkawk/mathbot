"""Telegram-бот з рандомними математичними прикладами (5-9 класи)."""
from __future__ import annotations

import html
import json
import logging
import os
import sys
import threading
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import (
    ChatMember,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ChatType, ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import problems as P

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

TIMEZONE = ZoneInfo("Europe/Kyiv")
SEND_HOURS = (8, 13, 18)
ALL_GRADES = list(P.GRADES)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("mathbot")

HELP_TEXT = """🎓 <b>MATH BOT</b> — твоє щоденне математичне тренування

<i>5–9 класи · 11 тем · 3 повідомлення щодня</i>

━━━━━━━━━━━━━━━━━
🗓 <b>Розклад</b>:  <b>08:00</b> · <b>13:00</b> · <b>18:00</b> (київський час)
Класи чергуються: 5 → 6 → 7 → 8 → 9 → 5 …
━━━━━━━━━━━━━━━━━

<b>Як грати</b>
1️⃣ Приклад приходить за розкладом
2️⃣ Розв'яжи сам — підказка ховається під спойлером
3️⃣ Натисни <b>«Показати відповідь»</b> і звір

<b>Команди</b> (або кнопки знизу):
🧮 приклад зараз  ·  ⚙️ теми і класи
📊 статистика  ·  ⏰ розклад
⏸ стоп  ·  ▶️ старт  ·  ❓ допомога

<i>Просто додай мене в групу — і розсилка стартує сама 🚀</i>"""

BTN_NOW = "🧮 Приклад"
BTN_SETTINGS = "⚙️ Налаштування"
BTN_STATS = "📊 Статистика"
BTN_NEXT = "⏰ Розклад"
BTN_PAUSE = "⏸ Стоп"
BTN_RESUME = "▶️ Старт"
BTN_HELP = "❓ Допомога"
BTN_HIDE = "🙈 Прибрати клавіатуру"

_BUTTON_ACTIONS = {
    BTN_NOW: "now",
    BTN_SETTINGS: "settings",
    BTN_STATS: "stats",
    BTN_NEXT: "next",
    BTN_PAUSE: "pause",
    BTN_RESUME: "resume",
    BTN_HELP: "help",
}


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_NOW, BTN_SETTINGS],
            [BTN_STATS, BTN_NEXT],
            [BTN_PAUSE, BTN_RESUME],
            [BTN_HELP, BTN_HIDE],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

# ---------------------------------------------------------------- storage

def load_data() -> dict:
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            log.exception("Не вдалося прочитати %s, створюю новий", DATA_FILE)
            data = {}
    else:
        data = {}
    data.setdefault("rotation", 0)
    data.setdefault("chats", {})
    return data


def save_data(data: dict) -> None:
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_chat(chat_id: int) -> dict:
    meta = load_data()["chats"].setdefault(str(chat_id), {})
    meta.setdefault("enabled", False)
    meta.setdefault("grades", ALL_GRADES.copy())
    meta.setdefault("topics", list(P.TOPICS))
    meta.setdefault("stats", {"sent": 0, "revealed": 0})
    meta["stats"].setdefault("sent", 0)
    meta["stats"].setdefault("revealed", 0)
    return meta


def update_chat(chat_id: int, mutator) -> dict:
    data = load_data()
    meta = data["chats"].setdefault(str(chat_id), {})
    meta.setdefault("enabled", False)
    meta.setdefault("grades", ALL_GRADES.copy())
    meta.setdefault("topics", list(P.TOPICS))
    meta.setdefault("stats", {"sent": 0, "revealed": 0})
    meta["stats"].setdefault("sent", 0)
    meta["stats"].setdefault("revealed", 0)
    mutator(meta)
    save_data(data)
    return meta


def set_chat_enabled(chat_id: int, enabled: bool) -> None:
    update_chat(chat_id, lambda m: m.__setitem__("enabled", enabled))


def is_chat_enabled(chat_id: int) -> bool:
    return bool(get_chat(chat_id)["enabled"])


def bump_stat(chat_id: int, key: str) -> None:
    def mut(m):
        m["stats"][key] = m["stats"].get(key, 0) + 1
    update_chat(chat_id, mut)


# ---------------------------------------------------------------- schedule

def schedule_chat(job_queue, chat_id: int) -> None:
    for hour in SEND_HOURS:
        name = f"{chat_id}|{hour}"
        if not job_queue.get_jobs_by_name(name):
            job_queue.run_daily(
                send_daily,
                time=time(hour, 0, tzinfo=TIMEZONE),
                data={"chat_id": chat_id},
                name=name,
            )


def unschedule_chat(job_queue, chat_id: int) -> None:
    for hour in SEND_HOURS:
        for job in job_queue.get_jobs_by_name(f"{chat_id}|{hour}"):
            job.schedule_removal()


def _next_slot_text() -> str:
    now = datetime.now(TIMEZONE)
    slots = [now.replace(hour=h, minute=0, second=0, microsecond=0) for h in SEND_HOURS]
    upcoming = next((s for s in slots if s > now), slots[0] + timedelta(days=1))
    return upcoming.strftime("%H:%M")


# ---------------------------------------------------------------- problems

def next_problem(chat_id: int) -> tuple[int, P.Problem]:
    meta = get_chat(chat_id)
    topics = meta["topics"] or list(P.TOPICS)
    allowed = P.grades_for(topics)
    grades = [g for g in meta["grades"] if g in allowed] or list(allowed)

    def mut(m):
        m["rotation"] = m.get("rotation", 0) + 1

    rotation = update_chat(chat_id, mut)["rotation"]
    grade = grades[rotation % len(grades)]
    return grade, P.make_problem(grade, topics)


def render_problem(grade: int, prob: P.Problem, revealed: bool = False) -> str:
    answer = html.escape(prob.answer)
    answer_html = answer if revealed else f"<tg-spoiler>{answer}</tg-spoiler>"
    hint = html.escape(prob.hint)
    fire = "🔥" * prob.difficulty + "○" * (3 - prob.difficulty)
    return (
        f"🧮 <b>MATH BOT</b>  ·  <b>{grade} клас</b>\n"
        f"📚 {html.escape(prob.topic)}  ·  {fire}\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"<blockquote>{html.escape(prob.question)}</blockquote>\n\n"
        f"💡 Підказка: <tg-spoiler>{hint}</tg-spoiler>\n"
        f"✅ Відповідь: {answer_html}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"⏭ Наступний приклад о <b>{_next_slot_text()}</b>"
    )


def _problem_keyboard(chat_id: int, revealed: bool) -> InlineKeyboardMarkup:
    rows = []
    if not revealed:
        rows.append([InlineKeyboardButton("✅ Відповідь", callback_data=f"r|{chat_id}")])
    rows.append([InlineKeyboardButton("🔁 Ще приклад", callback_data=f"m|{chat_id}")])
    return InlineKeyboardMarkup(rows)


# повідомлення, які чекають на розкриття відповіді: (chat_id, message_id) -> (grade, problem)
_PENDING: dict[tuple[int, int], tuple[int, P.Problem]] = {}


async def send_problem(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if len(_PENDING) > 3000:
        _PENDING.clear()
    grade, prob = next_problem(chat_id)
    try:
        msg = await context.bot.send_message(
            chat_id,
            render_problem(grade, prob),
            parse_mode=ParseMode.HTML,
            reply_markup=_problem_keyboard(chat_id, revealed=False),
        )
    except TelegramError as exc:
        log.warning("Не вдалося надіслати в %s: %s", chat_id, exc)
        return False
    _PENDING[(chat_id, msg.message_id)] = (grade, prob)
    bump_stat(chat_id, "sent")
    return True


# ---------------------------------------------------------------- handlers

async def send_daily(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data["chat_id"]
    if not is_chat_enabled(chat_id):
        return
    if not await send_problem(chat_id, context):
        set_chat_enabled(chat_id, False)
        unschedule_chat(context.job_queue, chat_id)
        log.info("Чат %s вимкнено (бот, ймовірно, видалений)", chat_id)


async def _enable(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_chat_enabled(chat_id, True)
    schedule_chat(context.job_queue, chat_id)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    await _enable(chat.id, context)
    await update.message.reply_text(
        HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=main_keyboard()
    )


async def cmd_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    if chat.type != ChatType.PRIVATE and not is_chat_enabled(chat.id):
        await update.message.reply_text(
            "Розсилку вимкнено — натисни ▶️ Старт або /start"
        )
        return
    await send_problem(chat.id, context)


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    set_chat_enabled(chat.id, False)
    unschedule_chat(context.job_queue, chat.id)
    await update.message.reply_text(
        "⏸ <b>Розсилку зупинено</b>\nЩоб повернути — натисни ▶️ Старт",
        parse_mode=ParseMode.HTML,
    )


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    await _enable(chat.id, context)
    await update.message.reply_text(
        "▶️ <b>Розсилку ввімкнено!</b> Ось приклад на тест 👇",
        parse_mode=ParseMode.HTML,
    )
    await send_problem(chat.id, context)


async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    hours = "  ·  ".join(f"<b>{h:02d}:00</b>" for h in SEND_HOURS)
    enabled = is_chat_enabled(update.effective_chat.id)
    status = "🟢 увімкнено" if enabled else "🔴 вимкнено (▶️ Старт)"
    await update.message.reply_text(
        f"⏰ <b>РОЗКЛАД</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{hours}  (київський час)\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"Стан: {status}\n"
        f"⏭ Наступний приклад о <b>{_next_slot_text()}</b>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    meta = get_chat(chat.id)
    stats = meta["stats"]
    grades = " → ".join(str(g) for g in meta["grades"]) or "—"
    topics = len(meta["topics"])
    total = len(P.TOPICS)
    status = "🟢 увімкнено" if meta["enabled"] else "🔴 вимкнено"
    pct = round(stats["revealed"] / stats["sent"] * 100) if stats["sent"] else 0
    await update.message.reply_text(
        f"📊 <b>СТАТИСТИКА ЧАТУ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📨 Надіслано прикладів: <b>{stats['sent']}</b>\n"
        f"👁 Розкрито відповідей: <b>{stats['revealed']}</b> ({pct}%)\n"
        f"🎯 Класи: {grades}\n"
        f"📚 Тем: {topics} з {total}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"Стан: {status}  ·  ⏭ о <b>{_next_slot_text()}</b>\n\n"
        f"⚙️ Змінити теми й класи — кнопка Налаштування",
        parse_mode=ParseMode.HTML,
    )


def _settings_keyboard(meta: dict) -> InlineKeyboardMarkup:
    rows = []
    grade_row = []
    for g in P.GRADES:
        mark = "✅" if g in meta["grades"] else "▫️"
        grade_row.append(
            InlineKeyboardButton(f"{mark} {g}", callback_data=f"g|{g}")
        )
    rows.append(grade_row)
    row = []
    for topic in P.TOPICS:
        mark = "✅" if topic in meta["topics"] else "▫️"
        row.append(InlineKeyboardButton(f"{mark} {topic}", callback_data=f"t|{topic}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("✅ Готово", callback_data="done")])
    return InlineKeyboardMarkup(rows)


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    await _enable(chat.id, context)
    meta = get_chat(chat.id)
    await update.message.reply_text(
        "⚙️ <b>НАЛАШТУВАННЯ</b>\n"
        "━━━━━━━━━━━━━━━━━\n"
        "✅ — увімкнено   ·   ▫️ — вимкнено\n"
        "Натискай кнопки, щоб обрати класи та теми для цього чату 👇",
        parse_mode=ParseMode.HTML,
        reply_markup=_settings_keyboard(meta),
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    parts = data.split("|")
    kind = parts[0]
    chat = query.message.chat if query.message else None
    chat_id = chat.id if chat else None

    if kind == "r" and query.message is not None:
        await query.answer()
        key = (query.message.chat.id, query.message.message_id)
        stored = _PENDING.get(key)
        if stored is None:
            await query.edit_message_reply_markup(reply_markup=None)
            return
        grade, prob = stored
        try:
            await query.edit_message_text(
                render_problem(grade, prob, revealed=True),
                parse_mode=ParseMode.HTML,
                reply_markup=_problem_keyboard(query.message.chat.id, revealed=True),
            )
        except TelegramError:
            pass
        bump_stat(query.message.chat.id, "revealed")
        return

    if kind == "m" and chat_id is not None:
        await query.answer("Ось ще один! 💪")
        await send_problem(chat_id, context)
        return

    if kind in ("g", "t") and chat_id is not None:
        def mut(m):
            if kind == "g":
                g = int(parts[1])
                grades = m["grades"]
                if g in grades:
                    if len(grades) > 1:
                        grades.remove(g)
                elif g not in grades:
                    grades.append(g)
                    grades.sort()
            else:
                topic = parts[1]
                topics = m["topics"]
                if topic in topics:
                    if len(topics) > 1:
                        topics.remove(topic)
                elif topic not in topics:
                    topics.append(topic)

        meta = update_chat(chat_id, mut)
        try:
            await query.edit_message_reply_markup(reply_markup=_settings_keyboard(meta))
        except TelegramError:
            pass
        await query.answer("Оновлено ✅")
        return

    if kind == "done":
        await query.answer("Готово! 🎉")
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except TelegramError:
            pass
        return

    await query.answer()


async def on_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cm = update.my_chat_member
    if cm is None:
        return
    chat_id = cm.chat.id
    status = cm.new_chat_member.status
    if status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
        await _enable(chat_id, context)
        log.info("Бот доданий у чат %s", chat_id)
        try:
            await context.bot.send_message(
                chat_id,
                "🚀 <b>Я тут!</b> Тепер щодня о <b>08:00 · 13:00 · 18:00</b>\n"
                "у цю групу приходитимуть математичні приклади (5–9 класи).\n\n"
                "🧮 Приклад зараз  ·  ⚙️ Теми й класи  ·  📊 Статистика  ·  ⏸ Стоп\n"
                "Натисни <b>/start</b> або кнопку «Приклад», щоб перевірити 👇",
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            pass
    elif status in (ChatMember.LEFT, ChatMember.BANNED):
        set_chat_enabled(chat_id, False)
        unschedule_chat(context.job_queue, chat_id)
        log.info("Бот видалений з чату %s", chat_id)


async def on_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None:
        return
    bot_id = context.bot.id
    for member in message.new_chat_members or []:
        if member.id == bot_id:
            continue
        name = html.escape(member.full_name)
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"Вітаю, {name}! 🎉 Ось тобі приклад для розігріву 👇",
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            continue
        await send_problem(chat.id, context)


async def on_button_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return
    text = message.text.strip()
    action = _BUTTON_ACTIONS.get(text)
    if action == "now":
        await cmd_now(update, context)
    elif action == "settings":
        await cmd_settings(update, context)
    elif action == "stats":
        await cmd_stats(update, context)
    elif action == "next":
        await cmd_next(update, context)
    elif action == "pause":
        await cmd_pause(update, context)
    elif action == "resume":
        await cmd_resume(update, context)
    elif action == "help":
        await message.reply_text(
            HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=main_keyboard()
        )
    elif text == BTN_HIDE:
        await message.reply_text(
            "🙈 Клавіатуру прибрано.\nПовернути: /start",
            reply_markup=ReplyKeyboardRemove(),
        )


async def post_init(app: Application) -> None:
    count = 0
    for chat_id, meta in load_data()["chats"].items():
        if meta.get("enabled", False):
            schedule_chat(app.job_queue, int(chat_id))
            count += 1
    log.info("Заплановано розсилку для %d чатів", count)


# ---------------------------------------------------------------- main

def _load_token() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv(BASE_DIR / ".env")
    except ImportError:
        pass
    token = os.getenv("BOT_TOKEN")
    if not token:
        sys.exit(
            "Задайте токен: створіть файл .env з рядком BOT_TOKEN=... "
            "(приклад у .env.example) або змінну середовища BOT_TOKEN."
        )
    return token


def main() -> None:
    app = (
        Application.builder()
        .token(_load_token())
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler("now", cmd_now))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("next", cmd_next))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_button_text))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(ChatMemberHandler(on_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_members))
    log.info("Бот запущено")
    run_for = int(os.getenv("RUN_FOR_SECONDS", "0"))
    if run_for > 0:
        # режим GitHub Actions: виходимо перед кінцем рану, стан зберігається у data.json
        threading.Timer(run_for, lambda: os._exit(0)).start()
        log.info("Автозавершення через %d с", run_for)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
