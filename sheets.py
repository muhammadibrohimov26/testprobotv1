"""
Google Sheets integratsiya moduli.
Service Account orqali Sheets ga ma'lumot yozadi.
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import logging

from config import SHEET_ID, SHEET_NAME

logger = logging.getLogger(__name__)

# Google API uchun kerakli huquqlar (scopes)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Credentials fayli joylashuvi
CREDENTIALS_FILE = "credentials.json"


def get_worksheet():
    """Google Sheets varag'iga ulanadi va qaytaradi."""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)

        # Varag'ni topishga harakat qilamiz
        try:
            worksheet = spreadsheet.worksheet(SHEET_NAME)
        except gspread.WorksheetNotFound:
            # Varaq topilmasa, yangi varaq yaratamiz
            worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=10)
            logger.info(f"Yangi varaq yaratildi: {SHEET_NAME}")

        return worksheet
    except FileNotFoundError:
        logger.error(f"❌ credentials.json fayli topilmadi!")
        raise
    except Exception as e:
        logger.error(f"❌ Google Sheets ulanishida xato: {e}")
        raise


def ensure_headers(worksheet):
    """Agar sarlavhalar yo'q bo'lsa, birinchi qatorga qo'shadi."""
    try:
        first_row = worksheet.row_values(1)
        if not first_row:
            headers = ["№", "Ism", "Telefon raqam", "Yosh", "Ro'yxatdan o'tgan vaqt", "Telegram ID"]
            worksheet.append_row(headers, value_input_option="USER_ENTERED")
            logger.info("Sarlavhalar qo'shildi.")
    except Exception as e:
        logger.error(f"Sarlavha tekshirishda xato: {e}")


def add_user_to_sheet(name: str, phone: str, age: str, telegram_id: int) -> bool:
    """
    Yangi foydalanuvchi ma'lumotlarini Google Sheets ga qo'shadi.
    
    Args:
        name: Foydalanuvchi ismi
        phone: Telefon raqami
        age: Yoshi
        telegram_id: Telegram user ID
    
    Returns:
        True - muvaffaqiyatli, False - xato
    """
    try:
        worksheet = get_worksheet()
        ensure_headers(worksheet)

        # Mavjud qatorlar sonini aniqlaymiz (sarlavha hisoblanmaydi)
        all_values = worksheet.get_all_values()
        row_number = len(all_values)  # sarlavha bor bo'lsa, haqiqiy tartib raqam shu

        # Vaqt formati
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        # Yangi qator ma'lumotlari
        new_row = [row_number, name, phone, age, timestamp, str(telegram_id)]

        worksheet.append_row(new_row, value_input_option="USER_ENTERED")
        logger.info(f"✅ Yangi foydalanuvchi qo'shildi: {name} | {phone} | {age}")
        return True

    except Exception as e:
        logger.error(f"❌ Sheets ga yozishda xato: {e}")
        return False
