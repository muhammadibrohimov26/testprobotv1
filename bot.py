"""
Telegram Ro'yxatdan O'tish Boti
================================
Foydalanuvchilar: Ism, Telefon va Yosh kiritadi.
Ma'lumotlar Google Sheets ga saqlanadi.
"""

import logging
import re
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN
from sheets import add_user_to_sheet

# ── Logging sozlash ──────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Holat konstantalari ──────────────────────────────────────────────────────
ASKING_NAME, ASKING_PHONE, ASKING_AGE = range(3)


# ────────────────────────────────────────────────────────────────────────────
# YORDAMCHI FUNKSIYALAR
# ────────────────────────────────────────────────────────────────────────────

def is_valid_phone(phone: str) -> bool:
    """Telefon raqamini tekshiradi. +998XXXXXXXXX yoki 998XXXXXXXXX."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    pattern = r"^(\+998|998|8)?[0-9]{9,10}$"
    return bool(re.match(pattern, cleaned))


def is_valid_age(age: str) -> bool:
    """Yoshni tekshiradi. 1 dan 120 gacha bo'lishi kerak."""
    if age.isdigit():
        age_int = int(age)
        return 1 <= age_int <= 120
    return False


def format_phone(phone: str) -> str:
    """Telefon raqamini standart formatga keltiradi."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if cleaned.startswith("8") and len(cleaned) == 11:
        cleaned = "+7" + cleaned[1:]
    elif cleaned.startswith("998") and not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    elif not cleaned.startswith("+") and len(cleaned) == 9:
        cleaned = "+998" + cleaned
    return cleaned


# ────────────────────────────────────────────────────────────────────────────
# HANDLER FUNKSIYALAR
# ────────────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bot boshlanishi — /start buyrug'i."""
    user = update.effective_user
    logger.info(f"/start → {user.id} ({user.full_name})")

    # Oldingi ma'lumotlarni tozalash
    context.user_data.clear()

    welcome_text = (
        f"👋 Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
        "🤖 Ushbu bot orqali <b>ro'yxatdan o'tishingiz</b> mumkin.\n\n"
        "📋 Siz quyidagi ma'lumotlarni kiritasiz:\n"
        "  • 👤 Ism va Familiya\n"
        "  • 📞 Telefon raqam\n"
        "  • 🎂 Yosh\n\n"
        "▶️ Boshlash uchun quyidagi tugmani bosing:"
    )

    keyboard = [[KeyboardButton("✅ Ro'yxatdan o'tish")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    return ASKING_NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ism so'rash bosqichi."""
    await update.message.reply_text(
        "👤 <b>Ismingiz va Familiyangizni</b> kiriting:\n\n"
        "<i>Misol: Alisher Karimov</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )
    return ASKING_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ism qabul qilindi, telefon so'raymiz."""
    text = update.message.text.strip()

    # "Ro'yxatdan o'tish" tugmasini bosgan bo'lsa
    if text in ("✅ Ro'yxatdan o'tish", "/start"):
        await update.message.reply_text(
            "👤 <b>Ismingiz va Familiyangizni</b> kiriting:\n\n"
            "<i>Misol: Alisher Karimov</i>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        return ASKING_NAME

    # Ism validatsiyasi
    if len(text) < 2:
        await update.message.reply_text(
            "⚠️ Ism juda qisqa. Iltimos, to'liq ism kiriting:"
        )
        return ASKING_NAME

    if len(text) > 60:
        await update.message.reply_text(
            "⚠️ Ism juda uzun. Iltimos, qayta kiriting:"
        )
        return ASKING_NAME

    # Ismni saqlash
    context.user_data["name"] = text

    # Telefon raqam so'rash — kontakt yuborish tugmasi
    phone_keyboard = [[KeyboardButton("📱 Raqamni avtomatik yuborish", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(phone_keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"✅ Rahmat, <b>{text}</b>!\n\n"
        "📞 <b>Telefon raqamingizni</b> kiriting:\n\n"
        "📱 Tugmani bosib avtomatik yuboring <i>yoki</i>\n"
        "✏️ Qo'lda kiriting: <code>+998901234567</code>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return ASKING_PHONE


async def received_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Telefon raqami qabul qilindi, yosh so'raymiz."""
    # Kontakt orqali yuborilganmi yoki matn?
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    else:
        phone = update.message.text.strip()
        if not is_valid_phone(phone):
            await update.message.reply_text(
                "⚠️ Telefon raqam noto'g'ri kiritildi!\n\n"
                "Iltimos, to'g'ri formatda kiriting:\n"
                "📌 <code>+998901234567</code>\n"
                "📌 <code>998901234567</code>\n"
                "📌 <code>901234567</code>",
                parse_mode="HTML",
            )
            return ASKING_PHONE

    # Raqamni formatlash
    phone = format_phone(phone)
    context.user_data["phone"] = phone

    await update.message.reply_text(
        f"✅ Telefon raqam saqlandi: <code>{phone}</code>\n\n"
        "🎂 <b>Yoshingizni</b> kiriting (raqamda):\n\n"
        "<i>Misol: 25</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )
    return ASKING_AGE


async def received_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Yosh qabul qilindi — ma'lumotlarni saqlaydi."""
    age_text = update.message.text.strip()

    if not is_valid_age(age_text):
        await update.message.reply_text(
            "⚠️ Yosh noto'g'ri kiritildi!\n\n"
            "Iltimos, faqat raqam kiriting (1-120 oralig'ida):\n"
            "<i>Misol: 25</i>",
            parse_mode="HTML",
        )
        return ASKING_AGE

    # Ma'lumotlarni yig'ish
    name = context.user_data["name"]
    phone = context.user_data["phone"]
    age = age_text
    telegram_id = update.effective_user.id

    # Kutish xabari
    processing_msg = await update.message.reply_text(
        "⏳ Ma'lumotlar saqlanmoqda...",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Google Sheets ga yozish
    success = add_user_to_sheet(name=name, phone=phone, age=age, telegram_id=telegram_id)

    # Xabarni o'chirish
    await processing_msg.delete()

    if success:
        summary = (
            "🎉 <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\n"
            "📋 <b>Sizning ma'lumotlaringiz:</b>\n"
            f"  👤 Ism: <b>{name}</b>\n"
            f"  📞 Telefon: <code>{phone}</code>\n"
            f"  🎂 Yosh: <b>{age}</b>\n\n"
            "✅ Ma'lumotlaringiz tizimga saqlandi.\n"
            "🙏 Ro'yxatdan o'tganingiz uchun rahmat!"
        )

        keyboard = [[KeyboardButton("🔄 Qaytadan ro'yxatdan o'tish")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(
            "❌ Xatolik yuz berdi. Ma'lumotlar saqlanmadi.\n\n"
            "Iltimos, qaytadan urinib ko'ring: /start",
            reply_markup=ReplyKeyboardRemove(),
        )

    # User data ni tozalash
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/cancel — jarayonni bekor qilish."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Ro'yxatdan o'tish bekor qilindi.\n\n"
        "Qaytadan boshlash uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Qaytadan ro'yxatdan o'tish tugmasi."""
    return await start(update, context)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Noto'g'ri buyruqlar uchun."""
    await update.message.reply_text(
        "🤔 Bu buyruqni bilmayman.\n\n"
        "Boshlash uchun /start bosing."
    )


# ────────────────────────────────────────────────────────────────────────────
# ASOSIY FUNKSIYA
# ────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Botni ishga tushiradi."""
    logger.info("🚀 Bot ishga tushmoqda...")

    # Application yaratish
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler — asosiy jarayon
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r"^🔄 Qaytadan ro'yxatdan o'tish$"), restart),
        ],
        states={
            ASKING_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    received_name,
                ),
            ],
            ASKING_PHONE: [
                MessageHandler(filters.CONTACT, received_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_phone),
            ],
            ASKING_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_age),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    # Handlerlarni qo'shish
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Botni ishga tushirish (polling rejimi)
    logger.info("✅ Bot muvaffaqiyatli ishga tushdi! Ctrl+C bilan to'xtatish mumkin.")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
