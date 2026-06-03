import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.keyboards.menu import get_main_menu

logger = logging.getLogger(__name__)
router = Router(name="common_router")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Handles the /start command."""
    await state.clear()
    first_name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    welcome_text = (
        f"👋 Salom, {first_name}!\n\n"
        "**PDF Tools Bot**ga xush kelibsiz. Men sizga PDF hujjatlarini tez va oson qayta ishlashga yordam beraman.\n\n"
        "Boshlash uchun quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@router.message(F.text == "ℹ️ Yordam")
@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    """Handles the help request."""
    await state.clear()
    help_text = (
        "🛠 **PDF Tools Bot - Yordam yo'riqnomasi**\n\n"
        "Asosiy menyudan kerakli amalni tanlang:\n\n"
        "📎 **PDF Birlashtirish**\n"
        "• Ikki yoki undan ko'p PDF fayllarni ketma-ket yuboring.\n"
        "• Bot ularni yuborilgan tartibda birlashtiradi.\n"
        "• Yakunlash uchun *Bajarildi (Birlashtirish)* tugmasini bosing.\n\n"
        "✂️ **PDF Ajratish**\n"
        "• PDF faylini yuklang.\n"
        "• Kerakli amalni tanlang: har bir sahifani ajratish, sahifalar oralig'i (masalan, 1-3) yoki tanlangan sahifalarni ajratish (masalan, 1,3,5).\n\n"
        "🖼 **JPG(s) → PDF**\n"
        "• Bir yoki bir nechta rasm yuboring (JPG, JPEG, PNG).\n"
        "• Bot ularni bitta PDF hujjatiga birlashtiradi.\n"
        "• Yakunlash uchun *Bajarildi (Konvertatsiya)* tugmasini bosing.\n\n"
        "📄 **Word → PDF**\n"
        "• Bitta Word hujjatini yuboring (.doc yoki .docx).\n"
        "• Bot uni formati saqlangan holda PDF-ga aylantiradi.\n\n"
        "💡 *Eslatma:* Har qanday amalni istalgan vaqtda bekor qilish tugmasi orqali to'xtatishingiz mumkin."
    )
    await message.answer(text=help_text, parse_mode="Markdown")

