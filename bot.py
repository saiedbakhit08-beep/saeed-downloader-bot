import os
import re
import asyncio
import tempfile
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

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
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(url, download=True)

    candidates = [
        p for p in Path(workdir).iterdir()
        if p.is_file() and p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}
    ]
    if not candidates:
        raise RuntimeError("No video file was produced.")
    return max(candidates, key=lambda p: p.stat().st_size)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 أهلاً بيك في Saeed Downloader\n\n"
        "ابعت لينك TikTok أو Instagram أو Facebook.\n"
        "هحاول أنزل أعلى جودة متاحة من الرابط العام."
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = URL_RE.search(text)
    if not match or not is_supported_url(match.group(0)):
        await update.message.reply_text("❌ ابعت رابط TikTok أو Instagram أو Facebook صالح.")
        return

    url = match.group(0).rstrip(").,]>")
    status = await update.message.reply_text("⏳ جاري التحميل بأعلى جودة متاحة...")
    loop = asyncio.get_running_loop()

    with tempfile.TemporaryDirectory(prefix="saeed_dl_") as workdir:
        try:
            path = await loop.run_in_executor(None, download_media, url, workdir)

            if path.stat().st_size > 50 * 1024 * 1024:
                await status.edit_text(
                    "⚠️ الفيديو أكبر من 50MB، وBot API العادي لا يرسله بهذا الحجم."
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
            await status.edit_text("❌ تعذر تنزيل الرابط.\n\n" + msg)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saeed Downloader Bot is running.")

    def log_message(self, format, *args):
        return

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

def main():
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    print(f"Saeed Downloader Bot is running on port {PORT}")
    app.run_polling()

if __name__ == "__main__":
    main()
        
