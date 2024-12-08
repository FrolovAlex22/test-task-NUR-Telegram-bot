from datetime import datetime
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import orm_get_channels
from keyboards.inline import BACK_TO_MAIN_MENU, POST_CHOISE_ADD_OR_NOT, POST_CHOISE_AFTER_ADD, POST_MENU, ChannelstCallBack, get_callback_btns, get_channel_for_post_btns
from keyboards.my_calendar import CalendarMarkup
from lexicon.lexicon import LEXICON_POST
from middlewares.db import DataBaseSession
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


class ChannelsForSendingPost(StatesGroup):
    """FSM для добавления постов."""
    channel_1 = State()


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
    data = await state.get_data()
    text = f"{LEXICON_POST["created_post_message"]}\nДата: {data['date']}"
    await callback.message.edit_text(
        text,
        reply_markup=POST_CHOISE_AFTER_ADD
    )
    await state.clear()


@post_router.callback_query(StateFilter(AddPost.date), F.data != "main_menu")
async def post_add_date(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    post_list = ""
    for channel in await orm_get_channels(session):
        post_list += f"{channel.name}/0 "
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
        await state.update_data(date=str_date)
        await state.set_state(AddPost.channel_list)
        await callback.message.answer(
            text=LEXICON_POST["channel_list_to_post"],
            reply_markup=get_channel_for_post_btns(channel_btns_str=post_list),
        )

        # await callback.message.answer(
        #     "Теперь выберите каналы для публикации",
        #     reply_markup=BACK_TO_MAIN_MENU
        # )
        # text = f"{LEXICON_POST["channel_list_to_post"]}{str_date}"
        # await callback.message.answer(
        #     text,
        #     reply_markup=POST_CHOISE_ADD_OR_NOT
        # )
        await state.update_data(date=str_date)
    elif "back" in mes or "next" in mes:
        await get_next_anither_month(callback)
        # return
    # text = f"{LEXICON_POST["created_post_choise"]}{str_date}"
    # await callback.message.answer(
    #     text,
    #     reply_markup=POST_CHOISE_ADD_OR_NOT
    # )


@post_router.callback_query(
        StateFilter(AddPost.channel_list),
        ChannelstCallBack.filter(F.title == "completed")
    )
@post_router.callback_query(F.data == "created_post")
async def add_post(
    callback: CallbackQuery,
    callback_data: ChannelstCallBack,
    state: FSMContext
):
    post_list = [post for post in callback_data.channel_name.split(" ")]
    data = await state.get_data()

    text = f"Рассылка создана\nДата: {data['date']}\nКаналы: {post_list}"
    await callback.message.edit_text(
        text,
        reply_markup=POST_CHOISE_AFTER_ADD
    )
    await state.clear()


@post_router.callback_query(
        StateFilter(AddPost.channel_list),
        ChannelstCallBack.filter()
    )
async def change_in_material_quantity(
    callback: CallbackQuery,
    callback_data: ChannelstCallBack,
    state: FSMContext
    # session: AsyncSession
) -> None:
    """Изменение количества материала"""
    channel_list_after = ""
    channel_list = callback_data.channel_name.split(" ")
    channel_name = callback_data.title.split(":")[-1]
    # channel_name = callback.data.split(":")[-1]
    print(channel_list)
    print(channel_name)
    print("_____________________________________")

    await callback.answer()
    for channel in channel_list:
        # channel_text = channel.split("/")[0]
        if channel == "":
            continue
        print(channel+"|||")
        # print(channel[-1])
        print(channel[:-2])
        print(channel+"****")
        if channel[:-2] == channel_name:
            if channel[-1] == "1":
                new_channel = f"{channel[:-1]}2"
            elif channel[-1] == "2" or channel[-1] == "0":
                new_channel = f"{channel[:-1]}1"
            # else:
            #     new_channel = f"{channel}/0"
            print(new_channel)
            channel_list_after += f"{new_channel} "


        else:
            channel_list_after += f"{channel} "
        print(channel_list_after)
        # print(channel_name["user_chanels"])
        # if len(channel_text) >= 1:
        #     status = channel_text[-1]
        #     if channel_text[0] == channel_name:
        #         if status == "✅":
        #             channel_list_after += f" {channel_text}/❌"
        #         else:
        #             channel_list_after += f" {channel_text}/✅"
        #         print("1")
        #     elif channel == channel_name:
        #         channel_list_after += f" {channel}/✅"
        #         print("2")
        #     else:
        #         channel_list_after += f" {channel}"
        #         print("3")
    # if state_list != "":
    #     await state.update_data(channel_list=state_list)
    await callback.message.delete()
    await callback.message.answer(
        text="Теперь выберите каналы для публикации",
        reply_markup=get_channel_for_post_btns(
            channel_btns_str=channel_list_after
        )
    )



    # if callback_data.action == "minus_material":
    #     if callback_data.quantity_material == 1:
    #         await callback.answer(text="Минимальное количество 1")
    #         return

    # if callback_data.action == "plus_material":
    #     new_quantity = callback_data.quantity_material + 1
    # else:
    #     new_quantity = callback_data.quantity_material - 1

    # try:
    #     await material_fix_quantity(
    #         session,
    #         callback_data.material_id,
    #         new_quantity=new_quantity
    #     )
    # except Exception as ex:
    #     await callback.answer("Произошла ошибка")
    #     print(ex)
    #     return

    # await callback.message.edit_text(
    #     text=(
    #         f"<b>Название:</b> {callback_data.title}\n\n"
    #         f"<b>Описание:</b> {callback_data.description}\n"
    #         f"<b>Цена:</b> {callback_data.price}\n"
    #         f"<b>Количество:</b> {new_quantity}\n"
    #     ),
    #     reply_markup=get_callback_btns(
    #         btns={
    #             "Убавить -1": MaterialCallBack(
    #                 action="minus_material",
    #                 material_id=callback_data.material_id,
    #                 title=callback_data.title,
    #                 description=callback_data.description,
    #                 price=callback_data.price,
    #                 quantity_material=new_quantity,
    #                 packing=callback_data.packing
    #             ).pack(),
    #             "Прибавить +1": MaterialCallBack(
    #                 action="plus_material",
    #                 material_id=callback_data.material_id,
    #                 title=callback_data.title,
    #                 description=callback_data.description,
    #                 price=callback_data.price,
    #                 quantity_material=new_quantity,
    #                 packing=callback_data.packing
    #             ).pack(),
    #             "Удалить": f"delete_material_{callback_data.material_id}",
    #             "Изменить": f"change_material_{callback_data.material_id}",
    #         }
    #     ),
    # )


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
