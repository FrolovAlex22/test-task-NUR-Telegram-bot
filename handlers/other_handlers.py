from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter, or_f, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.inline import MAIN_MENU
from lexicon.lexicon import LEXICON_OTHER


other_router = Router()


@other_router.message(CommandStart())
async def start_cmd(message: Message):

    await message.answer(LEXICON_OTHER["hello"], reply_markup=MAIN_MENU)


@other_router.callback_query(F.data == "main_menu")
async def main_menu_cb(callback: CallbackQuery, state: FSMContext | None):
    if state:
        await state.clear()
    await callback.message.edit_text(
        LEXICON_OTHER["hello"],
        reply_markup=MAIN_MENU
    )


@other_router.message()
async def echo(message: Message):
    await message.answer(LEXICON_OTHER["other_answer"])
