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

# ===== CONFIGURATION =====

ADMIN_ID = 5269002026  # Remplace par ton identifiant Telegram

CHANNELS = [
    {
        "id": "@academie_trading_pro",
        "name": "🎓📈 Académie du Trading",
        "url": "https://t.me/academie_trading_pro",
    }
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
# ===== MENU PRINCIPAL =====

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📱 MTN", "🟠 Orange"],
        ["👤 Mon compte", "👥 Parrainage"],
        ["🎁 Bonus", "📞 Support"],
    ],
    resize_keyboard=True,
)

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


# ===== MENU PRINCIPAL =====

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💸 Faire un retrait MTN"],
        ["💸 Faire un retrait Orange"],
        ["❓ Comment ça marche"],
        ["👤 Mon compte", "👥 Parrainage"],
        ["🎁 Bonus"],
    ],
    resize_keyboard=True,
)


# ===== MENU =====

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user = update.effective_user

    if text == "💸 Faire un retrait MTN":

        await update.message.reply_text(
            "💸 Retrait MTN\n\n"
            "Pour effectuer un retrait MTN, envoyez :\n\n"
            "📱 Votre numéro MTN\n"
            "💰 Le montant souhaité"
        )


    elif text == "💸 Faire un retrait Orange":

        await update.message.reply_text(
            "💸 Retrait Orange\n\n"
            "Pour effectuer un retrait Orange, envoyez :\n\n"
            "📱 Votre numéro Orange\n"
            "💰 Le montant souhaité"
        )


    elif text == "❓ Comment ça marche":

        await update.message.reply_text(
            "🎉 Gagnez jusqu’à 5 000 FCFA grâce au partage ! 💰\n\n"
            "Invitez vos amis à rejoindre notre bot en partageant votre lien de parrainage personnel.\n\n"
            "✅ Objectif : atteindre le nombre de partages ou de filleuls requis.\n\n"
            "🎁 Récompense : recevez 5 000 FCFA une fois l’objectif atteint et validé.\n\n"
            "🔗 Partagez votre lien dès maintenant et commencez à gagner !\n\n"
            "⚠️ Seuls les partages et les inscriptions valides sont pris en compte. "
            "Toute tentative de fraude entraînera l’annulation des récompenses."
        )


    elif text == "👤 Mon compte":

        cursor.execute(
            "SELECT referrals FROM users WHERE id=?",
            (user.id,)
        )

        result = cursor.fetchone()

        referrals = result[0] if result else 0

        await update.message.reply_text(
            f"👤 Mon compte\n\n"
            f"🆔 ID : {user.id}\n"
            f"👥 Filleuls : {referrals}"
        )


    elif text == "👥 Parrainage":

        bot_username = (await context.bot.get_me()).username

        link = f"https://t.me/{bot_username}?start={user.id}"

        await update.message.reply_text(
            f"👥 Ton lien de parrainage :\n\n{link}"
        )


    elif text == "🎁 Bonus":

        cursor.execute(
            "SELECT referrals FROM users WHERE id=?",
            (user.id,)
        )

        result = cursor.fetchone()

        referrals = result[0] if result else 0

        if referrals >= 20:

            await update.message.reply_text(
                "🎉 Félicitations ! Vous pouvez réclamer votre récompense."
            )

        else:

            reste = 20 - referrals

            await update.message.reply_text(
                f"🎁 Il vous manque encore {reste} filleul(s) pour débloquer votre bonus."
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
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, menu)
)
print("Bot lancé...")

app.run_polling()
