from aiogram import F, Bot, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import session_maker
from database.methods import (
    orm_add_channel,
    orm_delete_channel,
    orm_get_channels
)
from keyboards.inline import (
    BACK_TO_MAIN_MENU,
    CHANNEL_LIST_MENU,
    CHANNEL_MENU,
    CHANNEL_MENU_AFTER_ADD,
    get_callback_btns
)
from lexicon.lexicon import LEXICON_CHANNEL
from middlewares.db import DataBaseSession


channel_router = Router()

channel_router.message.middleware(
    DataBaseSession(session_pool=session_maker)
)
channel_router.callback_query.middleware(
    DataBaseSession(session_pool=session_maker)
)


class AddChannel(StatesGroup):
    """FSM для добавления каналов"""
    name = State()


@channel_router.callback_query(F.data == "channel_menu")
async def channel_menu(callback: CallbackQuery):
    """Переход в меню каналов"""
    await callback.answer()
    await callback.message.edit_text(
        LEXICON_CHANNEL["channel_start"],
        reply_markup=CHANNEL_MENU
    )


@channel_router.callback_query(F.data == "add_channel")
async def channel_add(callback: CallbackQuery, state: FSMContext):
    """Начало добавления канала"""
    await callback.message.edit_text(
        LEXICON_CHANNEL["add_channel_name"], reply_markup=BACK_TO_MAIN_MENU
    )
    await state.set_state(AddChannel.name)


@channel_router.message(StateFilter(AddChannel.name), ~F.text)
async def wrong_add_channel(message: Message):
    """Ошибка при добавлении канала"""
    await message.answer(
        LEXICON_CHANNEL["channel_name_error"],
        reply_markup=BACK_TO_MAIN_MENU
    )


@channel_router.message(StateFilter(AddChannel.name), F.text)
async def add_channel(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot
):
    """Добавление канала в БД"""
    if not message.text.startswith("@"):
        channel_text = message.text.split("/t.me/")
        channel_name = f"@{channel_text[-1]}"

    if message.text in [
        channel.name for channel in await orm_get_channels(session)
    ]:  # Проверка на существующий канал
        await message.answer(
            LEXICON_CHANNEL["channel_name_exist"],
            reply_markup=BACK_TO_MAIN_MENU
        )
        return

    try:  # Проверка на администратора
        await bot.get_chat_administrators(channel_name)
    except Exception:
        await message.answer(
            LEXICON_CHANNEL["channel_no_admin"],
            reply_markup=BACK_TO_MAIN_MENU
        )
        return

    await orm_add_channel(session, {"name": channel_name})
    await state.clear()
    text = f"Канал '{message.text}' {LEXICON_CHANNEL["channel_name_added"]}"
    await message.answer(
        text,
        reply_markup=CHANNEL_MENU_AFTER_ADD
    )


@channel_router.callback_query(F.data == "list_channel")
async def list_channel(callback: CallbackQuery, session: AsyncSession):
    """Список каналов"""
    await callback.answer()
    for channel in await orm_get_channels(session):
        await callback.message.answer(
            text=(
                f"<b>Название канала:</b> {channel.name}\n\n"
            ),
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"delete_channel_{channel.id}",
                }
            ),
        )

    await callback.message.answer(
        "Выше список каналов, которые вы добавили",
        reply_markup=CHANNEL_LIST_MENU
    )


@channel_router.callback_query(F.data.startswith("delete_channel_"))
async def delete_record_cb(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Удаляем канал"""
    channel_id = callback.data.split("_")[-1]
    await orm_delete_channel(session, int(channel_id))

    await callback.answer("Канал удален!")
    await callback.message.answer("Канал удален!")
