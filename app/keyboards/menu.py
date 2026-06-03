from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    """Returns the main menu keyboard markup."""
    keyboard = [
        [
            KeyboardButton(text="📎 PDF Birlashtirish"),
            KeyboardButton(text="✂️ PDF Ajratish")
        ],
        [
            KeyboardButton(text="🖼 JPG(s) → PDF"),
            KeyboardButton(text="📄 Word → PDF")
        ],
        [
            KeyboardButton(text="ℹ️ Yordam")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )

