import logging
import random
import time
from datetime import time as dt_time
from zoneinfo import ZoneInfo
from collections import defaultdict

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    PollAnswerHandler, filters, ContextTypes
)

# ========== BOT TOKEN ==========
# Bu yerga o'zingizning bot tokeningizni yozing
TOKEN = "8999046582:AAGTko9xgtVqN791RnBUGL0HFJY5oaLpwd0"

# ========== RUSCHA AVTO SAVOLLAR ==========
QUESTIONS = [
    {
        "question": "Какой автомобиль считается самым продаваемым в мире за всё время?",
        "options": ["Toyota Corolla", "Volkswagen Golf", "Ford F-Series", "Honda Civic"],
        "correct": 0
    },
    {
        "question": "В каком году был представлен первый серийный автомобиль с двигателем внутреннего сгорания?",
        "options": ["1885", "1901", "1895", "1910"],
        "correct": 0
    },
    {
        "question": "Какая компания производит автомобили под брендом «Лада»?",
        "options": ["ГАЗ", "АвтоВАЗ", "УАЗ", "КамАЗ"],
        "correct": 1
    },
    {
        "question": "Что означает аббревиатура ABS в автомобиле?",
        "options": ["Anti-lock Braking System", "Automatic Brake System", "Advanced Brake Support", "Active Brake System"],
        "correct": 0
    },
    {
        "question": "Какой двигатель обычно имеет более высокий крутящий момент на низких оборотах?",
        "options": ["Бензиновый", "Дизельный", "Электрический", "Роторный"],
        "correct": 1
    },
    {
        "question": "Какая марка автомобиля имеет логотип в виде трёхконечной звезды?",
        "options": ["BMW", "Mercedes-Benz", "Audi", "Porsche"],
        "correct": 1
    },
    {
        "question": "Что такое турбонаддув?",
        "options": ["Система охлаждения", "Система повышения мощности за счёт отработавших газов", "Тип трансмиссии", "Система подвески"],
        "correct": 1
    },
    {
        "question": "Какой автомобиль называют «народным» в Германии?",
        "options": ["BMW 3 Series", "Volkswagen Beetle (Жук)", "Mercedes C-Class", "Opel Astra"],
        "correct": 1
    },
    {
        "question": "Сколько цилиндров обычно имеет рядный двигатель R4?",
        "options": ["2", "4", "6", "8"],
        "correct": 1
    },
    {
        "question": "Что означает полный привод 4WD / AWD?",
        "options": ["Привод только на передние колёса", "Привод на все четыре колеса", "Привод только на задние колёса", "Гибридный привод"],
        "correct": 1
    },
    {
        "question": "Какая компания первой запустила массовое производство электромобилей в XXI веке?",
        "options": ["Nissan", "Tesla", "Chevrolet", "BMW"],
        "correct": 1
    },
    {
        "question": "Что такое ESP в современном автомобиле?",
        "options": ["Система курсовой устойчивости", "Электронная система парковки", "Система экономии топлива", "Система освещения"],
        "correct": 0
    },
]

# Qiziqarli stikerlar
STICKERS = [
    "🚗💨", "🏎️🔥", "🚙✨", "🚘💪", "🚕😎",
    "🚛💥", "🚓🚨", "🛻🔥", "🚌😂", "🏍️💨",
    "🏁🔥", "🔧😎", "🛠️💪", "⚡🚗", "🌪️🚘"
]

TRIGGERS = ["savol yubor", "savol", "викторина", "вопрос", "quiz", "viktorina"]
COOLDOWN = 60  # 1 daqiqa

scores = defaultdict(lambda: defaultdict(int))
active_polls = {}
chat_data = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚗 *Авто-викторина боти*\n\n"
        "• «savol yubor» — савол юборади\n"
        "• /reyting — ҳозирги натижалар\n"
        "• Ҳар куни 22:00 да (Тошкент вақти) Топ-3 эълон қилинади",
        parse_mode="Markdown"
    )


async def reyting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users = scores.get(chat_id, {})

    if not users:
        await update.message.reply_text("Ҳали ҳеч ким балл олмаган.")
        return

    sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "📊 *Ҳозирги рейтинг:*\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (user_id, score) in enumerate(sorted_users):
        try:
            user = await context.bot.get_chat(user_id)
            name = user.first_name or "Номаълум"
        except:
            name = f"ID:{user_id}"

        if i < 3:
            text += f"{medals[i]} {name} — *{score}* балл\n"
        else:
            text += f"{i+1}. {name} — *{score}* балл\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower().strip()
    chat_id = update.effective_chat.id

    if not any(trigger in text for trigger in TRIGGERS):
        return

    now = time.time()

    if chat_id not in chat_data:
        chat_data[chat_id] = {"last_time": 0}

    data = chat_data[chat_id]

    if now - data["last_time"] < COOLDOWN:
        qolgan = int(COOLDOWN - (now - data["last_time"]))
        await update.message.reply_text(f"⏳ Бироз кутинг... Янги савол {qolgan} сониядан кейин.")
        return

    q = random.choice(QUESTIONS)
    data["last_time"] = now

    # Stiker yuborish
    sticker = random.choice(STICKERS)
    await update.message.reply_text(sticker)

    # Poll yuborish
    message = await context.bot.send_poll(
        chat_id=chat_id,
        question=f"❓ {q['question']}",
        options=q["options"],
        is_anonymous=False,
        allows_multiple_answers=False,
        reply_to_message_id=update.message.message_id
    )

    active_polls[message.poll.id] = {
        "chat_id": chat_id,
        "correct": q["correct"]
    }


async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    poll_id = answer.poll_id
    user_id = answer.user.id
    selected = answer.option_ids[0] if answer.option_ids else None

    if poll_id not in active_polls or selected is None:
        return

    poll_info = active_polls[poll_id]
    chat_id = poll_info["chat_id"]
    correct = poll_info["correct"]

    if selected == correct:
        scores[chat_id][user_id] += 1


async def daily_winner(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, users in scores.items():
        if not users:
            continue

        sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)
        top3 = sorted_users[:3]

        if not top3:
            continue

        text = "🏆 *Бугунги якуний натижалар:*\n\n"
        medals = ["🥇", "🥈", "🥉"]

        for i, (user_id, score) in enumerate(top3):
            try:
                user = await context.bot.get_chat(user_id)
                name = user.first_name or "Номаълум"
            except:
                name = f"ID:{user_id}"

            text += f"{medals[i]} {i+1}-ўрин: *{name}* — {score} балл\n"

        text += "\n🎉 Tabriklaymiz barcha ishtirokchilarni!"

        try:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Xato: {e}")

        scores[chat_id].clear()


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reyting", reyting))
    app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_message))
    app.add_handler(PollAnswerHandler(receive_poll_answer))

    # Har kuni 22:00 Toshkent vaqti
    tashkent = ZoneInfo("Asia/Tashkent")
    app.job_queue.run_daily(
        daily_winner,
        time=dt_time(hour=22, minute=0, tzinfo=tashkent),
        name="daily_winner"
    )

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
