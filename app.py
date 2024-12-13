import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config.config import Config, load_config
from database.engine import create_db, drop_db
from handlers import channel_handlers, other_handlers, post_handlers
from middlewares.apscheduler_midleware import SchedulerMiddleware


config: Config = load_config()


bot = Bot(
    token=config.tg_bot.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


async def on_startup(bot):

    # run_param = True
    run_param = False
    if run_param:
        await drop_db()

    await create_db()


async def on_shutdown(bot):
    print('бот лег')


async def main():
    scheduler = AsyncIOScheduler(timezone="Asia/Yekaterinburg")
    scheduler.start()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(
        SchedulerMiddleware(scheduler=scheduler),
    )
    dp.include_router(channel_handlers.channel_router)
    dp.include_router(post_handlers.post_router)
    dp.include_router(other_handlers.other_router)
    await dp.start_polling(bot)

asyncio.run(main())
