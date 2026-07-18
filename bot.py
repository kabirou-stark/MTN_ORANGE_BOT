import sqlite3
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

# ===== CONFIGURATION =====

ADMIN_ID = 123456789  # Remplace par ton identifiant Telegram

CHANNELS = [
    {
        "id": "@TonCanalMTN",
        "name": "📱 Canal MTN",
        "url": "https://t.me/TonCanalMTN",
    },
    {
        "id": "@TonCanalOrange",
        "name": "🟠 Canal Orange",
        "url": "https://t.me/TonCanalOrange",
    },
]

# ===== BASE DE DONNÉES =====

db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
referrer INTEGER,
referrals INTEGER DEFAULT 0
)
""")

db.commit()


def register_user(user_id, referrer=None):
    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if cursor.fetchone():
        return

    cursor.execute(
        "INSERT INTO users(id,referrer) VALUES(?,?)",
        (user_id, referrer),
    )

    if referrer:
        cursor.execute(
            "UPDATE users SET referrals=referrals+1 WHERE id=?",
            (referrer,),
        )

    db.commit()


# ===== MENU =====

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📱 MTN", "🟠 Orange"],
        ["👤 Mon compte", "👥 Parrainage"],
        ["🎁 Bonus", "📞 Support"],
    ],
    resize_keyboard=True,
)


# ===== /START =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    referrer = None

    if context.args:
        try:
            referrer = int(context.args[0])

            if referrer == user.id:
                referrer = None

        except:
            pass

    register_user(user.id, referrer)

    keyboard = []

    for c in CHANNELS:
        keyboard.append(
            [InlineKeyboardButton(c["name"], url=c["url"])]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "✅ J'ai rejoint",
                callback_data="check",
            )
        ]
    )

    await update.message.reply_text(
        "👋 Bienvenue !\n\n"
        "Avant de continuer, rejoignez tous les canaux ci-dessous puis cliquez sur "
        "« ✅ J'ai rejoint ».",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ===== VÉRIFICATION =====

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user = query.from_user.id

    for channel in CHANNELS:

        member = await context.bot.get_chat_member(
            channel["id"],
            user,
        )

        if member.status in ["left", "kicked"]:

            await query.answer(
                "Vous devez rejoindre tous les canaux.",
                show_alert=True,
            )
            return

    await query.message.reply_text(
        "✅ Vérification réussie !",
        reply_markup=MAIN_MENU,
    )


# ===== LANCEMENT =====

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check, pattern="check"))

print("Bot lancé...")

app.run_polling()
