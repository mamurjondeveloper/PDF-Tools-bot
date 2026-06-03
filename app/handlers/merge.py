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

@router.message(F.text == "📎 PDF Merge")
async def start_merge(message: Message, state: FSMContext) -> None:
    """Initiates the PDF merge workflow."""
    await state.clear()
    
    # Generate a unique session ID for this merge process
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"{message.from_user.id}_merge_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    
    await state.set_state(MergeStates.waiting_for_pdfs)
    await state.update_data(
        session_dir=session_dir,
        file_paths=[]
    )
    
    await message.answer(
        text=(
            "📥 **PDF Merge Mode**\n\n"
            "Please send the PDF files you want to merge one by one in the order they should appear.\n"
            "Once you have uploaded all files, click **Done (Merge)** below."
        ),
        reply_markup=get_merge_keyboard(),
        parse_mode="Markdown"
    )

@router.message(MergeStates.waiting_for_pdfs, F.document)
async def collect_pdf(message: Message, state: FSMContext, bot: Bot) -> None:
    """Collects uploaded PDFs and saves them to the session directory."""
    doc = message.document
    if not doc or not (doc.file_name.lower().endswith(".pdf") or doc.mime_type == "application/pdf"):
        await message.answer("⚠️ Please upload only PDF files.")
        return
        
    data = await state.get_data()
    session_dir = data["session_dir"]
    file_paths = data["file_paths"]
    
    # Send temporary progress message
    status_msg = await message.answer(f"📥 Downloading `{doc.file_name}`...", parse_mode="Markdown")
    
    try:
        # Save file with a safe, ordered name
        file_idx = len(file_paths) + 1
        safe_name = f"file_{file_idx:03d}_{uuid.uuid4().hex[:6]}.pdf"
        dest_path = os.path.join(session_dir, safe_name)
        
        await bot.download(file=doc.file_id, destination=dest_path)
        
        file_paths.append(dest_path)
        await state.update_data(file_paths=file_paths)
        
        await status_msg.edit_text(
            text=(
                f"✅ Added file #{file_idx}: `{doc.file_name}`\n\n"
                f"Total files uploaded: **{file_idx}**\n"
                "Send another PDF or click **Done (Merge)** to compile."
            ),
            reply_markup=get_merge_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error downloading PDF file: {e}", exc_info=True)
        await status_msg.edit_text("❌ Failed to download file. Please try again.")

@router.callback_query(MergeStates.waiting_for_pdfs, F.data == "merge_done")
async def process_merge(callback: CallbackQuery, state: FSMContext) -> None:
    """Executes the merge operation and sends the compiled PDF."""
    data = await state.get_data()
    file_paths = data.get("file_paths", [])
    session_dir = data.get("session_dir")
    
    if len(file_paths) < 2:
        await callback.answer("⚠️ You must upload at least 2 PDF files to merge.", show_alert=True)
        return
        
    await callback.message.edit_text("⏳ Merging files, please wait...")
    
    output_path = os.path.join(session_dir, "merged_output.pdf")
    
    try:
        # Perform PDF merge in background thread
        await merge_pdfs(file_paths, output_path)
        
        # Send merged file
        await callback.message.edit_text("📤 Sending merged PDF...")
        merged_file = FSInputFile(output_path, filename="merged_document.pdf")
        
        await callback.message.answer_document(
            document=merged_file,
            caption="🎉 Here is your merged PDF document!"
        )
        
        # Increment statistics in DB
        await log_conversion(callback.from_user.id, "merge")
        
        # Remove original status message
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Failed to merge PDFs: {e}", exc_info=True)
        await callback.message.answer("❌ An error occurred while merging your PDF files. Please try again.")
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
    await callback.message.edit_text("❌ Merge operation cancelled.")
    
    if session_dir:
        await asyncio.to_thread(delete_path, session_dir)
