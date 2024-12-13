from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import F, Bot, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import orm_get_channels
from database.engine import session_maker
from keyboards.inline import (
    BACK_TO_MAIN_MENU,
    POST_CHOISE_AFTER_ADD,
    ChannelstCallBack,
    get_callback_hour_or_minute_btns,
    get_channel_for_post_btns
)
from keyboards.my_calendar import CalendarMarkup
from lexicon.lexicon import LEXICON_POST
from middlewares.db import DataBaseSession


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


@post_router.callback_query(F.data == "add_post")
async def add_post(callback: CallbackQuery, state: FSMContext):
    """Начало добавления поста."""
    await callback.answer()
    await callback.message.answer(
        LEXICON_POST["add_post"],
        reply_markup=BACK_TO_MAIN_MENU
    )
    await state.set_state(AddPost.post)


@post_router.message(
    StateFilter(AddPost.post),
    F.content_type.in_({"photo", "video", "text", "video_note"})
)
async def post_choise_date(message: Message, state: FSMContext):
    """Сохранение данных о посте в FSM."""
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    await message.answer(
        LEXICON_POST["choise_date"],
        reply_markup=CalendarMarkup(current_month, current_year).build.kb
    )
    message_id = message.message_id
    chat_id = message.chat.id
    text = f"{chat_id}_{message_id}"

    await state.update_data(post=text)
    await state.set_state(AddPost.date)


@post_router.message(StateFilter(AddPost.post))
async def post_error(message: Message):
    """Ошибка при добавлении неправильного типа поста."""
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
    if "date" in mes:  # Добавление дня, месяца, года
        str_date = callback.data.split()[1]
        date = datetime.strptime(str_date, "%d.%m.%Y")
        var = date + timedelta(days=1)
        print(var)
        if var < datetime.now():  # Если выбрана прошедшая дата + месяц
            date_plus_month = date + relativedelta(months=+1)
            date_to_db = datetime.strftime(
                date_plus_month,
                "%d.%m.%Y"
            )
            await state.update_data(date=date_to_db)
        else:
            await state.update_data(date=str_date)

    if mes.startswith("hour"):  # Вывод клавиатуры с выбором минуты
        houre = mes.split("_")[1]
        new_date = f"{state_info["date"]} {houre}"
        await state.update_data(date=new_date)
        await callback.message.edit_text(
            LEXICON_POST["choise_minute"],
            reply_markup=get_callback_hour_or_minute_btns(type_time="minute")
        )
    elif mes.startswith("minute"):  # Формирование клавиатуры с каналами.
        minute = mes.split("_")[1]
        new_date = f"{state_info["date"]}:{minute}"
        dt = datetime.strptime(new_date, "%d.%m.%Y %H:%M")
        if dt < datetime.now():
            print(dt)
            await callback.message.delete()
            await state.update_data(date=None)
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            await callback.message.answer(
                LEXICON_POST["choise_date_error"],
                reply_markup=CalendarMarkup(
                    current_month, current_year
                ).build.kb
            )
            return
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
    else:  # Вывод клавиатуры с выбором часа
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
    """Изменение клавиатуры перед добавлением поста. Вывод обновленного списка
    каналов с учетом изменений в статусе отправки.
    """
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
        LEXICON_POST["channel_list_to_post"],
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
    """Пересылка сообщения в выбранные каналы."""
    flag = False
    post_list = [
        post for post in callback_data.channel_name.split(" ") if post != ""
    ]
    for post in post_list:  # Проверка на наличие выбранных каналов
        if post.split("/")[-1] != "0":
            flag = True
    if not flag:
        await callback.message.edit_text(
            LEXICON_POST["post_choise_add_clear_list"],
            reply_markup=callback.message.reply_markup
        )
        return

    data = await state.get_data()  # Данные состояния для пересылки сообщения
    from_chat_id = data["post"].split("_")[0]
    from_message_id = data["post"].split("_")[1]

    clear_post_list = [
        post.split("/")[0] for post in post_list
        if post.split("/")[-1] == "1"
    ]  # Формируем список каналов для пересылки
    text_to_message = f"Рассылка создана\nДата: {data['date']}\nКаналы:\n"
    for channel in clear_post_list:
        text_to_message += f"{channel}\n"

    dt = datetime.strptime(data["date"], "%d.%m.%Y %H:%M")  # Формируем дату

    post_info = await bot.forward_message(
        chat_id=callback.from_user.id,
        from_chat_id=from_chat_id,
        message_id=from_message_id
    )  # Получаем информацию о посте

    # В зависимости от типа поста(фото; текст; видео) формируем отложенную отправку
    if post_info.content_type == "photo":
        photo_id = post_info.photo[0].file_id
        text_for_photo = post_info.caption

        for channel in clear_post_list:
            if text_for_photo is None:
                apscheduler.add_job(
                    bot.send_photo,
                    trigger="date",
                    run_date=dt,
                    kwargs={
                        "chat_id": channel,
                        "photo": photo_id,
                    }
                )
            else:
                text = f"{text_for_photo} {channel}"
                apscheduler.add_job(
                    bot.send_photo,
                    trigger="date",
                    run_date=dt,
                    kwargs={
                        "chat_id": channel,
                        "photo": photo_id,
                        "caption": text,
                    }
                )
    elif post_info.content_type == "text":
        text_for_message = post_info.text

        for channel in clear_post_list:
            text_to_post = f"{text_for_message} {channel}"
            apscheduler.add_job(
                bot.send_message,
                trigger="date",
                run_date=dt,
                kwargs={
                    "chat_id": channel,
                    "text": text_to_post
                }
            )
    elif post_info.content_type == "video":
        video_id = post_info.video.file_id
        text_for_video = post_info.caption

        if text_for_video is None:
            for channel in clear_post_list:
                apscheduler.add_job(
                    bot.send_video,
                    trigger="date",
                    run_date=dt,
                    kwargs={
                        "chat_id": channel,
                        "video": video_id,
                    }
                )
        else:
            for channel in clear_post_list:
                text_to_post = f"{text_for_video} {channel}"
                apscheduler.add_job(
                    bot.send_video,
                    trigger="date",
                    run_date=dt,
                    kwargs={
                        "chat_id": channel,
                        "video": video_id,
                        "caption": text_to_post
                    }
                )
    elif post_info.content_type == "video_note":
        video_note_id = post_info.video_note.file_id
        for channel in clear_post_list:
            apscheduler.add_job(
                bot.send_video_note,
                trigger="date",
                run_date=dt,
                kwargs={
                    "chat_id": channel,
                    "video_note": video_note_id
                }
            )
    await post_info.delete()

    await callback.message.edit_text(
        text_to_message,
        reply_markup=POST_CHOISE_AFTER_ADD
    )
    await state.clear()
