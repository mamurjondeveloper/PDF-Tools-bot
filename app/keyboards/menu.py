from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    """Returns the main menu keyboard markup."""
    keyboard = [
        [
            KeyboardButton(text="📎 PDF Merge"),
            KeyboardButton(text="✂️ PDF Split")
        ],
        [
            KeyboardButton(text="🖼 JPG(s) → PDF"),
            KeyboardButton(text="📄 DOC → PDF")
        ],
        [
            KeyboardButton(text="ℹ️ Help")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )
