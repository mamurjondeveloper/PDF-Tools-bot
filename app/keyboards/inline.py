from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cancel_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Returns a general cancel button markup."""
    keyboard = [
        [InlineKeyboardButton(text="❌ Cancel", callback_data=f"{prefix}_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_merge_keyboard() -> InlineKeyboardMarkup:
    """Returns the keyboard for the PDF merge operation."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Done (Merge)", callback_data="merge_done"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="merge_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_jpg2pdf_keyboard() -> InlineKeyboardMarkup:
    """Returns the keyboard for JPG(s) to PDF conversion."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Done (Convert)", callback_data="jpg2pdf_done"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="jpg2pdf_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_split_options_keyboard() -> InlineKeyboardMarkup:
    """Returns selection buttons for PDF split options."""
    keyboard = [
        [InlineKeyboardButton(text="📄 Split Every Page", callback_data="split_opt_all")],
        [InlineKeyboardButton(text="🔢 Split by Range (e.g. 1-3, 5-8)", callback_data="split_opt_range")],
        [InlineKeyboardButton(text="🎯 Extract Selected Pages (e.g. 1, 3, 5)", callback_data="split_opt_extract")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="split_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Returns the dashboard keyboard for the admin panel."""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 User Stats", callback_data="admin_user_stats"),
            InlineKeyboardButton(text="📈 Conversion Stats", callback_data="admin_conv_stats")
        ],
        [
            InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="📆 Daily Activity", callback_data="admin_daily_stats")
        ],
        [
            InlineKeyboardButton(text="❌ Close Panel", callback_data="admin_close")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
