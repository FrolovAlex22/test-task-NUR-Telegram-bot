from datetime import datetime, timedelta
from aiogram import F, Bot, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import orm_get_channels
from handlers.handlers_methods import send_message_in_time
from keyboards.inline import BACK_TO_MAIN_MENU, POST_CHOISE_ADD_OR_NOT, POST_CHOISE_AFTER_ADD, POST_MENU, ChannelstCallBack, get_callback_btns, get_callback_hour_or_minute_btns, get_channel_for_post_btns
from keyboards.my_calendar import CalendarMarkup
from lexicon.lexicon import LEXICON_POST
from middlewares.db import DataBaseSession
from middlewares.apscheduler_midleware import SchedulerMiddleware
from database.engine import session_maker


post_router = Router()

post_router.message.middleware(
    DataBaseSession(session_pool=session_maker)
)

post_router.callback_query.middleware(
    DataBaseSession(session_pool=session_maker)
)


class AddPost(StatesGroup):
    """FSM для добавления постов."""
    post = State()
    date = State()
    channel_list = State()


@post_router.callback_query(F.data == "post_menu")
async def post_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        LEXICON_POST["post_start"],
        reply_markup=POST_MENU
    )


@post_router.callback_query(F.data == "add_post")
async def add_post(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        LEXICON_POST["add_post"],
        reply_markup=BACK_TO_MAIN_MENU
    )
    await state.set_state(AddPost.post)


@post_router.message(
    StateFilter(AddPost.post),
    F.content_type.in_({"photo", "video", "text" , "video_note"})
)
async def post_choise_date(message: Message, state: FSMContext):
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    await message.answer(
        LEXICON_POST["coise_date"],
        reply_markup=CalendarMarkup(current_month, current_year).build.kb
    )
    message_id = message.message_id
    chat_id = message.chat.id
    text = f"{chat_id}_{message_id}"

    await state.update_data(post=text)
    await state.set_state(AddPost.date)


@post_router.message(StateFilter(AddPost.post))
async def post_error(message: Message):
    await message.answer(
        LEXICON_POST["post_error"],
        reply_markup=BACK_TO_MAIN_MENU
    )


@post_router.callback_query(StateFilter(AddPost.date), F.data != "main_menu")
async def post_add_date(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Поэтапное добавление времени, формирование даты публикации."""

    await callback.answer()
    mes = callback.data
    state_info = await state.get_data()
    if "date" in mes: # Добавление дня, месяца, года
        str_date = callback.data.split()[1]
        date = datetime.strptime(str_date, "%d.%m.%Y")
        var = date + timedelta(days=1)
        print(var)
        if var < datetime.now(): # Если выбрана прошедшая дата + месяц
            date_plus_month = date + relativedelta(months=+1)
            date_to_db = datetime.strftime(
                date_plus_month,
                "%d.%m.%Y"
            )
            await state.update_data(date=date_to_db)
        else:
            await state.update_data(date=str_date)

    if mes.startswith("hour"): # Вывод клавиатуры с выбором минуты
        houre = mes.split("_")[1]
        new_date = f"{state_info["date"]} {houre}"
        await state.update_data(date=new_date)
        await callback.message.edit_text(
            LEXICON_POST["choise_minute"],
            reply_markup=get_callback_hour_or_minute_btns(type_time="minute")
        )
    elif mes.startswith("minute"): # Формирование клавиатуры с каналами.
        minute = mes.split("_")[1]
        new_date = f"{state_info["date"]}:{minute}"
        await state.update_data(date=new_date)
        await state.set_state(AddPost.channel_list)
        await callback.message.delete()

        post_list = ""
        for channel in await orm_get_channels(session):
            post_list += f"{channel.name}/0 "
        await callback.message.answer(
            text=LEXICON_POST["channel_list_to_post"],
            reply_markup=get_channel_for_post_btns(channel_btns_str=post_list),
        )
    else: # Вывод клавиатуры с выбором часа
        await callback.message.edit_text(
            LEXICON_POST["choise_hour"],
            reply_markup=get_callback_hour_or_minute_btns(type_time="hour")
        )


@post_router.callback_query(
        StateFilter(AddPost.channel_list),
        ChannelstCallBack.filter(F.title != "completed")
    )
async def change_kb_post_before_add(
    callback: CallbackQuery,
    callback_data: ChannelstCallBack,
    state: FSMContext
) -> None:
    channel_list_after = ""
    channel_list = callback_data.channel_name.split(" ")
    channel_name = callback_data.title.split(":")[-1]

    await callback.answer()
    for channel in channel_list:
        if channel == "":
            continue
        if channel[:-2] == channel_name:
            if channel[-1] == "1":
                new_channel = f"{channel[:-1]}2"
            elif channel[-1] == "2" or channel[-1] == "0":
                new_channel = f"{channel[:-1]}1"
            channel_list_after += f"{new_channel} "
        else:
            channel_list_after += f"{channel} "

    await callback.message.delete()
    await callback.message.answer(
        text="Теперь выберите каналы для публикации",
        reply_markup=get_channel_for_post_btns(
            channel_btns_str=channel_list_after
        )
    )


@post_router.callback_query(
        StateFilter(AddPost.channel_list),
        ChannelstCallBack.filter(F.title == "completed")
    )
async def message_after_add_post(
    callback: CallbackQuery,
    callback_data: ChannelstCallBack,
    bot: Bot,
    state: FSMContext,
    apscheduler: AsyncIOScheduler,
):
    flag = False
    post_list = [
        post for post in callback_data.channel_name.split(" ") if post != ""
    ]
    for post in post_list: # Проверка на наличие выбранных каналов
        if post.split("/")[-1] != "0":
            flag = True
    if not flag:
        await callback.message.edit_text(
            LEXICON_POST["post_choise_add_clear_list"],
            reply_markup=callback.message.reply_markup
        )
        return

    data = await state.get_data() # Данные из состояния для пересылки сообщения
    from_chat_id = data["post"].split("_")[0]
    from_message_id = data["post"].split("_")[1]

    clear_post_list = [
        post.split("/")[0] for post in post_list
        if post.split("/")[-1] == "1"
    ] # Список каналов для пересылки
    text = f"Рассылка создана\nДата: {data['date']}\nКаналы: "
    for channel in clear_post_list:
        text += f"{channel}\n"

    dt = datetime.strptime(data["date"], "%d.%m.%Y %H:%M") # Формируем дату

    for channel in clear_post_list:
        apscheduler.add_job(
            send_message_in_time,
            trigger="date",
            run_date=dt,
            kwargs={
                "bot": bot,
                "chat_id": channel,
                "from_chat_id": from_chat_id,
                "message_id": from_message_id
            }
        ) # Создание отложенных рассылок

    await callback.message.edit_text(
        text,
        reply_markup=POST_CHOISE_AFTER_ADD
    )
    await state.clear()
