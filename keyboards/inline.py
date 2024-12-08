from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ChannelstCallBack(CallbackData, prefix="user_chanels"):
    channel_name: str | None = None
    title: str | None = None


def get_callback_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)
) -> InlineKeyboardBuilder:

    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():

        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

# MAIN MENU
MAIN_MENU = get_callback_btns(
    btns={
        "Меню постов": "post_menu",
        "Меню каналов": "channel_menu",
    },
    sizes=(2, ),
)


BACK_TO_MAIN_MENU = get_callback_btns(
    btns={
        "Отменить и вернуться в главное меню": "main_menu",
    },
    sizes=(2, ),
)

# CHANNEL
CHANNEL_MENU = get_callback_btns(
    btns={
        "Добавить канал": "add_channel",
        "Управление списком каналов": "list_channel",
    },
    sizes=(2, ),
)


CHANNEL_LIST_MENU = get_callback_btns(
    btns={
        "Добавить канал": "add_channel",
        "Управление списком каналов": "list_channel",
        "Главное меню": "main_menu",
    },
    sizes=(2, ),
)


CHANNEL_MENU_AFTER_ADD = get_callback_btns(
    btns={
        "Добавить следующий канал": "add_channel",
        "Список каналов": "list_channel",
        "Главное меню": "main_menu",
    },
    sizes=(2, ),
)

# POST
POST_MENU = get_callback_btns(
    btns={
        "Добавить пост": "add_post",
        "Управление списком постов": "list_post",
    },
    sizes=(2, ),
)


POST_CHOISE_ADD_OR_NOT = get_callback_btns(
    btns={
        "Далее": "created_post",
        "Отменить рассылку": "main_menu",
    },
    sizes=(2, ),
)


POST_CHOISE_AFTER_ADD = get_callback_btns(
    btns={
        "Создать рассылку": "add_post",
        "Главное меню": "main_menu",
    },
    sizes=(2, ),
)


def get_channel_for_post_btns(
    *,
    channel_btns_str: str,
    sizes: tuple[int] = (1, )
    # sizes: list[str] = (1, ),
):
    keyboard = InlineKeyboardBuilder()

    # keyboard.adjust(*sizes)
    row = []
    for text_in_list in channel_btns_str.split(" "):
        text = text_in_list.split("/")
        # text_var = None
        if len(text) == 1:
            continue
        #     text_var = text[0]
        # else:
        if text[-1] == "0":
            text_status = ""
        elif text[-1] == "1":
            text_status = " ✅"
        elif text[-1] == "2":
            text_status = " ❌"
        new_text = f"{text[0]}{text_status}"
        text_channel = text[0]
        row.append(InlineKeyboardButton(
            text=new_text,
            callback_data=ChannelstCallBack(
                channel_name=channel_btns_str,
                title = text_channel
            ).pack()))
    row.append(InlineKeyboardButton(
        text="Далее",
        callback_data=ChannelstCallBack(
            channel_name=channel_btns_str,
            title="completed"
        ).pack()))
    row.append(InlineKeyboardButton(
        text="Вернуться в главное меню",
        callback_data="main_menu")
    )

    # keyboard.add(InlineKeyboardButton(text="Вернуться в главное меню", callback_data="main_menu"))

    return keyboard.row(*row).adjust(*sizes).as_markup()