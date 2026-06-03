import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from app.filters.admin import IsAdmin
from app.keyboards.inline import get_admin_keyboard, get_cancel_keyboard
from app.database import db

logger = logging.getLogger(__name__)
router = Router(name="admin_router")
# Apply admin filter to all handlers in this router
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

class AdminStates(StatesGroup):
    waiting_for_broadcast_msg = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """Displays the admin dashboard panel."""
    await state.clear()
    await message.answer(
        text=(
            "🛡 **PDF Tools Bot - Admin boshqaruv paneli**\n\n"
            "Statistikalarni ko'rish yoki foydalanuvchilarga xabar tarqatish uchun quyidagi buyruqlardan birini tanlang."
        ),
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_user_stats")
async def show_user_stats(callback: CallbackQuery) -> None:
    """Queries and displays user registration statistics."""
    stats = await db.get_user_stats()
    
    text = (
        "📊 **Foydalanuvchilar statistikasi**\n\n"
        f"• **Jami ro'yxatdan o'tganlar:** {stats.get('total_users', 0)} ta\n"
        f"• **Bugun qo'shilganlar:** {stats.get('new_users_today', 0)} ta\n"
        f"• **Oxirgi 24 soatda faollar:** {stats.get('active_users_24h', 0)} ta\n"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_conv_stats")
async def show_conversion_stats(callback: CallbackQuery) -> None:
    """Queries and displays file conversion statistics."""
    stats = await db.get_conversion_stats()
    by_type = stats.get("by_type", {})
    
    # Extract types with nice labels
    merge_c = by_type.get("merge", 0)
    split_c = by_type.get("split", 0)
    jpg2pdf_c = by_type.get("jpg2pdf", 0)
    doc2pdf_c = by_type.get("doc2pdf", 0)
    
    text = (
        "📈 **Konvertatsiyalar statistikasi**\n\n"
        f"• **Jami operatsiyalar:** {stats.get('total_conversions', 0)} ta\n"
        f"• **Oxirgi 24 soatda bajarilganlar:** {stats.get('conversions_24h', 0)} ta\n\n"
        "**Amallar turi bo'yicha taqsimot:**\n"
        f"• 📎 PDF Birlashtirish: {merge_c} ta\n"
        f"• ✂️ PDF Ajratish: {split_c} ta\n"
        f"• 🖼 JPG to PDF: {jpg2pdf_c} ta\n"
        f"• 📄 Word to PDF: {doc2pdf_c} ta\n"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_daily_stats")
async def show_daily_activity(callback: CallbackQuery) -> None:
    """Queries daily active statistics."""
    stats = await db.get_daily_activity()
    text = (
        "📆 **Oxirgi 24 soatlik faollik hisoboti**\n\n"
        f"• **Faol foydalanuvchilar soni:** {stats.get('active_users', 0)} ta\n"
        f"• **Bajarilgan amallar soni:** {stats.get('total_conversions', 0)} ta\n"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Requests the message content for broadcasting."""
    await state.set_state(AdminStates.waiting_for_broadcast_msg)
    await callback.message.edit_text(
        text=(
            "📢 **Reklama va xabarlar tarqatish tizimi**\n\n"
            "Iltimos, barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring. Xabarda rasm, video, formatlangan matn yoki tugmalar bo'lishi mumkin.\n"
            "Bot ushbu xabarni nusxalab, barcha foydalanuvchilarga yuboradi."
        ),
        reply_markup=get_cancel_keyboard("admin_broad"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_broadcast_msg)
async def execute_broadcast(message: Message, state: FSMContext, bot: Bot) -> None:
    """Copies and broadcasts the message to all users, handling block/deletion exceptions."""
    user_ids = await db.get_all_user_ids()
    total_users = len(user_ids)
    
    if total_users == 0:
        await message.answer("⚠️ Bazada xabar yuborish uchun foydalanuvchilar topilmadi.")
        await state.clear()
        return
        
    status_msg = await message.answer(f"📢 **{total_users}** ta foydalanuvchiga xabar yuborish boshlandi...")
    
    success_count = 0
    fail_count = 0
    
    for idx, user_id in enumerate(user_ids):
        try:
            # Copy original message structure (preserves photos/formatting/captions)
            await message.copy_to(chat_id=user_id)
            success_count += 1
        except Exception as e:
            logger.debug(f"Failed to send broadcast to user {user_id}: {e}")
            fail_count += 1
            
        # Update progress every 15 messages to avoid API spamming
        if (idx + 1) % 15 == 0 or idx == total_users - 1:
            try:
                await status_msg.edit_text(
                    f"📢 Xabar tarqatish davom etmoqda...\n"
                    f"Bajarildi: **{idx + 1}** / **{total_users}**\n"
                    f"✅ Muvaffaqiyatli: {success_count}\n"
                    f"❌ Xatolik bilan: {fail_count}"
                )
            except Exception:
                pass
        
        # Micro-sleep to respect Telegram API rate limits (30 messages per second)
        await asyncio.sleep(0.05)
        
    await status_msg.edit_text(
        text=(
            "📢 **Xabar yuborish yakunlandi!**\n\n"
            f"• **Foydalanuvchilar soni:** {total_users} ta\n"
            f"• **✅ Yetkazildi:** {success_count} ta\n"
            f"• **❌ Yetkazilmadi (bloklanganlar):** {fail_count} ta"
        ),
        parse_mode="Markdown"
    )
    await state.clear()

@router.callback_query(F.data == "admin_broad_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancels the broadcast process."""
    await state.clear()
    await callback.message.edit_text(
        text="❌ Xabar tarqatish bekor qilindi.",
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(F.data == "admin_close")
async def close_admin_panel(callback: CallbackQuery) -> None:
    """Closes the admin panel."""
    await callback.message.delete()

