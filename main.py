import os
import asyncio
import logging
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sir, Enter your link please.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = update.message.text
    chat_id = update.message.chat_id

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("Please send a valid video URL.")
        return

    status_message = await update.message.reply_text("Processing your video... ⏳")

    output_template = f"video_{chat_id}.%(ext)s"

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "max_filesize": MAX_FILE_SIZE,
        "quiet": True,
        "no_warnings": True,
    }

    filename = None

    try:
        loop = asyncio.get_running_loop()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(
                None,
                lambda: ydl.extract_info(url, download=True)
            )
            filename = ydl.prepare_filename(info)

        if os.path.exists(filename):

            with open(filename, "rb") as video:
                await update.message.reply_video(video=video)

            await status_message.delete()

        else:
            await status_message.edit_text("Could not find the downloaded file.")

    except yt_dlp.utils.DownloadError as e:

        if "too large" in str(e).lower():
            await status_message.edit_text("Video too large to send.")
        else:
            await status_message.edit_text(
                "Error: Failed to download video. Make sure the link is supported."
            )

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_message.edit_text("An unexpected error occurred.")

    finally:

        if filename and os.path.exists(filename):
            os.remove(filename)


if __name__ == "__main__":

    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set.")
        exit(1)

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...")

    application.run_polling()
