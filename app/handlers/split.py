import os
import uuid
import shutil
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.config.config import TEMP_DIR
from app.keyboards.inline import get_split_options_keyboard, get_cancel_keyboard
from app.services.pdf_service import (
    get_pdf_page_count,
    split_all_pages,
    extract_pdf_pages,
    parse_range_string
)
from app.services.cleanup_service import delete_path
from app.database.db import log_conversion

logger = logging.getLogger(__name__)
router = Router(name="split_router")

class SplitStates(StatesGroup):
    waiting_for_pdf = State()
    waiting_for_option = State()
    waiting_for_range = State()
    waiting_for_extract = State()

@router.message(F.text == "✂️ PDF Split")
async def start_split(message: Message, state: FSMContext) -> None:
    """Initiates the PDF split workflow."""
    await state.clear()
    await state.set_state(SplitStates.waiting_for_pdf)
    await message.answer(
        text=(
            "📥 **PDF Split Mode**\n\n"
            "Please upload the PDF file you wish to split."
        ),
        reply_markup=get_cancel_keyboard("split"),
        parse_mode="Markdown"
    )

@router.message(SplitStates.waiting_for_pdf, F.document)
async def collect_pdf_for_split(message: Message, state: FSMContext, bot: Bot) -> None:
    """Accepts and processes the uploaded PDF for splitting."""
    doc = message.document
    if not doc or not (doc.file_name.lower().endswith(".pdf") or doc.mime_type == "application/pdf"):
        await message.answer("⚠️ Please upload only PDF files.")
        return
        
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, f"{message.from_user.id}_split_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    
    input_path = os.path.join(session_dir, "input.pdf")
    
    status_msg = await message.answer("📥 Downloading PDF...")
    
    try:
        await bot.download(file=doc.file_id, destination=input_path)
        
        # Determine page count
        page_count = get_pdf_page_count(input_path)
        
        await state.update_data(
            session_dir=session_dir,
            input_path=input_path,
            page_count=page_count,
            status_msg_id=status_msg.message_id
        )
        
        await state.set_state(SplitStates.waiting_for_option)
        await status_msg.edit_text(
            text=(
                f"📊 Document: `{doc.file_name}`\n"
                f"Pages detected: **{page_count}**\n\n"
                "How would you like to split this PDF? Select an option below:"
            ),
            reply_markup=get_split_options_keyboard(),
            parse_mode="Markdown"
        )
    except ValueError as ve:
        await status_msg.edit_text(f"⚠️ {str(ve)}")
        await state.clear()
        await asyncio.to_thread(delete_path, session_dir)
    except Exception as e:
        logger.error(f"Error handling PDF split file: {e}", exc_info=True)
        await status_msg.edit_text("❌ Failed to process document. Please try again.")
        await state.clear()
        if session_dir:
            await asyncio.to_thread(delete_path, session_dir)

@router.callback_query(SplitStates.waiting_for_option, F.data == "split_opt_all")
async def process_split_all(callback: CallbackQuery, state: FSMContext) -> None:
    """Splits every page of the PDF, packaging as a ZIP if there are more than 3 pages."""
    data = await state.get_data()
    input_path = data["input_path"]
    session_dir = data["session_dir"]
    page_count = data["page_count"]
    
    await callback.message.edit_text("⏳ Splitting pages, please wait...")
    
    try:
        # Create output dir for split pages
        split_dir = os.path.join(session_dir, "split_pages")
        os.makedirs(split_dir, exist_ok=True)
        
        # Async run split all
        split_files = await split_all_pages(input_path, split_dir)
        
        if page_count <= 3:
            # Send them individually
            for fpath in split_files:
                fname = os.path.basename(fpath)
                await callback.message.answer_document(
                    document=FSInputFile(fpath),
                    caption=f"📄 {fname}"
                )
        else:
            # Create a zip file
            zip_base = os.path.join(session_dir, "split_pages_archive")
            zip_path = await asyncio.to_thread(shutil.make_archive, zip_base, "zip", split_dir)
            
            await callback.message.answer_document(
                document=FSInputFile(zip_path, filename="split_pages.zip"),
                caption=f"📦 Split successfully! Here are all {page_count} pages archived as a ZIP file."
            )
            
        await log_conversion(callback.from_user.id, "split")
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Error in split_all handler: {e}", exc_info=True)
        await callback.message.answer("❌ An error occurred during splitting.")
    finally:
        await state.clear()
        await asyncio.to_thread(delete_path, session_dir)

@router.callback_query(SplitStates.waiting_for_option, F.data == "split_opt_range")
async def ask_split_range(callback: CallbackQuery, state: FSMContext) -> None:
    """Prompts the user for a range expression."""
    data = await state.get_data()
    page_count = data["page_count"]
    
    await state.set_state(SplitStates.waiting_for_range)
    await callback.message.edit_text(
        text=(
            f"🔢 **Split by Page Range**\n\n"
            f"Please enter the page range you want to extract.\n"
            f"Use numbers and dashes/commas (e.g. `1-3, 5-8`).\n\n"
            f"Total Pages in document: **{page_count}**"
        ),
        reply_markup=get_cancel_keyboard("split"),
        parse_mode="Markdown"
    )

@router.callback_query(SplitStates.waiting_for_option, F.data == "split_opt_extract")
async def ask_split_extract(callback: CallbackQuery, state: FSMContext) -> None:
    """Prompts the user for a list of pages."""
    data = await state.get_data()
    page_count = data["page_count"]
    
    await state.set_state(SplitStates.waiting_for_extract)
    await callback.message.edit_text(
        text=(
            f"🎯 **Extract Selected Pages**\n\n"
            f"Please enter the specific page numbers you want to extract, separated by commas (e.g. `1, 3, 5`).\n\n"
            f"Total Pages in document: **{page_count}**"
        ),
        reply_markup=get_cancel_keyboard("split"),
        parse_mode="Markdown"
    )

@router.message(SplitStates.waiting_for_range)
@router.message(SplitStates.waiting_for_extract)
async def process_custom_split(message: Message, state: FSMContext) -> None:
    """Validates ranges/pages and extracts the requested PDF portions."""
    data = await state.get_data()
    input_path = data["input_path"]
    session_dir = data["session_dir"]
    page_count = data["page_count"]
    
    user_input = message.text.strip() if message.text else ""
    
    # Parse check first
    valid_pages = parse_range_string(user_input, page_count)
    if not valid_pages:
        await message.answer(
            f"⚠️ Invalid format or page numbers out of range.\n"
            f"Please enter valid pages between 1 and {page_count} (e.g., `1-3, 5`)."
        )
        return
        
    status_msg = await message.answer("⏳ Processing split request...")
    output_path = os.path.join(session_dir, "extracted_output.pdf")
    
    try:
        await extract_pdf_pages(input_path, user_input, output_path)
        
        await status_msg.edit_text("📤 Sending extracted PDF...")
        extracted_file = FSInputFile(output_path, filename="extracted_document.pdf")
        
        await message.answer_document(
            document=extracted_file,
            caption=f"🎉 Successfully extracted pages: {user_input}"
        )
        
        await log_conversion(message.from_user.id, "split")
        
        # Clean status message
        await status_msg.delete()
        # Clean inline choices message if we have ID
        if "status_msg_id" in data:
            try:
                await message.bot.delete_message(message.chat.id, data["status_msg_id"])
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Error in custom split: {e}", exc_info=True)
        await status_msg.edit_text("❌ An error occurred while extracting PDF pages.")
    finally:
        await state.clear()
        await asyncio.to_thread(delete_path, session_dir)

@router.callback_query(F.data == "split_cancel")
async def cancel_split(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancels the split process and cleans up files."""
    data = await state.get_data()
    session_dir = data.get("session_dir")
    
    await state.clear()
    await callback.message.edit_text("❌ Split operation cancelled.")
    
    if session_dir:
        await asyncio.to_thread(delete_path, session_dir)
