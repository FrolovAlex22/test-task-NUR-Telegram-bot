from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


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
        "Добавить каналов": "add_channel",
        "Управление списком каналов": "list_channel",
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
