from aiogram import Bot
from aiogram import types


async def send_message_in_time(
        bot: Bot, chat_id: int | str, from_chat_id: int, message_id: int
    ) -> None:
    await bot.forward_message(
        chat_id=chat_id,
        from_chat_id=from_chat_id,
        message_id=message_id
    )
