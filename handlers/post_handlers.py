from datetime import datetime
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.inline import BACK_TO_MAIN_MENU, POST_CHOISE_ADD_OR_NOT, POST_CHOISE_AFTER_ADD, POST_MENU
from keyboards.my_calendar import CalendarMarkup
from lexicon.lexicon import LEXICON_POST


post_router = Router()


class AddPost(StatesGroup):
    """FSM для добавления постов."""
    post = State()
    date = State()


@post_router.callback_query(F.data == "post_menu")
async def post_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        LEXICON_POST["post_start"],
        reply_markup=POST_MENU
    )


@post_router.callback_query(F.data == "add_post")
async def add_post(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        LEXICON_POST["add_post"],
        reply_markup=BACK_TO_MAIN_MENU
    )
    await state.set_state(AddPost.post)


@post_router.message(
    StateFilter(AddPost.post),
    F.content_type.in_({"photo", "video", "text" , "video_note"})
)
async def post_coise_date(message: Message, state: FSMContext):
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    await message.answer(
        LEXICON_POST["coise_date"],
        reply_markup=CalendarMarkup(current_month, current_year).build.kb
    )
    await state.set_state(AddPost.date)


@post_router.message(StateFilter(AddPost.post))
async def post_error(message: Message):
    await message.answer(
        LEXICON_POST["post_error"],
        reply_markup=BACK_TO_MAIN_MENU
    )



@post_router.callback_query(
        StateFilter(AddPost.date),
        F.data == "created_post"
    )
async def add_post(callback: CallbackQuery, state: FSMContext):
    print("Yes")
    data = await state.get_data()
    text = f"{LEXICON_POST["created_post_message"]}\nДата: {data['date']}"
    await callback.message.edit_text(
        text,
        reply_markup=POST_CHOISE_AFTER_ADD
    )
    await state.clear()


@post_router.callback_query(StateFilter(AddPost.date))
async def post_add_date(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()
    mes = callback.data
    if "date" in mes:
        str_date = callback.data.split()[1]
        date = datetime.strptime(str_date, '%d.%m.%Y')
        if date < datetime.now():
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            await callback.message.edit_text(
                "Дата должна быть в будущем",
                reply_markup=CalendarMarkup(
                    current_month, current_year
                ).build.kb
            )
            return
        await callback.message.answer(
            f"Теперь выберите каналы для публикации",
            reply_markup=BACK_TO_MAIN_MENU
        )
        text = f"{LEXICON_POST["created_post_choise"]}{str_date}"
        await callback.message.answer(
            text,
            reply_markup=POST_CHOISE_ADD_OR_NOT
        )
        await state.update_data(date=str_date)
    elif "back" in mes or "next" in mes:
        await get_next_anither_month(callback)
        # return
    # text = f"{LEXICON_POST["created_post_choise"]}{str_date}"
    # await callback.message.answer(
    #     text,
    #     reply_markup=POST_CHOISE_ADD_OR_NOT
    # )


@post_router.callback_query(F.data == "created_post")
async def add_post(callback: CallbackQuery, state: FSMContext):
    print("Yes")
    data = await state.get_data()
    text = f"{LEXICON_POST["created_post_message"]}\nДата: {data['date']}"
    await callback.message.edit_text(
        text,
        reply_markup=POST_CHOISE_AFTER_ADD
    )
    await state.clear()


async def get_next_anither_month(callback: CallbackQuery) -> None:
    """Смена месяца на клавиатуре"""
    month, year = map(int, callback.data.split()[1].split("."))
    calendar = CalendarMarkup(month, year)
    if "next" in callback.data:
        await callback.message.edit_reply_markup(
            reply_markup=calendar.next_month().kb
        )
    elif "back" in callback.data:
        await callback.message.edit_reply_markup(
            reply_markup=calendar.previous_month().kb
        )
