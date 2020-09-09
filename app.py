async def on_startup(dp):
    import filters
    import middlewares
    filters.setup(dp)
    middlewares.setup(dp)

    from utils.notify_admins import on_startup_notify
    await on_startup_notify(dp)


if __name__ == '__main__':
    from aiogram import executor
    from handlers import dp
    from utils.task import scheduled_task

    dp.loop.create_task(scheduled_task(60))
    executor.start_polling(dp, on_startup=on_startup)
