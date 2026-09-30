# Saeed Downloader Bot

Telegram downloader for publicly accessible TikTok, Instagram and Facebook video URLs.

## Supported examples
- TikTok video links
- Instagram Reels / Posts
- Facebook Reels / public video links

## Important
- The bot selects the highest quality stream available to yt-dlp.
- It does NOT remove an existing creator/platform watermark by editing or hiding it.
- If a platform exposes a direct version without a watermark, that source can be downloaded.
- Private/login-only content may require authentication and is not handled by this basic version.
- Telegram's standard Bot API currently limits bot uploads to 50 MB. A local Bot API server can raise the upload limit substantially.

## Run with Docker

1. Copy `.env.example` to `.env`.
2. Put the NEW BotFather token in `.env`.
3. Run:
   `docker compose up -d --build`

## Run directly

Install FFmpeg, then:
`pip install -r requirements.txt`

Linux/macOS:
`export BOT_TOKEN="YOUR_NEW_TOKEN"`
`python bot.py`

Windows PowerShell:
`$env:BOT_TOKEN="YOUR_NEW_TOKEN"`
`python bot.py`
