import os
import uuid
import logging
from aiogram import Router, F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.config.config import TEMP_DIR
from app.keyboards.inline import get_merge_keyboard
from app.services.pdf_service import merge_pdfs
from app.services.cleanup_service import delete_path
from app.database.db import log_conversion

logger = logging.getLogger(__name__)
router = Router(name="merge_router")

class MergeStates(StatesGroup):
    waiting_for_pdfs = State()

@router.message(F.text == "📎 PDF Birlashtirish")
async def start_merge(message: Message, state: FSMContext) -> None:
    """Initiates the PDF merge workflow."""
    await state.clear()
    
    # Generate a unique session ID for this merge process
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"{message.from_user.id}_merge_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    
    status_msg = await message.answer(
        text=(
            "📥 **PDF Birlashtirish rejimi**\n\n"
            "Iltimos, birlashtirmoqchi bo'lgan PDF fayllaringizni ketma-ket yuboring.\n"
            "Hozircha yuklangan fayllar: **0** ta\n\n"
            "Barcha fayllarni yuklab bo'lgach, **Bajarildi (Birlashtirish)** tugmasini bosing."
        ),
        reply_markup=get_merge_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(MergeStates.waiting_for_pdfs)
    await state.update_data(
        session_dir=session_dir,
        file_paths=[],
        status_msg_id=status_msg.message_id
    )

@router.message(MergeStates.waiting_for_pdfs, F.document)
async def collect_pdf(message: Message, state: FSMContext, bot: Bot) -> None:
    """Collects uploaded PDFs and saves them to the session directory."""
    doc = message.document
    if not doc or not (doc.file_name.lower().endswith(".pdf") or doc.mime_type == "application/pdf"):
        await message.answer("⚠️ Iltimos, faqat PDF fayllarini yuklang.")
        return
        
    data = await state.get_data()
    session_dir = data["session_dir"]
    file_paths = data["file_paths"]
    status_msg_id = data.get("status_msg_id")
    
    try:
        # Save file with a safe, ordered name
        file_idx = len(file_paths) + 1
        safe_name = f"file_{file_idx:03d}_{uuid.uuid4().hex[:6]}.pdf"
        dest_path = os.path.join(session_dir, safe_name)
        
        await bot.download(file=doc.file_id, destination=dest_path)
        
        file_paths.append(dest_path)
        await state.update_data(file_paths=file_paths)
        
        if status_msg_id:
            new_text = (
                f"📥 **PDF Birlashtirish rejimi**\n\n"
                f"✅ Yuklandi: `{doc.file_name}`\n"
                f"Yuklangan jami fayllar: **{file_idx}** ta\n\n"
                f"Yana PDF yuborishingiz mumkin yoki **Bajarildi (Birlashtirish)** tugmasini bosing."
            )
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg_id,
                    text=new_text,
                    reply_markup=get_merge_keyboard(),
                    parse_mode="Markdown"
                )
            except Exception as edit_err:
                logger.debug(f"Failed to edit status message: {edit_err}")
    except Exception as e:
        logger.error(f"Error downloading PDF file: {e}", exc_info=True)
        await message.answer(f"⚠️ `{doc.file_name}` yuklab olishda xatolik yuz berdi.")

@router.callback_query(MergeStates.waiting_for_pdfs, F.data == "merge_done")
async def process_merge(callback: CallbackQuery, state: FSMContext) -> None:
    """Executes the merge operation and sends the compiled PDF."""
    data = await state.get_data()
    file_paths = data.get("file_paths", [])
    session_dir = data.get("session_dir")
    
    if len(file_paths) < 2:
        await callback.answer("⚠️ Birlashtirish uchun kamida 2 ta PDF fayl yuklashingiz kerak.", show_alert=True)
        return
        
    await callback.message.edit_text("⏳ PDF fayllar birlashtirilmoqda, iltimos kuting...")
    
    output_path = os.path.join(session_dir, "merged_output.pdf")
    
    try:
        # Perform PDF merge in background thread
        await merge_pdfs(file_paths, output_path)
        
        # Send merged file
        await callback.message.edit_text("📤 Birlashtirilgan PDF yuborilmoqda...")
        merged_file = FSInputFile(output_path, filename="birlashtirilgan_hujjat.pdf")
        
        await callback.message.answer_document(
            document=merged_file,
            caption="🎉 Birlashtirilgan PDF hujjatingiz tayyor!"
        )
        
        # Increment statistics in DB
        await log_conversion(callback.from_user.id, "merge")
        
        # Remove original status message
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Failed to merge PDFs: {e}", exc_info=True)
        await callback.message.answer("❌ PDF fayllarni birlashtirishda xatolik yuz berdi. Qaytadan urinib ko'ring.")
    finally:
        # Cleanup session directory and clear state
        await state.clear()
        if session_dir:
            await asyncio.to_thread(delete_path, session_dir)

@router.callback_query(MergeStates.waiting_for_pdfs, F.data == "merge_cancel")
async def cancel_merge(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancels the merge process and cleans up files."""
    data = await state.get_data()
    session_dir = data.get("session_dir")
    
    await state.clear()
    await callback.message.edit_text("❌ Birlashtirish amali bekor qilindi.")
    
    if session_dir:
        await asyncio.to_thread(delete_path, session_dir)


