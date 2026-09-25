"""
Konfiguratsiya moduli.
.env fayldan muhit o'zgaruvchilarini yuklaydi.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot tokeni
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Google Sheets sozlamalari
SHEET_ID: str = os.getenv("SHEET_ID", "")
SHEET_NAME: str = os.getenv("SHEET_NAME", "Ro'yxat")

# Tekshiruv
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN .env faylda topilmadi! .env.example ga qarang.")

if not SHEET_ID:
    raise ValueError("❌ SHEET_ID .env faylda topilmadi! .env.example ga qarang.")
