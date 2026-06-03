import os
import uuid
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.config.config import TEMP_DIR
from app.keyboards.inline import get_jpg2pdf_keyboard
from app.services.image_service import images_to_pdf
from app.services.cleanup_service import delete_path
from app.database.db import log_conversion

logger = logging.getLogger(__name__)
router = Router(name="jpg2pdf_router")

class JpgToPdfStates(StatesGroup):
    waiting_for_images = State()

@router.message(F.text == "🖼️ Rasmlar → PDF")
async def start_jpg2pdf(message: Message, state: FSMContext) -> None:
    """Initiates the JPG/PNG to PDF workflow."""
    await state.clear()
    
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"{message.from_user.id}_jpg2pdf_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    
    status_msg = await message.answer(
        text=(
            "📥 **Rasmlar → PDF rejimi**\n\n"
            "Iltimos, PDF-ga aylantirmoqchi bo'lgan rasmlaringizni (JPG, JPEG yoki PNG) ketma-ket yuboring.\n"
            "Rasmlarni oddiy rasm yoki siqilmagan hujjat shaklida yuborishingiz mumkin.\n"
            "Hozircha yuklangan rasmlar: **0** ta\n\n"
            "Tayyor bo'lgach, **Bajarildi (Konvertatsiya)** tugmasini bosing."
        ),
        reply_markup=get_jpg2pdf_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(JpgToPdfStates.waiting_for_images)
    await state.update_data(
        session_dir=session_dir,
        image_paths=[],
        status_msg_id=status_msg.message_id
    )

async def handle_image_download(message: Message, state: FSMContext, bot: Bot, file_id: str, original_name: str) -> None:
    """Helper method to download files and update FSM state data."""
    data = await state.get_data()
    session_dir = data["session_dir"]
    image_paths = data["image_paths"]
    status_msg_id = data.get("status_msg_id")
    
    try:
        # Determine file extension
        ext = os.path.splitext(original_name)[1]
        if not ext:
            ext = ".jpg"
            
        file_idx = len(image_paths) + 1
        safe_name = f"image_{file_idx:03d}_{uuid.uuid4().hex[:6]}{ext}"
        dest_path = os.path.join(session_dir, safe_name)
        
        await bot.download(file=file_id, destination=dest_path)
        
        image_paths.append(dest_path)
        await state.update_data(image_paths=image_paths)
        
        if status_msg_id:
            new_text = (
                f"📥 **Rasmlar → PDF rejimi**\n\n"
                f"✅ Yuklandi: `{original_name}`\n"
                f"Jami yuklangan rasmlar: **{file_idx}** ta\n\n"
                f"Yana rasm yuborishingiz mumkin yoki **Bajarildi (Konvertatsiya)** tugmasini bosing."
            )
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg_id,
                    text=new_text,
                    reply_markup=get_jpg2pdf_keyboard(),
                    parse_mode="Markdown"
                )
            except Exception as edit_err:
                logger.debug(f"Failed to edit status message: {edit_err}")
    except Exception as e:
        logger.error(f"Error downloading image: {e}", exc_info=True)
        await message.answer(f"⚠️ `{original_name}` yuklab olishda xatolik yuz berdi.")

@router.message(JpgToPdfStates.waiting_for_images, F.photo)
async def collect_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    """Collects photo attachments (compressed Telegram photos)."""
    photo = message.photo[-1]  # Get highest resolution
    original_name = f"photo_{photo.file_unique_id}.jpg"
    await handle_image_download(message, state, bot, photo.file_id, original_name)

@router.message(JpgToPdfStates.waiting_for_images, F.document)
async def collect_document_image(message: Message, state: FSMContext, bot: Bot) -> None:
    """Collects image files sent as uncompressed documents."""
    doc = message.document
    if not doc or not (doc.file_name.lower().endswith((".jpg", ".jpeg", ".png")) or (doc.mime_type and doc.mime_type.startswith("image/"))):
        await message.answer("⚠️ Iltimos, faqat JPG, JPEG yoki PNG formatidagi rasmlarni yuklang.")
        return
        
    await handle_image_download(message, state, bot, doc.file_id, doc.file_name)

@router.callback_query(JpgToPdfStates.waiting_for_images, F.data == "jpg2pdf_done")
async def process_jpg2pdf(callback: CallbackQuery, state: FSMContext) -> None:
    """Converts collected images into a PDF and sends it back to the user."""
    data = await state.get_data()
    image_paths = data.get("image_paths", [])
    session_dir = data.get("session_dir")
    
    if not image_paths:
        await callback.answer("⚠️ Konvertatsiya qilish uchun kamida 1 ta rasm yuklashingiz kerak.", show_alert=True)
        return
        
    await callback.message.edit_text("⏳ Rasmlar PDF-ga joylanmoqda, iltimos kuting...")
    
    output_path = os.path.join(session_dir, "converted_images.pdf")
    
    try:
        # Perform Image conversion in background thread
        await images_to_pdf(image_paths, output_path)
        
        # Send PDF file
        await callback.message.edit_text("📤 PDF yuborilmoqda...")
        pdf_file = FSInputFile(output_path, filename="rasmlar_to'plami.pdf")
        
        await callback.message.answer_document(
            document=pdf_file,
            caption="🎉 Rasmlardan tayyorlangan PDF hujjatingiz tayyor!"
        )
        
        # Log conversion statistics
        await log_conversion(callback.from_user.id, "jpg2pdf")
        
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Failed to convert images to PDF: {e}", exc_info=True)
        await callback.message.answer("❌ Rasmlarni PDF-ga aylantirishda xatolik yuz berdi. Qaytadan urinib ko'ring.")
    finally:
        # Cleanup files and state
        await state.clear()
        if session_dir:
            await asyncio.to_thread(delete_path, session_dir)

@router.callback_query(JpgToPdfStates.waiting_for_images, F.data == "jpg2pdf_cancel")
async def cancel_jpg2pdf(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancels the image conversion process and cleans up files."""
    data = await state.get_data()
    session_dir = data.get("session_dir")
    
    await state.clear()
    await callback.message.edit_text("❌ Rasmlarni PDF-ga aylantirish amali bekor qilindi.")
    
    if session_dir:
        await asyncio.to_thread(delete_path, session_dir)


