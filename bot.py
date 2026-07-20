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
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

# ===== CONFIG =====

ADMIN_ID = 5269002026

CHANNELS = [
    {
        "id": "@academie_trading_pro",
        "name": "🎓📈 Académie du Trading",
        "url": "https://t.me/academie_trading_pro",
    },
    {
        "id": "@leroi5pronos",
        "name": "🔥 Ultras Prono VIP",
        "url": "https://t.me/leroi5pronos",
    }
]

# ===== DATABASE =====

db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer INTEGER,
    referrals INTEGER DEFAULT 0,
    balance INTEGER DEFAULT 0
)
""")

db.commit()

# ===== REGISTER USER =====

def register_user(user_id, referrer=None):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    
    if cursor.fetchone():
        return

    cursor.execute(
        "INSERT INTO users(user_id, referrer) VALUES(?, ?)",
        (user_id, referrer),
    )

    if referrer:
        cursor.execute(
            "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
            (referrer,),
        )

    db.commit()

# ===== MENU =====

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💸 Retrait MTN", "💸 Retrait Orange"],
        ["💸 Retrait USDT"],
        ["💰 Mon solde"],
        ["👤 Mon compte", "👥 Parrainage"],
        ["🎁 Bonus", "❓ Comment ça marche"],
    ],
    resize_keyboard=True,
)

# ===== MENU HANDLER =====

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # récupérer solde
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    solde = result[0] if result else 0

    if text == "💰 Mon solde":
        await update.message.reply_text(f"💰 Solde : {solde} FCFA")

    elif "Retrait" in text:
        if solde < 5000:
            await update.message.reply_text(
                "❌ Solde insuffisant (min 5000 FCFA)"
            )
        else:
            await update.message.reply_text(
                "✅ Envoyez vos infos de retrait"
            )

    elif text == "👤 Mon compte":
        cursor.execute(
            "SELECT referrals FROM users WHERE user_id=?",
            (user_id,),
        )
        referrals = cursor.fetchone()[0]

        await update.message.reply_text(
            f"👤 ID: {user_id}\n👥 Filleuls: {referrals}"
        )

    elif text == "👥 Parrainage":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={user_id}"

        await update.message.reply_text(f"🔗 Ton lien:\n{link}")

    elif text == "🎁 Bonus":
        cursor.execute(
            "SELECT referrals FROM users WHERE user_id=?",
            (user_id,),
        )
        referrals = cursor.fetchone()[0]

        if referrals >= 20:
            await update.message.reply_text("🎉 Bonus débloqué !")
        else:
            await update.message.reply_text(
                f"Il te manque {20 - referrals} filleuls"
            )

    elif text == "❓ Comment ça marche":
        await update.message.reply_text(
            "Invite tes amis et gagne de l'argent 💰"
        )

# ===== START =====

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
        keyboard.append([InlineKeyboardButton(c["name"], url=c["url"])])

    keyboard.append(
        [InlineKeyboardButton("✅ J'ai rejoint", callback_data="check")]
    )

    await update.message.reply_text(
        "👋 Rejoins les canaux puis clique sur le bouton",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ===== CHECK =====

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    for channel in CHANNELS:
        member = await context.bot.get_chat_member(
            channel["id"], user_id
        )

        if member.status in ["left", "kicked"]:
            await query.answer(
                "❌ Rejoins tous les canaux",
                show_alert=True,
            )
            return

    await query.message.reply_text(
        "✅ Accès autorisé",
        reply_markup=MAIN_MENU,
    )

# ===== RUN =====

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check, pattern="check"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

print("Bot lancé 🚀")
app.run_polling()
