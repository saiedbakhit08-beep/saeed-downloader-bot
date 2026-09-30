import os
import re
import asyncio
import tempfile
from pathlib import Path

import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN environment variable first.")

URL_RE = re.compile(r"https?://\S+")

def is_supported_url(url: str) -> bool:
    u = url.lower()
    return any(x in u for x in (
        "tiktok.com/", "vm.tiktok.com/", "vt.tiktok.com/",
        "instagram.com/reel/", "instagram.com/p/",
        "facebook.com/reel/", "facebook.com/watch",
        "fb.watch/", "facebook.com/",
    ))

def download_media(url: str, workdir: str) -> Path:
    outtmpl = str(Path(workdir) / "%(id)s.%(ext)s")
    opts = {
        # Highest available video+audio, then best single-file format.
        "format": "bv*+ba/b",
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
    }

    # yt-dlp does not remove an existing creator watermark. If the platform
    # exposes a direct, unwatermarked stream, yt-dlp can select it when available.
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        requested = info.get("requested_downloads") or []
        candidates = []
        for p in Path(workdir).iterdir():
            if p.is_file() and p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
                candidates.append(p)
        if not candidates:
            raise RuntimeError("No video file was produced.")
        return max(candidates, key=lambda p: p.stat().st_size)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 أهلاً بيك في Saeed Downloader\n\n"
        "ابعت لينك TikTok أو Instagram Reel/Post أو Facebook Reel/Video، "
        "وهحاول أجيب أعلى جودة متاحة.\n\n"
        "ملاحظة: البوت لا يزيل علامة مائية موجودة بالفعل من فيديو؛ "
        "لو المصدر نفسه يوفر نسخة مباشرة بدون علامة، يتم تنزيلها."
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = URL_RE.search(text)
    if not match or not is_supported_url(match.group(0)):
        await update.message.reply_text(
            "❌ ابعت رابط TikTok أو Instagram أو Facebook صالح."
        )
        return

    url = match.group(0).rstrip(").,]>")
    status = await update.message.reply_text("⏳ جاري التحميل بأعلى جودة متاحة...")
    loop = asyncio.get_running_loop()

    with tempfile.TemporaryDirectory(prefix="saeed_dl_") as workdir:
        try:
            path = await loop.run_in_executor(None, download_media, url, workdir)

            # Standard Telegram Bot API upload limit is currently 50 MB.
            if path.stat().st_size > 50 * 1024 * 1024:
                await status.edit_text(
                    "⚠️ الفيديو أكبر من 50MB، لذلك لم أرسله داخل تيليجرام.\n"
                    "يمكن تشغيل Local Bot API Server لرفع ملفات أكبر."
                )
                return

            await status.edit_text("📤 تم التحميل، جاري الإرسال...")
            with path.open("rb") as f:
                await update.message.reply_video(
                    video=f,
                    supports_streaming=True,
                    caption="✅ أعلى جودة متاحة"
                )
            await status.delete()
        except Exception as e:
            msg = str(e)
            if len(msg) > 700:
                msg = msg[-700:]
            await status.edit_text(
                "❌ مقدرتش أنزّل الرابط.\n\n"
                "ممكن يكون الفيديو خاص، أو المنصة غيّرت طريقة الوصول، "
                "أو الرابط غير مدعوم حاليًا.\n\n"
                f"التفاصيل: {msg}"
            )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    print("Saeed Downloader Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
