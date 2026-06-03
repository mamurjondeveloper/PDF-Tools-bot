import os
import uuid
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.config.config import TEMP_DIR
from app.keyboards.inline import get_cancel_keyboard
from app.services.doc_service import doc_to_pdf
from app.services.cleanup_service import delete_path
from app.database.db import log_conversion

logger = logging.getLogger(__name__)
router = Router(name="doc2pdf_router")

class DocToPdfStates(StatesGroup):
    waiting_for_doc = State()

@router.message(F.text == "📄 Word → PDF")
async def start_doc2pdf(message: Message, state: FSMContext) -> None:
    """Initiates the DOC/DOCX to PDF workflow."""
    await state.clear()
    await state.set_state(DocToPdfStates.waiting_for_doc)
    
    await message.answer(
        text=(
            "📥 **Word → PDF rejimi**\n\n"
            "Iltimos, PDF-ga aylantirmoqchi bo'lgan Microsoft Word hujjatingizni (`.doc` yoki `.docx`) yuklang."
        ),
        reply_markup=get_cancel_keyboard("doc2pdf"),
        parse_mode="Markdown"
    )

@router.message(DocToPdfStates.waiting_for_doc, F.document)
async def process_doc(message: Message, state: FSMContext, bot: Bot) -> None:
    """Downloads the Word document and calls the conversion service."""
    doc = message.document
    if not doc or not doc.file_name.lower().endswith((".doc", ".docx")):
        await message.answer("⚠️ Iltimos, faqat Microsoft Word hujjatlarini (`.doc` yoki `.docx`) yuklang.")
        return
        
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"{message.from_user.id}_doc2pdf_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    
    input_ext = os.path.splitext(doc.file_name)[1].lower()
    input_path = os.path.join(session_dir, f"input{input_ext}")
    output_path = os.path.join(session_dir, "converted_output.pdf")
    
    status_msg = await message.answer("📥 Hujjat yuklab olinmoqda...")
    
    try:
        await bot.download(file=doc.file_id, destination=input_path)
        
        await status_msg.edit_text("⏳ Hujjat PDF-ga aylantirilmoqda, iltimos kuting...")
        
        # Call the DOC to PDF service
        await doc_to_pdf(input_path, output_path)
        
        await status_msg.edit_text("📤 PDF yuborilmoqda...")
        
        # Build target output filename
        original_base = os.path.splitext(doc.file_name)[0]
        output_filename = f"{original_base}.pdf"
        
        pdf_file = FSInputFile(output_path, filename=output_filename)
        await message.answer_document(
            document=pdf_file,
            caption="🎉 Hujjat muvaffaqiyatli aylantirildi! Tayyor bo'lgan PDF hujjatingiz."
        )
        
        # Log conversion statistics
        await log_conversion(message.from_user.id, "doc2pdf")
        
        await status_msg.delete()
        
    except NotImplementedError as nie:
        await status_msg.edit_text(f"⚠️ {str(nie)}")
    except RuntimeError as re:
        await status_msg.edit_text(f"❌ Konvertatsiya amalga oshmadi: {str(re)}")
    except Exception as e:
        logger.error(f"Error converting DOC to PDF: {e}", exc_info=True)
        await status_msg.edit_text("❌ Faylni konvertatsiya qilishda xatolik yuz berdi. Iltimos, fayl buzilmaganligini tekshiring.")
    finally:
        await state.clear()
        await asyncio.to_thread(delete_path, session_dir)

@router.callback_query(F.data == "doc2pdf_cancel")
async def cancel_doc2pdf(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancels the DOC to PDF conversion process."""
    await state.clear()
    await callback.message.edit_text("❌ Word-dan PDF-ga aylantirish amali bekor qilindi.")

