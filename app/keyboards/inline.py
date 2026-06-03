from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cancel_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Returns a general cancel button markup."""
    keyboard = [
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"{prefix}_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_merge_keyboard() -> InlineKeyboardMarkup:
    """Returns the keyboard for the PDF merge operation."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Bajarildi (Birlashtirish)", callback_data="merge_done"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="merge_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_jpg2pdf_keyboard() -> InlineKeyboardMarkup:
    """Returns the keyboard for JPG(s) to PDF conversion."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Bajarildi (Konvertatsiya)", callback_data="jpg2pdf_done"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="jpg2pdf_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_split_options_keyboard() -> InlineKeyboardMarkup:
    """Returns selection buttons for PDF split options."""
    keyboard = [
        [InlineKeyboardButton(text="📄 Har bir sahifani ajratish", callback_data="split_opt_all")],
        [InlineKeyboardButton(text="🔢 Sahifalar oralig'i bo'yicha (masalan, 1-3, 5-8)", callback_data="split_opt_range")],
        [InlineKeyboardButton(text="🎯 Tanlangan sahifalarni ajratish (masalan, 1, 3, 5)", callback_data="split_opt_extract")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="split_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Returns the dashboard keyboard for the admin panel."""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Foydalanuvchilar statistikasi", callback_data="admin_user_stats"),
            InlineKeyboardButton(text="📈 Konvertatsiyalar statistikasi", callback_data="admin_conv_stats")
        ],
        [
            InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="📆 Kunlik faollik", callback_data="admin_daily_stats")
        ],
        [
            InlineKeyboardButton(text="❌ Panelni yopish", callback_data="admin_close")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

