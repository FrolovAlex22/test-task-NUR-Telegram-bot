from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.inline import BACK_TO_MAIN_MENU, CHANNEL_MENU, CHANNEL_MENU_AFTER_ADD
from lexicon.lexicon import LEXICON_CHANNEL


channel_router = Router()


class AddChannel(StatesGroup):
    """FSM для добавления каналов"""
    name = State()


@channel_router.callback_query(F.data == "channel_menu")
async def channel_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        LEXICON_CHANNEL["channel_start"],
        reply_markup=CHANNEL_MENU
    )


@channel_router.callback_query(F.data == "add_channel")
async def channel_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        LEXICON_CHANNEL["add_channel_name"], reply_markup=BACK_TO_MAIN_MENU
    )
    await state.set_state(AddChannel.name)


@channel_router.message(StateFilter(AddChannel.name), ~F.text)
async def wrong_add_channel(message: Message, state: FSMContext):
    await message.answer(
        LEXICON_CHANNEL["channel_name_error"],
        reply_markup=BACK_TO_MAIN_MENU
    )


@channel_router.message(StateFilter(AddChannel.name), F.text)
async def add_channel(message: Message, state: FSMContext):
    # тут сохраняем канал
    await state.clear()
    text = f"Канал '{message.text}' {LEXICON_CHANNEL["channel_name_added"]}"
    await message.answer(
        text,
        reply_markup=CHANNEL_MENU_AFTER_ADD
    )


@channel_router.callback_query(F.data == "list_channel")
async def channel_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Тут список каналов",
        reply_markup=BACK_TO_MAIN_MENU
    )
