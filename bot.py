import os
import random
import string
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─────────────────── ENV ────────────────────
BOT_TOKEN  = os.environ["BOT_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])          # e.g. -1001234567890
DATABASE_URL = os.environ["DATABASE_URL"]


# ─────────────────── DB ─────────────────────
def get_conn():
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url, sslmode="require")


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id          SERIAL PRIMARY KEY,
                    file_code   VARCHAR(10) UNIQUE NOT NULL,
                    message_id  BIGINT NOT NULL,
                    user_id     BIGINT NOT NULL,
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
    logger.info("Database initialised ✓")


def gen_unique_code() -> str:
    chars = string.ascii_uppercase + string.digits
    with get_conn() as conn:
        with conn.cursor() as cur:
            while True:
                code = "".join(random.choices(chars, k=10))
                cur.execute("SELECT 1 FROM files WHERE file_code = %s", (code,))
                if cur.fetchone() is None:
                    return code


def save_file(file_code: str, message_id: int, user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO files (file_code, message_id, user_id) VALUES (%s, %s, %s)",
                (file_code, message_id, user_id),
            )
        conn.commit()


def fetch_file(file_code: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM files WHERE file_code = %s", (file_code.upper(),)
            )
            return cur.fetchone()


def count_user_files(user_id: int) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM files WHERE user_id = %s", (user_id,))
            return cur.fetchone()[0]


# ─────────────────── UI HELPERS ──────────────
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 How to Store",    callback_data="help_store"),
            InlineKeyboardButton("📥 How to Retrieve", callback_data="help_get"),
        ],
        [
            InlineKeyboardButton("📦 My Files", callback_data="my_files"),
        ],
    ])


# ─────────────────── HANDLERS ────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        "🔮 *AS CLOUD SYSTEM*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"Welcome, *{user.first_name}*! 👋\n\n"
        "Send me any file — photo, video, document, audio, sticker — "
        "and I'll store it in the cloud. You get a unique *10-character code* "
        "to retrieve it anytime, from anywhere.\n\n"
        "▸ Send a file to store it\n"
        "▸ `/give CODE` to retrieve it"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


async def cb_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "help_store":
        await q.edit_message_text(
            "📁 *Storing Files*\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "Just send any of the following to this bot:\n\n"
            "📷 Photos\n"
            "🎬 Videos\n"
            "🎵 Audio / Voice Notes\n"
            "📄 Documents\n"
            "🎭 Stickers\n\n"
            "You will instantly receive a unique *10-character code* like `A3BX7KQ2LP`.\n\n"
            "Keep it safe — that's your key! 🔑",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="back_home")]
            ]),
        )

    elif q.data == "help_get":
        await q.edit_message_text(
            "📥 *Retrieving Files*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Use the command:\n\n"
            "`/give A3BX7KQ2LP`\n\n"
            "Replace `A3BX7KQ2LP` with your actual file code.\n\n"
            "✅ Works from any device, any time.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="back_home")]
            ]),
        )

    elif q.data == "my_files":
        count = count_user_files(q.from_user.id)
        await q.edit_message_text(
            f"📦 *Your Storage*\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"Files stored: *{count}*\n\n"
            f"Send any file to store more!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="back_home")]
            ]),
        )

    elif q.data == "back_home":
        user = q.from_user
        text = (
            "🔮 *AS CLOUD SYSTEM*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            f"Welcome back, *{user.first_name}*! 👋\n\n"
            "Send me any file — photo, video, document, audio, sticker — "
            "and I'll store it in the cloud. You get a unique *10-character code* "
            "to retrieve it anytime, from anywhere.\n\n"
            "▸ Send a file to store it\n"
            "▸ `/give CODE` to retrieve it"
        )
        await q.edit_message_text(
            text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
        )

    elif q.data.startswith("show_code:"):
        code = q.data.split(":", 1)[1]
        await q.answer(f"Your code: {code}", show_alert=True)


async def handle_media(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = msg.from_user.id

    # Copy to channel — copy_message has NO forwarded-from header
    try:
        copied = await ctx.bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
        )
    except Exception as e:
        logger.error("copy_message failed: %s", e)
        await msg.reply_text("❌ Storage failed. Please try again.")
        return

    code = gen_unique_code()
    save_file(code, copied.message_id, user_id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 Show Code", callback_data=f"show_code:{code}"),
        ],
        [
            InlineKeyboardButton("📦 My Files", callback_data="my_files"),
            InlineKeyboardButton("🏠 Home",     callback_data="back_home"),
        ],
    ])

    await msg.reply_text(
        f"✅ *Stored Successfully!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔑 *Your File Code:*\n"
        f"`{code}`\n\n"
        f"Use `/give {code}` to retrieve this file anytime.\n\n"
        f"_Tap 🔍 Show Code to see it as an alert._",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def cmd_give(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "❌ *Missing code!*\n\nUsage: `/give A3BX7KQ2LP`",
            parse_mode="Markdown",
        )
        return

    code = ctx.args[0].strip().upper()

    if len(code) != 10 or not code.isalnum():
        await update.message.reply_text(
            "⚠️ *Invalid code format.*\n\nCodes are exactly 10 alphanumeric characters.",
            parse_mode="Markdown",
        )
        return

    file_data = fetch_file(code)
    if not file_data:
        await update.message.reply_text(
            f"❌ *File not found!*\n\nNo file with code `{code}` exists.",
            parse_mode="Markdown",
        )
        return

    try:
        # copy_message — no forwarded-from header
        await ctx.bot.copy_message(
            chat_id=update.message.chat_id,
            from_chat_id=CHANNEL_ID,
            message_id=file_data["message_id"],
        )
    except Exception as e:
        logger.error("retrieve failed: %s", e)
        await update.message.reply_text(
            "❌ Could not retrieve the file. It may have been removed from storage."
        )
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏠 Home",      callback_data="back_home"),
            InlineKeyboardButton("📦 My Files", callback_data="my_files"),
        ]
    ])
    await update.message.reply_text(
        f"✅ *File Retrieved!*\n\n🔑 Code: `{code}`",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


# ─────────────────── MAIN ────────────────────
def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    media_filter = (
        filters.Document.ALL
        | filters.PHOTO
        | filters.VIDEO
        | filters.AUDIO
        | filters.VOICE
        | filters.VIDEO_NOTE
        | filters.Sticker.ALL
        | filters.ANIMATION
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("give",  cmd_give))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(media_filter, handle_media))

    logger.info("AS CLOUD SYSTEM bot starting…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
