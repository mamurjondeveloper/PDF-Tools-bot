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
    first_name = message.from_user.first_name if message.from_user else "User"
    welcome_text = (
        f"👋 Hello, {first_name}!\n\n"
        "Welcome to **PDF Tools Bot**. I can help you process PDF documents quickly and easily.\n\n"
        "Please select an option from the menu below to get started:"
    )
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@router.message(F.text == "ℹ️ Help")
@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    """Handles the help request."""
    await state.clear()
    help_text = (
        "🛠 **PDF Tools Bot Help Guide**\n\n"
        "Select any action from the main menu:\n\n"
        "📎 **PDF Merge**\n"
        "• Send two or more PDF files.\n"
        "• The bot will merge them in the order they were sent.\n"
        "• Click *Done (Merge)* to complete.\n\n"
        "✂️ **PDF Split**\n"
        "• Upload a PDF file.\n"
        "• Choose to split every page, a page range (e.g. 1-3), or extract specific pages (e.g. 1,3,5).\n\n"
        "🖼 **JPG(s) → PDF**\n"
        "• Send one or more images (JPG, JPEG, PNG).\n"
        "• The bot will merge them into a single PDF document.\n"
        "• Click *Done (Convert)* to complete.\n\n"
        "📄 **DOC → PDF**\n"
        "• Send a single Word document (.doc or .docx).\n"
        "• The bot will convert it to a PDF with formatting preserved.\n\n"
        "💡 *Note:* You can cancel any operation at any time using the cancel buttons."
    )
    await message.answer(text=help_text, parse_mode="Markdown")
